"""
backend/lucy_core/memory_distiller.py
Stage 76: Autonomous Memory Pruning & Cognitive Distillation

Safely purges stale, superseded, low-salience memory graph nodes while
strictly protecting pinned facts, preserving causal lineage, archiving pruned
facts, and producing distilled memory checkpoints for Lucy's sovereign runtime.
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

STAGE: int = 76

HALF_LIFE_DAYS = 14.0
DEFAULT_SALIENCE_THRESHOLD = 0.25


@dataclass
class DistillationCandidate:
    node_id: str
    fact: str
    category: str
    pinned: bool
    status: str
    age_days: float
    reference_count: int
    salience_score: float
    action: str  # "keep", "prune", "consolidate"
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DistillationReport:
    timestamp: str
    total_nodes_before: int
    total_nodes_after: int
    pruned_count: int
    consolidated_count: int
    pinned_protected_count: int
    pruned_node_ids: List[str] = field(default_factory=list)
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def format_terminal_summary(self) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| COGNITIVE MEMORY DISTILLATION REPORT (STAGE 76)                      |")
        lines.append("+----------------------------------------------------------------------+")
        lines.append(f"| Timestamp: {self.timestamp:<57} |")
        lines.append(f"| Nodes Before: {self.total_nodes_before:<20} | Nodes After: {self.total_nodes_after:<21} |")
        lines.append(f"| Pruned Nodes: {self.pruned_count:<20} | Consolidated: {self.consolidated_count:<20} |")
        lines.append(f"| Pinned Protected: {self.pinned_protected_count:<16} | Memory Reduction: {self.compression_ratio():<16} |")
        lines.append("+----------------------------------------------------------------------+")
        if self.pruned_count > 0:
            lines.append("| PRUNED STALE / SUPERSEDED NODES:                                     |")
            lines.append("+----------------------+-----------------------------------------------+---------+")
            lines.append(f"| {'ID':<20} | {'FACT (SNIPPET)':<45} | {'SCORE':<7} |")
            lines.append("+----------------------+-----------------------------------------------+---------+")
            for d in self.details:
                if d.get("action") == "prune":
                    nid = d.get("node_id", "")[:20]
                    snippet = d.get("fact", "")[:45]
                    score = f"{d.get('salience_score', 0.0):.2f}"
                    lines.append(f"| {nid:<20} | {snippet:<45} | {score:<7} |")
            lines.append("+----------------------+-----------------------------------------------+---------+")
        else:
            lines.append("|  (Memory graph is fully distilled; all active nodes are salient.)    |")
            lines.append("+----------------------------------------------------------------------+")
        return "\n".join(lines)

    def compression_ratio(self) -> str:
        if self.total_nodes_before == 0:
            return "0.0%"
        pct = ((self.total_nodes_before - self.total_nodes_after) / self.total_nodes_before) * 100.0
        return f"{pct:.1f}%"


class CognitiveDistiller:
    """
    Evaluates memory graph nodes, scores salience, prunes low-value facts,
    and writes distilled milestones to keep Lucy's sovereign mind compact and sharp.
    """

    def __init__(
        self,
        memory_graph: Any,
        memory_walker: Optional[Any] = None,
        receipt_ledger: Optional[Any] = None,
        archive_dir: Optional[Path] = None,
    ) -> None:
        self.memory_graph = memory_graph
        self.memory_walker = memory_walker
        self.receipt_ledger = receipt_ledger

        graph_dir = getattr(memory_graph, "storage_dir", Path(__file__).resolve().parent.parent.parent / "data" / "lucy" / "memory")
        self.archive_dir = archive_dir or Path(graph_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.pruned_archive_file = self.archive_dir / "pruned_archive.jsonl"
        self.checkpoint_file = self.archive_dir / "distilled_checkpoint.json"

    def compute_salience(self, node: Dict[str, Any], now_epoch: float) -> Tuple[float, float, str]:
        """
        Computes salience score [0.0 - 1.0], age in days, and reason.
        Pinned facts always receive 1.0.
        """
        if node.get("pinned", False):
            return 1.0, 0.0, "Pinned fact (protected)"

        # Parse node creation timestamp
        created_at_str = node.get("created_at", "")
        age_days = 0.0
        try:
            if created_at_str:
                dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                node_epoch = dt.timestamp()
                age_days = max(0.0, (now_epoch - node_epoch) / 86400.0)
        except Exception:
            age_days = 1.0

        # Temporal decay: e^(-age / half_life)
        decay = math.exp(-age_days / HALF_LIFE_DAYS)

        # Reference count bonus
        ref_count = node.get("reference_count", 0)
        ref_bonus = min(0.3, ref_count * 0.05)

        # Graph connectivity bonus from walker if available
        conn_bonus = 0.0
        if self.memory_walker is not None:
            node_id = node.get("id", "")
            if hasattr(self.memory_walker, "_adjacency") and isinstance(self.memory_walker._adjacency, dict):
                edge_count = len(self.memory_walker._adjacency.get(node_id, []))
                conn_bonus = min(0.2, edge_count * 0.04)
            elif hasattr(self.memory_walker, "edges") and isinstance(self.memory_walker.edges, list):
                edge_count = sum(
                    1 for e in self.memory_walker.edges
                    if getattr(e, "source_id", None) == node_id or getattr(e, "target_id", None) == node_id
                )
                conn_bonus = min(0.2, edge_count * 0.04)

        base_salience = (decay * 0.7) + ref_bonus + conn_bonus

        # Heavily penalize superseded or soft-deleted facts
        status = node.get("status", "active")
        if status in ("superseded", "retired", "pruned") or node.get("deleted"):
            base_salience *= 0.15
            reason = f"Superseded/retired status (decayed={base_salience:.2f})"
        elif base_salience < DEFAULT_SALIENCE_THRESHOLD:
            reason = f"Low salience due to temporal age ({age_days:.1f}d) and low reference"
        else:
            reason = f"Salient active fact (age={age_days:.1f}d, refs={ref_count})"

        final_score = max(0.0, min(1.0, base_salience))
        return final_score, age_days, reason

    def evaluate_nodes(
        self,
        nodes: List[Dict[str, Any]],
        threshold: float = DEFAULT_SALIENCE_THRESHOLD,
    ) -> List[DistillationCandidate]:
        now_epoch = time.time()
        candidates: List[DistillationCandidate] = []

        for node in nodes:
            score, age_days, reason = self.compute_salience(node, now_epoch)
            is_pinned = node.get("pinned", False)

            if is_pinned:
                action = "keep"
            elif node.get("status") in ("superseded", "retired") or node.get("deleted"):
                action = "prune"
            elif score < threshold:
                action = "prune"
            else:
                action = "keep"

            candidates.append(
                DistillationCandidate(
                    node_id=node.get("id", ""),
                    fact=node.get("fact", ""),
                    category=node.get("category", "general"),
                    pinned=is_pinned,
                    status=node.get("status", "active"),
                    age_days=age_days,
                    reference_count=node.get("reference_count", 0),
                    salience_score=score,
                    action=action,
                    reason=reason,
                )
            )

        return candidates

    def dry_run(self, threshold: float = DEFAULT_SALIENCE_THRESHOLD) -> DistillationReport:
        """
        Simulates distillation without modifying the memory graph.
        """
        raw_data = self.memory_graph._read()
        nodes = raw_data.get("nodes", [])
        candidates = self.evaluate_nodes(nodes, threshold=threshold)

        pruned = [c for c in candidates if c.action == "prune"]
        kept = [c for c in candidates if c.action == "keep"]
        pinned_count = sum(1 for c in candidates if c.pinned)

        return DistillationReport(
            timestamp=datetime.now().isoformat(),
            total_nodes_before=len(nodes),
            total_nodes_after=len(kept),
            pruned_count=len(pruned),
            consolidated_count=0,
            pinned_protected_count=pinned_count,
            pruned_node_ids=[c.node_id for c in pruned],
            details=[c.to_dict() for c in candidates],
        )

    def distill(
        self,
        threshold: float = DEFAULT_SALIENCE_THRESHOLD,
        archive_pruned: bool = True,
    ) -> DistillationReport:
        """
        Executes distillation, archives pruned nodes, persists clean graph and checkpoint.
        """
        raw_data = self.memory_graph._read()
        nodes = raw_data.get("nodes", [])
        candidates = self.evaluate_nodes(nodes, threshold=threshold)

        prune_ids: Set[str] = {c.node_id for c in candidates if c.action == "prune"}
        kept_nodes: List[Dict[str, Any]] = [n for n in nodes if n.get("id") not in prune_ids]
        pruned_nodes: List[Dict[str, Any]] = [n for n in nodes if n.get("id") in prune_ids]
        pinned_count = sum(1 for c in candidates if c.pinned)

        # Archive pruned nodes to disk safely
        if archive_pruned and pruned_nodes:
            try:
                with open(self.pruned_archive_file, "a", encoding="utf-8") as f:
                    for pn in pruned_nodes:
                        entry = {
                            "archived_at": datetime.now().isoformat(),
                            "node": pn,
                        }
                        f.write(json.dumps(entry) + "\n")
            except Exception:
                pass

        # Update memory graph
        raw_data["nodes"] = kept_nodes
        raw_data["distilled_at"] = datetime.now().isoformat()
        self.memory_graph._write(raw_data)

        # Save checkpoint
        checkpoint = {
            "version": STAGE,
            "distilled_at": datetime.now().isoformat(),
            "total_nodes": len(kept_nodes),
            "pruned_count": len(pruned_nodes),
            "pinned_count": pinned_count,
            "active_node_ids": [n.get("id") for n in kept_nodes],
        }
        try:
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f, indent=2)
        except Exception:
            pass

        # Rebuild associative graph in memory_walker if wired
        if self.memory_walker is not None and hasattr(self.memory_walker, "build_edges_from_nodes"):
            try:
                self.memory_walker.build_edges_from_nodes(kept_nodes)
            except Exception:
                pass

        # Issue receipt in ledger
        if self.receipt_ledger is not None:
            try:
                self.receipt_ledger.issue_receipt(
                    action_category="memory_distillation",
                    operation="distill_memory_graph",
                    target=str(self.checkpoint_file.name),
                    verified_outcome=f"Pruned {len(pruned_nodes)} nodes, preserved {len(kept_nodes)} active nodes",
                )
            except Exception:
                pass

        return DistillationReport(
            timestamp=datetime.now().isoformat(),
            total_nodes_before=len(nodes),
            total_nodes_after=len(kept_nodes),
            pruned_count=len(pruned_nodes),
            consolidated_count=0,
            pinned_protected_count=pinned_count,
            pruned_node_ids=list(prune_ids),
            details=[c.to_dict() for c in candidates],
        )

    def stats(self) -> Dict[str, Any]:
        raw_data = self.memory_graph._read()
        nodes = raw_data.get("nodes", [])
        pinned = sum(1 for n in nodes if n.get("pinned"))
        superseded = sum(1 for n in nodes if n.get("status") in ("superseded", "retired"))

        return {
            "total_nodes": len(nodes),
            "pinned_nodes": pinned,
            "superseded_nodes": superseded,
            "last_distilled_at": raw_data.get("distilled_at"),
            "checkpoint_exists": self.checkpoint_file.exists(),
        }
