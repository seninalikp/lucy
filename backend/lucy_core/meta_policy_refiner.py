r"""
backend/lucy_core/meta_policy_refiner.py
Stage 128: Autonomous Meta-Policy Refiner
Era 13: Self-Reflective Symbolic Mesh & Cognitive Graph Synthesizer

100% offline, sovereign autonomous meta-policy optimizer, dynamic hyperparameter
tuner, and bounded policy governance engine for Lucy OS:
1. Dynamic Meta-Policy Governance:
   - Evaluates system-level heuristics and execution weights across:
     * RETRY_BUDGET: Max retry attempts before goal backoff (1 - 10).
     * SANDBOX_STRICTNESS: Sandbox boundary enforcement level (1.0 - 5.0).
     * EXPLORATION_RATIO: Balance between known paths vs exploration (0.05 - 0.50).
     * COMPRESSION_THRESHOLD: Token compression trigger ratio (0.50 - 0.95).
     * VERIFICATION_RIGOR: Oracle proof strictness tier (1.0 - 3.0).
     * THERMAL_SENSITIVITY: Throttle trigger threshold multiplier (0.70 - 1.30).
2. Safe Self-Tuning Guardrails:
   - Inviolable bounds prevent runaway parameter drift or safety relaxation.
   - Core operator identity (Senin / Senin Ali K P) is non-negotiable.
3. Performance Feedback & Reward Tracking:
   - Records execution outcomes (success/failure, duration, resource usage)
     to compute rolling policy utility and adjust weights conservatively.
4. Receipts & Persistence:
   - Emits META_POLICY_EVALUATED, META_POLICY_TUNED, and POLICY_INVARIANT_PROTECTED receipts.
   - Persists state to data/lucy/policies/meta_policies.json.
5. Strict CP1252-Safe ASCII Presentation:
   - /policy-status
   - /tune-policy [policy_name] [value]
   - /evaluate-policies
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

STAGE: int = 127 + 1
ERA: int = 13
ERA_NAME: str = "Self-Reflective Symbolic Mesh & Cognitive Graph Synthesizer"
STAGE_NAME: str = "Autonomous Meta-Policy Refiner"

CREATOR_NAME: str = "Senin"
CREATOR_FULL_NAME: str = "Senin Ali K P"


# =============================================================================
# Policy Definitions & Guardrails
# =============================================================================

@dataclass
class MetaPolicyParam:
    name: str
    current_value: float
    min_bound: float
    max_bound: float
    default_value: float
    category: str
    description: str
    total_adjustments: int = 0
    is_locked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


DEFAULT_POLICIES: List[MetaPolicyParam] = [
    MetaPolicyParam(
        name="RETRY_BUDGET",
        current_value=3.0,
        min_bound=1.0,
        max_bound=10.0,
        default_value=3.0,
        category="execution",
        description="Max autonomous retry attempts before triggering backoff",
    ),
    MetaPolicyParam(
        name="SANDBOX_STRICTNESS",
        current_value=4.0,
        min_bound=2.0,
        max_bound=5.0,
        default_value=4.0,
        category="security",
        description="Isolation barrier level (higher = stricter syscall filters)",
        is_locked=True,  # Safety invariant: cannot be lowered below safe boundary
    ),
    MetaPolicyParam(
        name="EXPLORATION_RATIO",
        current_value=0.20,
        min_bound=0.05,
        max_bound=0.50,
        default_value=0.20,
        category="reasoning",
        description="Epsilon exploration probability for counterfactual branching",
    ),
    MetaPolicyParam(
        name="COMPRESSION_THRESHOLD",
        current_value=0.80,
        min_bound=0.50,
        max_bound=0.95,
        default_value=0.80,
        category="memory",
        description="Token context utilization trigger for sliding compaction",
    ),
    MetaPolicyParam(
        name="VERIFICATION_RIGOR",
        current_value=2.0,
        min_bound=1.0,
        max_bound=3.0,
        default_value=2.0,
        category="verification",
        description="Oracle proof tier (1=Heuristic, 2=Deterministic, 3=Formal)",
    ),
    MetaPolicyParam(
        name="THERMAL_SENSITIVITY",
        current_value=1.0,
        min_bound=0.70,
        max_bound=1.30,
        default_value=1.0,
        category="hardware",
        description="Throttle trigger sensitivity multiplier relative to baseline",
    ),
]


# =============================================================================
# Autonomous Meta-Policy Refiner Core
# =============================================================================

class AutonomousMetaPolicyRefiner:
    """
    Sovereign, self-tuning policy governor and hyperparameter optimizer.
    """

    def __init__(
        self,
        project_root: Optional[Union[str, Path]] = None,
        runtime: Optional[Any] = None,
        data_dir: Optional[Union[str, Path]] = None,
        receipt_ledger: Optional[Any] = None,
    ) -> None:
        if project_root is None:
            self.project_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.project_root = Path(project_root)

        self.runtime = runtime
        if data_dir is None:
            self.data_dir = self.project_root / "data" / "lucy" / "policies"
        else:
            self.data_dir = Path(data_dir)

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.data_dir / "meta_policies.json"
        self.receipt_ledger = receipt_ledger

        self._lock = threading.RLock()
        self._policies: Dict[str, MetaPolicyParam] = {}
        self._total_sweeps: int = 0
        self._total_adjustments: int = 0

        self._load_policies()
        if not self._policies:
            for p in DEFAULT_POLICIES:
                self._policies[p.name] = MetaPolicyParam(**asdict(p))
            self._persist_policies()

    # =========================================================================
    # Policy Management & Tuning
    # =========================================================================

    def get_policy(self, name: str) -> Optional[MetaPolicyParam]:
        with self._lock:
            return self._policies.get(name.strip().upper())

    def get_value(self, name: str, fallback: float = 0.0) -> float:
        with self._lock:
            p = self._policies.get(name.strip().upper())
            return p.current_value if p else fallback

    def tune_policy(self, name: str, target_value: float, reason: str = "manual_tune") -> Tuple[bool, str, float]:
        """
        Adjusts a policy parameter within its strictly enforced min/max guardrails.
        """
        with self._lock:
            name_u = name.strip().upper()
            if name_u not in self._policies:
                return False, f"Policy '{name_u}' not found in sovereign policy registry.", 0.0

            param = self._policies[name_u]

            # Invariant check: cannot relax locked security policies below threshold
            if param.is_locked and target_value < param.default_value:
                self._emit_receipt(
                    "POLICY_INVARIANT_PROTECTED",
                    name_u,
                    f"Blocked relaxation of locked safety policy '{name_u}' below {param.default_value}",
                )
                return False, f"Policy '{name_u}' is locked to guarantee sovereign safety invariants (min {param.default_value}).", param.current_value

            # Clamp strictly within [min_bound, max_bound]
            clamped = max(param.min_bound, min(round(target_value, 3), param.max_bound))
            old_val = param.current_value
            param.current_value = clamped
            param.total_adjustments += 1
            self._total_adjustments += 1

            self._persist_policies()
            self._emit_receipt(
                "META_POLICY_TUNED",
                name_u,
                f"Tuned '{name_u}' from {old_val} to {clamped} ({reason})",
            )
            return True, f"Successfully tuned '{name_u}' to {clamped} (previous: {old_val}).", clamped

    def evaluate_and_refine_policies(
        self,
        recent_success_rate: float = 0.90,
        average_latency_ms: float = 150.0,
        ram_utilization_pct: float = 45.0,
    ) -> Dict[str, Any]:
        """
        Autonomous sweep that inspects recent execution performance and adjusts
        retry budgets, exploration rates, and compression thresholds.
        """
        with self._lock:
            adjustments = []

            # 1. High success rate (> 95%) allows slightly more exploratory branching
            if recent_success_rate >= 0.95:
                curr_exp = self.get_value("EXPLORATION_RATIO", 0.20)
                if curr_exp < 0.35:
                    success, msg, val = self.tune_policy("EXPLORATION_RATIO", curr_exp + 0.05, "high_success_reward")
                    adjustments.append({"policy": "EXPLORATION_RATIO", "new_value": val, "reason": "high_success"})
            # Lower success rate (< 75%) increases verification rigor and lowers exploration
            elif recent_success_rate < 0.75:
                curr_exp = self.get_value("EXPLORATION_RATIO", 0.20)
                self.tune_policy("EXPLORATION_RATIO", max(0.10, curr_exp - 0.05), "failure_mitigation")
                self.tune_policy("VERIFICATION_RIGOR", 3.0, "strict_verification_trigger")
                adjustments.append({"policy": "VERIFICATION_RIGOR", "new_value": 3.0, "reason": "failure_mitigation"})

            # 2. High RAM pressure (> 80%) tightens compression threshold
            if ram_utilization_pct > 80.0:
                self.tune_policy("COMPRESSION_THRESHOLD", 0.65, "ram_pressure_mitigation")
                adjustments.append({"policy": "COMPRESSION_THRESHOLD", "new_value": 0.65, "reason": "ram_pressure"})
            elif ram_utilization_pct < 40.0:
                self.tune_policy("COMPRESSION_THRESHOLD", 0.85, "low_ram_headroom")
                adjustments.append({"policy": "COMPRESSION_THRESHOLD", "new_value": 0.85, "reason": "low_ram"})

            # 3. High latency (> 500ms) trims retry budget to avoid compounding delays
            if average_latency_ms > 500.0:
                curr_retries = self.get_value("RETRY_BUDGET", 3.0)
                if curr_retries > 2.0:
                    self.tune_policy("RETRY_BUDGET", curr_retries - 1.0, "latency_reduction")
                    adjustments.append({"policy": "RETRY_BUDGET", "new_value": curr_retries - 1.0, "reason": "latency"})

            self._total_sweeps += 1
            self._persist_policies()

            self._emit_receipt(
                "META_POLICY_EVALUATED",
                f"sweep_{self._total_sweeps:04d}",
                f"Evaluated meta-policies with {len(adjustments)} autonomous adjustments (success_rate={recent_success_rate:.2f})",
            )

            return {
                "sweep_id": self._total_sweeps,
                "adjustments_count": len(adjustments),
                "adjustments": adjustments,
                "timestamp": time.time(),
            }

    # =========================================================================
    # Persistence & Receipts
    # =========================================================================

    def _persist_policies(self) -> None:
        try:
            data = {
                "stage": STAGE,
                "era": ERA,
                "total_sweeps": self._total_sweeps,
                "total_adjustments": self._total_adjustments,
                "policies": [p.to_dict() for p in self._policies.values()],
                "updated_at": time.time(),
            }
            tmp = self.manifest_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp.replace(self.manifest_file)
        except Exception:
            pass

    def _load_policies(self) -> None:
        if not self.manifest_file.exists():
            return
        try:
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._total_sweeps = data.get("total_sweeps", 0)
            self._total_adjustments = data.get("total_adjustments", 0)
            for p in data.get("policies", []):
                param = MetaPolicyParam(
                    name=p["name"],
                    current_value=p["current_value"],
                    min_bound=p["min_bound"],
                    max_bound=p["max_bound"],
                    default_value=p["default_value"],
                    category=p["category"],
                    description=p.get("description", ""),
                    total_adjustments=p.get("total_adjustments", 0),
                    is_locked=p.get("is_locked", False),
                )
                self._policies[param.name] = param
        except Exception:
            pass

    def _emit_receipt(self, action_cat: str, target: str, outcome: str) -> None:
        if self.receipt_ledger and hasattr(self.receipt_ledger, "record_receipt"):
            try:
                self.receipt_ledger.record_receipt(
                    action_category=action_cat,
                    operation="meta_policy_tuning",
                    target=target,
                    verified_outcome=outcome,
                )
            except Exception:
                pass

    # =========================================================================
    # ASCII Formatting & Status
    # =========================================================================

    def format_policy_status_table(self) -> str:
        """Renders CP1252-safe ASCII table of active meta-policies and bounds."""
        with self._lock:
            policies = sorted(self._policies.values(), key=lambda x: (x.category, x.name))
            count = len(policies)

        lines = [
            "+---------------------------------------------------------------------------------------------------+",
            "|                            LUCY OS - AUTONOMOUS META-POLICY REFINER                               |",
            "+------------------------------------------+--------------------------------------------------------+",
            "| Meta-Policy Metric                       | Current Operational Status                             |",
            "+------------------------------------------+--------------------------------------------------------+",
            f"| Total Monitored Meta-Policies            | {f'{count} policies active'.ljust(54)} |",
            f"| Total Autonomous Sweeps Executed         | {f'{self._total_sweeps} sweeps completed'.ljust(54)} |",
            f"| Total Policy Parameter Adjustments       | {f'{self._total_adjustments} tuning operations recorded'.ljust(54)} |",
            f"| Sovereign Human Operator                 | {f'{CREATOR_NAME} ({CREATOR_FULL_NAME})'.ljust(54)} |",
            "+------------------------------------------+--------------------------------------------------------+",
            "",
            "+-----------------------+---------------+---------+---------------+----------+----------------------+",
            "| Policy Parameter Name | Category      | Current | Bounds [m..M] | Changes  | Status / Lock        |",
            "+-----------------------+---------------+---------+---------------+----------+----------------------+",
        ]

        for p in policies:
            name_s = p.name[:21].ljust(21)
            cat_s = p.category[:13].ljust(13)
            val_s = f"{p.current_value:.2f}".center(7)
            bounds_s = f"[{p.min_bound:.1f} .. {p.max_bound:.1f}]".center(13)
            adj_s = str(p.total_adjustments).center(8)
            lock_s = ("LOCKED (Safety)" if p.is_locked else "DYNAMIC").center(20)
            lines.append(f"| {name_s} | {cat_s} | {val_s} | {bounds_s} | {adj_s} | {lock_s} |")

        lines.append("+-----------------------+---------------+---------+---------------+----------+----------------------+ contractors")
        # Replace contractors trail with clean border
        lines[-1] = "+-----------------------+---------------+---------+---------------+----------+----------------------+"
        return "\n".join(lines)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "era": ERA,
                "era_name": ERA_NAME,
                "stage_name": STAGE_NAME,
                "creator": CREATOR_NAME,
                "creator_full_name": CREATOR_FULL_NAME,
                "total_policies": len(self._policies),
                "total_sweeps": self._total_sweeps,
                "total_adjustments": self._total_adjustments,
            }
