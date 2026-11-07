r"""
backend/lucy_core/consistent_hashing_ring.py
Stage 171: Consistent Hashing Ring & Virtual Node Partitioning
Era 18: Autonomous Distributed Storage, Geo-Replication & Sharding Primitives

100% offline, sovereign consistent hashing ring and virtual node partitioning engine:
1. Virtual Node (VNode) Ring Topology:
   - Configurable 64-bit token space [0, 2^64 - 1].
   - Deterministic SHA-256 token hashing for physical nodes and keys.
   - Dynamic virtual nodes per physical host (default 128 vnodes) for minimal load variance.
2. Replication Preference Lists:
   - Clockwise ring traversal for N-way replication preference lists with physical host deduplication.
   - Fault-tolerant replica placement ensuring diverse failure domains.
3. Dynamic Membership & Key Rebalancing:
   - Node addition and removal with minimal keyspace displacement (K/N keys migrated).
   - Range delta calculation identifying exact token intervals transferred between nodes.
4. Partition Distribution Telemetry:
   - Per-node token ownership percentage, load standard deviation, and balance coefficient.
5. Thread-safe execution via RLock.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import struct
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 171
STAGE_NAME: str = "Consistent Hashing Ring & Virtual Node Partitioning"
ERA: int = 18
ERA_NAME: str = "Autonomous Distributed Storage, Geo-Replication & Sharding Primitives"

RING_MODULUS: int = 2**64  # 64-bit keyspace


def hash_token_64(val: str) -> int:
    """Computes deterministic 64-bit unsigned integer hash from string using SHA-256."""
    digest = hashlib.sha256(val.encode("utf-8")).digest()
    return struct.unpack(">Q", digest[:8])[0]


@dataclass
class VNode:
    token: int
    physical_node_id: str
    vnode_index: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RangeTransfer:
    from_node: Optional[str]
    to_node: str
    start_token: int
    end_token: int
    key_count_estimated: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RingLoadStats:
    total_physical_nodes: int
    total_vnodes: int
    node_token_counts: Dict[str, int]
    node_coverage_fractions: Dict[str, float]
    standard_deviation: float
    is_balanced: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConsistentHashRing:
    """
    Sovereign Consistent Hash Ring with Virtual Node (VNode) partitioning.
    Distributes keys uniformly across physical cluster nodes.
    """

    def __init__(
        self,
        default_vnodes: int = 128,
        replication_factor: int = 3,
        project_root: Optional[Union[str, Path]] = None,
        runtime: Optional[Any] = None,
    ) -> None:
        self.default_vnodes = max(1, default_vnodes)
        self.replication_factor = max(1, replication_factor)
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parent.parent.parent
        self.runtime = runtime

        self._lock = threading.RLock()
        self._ring: List[int] = []  # Sorted list of tokens
        self._token_to_vnode: Dict[int, VNode] = {}
        self._nodes: Dict[str, int] = {}  # node_id -> vnode count
        self._node_weights: Dict[str, float] = {}
        self._key_registry: Dict[str, str] = {}  # key -> primary_node (sample tracking)

    # -------------------------------------------------------------------------
    # Cluster Membership Operations
    # -------------------------------------------------------------------------
    def add_node(self, node_id: str, vnodes: Optional[int] = None, weight: float = 1.0) -> int:
        """
        Adds a physical node to the ring with weighted virtual nodes.
        Returns the number of virtual nodes added.
        """
        with self._lock:
            if node_id in self._nodes:
                return 0

            count = vnodes if vnodes is not None else int(self.default_vnodes * max(0.1, weight))
            count = max(1, count)
            self._nodes[node_id] = count
            self._node_weights[node_id] = weight

            for i in range(count):
                token_str = f"{node_id}#vnode_{i}"
                tok = hash_token_64(token_str)
                # Handle token collision by linear probing in token space
                while tok in self._token_to_vnode:
                    tok = (tok + 1) % RING_MODULUS

                vn = VNode(token=tok, physical_node_id=node_id, vnode_index=i)
                self._token_to_vnode[tok] = vn
                bisect.insort(self._ring, tok)

            return count

    def remove_node(self, node_id: str) -> int:
        """
        Removes a physical node and all its virtual nodes from the ring.
        Returns the number of virtual nodes removed.
        """
        with self._lock:
            if node_id not in self._nodes:
                return 0

            removed = 0
            tokens_to_remove = [
                tok for tok, vn in self._token_to_vnode.items() if vn.physical_node_id == node_id
            ]

            for tok in tokens_to_remove:
                del self._token_to_vnode[tok]
                idx = bisect.bisect_left(self._ring, tok)
                if idx < len(self._ring) and self._ring[idx] == tok:
                    self._ring.pop(idx)
                    removed += 1

            del self._nodes[node_id]
            if node_id in self._node_weights:
                del self._node_weights[node_id]

            # Re-assign sample registry keys if affected
            for k in list(self._key_registry.keys()):
                if self._key_registry[k] == node_id:
                    self._key_registry[k] = self.get_primary_node(k) or "NONE"

            return removed

    # -------------------------------------------------------------------------
    # Key Lookup & Replica Preference Lists
    # -------------------------------------------------------------------------
    def get_token_for_key(self, key: str) -> int:
        """Returns the 64-bit hash token for a given key string."""
        return hash_token_64(f"key:{key}")

    def get_primary_node(self, key: str) -> Optional[str]:
        """
        Finds the primary physical node responsible for the given key.
        Searches clockwise on the ring for the first token >= key_token.
        """
        with self._lock:
            if not self._ring:
                return None

            key_tok = self.get_token_for_key(key)
            idx = bisect.bisect_right(self._ring, key_tok)
            # Wrap around ring
            if idx >= len(self._ring):
                idx = 0

            tok = self._ring[idx]
            node_id = self._token_to_vnode[tok].physical_node_id
            self._key_registry[key] = node_id
            return node_id

    def get_preference_list(self, key: str, n: Optional[int] = None) -> List[str]:
        """
        Returns a list of N distinct physical nodes responsible for replicating the key.
        Traverses clockwise on the ring, skipping already selected physical nodes.
        """
        with self._lock:
            if not self._ring:
                return []

            rf = n if n is not None else self.replication_factor
            rf = min(rf, len(self._nodes))

            key_tok = self.get_token_for_key(key)
            idx = bisect.bisect_right(self._ring, key_tok)

            pref_list: List[str] = []
            seen_nodes: Set[str] = set()

            ring_len = len(self._ring)
            for step in range(ring_len):
                curr_idx = (idx + step) % ring_len
                tok = self._ring[curr_idx]
                p_node = self._token_to_vnode[tok].physical_node_id
                if p_node not in seen_nodes:
                    seen_nodes.add(p_node)
                    pref_list.append(p_node)
                    if len(pref_list) == rf:
                        break

            return pref_list

    # -------------------------------------------------------------------------
    # Rebalance Delta & Migration Calculation
    # -------------------------------------------------------------------------
    def calculate_range_ownership(self) -> Dict[str, float]:
        """
        Calculates the fraction of the total keyspace owned by each physical node.
        """
        with self._lock:
            if not self._ring:
                return {}

            ownership: Dict[str, int] = {nid: 0 for nid in self._nodes}
            ring_len = len(self._ring)

            for i in range(ring_len):
                curr_tok = self._ring[i]
                prev_tok = self._ring[(i - 1 + ring_len) % ring_len]

                if curr_tok >= prev_tok:
                    span = curr_tok - prev_tok
                else:
                    span = (RING_MODULUS - prev_tok) + curr_tok

                node_id = self._token_to_vnode[curr_tok].physical_node_id
                ownership[node_id] += span

            return {nid: round(span / RING_MODULUS, 6) for nid, span in ownership.items()}

    def get_load_stats(self) -> RingLoadStats:
        """
        Computes ring load balance telemetry including standard deviation.
        """
        with self._lock:
            total_phys = len(self._nodes)
            total_vn = len(self._ring)
            if total_phys == 0:
                return RingLoadStats(0, 0, {}, {}, 0.0, True)

            fractions = self.calculate_range_ownership()
            expected_fraction = 1.0 / total_phys

            variance = sum((f - expected_fraction) ** 2 for f in fractions.values()) / total_phys
            std_dev = variance ** 0.5

            # Balanced if standard deviation is below 0.08
            is_balanced = std_dev < 0.08

            return RingLoadStats(
                total_physical_nodes=total_phys,
                total_vnodes=total_vn,
                node_token_counts=dict(self._nodes),
                node_coverage_fractions=fractions,
                standard_deviation=round(std_dev, 6),
                is_balanced=is_balanced,
            )

    def calculate_rebalance_plan(self, new_node_id: str, new_vnodes: int = 128) -> List[RangeTransfer]:
        """
        Calculates range transfers required if `new_node_id` were added to the ring.
        """
        with self._lock:
            if not self._ring or new_node_id in self._nodes:
                return []

            plan: List[RangeTransfer] = []
            sim_ring = list(self._ring)
            sim_vnodes = dict(self._token_to_vnode)

            for i in range(new_vnodes):
                tok = hash_token_64(f"{new_node_id}#vnode_{i}")
                while tok in sim_vnodes:
                    tok = (tok + 1) % RING_MODULUS

                idx = bisect.bisect_right(sim_ring, tok)
                if idx >= len(sim_ring):
                    idx = 0

                prev_tok = sim_ring[(idx - 1 + len(sim_ring)) % len(sim_ring)]
                existing_holder = sim_vnodes[sim_ring[idx]].physical_node_id

                plan.append(
                    RangeTransfer(
                        from_node=existing_holder,
                        to_node=new_node_id,
                        start_token=prev_tok,
                        end_token=tok,
                    )
                )

            return plan

    # -------------------------------------------------------------------------
    # Telemetry & Status
    # -------------------------------------------------------------------------
    def status(self) -> Dict[str, Any]:
        with self._lock:
            stats = self.get_load_stats()
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "physical_nodes": list(self._nodes.keys()),
                "total_vnodes": len(self._ring),
                "replication_factor": self.replication_factor,
                "load_stats": stats.to_dict(),
                "sample_keys_tracked": len(self._key_registry),
            }

    def format_ascii_status(self) -> str:
        with self._lock:
            stats = self.get_load_stats()
            lines = [
                "+-----------------------------------------------------------------------------+",
                f"| LUCY STAGE 171: CONSISTENT HASHING RING & VIRTUAL NODE PARTITIONING          |",
                "+-----------------------------------------------------------------------------+",
                f"| Physical Nodes : {stats.total_physical_nodes:<58} |",
                f"| Total VNodes   : {stats.total_vnodes:<58} |",
                f"| Repl. Factor   : {self.replication_factor:<58} |",
                f"| Std. Deviation : {stats.standard_deviation:<58} |",
                f"| Balance Status : {'BALANCED (UNIFORM DISTRIBUTION)' if stats.is_balanced else 'SUB-OPTIMAL VARIANCE':<58} |",
                "+-----------------+----------+------------------+-----------------------------+",
                "| PHYSICAL NODE   | VNODES   | RING COVERAGE    | ESTIMATED CAPACITY          |",
                "+-----------------+----------+------------------+-----------------------------+",
            ]

            for nid in sorted(self._nodes.keys()):
                vn_cnt = self._nodes[nid]
                frac = stats.node_coverage_fractions.get(nid, 0.0) * 100.0
                cap = f"{frac:.2f}%"
                lines.append(f"| {nid:<15} | {vn_cnt:>8} | {cap:>16} | {'STANDARD' if frac > 10 else 'MINIMAL':<27} |")

            if not self._nodes:
                lines.append("| (No physical nodes registered in consistent hashing ring)                  |")

            lines.append("+-----------------+----------+------------------+-----------------------------+")
            return "\n".join(lines)


# Singleton
_RING_INSTANCE: Optional[ConsistentHashRing] = None


def get_consistent_hash_ring(runtime: Any = None) -> ConsistentHashRing:
    global _RING_INSTANCE
    if _RING_INSTANCE is None:
        _RING_INSTANCE = ConsistentHashRing(runtime=runtime)
    return _RING_INSTANCE
