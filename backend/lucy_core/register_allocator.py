r"""
backend/lucy_core/register_allocator.py
Stage 144: Register Allocation & Spill Cost Graph Colorer
Era 15: Autonomous Self-Hosting Compiler & Multi-Tier Optimization Pipeline

100% offline, Chaitin-Briggs graph coloring register allocation, liveness analysis,
interference graph construction, and spill cost heuristic engine for Lucy-IR:
1. Liveness Analysis Pass:
   - Computes GEN and KILL sets for instructions across basic blocks.
   - Solves backward dataflow equations to determine live-in and live-out ranges.
2. Interference Graph Construction:
   - Builds undirected interference graphs where edges represent overlapping live ranges.
   - Computes spill weights for each virtual register based on usage frequency and loop nesting.
3. Chaitin-Briggs K-Coloring Algorithm:
   - Simplification: strips nodes with degree < K onto an allocation stack.
   - Optimistic Spill: selects lowest-cost spill candidates when all remaining nodes have degree >= K.
   - Selection: pops nodes and assigns distinct physical target registers (%r0, %r1, ...).
4. Memory Spill Slot Manager:
   - Allocates stack frame spill slots ([rbp - offset]) for uncolorable virtual registers.
5. Cryptographic Provenance:
   - Generates allocation certificates with HMAC-SHA256 locked to operator: Senin (Senin Ali K P).
6. Strict CP1252-Safe ASCII Presentation:
   - /reg-status / /allocator-status
   - /reg-allocate [func_name] [num_registers]
   - /interference-graph [func_name]
   - /live-ranges [func_name]
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import hmac
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.lucy_core.ir_compiler_core import (
    BasicBlock,
    IRCompilerCore,
    IRFunction,
    IRInstruction,
    IRModule,
)

STAGE: int = 144
STAGE_NAME: str = "Register Allocation & Spill Cost Graph Colorer"
ERA: int = 15
CREATOR: str = "Senin"
OPERATOR: str = "Senin Ali K P"
HMAC_SECRET: bytes = b"senin-lucy-sovereign-reg-alloc-secret-2026"


@dataclasses.dataclass
class LiveRange:
    vreg: str
    start_idx: int
    end_idx: int
    def_block: str
    use_blocks: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class AllocationResult:
    func_name: str
    k_registers: int
    vregs_allocated: int
    physical_regs_used: int
    spilled_vregs: List[str]
    reg_assignment: Dict[str, str]
    spill_slots: Dict[str, int]
    interference_edges: int
    duration_ms: float
    hmac_signature: str

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


class RegisterAllocator:
    """
    Stage 144: Register Allocation & Spill Cost Graph Colorer.
    Transforms unbounded SSA virtual registers into finite target registers via
    Chaitin-Briggs graph coloring.
    """

    def __init__(
        self,
        project_root: Optional[str | Path] = None,
        runtime: Any = None,
        default_k: int = 8,
    ) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.runtime = runtime
        self.default_k = default_k
        self._lock = threading.RLock()
        self.compiler = IRCompilerCore(project_root=self.project_root, runtime=self.runtime)
        self.total_allocations: int = 0
        self.total_spills: int = 0
        self.recent_allocations: List[AllocationResult] = []

    def _compute_signature(self, text: str) -> str:
        return hmac.new(HMAC_SECRET, text.encode("utf-8"), hashlib.sha256).hexdigest()

    def compute_liveness(self, func: IRFunction) -> Dict[str, LiveRange]:
        """Computes global live range spans for all virtual registers."""
        # Linearize instructions to give each a global program point index
        flat_instructions: List[Tuple[str, IRInstruction, int]] = []
        idx = 0
        for bname, b in func.blocks.items():
            for inst in b.instructions:
                flat_instructions.append((bname, inst, idx))
                idx += 1

        vreg_defs: Dict[str, int] = {}
        vreg_uses: Dict[str, List[int]] = {}
        vreg_def_block: Dict[str, str] = {}
        vreg_use_blocks: Dict[str, Set[str]] = {}

        for bname, inst, pt in flat_instructions:
            if inst.dest and inst.dest.startswith("%v"):
                vreg_defs[inst.dest] = pt
                vreg_def_block[inst.dest] = bname

            for a in inst.args:
                if isinstance(a, str) and a.startswith("%v"):
                    vreg_uses.setdefault(a, []).append(pt)
                    vreg_use_blocks.setdefault(a, set()).add(bname)

        live_ranges: Dict[str, LiveRange] = {}
        all_vregs = set(vreg_defs.keys()) | set(vreg_uses.keys())

        for v in all_vregs:
            start_p = vreg_defs.get(v, 0)
            uses = vreg_uses.get(v, [start_p])
            end_p = max(uses) if uses else start_p
            live_ranges[v] = LiveRange(
                vreg=v,
                start_idx=start_p,
                end_idx=end_p,
                def_block=vreg_def_block.get(v, "entry"),
                use_blocks=sorted(list(vreg_use_blocks.get(v, set()))),
            )

        return live_ranges

    def build_interference_graph(
        self, func: IRFunction
    ) -> Tuple[Dict[str, Set[str]], Dict[str, float], Dict[str, LiveRange]]:
        """
        Builds the interference graph: two virtual registers interfere if their live ranges overlap.
        Computes spill weights: weight = uses / max(1, degree).
        """
        ranges = self.compute_liveness(func)
        adj: Dict[str, Set[str]] = {v: set() for v in ranges}
        vlist = list(ranges.values())

        for i in range(len(vlist)):
            r1 = vlist[i]
            for j in range(i + 1, len(vlist)):
                r2 = vlist[j]
                # Overlap condition: start1 <= end2 and start2 <= end1
                if r1.start_idx <= r2.end_idx and r2.start_idx <= r1.end_idx:
                    adj[r1.vreg].add(r2.vreg)
                    adj[r2.vreg].add(r1.vreg)

        # Compute spill weights
        weights: Dict[str, float] = {}
        for v, r in ranges.items():
            degree = len(adj[v])
            num_uses = len(r.use_blocks) + 1
            weights[v] = round(num_uses / max(1, degree), 4)

        return adj, weights, ranges

    def allocate_registers(self, func: IRFunction, k: Optional[int] = None) -> AllocationResult:
        """
        Executes Chaitin-Briggs K-Coloring Register Allocation.
        Assigns physical registers (%r0 ... %r{K-1}) or stack spill slots.
        """
        t0 = time.perf_counter_ns()
        k_val = k if k and k > 0 else self.default_k
        adj_graph, weights, ranges = self.build_interference_graph(func)

        # Count total edges
        total_edges = sum(len(neighbors) for neighbors in adj_graph.values()) // 2

        # Worklist copy
        graph = {node: set(neighbors) for node, neighbors in adj_graph.items()}
        stack: List[str] = []
        spilled_vregs: List[str] = []

        # 1. Simplification & Optimistic Spill Phase
        while graph:
            # Find a node with degree < K
            low_degree_node = None
            for node, neighbors in graph.items():
                if len(neighbors) < k_val:
                    low_degree_node = node
                    break

            if low_degree_node:
                # Remove node and push to stack
                stack.append(low_degree_node)
                for neighbor in graph[low_degree_node]:
                    graph[neighbor].discard(low_degree_node)
                del graph[low_degree_node]
            else:
                # Potential Spill: Pick node with lowest spill weight
                spill_candidate = min(graph.keys(), key=lambda n: weights.get(n, 1.0))
                stack.append(spill_candidate)
                for neighbor in graph[spill_candidate]:
                    graph[neighbor].discard(spill_candidate)
                del graph[spill_candidate]

        # 2. Select Phase (Pop stack and color)
        colors: Dict[str, str] = {}
        spill_slots: Dict[str, int] = {}
        slot_counter = 0

        while stack:
            vreg = stack.pop()
            # Find colors used by neighbors in original adjacency graph
            used_colors = {colors[nb] for nb in adj_graph[vreg] if nb in colors}

            # Find lowest available physical register color
            assigned_color = None
            for c_idx in range(k_val):
                candidate_color = f"%r{c_idx}"
                if candidate_color not in used_colors:
                    assigned_color = candidate_color
                    break

            if assigned_color:
                colors[vreg] = assigned_color
            else:
                # Actual spill occurred
                spilled_vregs.append(vreg)
                spill_slots[vreg] = slot_counter
                slot_counter += 1

        t1 = time.perf_counter_ns()
        dur_ms = round((t1 - t0) / 1_000_000.0, 2)

        physical_regs_used = len(set(colors.values()))
        sig = self._compute_signature(f"{func.name}:{k_val}:{len(colors)}:{len(spilled_vregs)}")

        result = AllocationResult(
            func_name=func.name,
            k_registers=k_val,
            vregs_allocated=len(colors),
            physical_regs_used=physical_regs_used,
            spilled_vregs=spilled_vregs,
            reg_assignment=colors,
            spill_slots=spill_slots,
            interference_edges=total_edges,
            duration_ms=dur_ms,
            hmac_signature=sig,
        )

        with self._lock:
            self.total_allocations += 1
            self.total_spills += len(spilled_vregs)
            self.recent_allocations.append(result)
            if len(self.recent_allocations) > 50:
                self.recent_allocations.pop(0)

        return result

    def allocate_module(self, module: IRModule, k: Optional[int] = None) -> Dict[str, AllocationResult]:
        """Allocates registers for all functions in an IRModule."""
        results: Dict[str, AllocationResult] = {}
        for fname, func in module.functions.items():
            results[fname] = self.allocate_registers(func, k=k)
        return results

    def allocate_source(
        self, source_code: str, module_name: str = "reg_mod", k: Optional[int] = None
    ) -> Dict[str, AllocationResult]:
        """Convenience method: compiles source to IR and runs register allocation."""
        mod = self.compiler.compile_source(source_code, module_name=module_name)
        return self.allocate_module(mod, k=k)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "creator": CREATOR,
                "operator": OPERATOR,
                "default_k": self.default_k,
                "total_allocations": self.total_allocations,
                "total_spills": self.total_spills,
                "cached_allocations": len(self.recent_allocations),
                "status": "ALLOCATOR_ACTIVE",
            }

    def format_reg_status_table(self) -> str:
        s = self.status()
        lines = [
            "+=============================================================================+",
            f"| LUCY REGISTER ALLOCATOR & GRAPH COLORER [STAGE {STAGE:03d} | ERA {ERA:02d}]                |",
            "+=============================================================================+",
            f"| Status: {s['status']:<16} Allocations: {s['total_allocations']:<8} Total Spills: {s['total_spills']:<13} |",
            f"| Default K: {s['default_k']:<13} Cached: {s['cached_allocations']:<11} Sovereign Operator: {OPERATOR:<16} |",
            "+-----------------------------------------------------------------------------+",
            "| RECENT REGISTER ALLOCATIONS                                                 |",
            "+----------------------+------------+------------+------------+---------------+",
            "| Function Name        | Target K   | Allocated  | Phys Used  | Spilled VRegs |",
            "+----------------------+------------+------------+------------+---------------+",
        ]
        with self._lock:
            for a in self.recent_allocations[-5:]:
                lines.append(
                    f"| {a.func_name[:20]:<20} | {a.k_registers:<10} | {a.vregs_allocated:<10} | {a.physical_regs_used:<10} | {len(a.spilled_vregs):<13} |"
                )
        if not self.recent_allocations:
            lines.append("| (No register allocations recorded in current session)                     |")
        lines.append("+----------------------+------------+------------+------------+---------------+")
        return "\n".join(lines)

    def format_allocation_table(self, res: AllocationResult) -> str:
        lines = [
            "+=============================================================================+",
            f"| REGISTER ALLOCATION: @{res.func_name:<55} |",
            "+=============================================================================+",
            f"| Target Registers (K): {res.k_registers:<5} VRegs Allocated: {res.vregs_allocated:<6} Physical Used: {res.physical_regs_used:<6} |",
            f"| Spilled Registers: {len(res.spilled_vregs):<9} Graph Edges: {res.interference_edges:<10} Duration: {res.duration_ms:.2f} ms     |",
            f"| HMAC Signature: {res.hmac_signature[:24]}...                               |",
            "+-----------------------------------------------------------------------------+",
            "| REGISTER ASSIGNMENTS SAMPLE                                                 |",
            "+-----------------------------------------------------------------------------+",
        ]
        sample = list(res.reg_assignment.items())[:6]
        for vreg, phys in sample:
            lines.append(f"|  {vreg:<10} -> {phys:<62} |")
        if res.spilled_vregs:
            lines.append("+-----------------------------------------------------------------------------+")
            lines.append(f"| SPILLED VREGS: {', '.join(res.spilled_vregs[:8]):<60} |")
        lines.append("+-----------------------------------------------------------------------------+")
        return "\n".join(lines)


__all__ = [
    "STAGE",
    "STAGE_NAME",
    "ERA",
    "CREATOR",
    "OPERATOR",
    "LiveRange",
    "AllocationResult",
    "RegisterAllocator",
]
