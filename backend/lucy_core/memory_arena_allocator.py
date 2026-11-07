r"""
backend/lucy_core/memory_arena_allocator.py
Stage 148: Zero-Copy Memory Arena & Memory Pool Allocator
Era 15: Autonomous Self-Hosting Compiler & Multi-Tier Optimization Pipeline

100% offline, zero-copy memory management, linear bump arena, segregated
free-list slab pooling, string interning, and canary boundary sentinels for Lucy OS:
1. Bump Arena Allocator (BumpArena):
   - Fast contiguous O(1) linear allocation with user-defined alignment (8/16/32/64 bytes).
   - O(1) bulk reset capability for fast compiler passes and AST/IR phases.
   - Sentinel canary protection (0xDEADBEEF) guarding against buffer overflows.
2. Segregated Free-List Object Pool (ObjectPool):
   - Power-of-two slab buckets (32B, 64B, 128B, 256B, 512B, 1024B, 4096B).
   - O(1) allocation and O(1) deallocation with free-list recycling.
   - Automatic slab chunk growth upon bucket exhaustion.
3. Zero-Copy Memory Slice (MemorySlice):
   - Backed by zero-copy memoryview and contiguous buffers.
   - Safe in-place read/write, slicing, and SHA-256 fingerprinting.
4. Sovereign Symbol & String Interner:
   - High-throughput string deduplication mapping names to immutable arena slices.
5. Strict CP1252-Safe ASCII Presentation:
   - /arena-status / /pool-status / /mem-stats
   - /arena-reset [arena_name]
   - /mem-audit
"""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
import os
import struct
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

STAGE: int = 148
STAGE_NAME: str = "Zero-Copy Memory Arena & Memory Pool Allocator"
ERA: int = 15
CREATOR: str = "Senin"
OPERATOR: str = "Senin Ali K P"
HMAC_SECRET: bytes = b"senin-lucy-sovereign-arena-secret-2026"
CANARY_MAGIC: bytes = b"\xde\xad\xbe\xef"


class MemoryCorruptionError(RuntimeError):
    """Raised when memory guard canaries or boundaries are violated."""
    pass


class OutOfMemoryError(RuntimeError):
    """Raised when an arena or pool exceeds its designated capacity."""
    pass


@dataclasses.dataclass
class MemorySlice:
    """
    Zero-copy slice wrapper over a backing buffer.
    """
    buffer: bytearray
    offset: int
    size: int
    owner_id: str
    canary_offset: Optional[int] = None

    def __post_init__(self) -> None:
        self._view = memoryview(self.buffer)[self.offset : self.offset + self.size]

    @property
    def view(self) -> memoryview:
        return self._view

    def to_bytes(self) -> bytes:
        return bytes(self._view)

    def write(self, data: bytes, target_offset: int = 0) -> int:
        if target_offset + len(data) > self.size:
            raise ValueError(
                f"Write exceeds slice boundary: offset={target_offset}, len={len(data)}, size={self.size}"
            )
        self.buffer[self.offset + target_offset : self.offset + target_offset + len(data)] = data
        return len(data)

    def read(self, read_offset: int = 0, read_len: Optional[int] = None) -> bytes:
        if read_len is None:
            read_len = self.size - read_offset
        if read_offset + read_len > self.size:
            raise ValueError("Read exceeds slice boundary")
        return bytes(self.buffer[self.offset + read_offset : self.offset + read_offset + read_len])

    def sha256(self) -> str:
        return hashlib.sha256(self._view).hexdigest()

    def __len__(self) -> int:
        return self.size


