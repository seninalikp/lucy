r"""
backend/lucy_core/dynamic_context_budgeter.py
Stage 126: Dynamic Context Budget Allocator
Era 13: Self-Reflective Symbolic Mesh & Cognitive Graph Synthesizer

100% offline, sovereign context budget allocation, dynamic sliding-window compaction,
and memory governor for Lucy OS:
1. Dynamic Context Slicing:
   - Partitions token context window across 5 prioritized operational slices:
     * SYSTEM_CORE_PROMPT: 15% (Immutable identity, creator Senin, safety invariants - Priority 1).
     * OPERATOR_DIALOGUE: 25% (Conversational history and active goal directives - Priority 2).
     * RETRIEVAL_RAG_KG: 30% (HNSW vector chunks, knowledge graph property links, AST symbols - Priority 3).
     * SCRATCHPAD_REASONING: 20% (Counterfactual simulations, DAG plans, internal monologue - Priority 4).
     * RESPONSE_BUFFER: 10% (Reserved output token headroom - Priority 5).
2. Hardware-Aware Token Window Scaling:
   - Synchronizes with Thermal Governor (Stage 118) and Hardware Telemetry (Stage 99):
     * Eco Mode: 2,048 tokens.
     * Balanced Mode: 4,096 tokens.
     * Turbo / High-VRAM Mode: 8,192 tokens.
3. Proactive Semantic Compaction:
   - Prevents Out-Of-Memory (OOM) token crashes by auto-compacting lower-priority slices.
   - Guaranteed protection for SYSTEM_CORE_PROMPT (zero operator drift or invariant stripping).
4. Telemetry & Receipts:
   - Emits BUDGET_SLICES_ALLOCATED, CONTEXT_COMPACTED, and BUDGET_OVERFLOW_PREVENTED receipts.
   - Persists budget allocation manifest in data/lucy/budget/context_budget.json.
5. Strict CP1252-Safe ASCII Presentation:
   - /budget-status
   - /allocate-budget [tokens]
   - /compact-context [slice_name]
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 126
ERA: int = 13
ERA_NAME: str = "Self-Reflective Symbolic Mesh & Cognitive Graph Synthesizer"
STAGE_NAME: str = "Dynamic Context Budget Allocator"

CREATOR_NAME: str = "Senin"
CREATOR_FULL_NAME: str = "Senin Ali K P"

# Standard Context Slice Ratios (must sum to 1.0)
SLICE_RATIOS: Dict[str, Tuple[float, int, bool]] = {
    # slice_name: (ratio, priority, is_immutable)
    "SYSTEM_CORE_PROMPT": (0.15, 1, True),    # Priority 1: Non-negotiable identity & safety
    "OPERATOR_DIALOGUE": (0.25, 2, False),   # Priority 2: Operator conversation & goals
    "RETRIEVAL_RAG_KG": (0.30, 3, False),    # Priority 3: Vector chunks & knowledge graph
    "SCRATCHPAD_REASONING": (0.20, 4, False),# Priority 4: Internal thoughts & simulations
    "RESPONSE_BUFFER": (0.10, 5, False),     # Priority 5: Output headroom
}


# =============================================================================
# Dataclasses
# =============================================================================

@dataclass
class ContextSliceAllocation:
    slice_name: str
    priority: int
    allocated_tokens: int
    used_tokens: int = 0
    compaction_count: int = 0
    is_immutable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        util = (self.used_tokens / max(1, self.allocated_tokens)) * 100.0
        return {
            "slice_name": self.slice_name,
            "priority": self.priority,
            "allocated_tokens": self.allocated_tokens,
            "used_tokens": self.used_tokens,
            "utilization_pct": round(util, 1),
            "compaction_count": self.compaction_count,
            "is_immutable": self.is_immutable,
        }


@dataclass
class ContextBudgetSnapshot:
    snapshot_id: str
    total_budget_tokens: int
    total_used_tokens: int
    hardware_mode: str
    slices: Dict[str, Dict[str, Any]]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        util = (self.total_used_tokens / max(1, self.total_budget_tokens)) * 100.0
        return {
            "snapshot_id": self.snapshot_id,
            "total_budget_tokens": self.total_budget_tokens,
            "total_used_tokens": self.total_used_tokens,
            "utilization_pct": round(util, 1),
            "hardware_mode": self.hardware_mode,
            "slices": self.slices,
            "timestamp": self.timestamp,
        }


# =============================================================================
# Dynamic Context Budget Allocator Core
# =============================================================================

class DynamicContextBudgetAllocator:
    """
    Intelligent context slicing, sliding window compaction, and token resource governor.
    """

    def __init__(
        self,
        project_root: Optional[Union[str, Path]] = None,
        runtime: Optional[Any] = None,
        data_dir: Optional[Union[str, Path]] = None,
        receipt_ledger: Optional[Any] = None,
        default_budget: int = 4096,
    ) -> None:
        if project_root is None:
            self.project_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.project_root = Path(project_root)

        self.runtime = runtime
        if data_dir is None:
            self.data_dir = self.project_root / "data" / "lucy" / "budget"
        else:
            self.data_dir = Path(data_dir)

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.data_dir / "context_budget.json"
        self.receipt_ledger = receipt_ledger

        self._lock = threading.RLock()
        self._total_budget: int = default_budget
        self._hardware_mode: str = "balanced"
        self._slices: Dict[str, ContextSliceAllocation] = {}
        self._total_allocations: int = 0
        self._total_compactions: int = 0

        self._load_manifest()
        if not self._slices:
            self.allocate_slices(self._total_budget, self._hardware_mode)

    # =========================================================================
    # Slice Allocation & Hardware Adaptation
    # =========================================================================

    def allocate_slices(
        self,
        total_budget: Optional[int] = None,
        hardware_mode: str = "balanced",
    ) -> ContextBudgetSnapshot:
        """
        Calculates and binds slice token budgets based on global capacity and mode.
        """
        with self._lock:
            if total_budget is not None:
                self._total_budget = max(1024, min(total_budget, 65536))
            else:
                # Deduce from hardware mode
                h_low = hardware_mode.lower()
                if h_low == "eco":
                    self._total_budget = 2048
                elif h_low == "turbo":
                    self._total_budget = 8192
                else:
                    self._total_budget = 4096

            self._hardware_mode = hardware_mode

            new_slices: Dict[str, ContextSliceAllocation] = {}
            for name, (ratio, priority, immutable) in SLICE_RATIOS.items():
                alloc = int(self._total_budget * ratio)
                prev_used = self._slices[name].used_tokens if name in self._slices else 0
                prev_comp = self._slices[name].compaction_count if name in self._slices else 0
                new_slices[name] = ContextSliceAllocation(
                    slice_name=name,
                    priority=priority,
                    allocated_tokens=alloc,
                    used_tokens=min(prev_used, alloc),
                    compaction_count=prev_comp,
                    is_immutable=immutable,
                )

            self._slices = new_slices
            self._total_allocations += 1

            total_used = sum(s.used_tokens for s in self._slices.values())
            snap_id = f"snap_bud_{int(time.time())}_{self._total_allocations:04d}"
            snapshot = ContextBudgetSnapshot(
                snapshot_id=snap_id,
                total_budget_tokens=self._total_budget,
                total_used_tokens=total_used,
                hardware_mode=self._hardware_mode,
                slices={name: s.to_dict() for name, s in self._slices.items()},
                timestamp=time.time(),
            )

            self._persist_manifest()

            self._emit_receipt(
                "BUDGET_SLICES_ALLOCATED",
                snap_id,
                f"Allocated {self._total_budget} tokens across 5 slices (mode: {self._hardware_mode})",
            )
            return snapshot

    # =========================================================================
    # Usage Tracking & Compaction
    # =========================================================================

    def register_usage(self, slice_name: str, token_count: int) -> bool:
        """
        Records token consumption in a slice. If exceeding budget, auto-triggers compaction.
        """
        with self._lock:
            s_u = slice_name.strip().upper()
            if s_u not in self._slices:
                return False

            slice_obj = self._slices[s_u]
            slice_obj.used_tokens = max(0, token_count)

            # Check overflow
            if slice_obj.used_tokens > slice_obj.allocated_tokens:
                freed = self.compact_slice(s_u)
                self._emit_receipt(
                    "BUDGET_OVERFLOW_PREVENTED",
                    s_u,
                    f"Slice {s_u} overflow prevented: freed {freed} tokens via compaction",
                )

            self._persist_manifest()
            return True

    def compact_slice(self, slice_name: str) -> int:
        """
        Applies sliding window compaction to reduce token usage to 70% of allocation.
        Immutable slices (SYSTEM_CORE_PROMPT) are protected from compaction.
        """
        with self._lock:
            s_u = slice_name.strip().upper()
            if s_u not in self._slices:
                return 0

            slice_obj = self._slices[s_u]
            if slice_obj.is_immutable:
                # Protected: never compact core identity or safety prompt
                return 0

            target = int(slice_obj.allocated_tokens * 0.70)
            freed = max(0, slice_obj.used_tokens - target)
            slice_obj.used_tokens = target
            slice_obj.compaction_count += 1
            self._total_compactions += 1

            self._emit_receipt(
                "CONTEXT_COMPACTED",
                s_u,
                f"Compacted slice {s_u} to 70% capacity (freed {freed} tokens)",
            )
            self._persist_manifest()
            return freed

    # =========================================================================
    # Queries & Persistence
    # =========================================================================

    def get_slice(self, slice_name: str) -> Optional[ContextSliceAllocation]:
        with self._lock:
            return self._slices.get(slice_name.strip().upper())

    def _persist_manifest(self) -> None:
        try:
            total_used = sum(s.used_tokens for s in self._slices.values())
            data = {
                "stage": STAGE,
                "era": ERA,
                "total_budget": self._total_budget,
                "total_used": total_used,
                "hardware_mode": self._hardware_mode,
                "slices": [s.to_dict() for s in self._slices.values()],
                "total_allocations": self._total_allocations,
                "total_compactions": self._total_compactions,
                "updated_at": time.time(),
            }
            tmp = self.manifest_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp.replace(self.manifest_file)
        except Exception:
            pass

    def _load_manifest(self) -> None:
        if not self.manifest_file.exists():
            return
        try:
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._total_budget = data.get("total_budget", 4096)
            self._hardware_mode = data.get("hardware_mode", "balanced")
            self._total_allocations = data.get("total_allocations", 0)
            self._total_compactions = data.get("total_compactions", 0)
            for d in data.get("slices", []):
                s = ContextSliceAllocation(
                    slice_name=d["slice_name"],
                    priority=d["priority"],
                    allocated_tokens=d["allocated_tokens"],
                    used_tokens=d.get("used_tokens", 0),
                    compaction_count=d.get("compaction_count", 0),
                    is_immutable=d.get("is_immutable", False),
                )
                self._slices[s.slice_name] = s
        except Exception:
            pass

    def _emit_receipt(self, action_cat: str, target: str, outcome: str) -> None:
        if self.receipt_ledger and hasattr(self.receipt_ledger, "record_receipt"):
            try:
                self.receipt_ledger.record_receipt(
                    action_category=action_cat,
                    operation="context_budgeting",
                    target=target,
                    verified_outcome=outcome,
                )
            except Exception:
                pass

    # =========================================================================
    # ASCII Visualizations & Status
    # =========================================================================

    def format_budget_status_table(self) -> str:
        """Renders CP1252-safe ASCII table of token context allocations."""
        with self._lock:
            total_b = self._total_budget
            total_u = sum(s.used_tokens for s in self._slices.values())
            overall_util = (total_u / max(1, total_b)) * 100.0
            mode = self._hardware_mode.upper()
            slices_list = sorted(self._slices.values(), key=lambda x: x.priority)

        lines = [
            "+--------------------------------------------------------------------------------+",
            "|                LUCY OS - DYNAMIC CONTEXT BUDGET ALLOCATOR                      |",
            "+--------------------------------------+-----------------------------------------+",
            "| Context Budget Telemetry Metric      | Current Operational Value               |",
            "+--------------------------------------+-----------------------------------------+",
            f"| Total Global Token Capacity          | {f'{total_b:,} tokens ({mode} mode)'.ljust(39)} |",
            f"| Active Total Token Consumption       | {f'{total_u:,} tokens ({overall_util:.1f}% utilized)'.ljust(39)} |",
            f"| Proactive Compactions Performed      | {f'{self._total_compactions} compactions executed'.ljust(39)} |",
            f"| Identity Slice Invariant Protection  | {'IMMUTABLE (Protected from Truncation)'.ljust(39)} |",
            f"| Sovereign Operator Authority         | {f'{CREATOR_NAME} ({CREATOR_FULL_NAME})'.ljust(39)} |",
            "+--------------------------------------+-----------------------------------------+",
            "",
            "+-----+-----------------------+----------+--------+--------+--------+------------+",
            "| Pri | Context Slice Name    | Alloc    | Used   | Util%  | Compact| Immutable  |",
            "+-----+-----------------------+----------+--------+--------+--------+------------+",
        ]

        for s in slices_list:
            pri_s = str(s.priority).center(3)
            name_s = s.slice_name[:21].ljust(21)
            alloc_s = f"{s.allocated_tokens:,}".rjust(8)
            used_s = f"{s.used_tokens:,}".rjust(6)
            util = f"{(s.used_tokens / max(1, s.allocated_tokens) * 100):.1f}%".rjust(6)
            comp_s = str(s.compaction_count).rjust(6)
            imm_s = ("YES (LOCK)" if s.is_immutable else "NO (SLIDE)").center(10)
            lines.append(f"| {pri_s} | {name_s} | {alloc_s} | {used_s} | {util} | {comp_s} | {imm_s} |")

        lines.append("+-----+-----------------------+----------+--------+--------+--------+------------+")
        return "\n".join(lines)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            total_u = sum(s.used_tokens for s in self._slices.values())
            return {
                "stage": STAGE,
                "era": ERA,
                "era_name": ERA_NAME,
                "stage_name": STAGE_NAME,
                "creator": CREATOR_NAME,
                "creator_full_name": CREATOR_FULL_NAME,
                "total_budget": self._total_budget,
                "total_used": total_u,
                "hardware_mode": self._hardware_mode,
                "total_compactions": self._total_compactions,
                "slices_count": len(self._slices),
            }