class BumpArena:
    """
    Contiguous O(1) Bump Pointer Arena Allocator.
    Ideal for compiler passes, AST transformations, and IR emission cycles.
    """

    def __init__(
        self,
        name: str = "default_arena",
        capacity_bytes: int = 4 * 1024 * 1024,  # 4 MB
        enable_canaries: bool = True,
    ) -> None:
        self.name = name
        self.capacity = capacity_bytes
        self.enable_canaries = enable_canaries
        self.buffer = bytearray(self.capacity)
        self.offset = 0
        self.allocated_count = 0
        self.peak_offset = 0
        self.canary_locations: List[int] = []
        self._lock = threading.RLock()

    @staticmethod
    def _align(val: int, alignment: int) -> int:
        return (val + alignment - 1) & ~(alignment - 1)

    def allocate(self, size_bytes: int, alignment: int = 8) -> MemorySlice:
        with self._lock:
            aligned_offset = self._align(self.offset, alignment)
            extra_canary = len(CANARY_MAGIC) if self.enable_canaries else 0
            required_space = aligned_offset + size_bytes + extra_canary

            if required_space > self.capacity:
                raise OutOfMemoryError(
                    f"Arena '{self.name}' capacity exceeded: required={required_space}, capacity={self.capacity}"
                )

            slice_offset = aligned_offset
            canary_offset = None

            if self.enable_canaries:
                c_pos = slice_offset + size_bytes
                self.buffer[c_pos : c_pos + len(CANARY_MAGIC)] = CANARY_MAGIC
                self.canary_locations.append(c_pos)
                canary_offset = c_pos

            self.offset = required_space
            self.allocated_count += 1
            if self.offset > self.peak_offset:
                self.peak_offset = self.offset

            return MemorySlice(
                buffer=self.buffer,
                offset=slice_offset,
                size=size_bytes,
                owner_id=self.name,
                canary_offset=canary_offset,
            )

    def reset(self) -> None:
        """O(1) arena wipe without reallocating underlying buffer."""
        with self._lock:
            self.offset = 0
            self.allocated_count = 0
            self.canary_locations.clear()

    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """Verifies that all canary sentinels remain uncorrupted."""
        with self._lock:
            violations: List[str] = []
            for c_pos in self.canary_locations:
                val = bytes(self.buffer[c_pos : c_pos + len(CANARY_MAGIC)])
                if val != CANARY_MAGIC:
                    violations.append(
                        f"Canary corruption at offset {c_pos}: expected {CANARY_MAGIC.hex()}, found {val.hex()}"
                    )
            return (len(violations) == 0, violations)

    def status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "capacity_bytes": self.capacity,
            "allocated_bytes": self.offset,
            "available_bytes": self.capacity - self.offset,
            "peak_offset": self.peak_offset,
            "allocation_count": self.allocated_count,
            "utilization_pct": round((self.offset / self.capacity) * 100, 2),
        }


class ObjectPool:
    """
    Segregated Free-List Slab Allocator for uniform object sizes:
    Buckets: 32B, 64B, 128B, 256B, 512B, 1024B, 4096B.
    """

    SUPPORTED_SIZES = (32, 64, 128, 256, 512, 1024, 4096)

    def __init__(self, name: str = "default_pool", slab_chunk_count: int = 128) -> None:
        self.name = name
        self.slab_chunk_count = slab_chunk_count
        self._lock = threading.RLock()

        # Free lists per bucket: bucket_size -> list of (slab_idx, block_idx)
        self.free_lists: Dict[int, List[Tuple[int, int]]] = {s: [] for s in self.SUPPORTED_SIZES}
        # Slabs per bucket: bucket_size -> list of bytearray slabs
        self.slabs: Dict[int, List[bytearray]] = {s: [] for s in self.SUPPORTED_SIZES}

        # Stats
        self.total_allocations: int = 0
        self.total_frees: int = 0
        self.active_allocations: int = 0

    def _select_bucket(self, size_bytes: int) -> int:
        for s in self.SUPPORTED_SIZES:
            if size_bytes <= s:
                return s
        raise ValueError(
            f"Requested size {size_bytes} exceeds max supported pool block size ({self.SUPPORTED_SIZES[-1]} bytes)"
        )

    def _expand_slab(self, bucket_size: int) -> None:
        slab_size = bucket_size * self.slab_chunk_count
        new_slab = bytearray(slab_size)
        slab_idx = len(self.slabs[bucket_size])
        self.slabs[bucket_size].append(new_slab)

        # Populate free-list for this new slab
        for i in range(self.slab_chunk_count):
            self.free_lists[bucket_size].append((slab_idx, i))

    def allocate(self, size_bytes: int) -> MemorySlice:
        with self._lock:
            bucket = self._select_bucket(size_bytes)
            if not self.free_lists[bucket]:
                self._expand_slab(bucket)

            slab_idx, block_idx = self.free_lists[bucket].pop()
            slab_buf = self.slabs[bucket][slab_idx]
            offset = block_idx * bucket

            self.total_allocations += 1
            self.active_allocations += 1

            return MemorySlice(
                buffer=slab_buf,
                offset=offset,
                size=size_bytes,
                owner_id=f"{self.name}:bucket_{bucket}:slab_{slab_idx}:block_{block_idx}",
            )

    def deallocate(self, mem_slice: MemorySlice) -> None:
        with self._lock:
            parts = mem_slice.owner_id.split(":")
            if len(parts) < 4 or parts[0] != self.name:
                raise ValueError("Cannot free slice not owned by this pool")

            bucket = int(parts[1].split("_")[1])
            slab_idx = int(parts[2].split("_")[1])
            block_idx = int(parts[3].split("_")[1])

            # Zero-out the block memory for hygiene
            slab_buf = self.slabs[bucket][slab_idx]
            offset = block_idx * bucket
            slab_buf[offset : offset + bucket] = b"\x00" * bucket

            self.free_lists[bucket].append((slab_idx, block_idx))
            self.total_frees += 1
            self.active_allocations -= 1

    def status(self) -> Dict[str, Any]:
        with self._lock:
            bucket_stats = {}
            total_bytes = 0
            for b in self.SUPPORTED_SIZES:
                slabs_count = len(self.slabs[b])
                free_blocks = len(self.free_lists[b])
                total_blocks = slabs_count * self.slab_chunk_count
                used_blocks = total_blocks - free_blocks
                slab_bytes = slabs_count * self.slab_chunk_count * b
                total_bytes += slab_bytes
                bucket_stats[f"{b}B"] = {
                    "slabs": slabs_count,
                    "total_blocks": total_blocks,
                    "used_blocks": used_blocks,
                    "free_blocks": free_blocks,
                    "allocated_bytes": slab_bytes,
                }
            return {
                "name": self.name,
                "total_resident_bytes": total_bytes,
                "active_allocations": self.active_allocations,
                "total_allocations": self.total_allocations,
                "total_frees": self.total_frees,
                "buckets": bucket_stats,
            }


class StringInterner:
    """
    Sovereign Symbol & String Interning Engine.
    Guarantees unique strings share identical underlying arena slices and integer IDs.
    """

    def __init__(self, arena: Optional[BumpArena] = None) -> None:
        self.arena = arena if arena else BumpArena(name="interner_arena", capacity_bytes=2 * 1024 * 1024)
        self._str_to_id: Dict[str, int] = {}
        self._id_to_slice: Dict[int, MemorySlice] = {}
        self._lock = threading.RLock()
        self.next_id: int = 1

    def intern(self, text: str) -> int:
        with self._lock:
            if text in self._str_to_id:
                return self._str_to_id[text]

            encoded = text.encode("utf-8")
            s = self.arena.allocate(len(encoded), alignment=4)
            s.write(encoded)

            assigned_id = self.next_id
            self.next_id += 1
            self._str_to_id[text] = assigned_id
            self._id_to_slice[assigned_id] = s
            return assigned_id

    def resolve(self, sym_id: int) -> Optional[str]:
        with self._lock:
            s = self._id_to_slice.get(sym_id)
            if s:
                return s.to_bytes().decode("utf-8")
            return None

    def __len__(self) -> int:
        return len(self._str_to_id)


class SovereignMemoryManager:
    """
    Stage 148: Centralized Sovereign Memory Manager.
    Coordinates bump arenas, segregated pools, string interners, and safety audits.
    """

    def __init__(self, project_root: Optional[str | Path] = None, runtime: Any = None) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.runtime = runtime
        self._lock = threading.RLock()

        # Primary Arenas
        self.arenas: Dict[str, BumpArena] = {
            "compiler": BumpArena("compiler", capacity_bytes=8 * 1024 * 1024),
            "jit": BumpArena("jit", capacity_bytes=4 * 1024 * 1024),
            "general": BumpArena("general", capacity_bytes=4 * 1024 * 1024),
        }

        # Primary Pools
        self.pools: Dict[str, ObjectPool] = {
            "general_pool": ObjectPool("general_pool", slab_chunk_count=64),
            "ir_node_pool": ObjectPool("ir_node_pool", slab_chunk_count=128),
        }

        # Interner
        self.interner = StringInterner(arena=self.arenas["compiler"])

    def get_arena(self, name: str = "compiler") -> BumpArena:
        with self._lock:
            if name not in self.arenas:
                self.arenas[name] = BumpArena(name=name)
            return self.arenas[name]

    def get_pool(self, name: str = "general_pool") -> ObjectPool:
        with self._lock:
            if name not in self.pools:
                self.pools[name] = ObjectPool(name=name)
            return self.pools[name]

    def reset_arena(self, name: str) -> bool:
        with self._lock:
            if name in self.arenas:
                self.arenas[name].reset()
                return True
            return False

    def run_memory_audit(self) -> Dict[str, Any]:
        """Audits all arenas and pools for corruption and memory health."""
        with self._lock:
            corruptions: List[str] = []
            total_allocated = 0
            total_capacity = 0

            for a_name, arena in self.arenas.items():
                ok, issues = arena.verify_integrity()
                if not ok:
                    corruptions.extend(issues)
                total_allocated += arena.offset
                total_capacity += arena.capacity

            for p_name, pool in self.pools.items():
                p_stat = pool.status()
                total_allocated += p_stat["total_resident_bytes"]
                total_capacity += p_stat["total_resident_bytes"]

            return {
                "healthy": len(corruptions) == 0,
                "corruptions": corruptions,
                "total_allocated_bytes": total_allocated,
                "total_capacity_bytes": total_capacity,
                "interned_symbols_count": len(self.interner),
            }

    # -------------------------------------------------------------------------
    # ASCII Presentation Tables
    # -------------------------------------------------------------------------
    def format_ascii_status(self) -> str:
        audit = self.run_memory_audit()
        alloc_str = f"{audit['total_allocated_bytes']:,} bytes"
        cap_str = f"{audit['total_capacity_bytes']:,} bytes"
        health_str = "HEALTHY" if audit['healthy'] else "CORRUPTED"
        lines = [
            "+-----------------------------------------------------------------------------+",
            f"| LUCY STAGE 148: ZERO-COPY MEMORY ARENA & POOL ALLOCATOR                     |",
            "+-----------------------------------------------------------------------------+",
            f"| Creator        : {CREATOR:<58} |",
            f"| Operator       : {OPERATOR:<58} |",
            f"| Health Status  : {health_str:<58} |",
            f"| Resident Total : {alloc_str:<58} |",
            f"| Total Capacity : {cap_str:<58} |",
            f"| Interned Syms  : {audit['interned_symbols_count']:<58} |",
            "+-----------------------------------------------------------------------------+",
            "| Arena Name   | Capacity      | Allocated     | Peak          | Allocs | Util % |",
            "+--------------+---------------+---------------+---------------+--------+--------+",
        ]
        for a_name, arena in self.arenas.items():
            st = arena.status()
            lines.append(
                f"| {st['name']:<12} | {st['capacity_bytes']:<13} | {st['allocated_bytes']:<13} | "
                f"{st['peak_offset']:<13} | {st['allocation_count']:<6} | {st['utilization_pct']:<6} |"
            )
        lines.append("+--------------+---------------+---------------+---------------+--------+--------+")
        return "\n".join(lines)


# Singleton
_INSTANCE: Optional[SovereignMemoryManager] = None


def get_memory_manager(runtime: Any = None) -> SovereignMemoryManager:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = SovereignMemoryManager(runtime=runtime)
    return _INSTANCE
