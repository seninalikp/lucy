r"""
backend/lucy_core/causal_dag_memory.py
Stage 97: Causal DAG Epistemic Memory & Counterfactual Timeline

Provides sovereign causal graph memory, root-cause lineage tracing, and counterfactual simulation:
1. Directed Acyclic Graph (DAG) Event Engine:
   - Records discrete system, user, tool, self-healing, and code patch events as CausalNodes
   - Tracks ancestor causes (cause_ids) and downstream consequences (consequence_ids)
   - Guarantees strict acyclicity and topological ordering
2. Causal "Why" Inference Engine:
   - Traces ancestral path from any decision or failure back to its root cause
   - Synthesizes clear, step-by-step causal explanations
   - Discloses epistemic certainty and contributing environmental context
3. Counterfactual Timeline Simulator:
   - Replays timelines under hypothetical interventions ("What if step X failed or was skipped?")
   - Traces downstream branch divergence and quantifies averted consequences
4. Timeline Visibility & Persistence:
   - /causal-why <event_or_id>
   - /dag-timeline
   - /counterfactual-replay <event_id> [intervention]
   - /prune-dag
   - Strict CP1252-safe ASCII table formatting (+, -, |)
   - Manifest persistence at data/lucy/causal_dag/causal_memory.json
"""

from __future__ import annotations

import collections
import hashlib
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 97


class CausalEventType(str, Enum):
    USER_INTENT = "USER_INTENT"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    CODE_PATCH = "CODE_PATCH"
    SELF_HEAL = "SELF_HEAL"
    BELIEF_UPDATE = "BELIEF_UPDATE"
    SPEC_REALIGNMENT = "SPEC_REALIGNMENT"
    WORKTREE_MERGE = "WORKTREE_MERGE"
    SYSTEM_DECISION = "SYSTEM_DECISION"


@dataclass
class CausalNode:
    node_id: str
    event_type: str
    title: str
    details: str
    timestamp: str
    cause_ids: List[str] = field(default_factory=list)
    consequence_ids: List[str] = field(default_factory=list)
    context_state: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    counterfactual_notes: str = ""
    is_synthetic: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CausalChain:
    query: str
    target_node: Optional[CausalNode]
    path_nodes: List[CausalNode]
    root_causes: List[CausalNode]
    depth: int
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "target_node": self.target_node.to_dict() if self.target_node else None,
            "path_nodes": [n.to_dict() for n in self.path_nodes],
            "root_causes": [r.to_dict() for r in self.root_causes],
            "depth": self.depth,
            "explanation": self.explanation,
        }

    def format_terminal_summary(self) -> str:
        lines: List[str] = [
            "+----------------------------------------------------------------------+",
            "| CAUSAL ROOT-CAUSE LINEAGE EXPLANATION (STAGE 97)                     |",
            "+----------------------------------------------------------------------+",
            f"| Query Target:      {self.query[:48]:<48} |",
            f"| Causal Depth:      {self.depth:<17} | Root Causes:       {len(self.root_causes):<17} |",
            "+----------------------------------------------------------------------+",
        ]
        if self.path_nodes:
            lines.append("| STEP-BY-STEP CAUSAL INFERENCE CHAIN:                                 |")
            lines.append("+----+----------+----------------------+-------------------------------+");
            lines.append("| #  | NODE ID  | TYPE                 | EVENT TITLE                   |")
            lines.append("+----+----------+----------------------+-------------------------------+");
            for idx, n in enumerate(self.path_nodes, 1):
                nid = (n.node_id[:8]).ljust(8)
                etype = (n.event_type[:20]).ljust(20)
                title = (n.title[:29]).ljust(29)
                lines.append(f"| {idx:<2} | {nid} | {etype} | {title} |")
            lines.append("+----+----------+----------------------+-------------------------------+");
            lines.append("| CAUSAL SYNTHESIS NARRATIVE:                                          |")
            for line in self.explanation.splitlines():
                while len(line) > 68:
                    lines.append(f"| {line[:68]} |")
                    line = line[68:]
                lines.append(f"| {line:<68} |")
            lines.append("+----------------------------------------------------------------------+");
        else:
            lines.append(f"| [Notice] No matching causal node found for query: '{self.query}'. |")
            lines.append("+----------------------------------------------------------------------+")
        return "\n".join(lines)


@dataclass
class CounterfactualTimelineResult:
    original_node_id: str
    original_event_title: str
    intervention: str
    branch_timeline_id: str
    averted_consequences: List[str]
    divergence_score: float
    narrative: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def format_terminal_summary(self) -> str:
        lines: List[str] = [
            "+----------------------------------------------------------------------+",
            "| COUNTERFACTUAL TIMELINE SIMULATION (STAGE 97)                        |",
            "+----------------------------------------------------------------------+",
            f"| Branch ID:         {self.branch_timeline_id:<17} | Divergence Score:  {self.divergence_score:.2f}{'':<13} |",
            f"| Intervention Node: {self.original_node_id:<17} | Averted Events:    {len(self.averted_consequences):<17} |",
            f"| Target Event:      {self.original_event_title[:48]:<48} |",
            f"| Intervention:      {self.intervention[:48]:<48} |",
            "+----------------------------------------------------------------------+",
            "| COUNTERFACTUAL NARRATIVE & DIVERGENCE:                               |",
        ]
        for line in self.narrative.splitlines():
            while len(line) > 68:
                lines.append(f"| {line[:68]} |")
                line = line[68:]
            lines.append(f"| {line:<68} |")
        lines.append("+----------------------------------------------------------------------+")
        if self.averted_consequences:
            lines.append("| AVERTED OR INVALIDATED DOWNSTREAM CONSEQUENCES:                      |")
            for ac in self.averted_consequences:
                ac_clean = (ac[:66]).ljust(66)
                lines.append(f"| * {ac_clean} |")
            lines.append("+----------------------------------------------------------------------+")
        return "\n".join(lines)


@dataclass
class DAGTimelineSummary:
    total_nodes: int
    total_edges: int
    root_nodes_count: int
    terminal_nodes_count: int
    timeline_nodes: List[CausalNode] = field(default_factory=list)

    def format_terminal_summary(self) -> str:
        lines: List[str] = [
            "+----------------------------------------------------------------------+",
            "| CAUSAL DAG TIMELINE & EPISTEMIC MEMORY (STAGE 97)                    |",
            "+----------------------------------------------------------------------+",
            f"| Total Events:      {self.total_nodes:<17} | Total Causal Links:{self.total_edges:<18} |",
            f"| Root Causes:       {self.root_nodes_count:<17} | Terminal Nodes:    {self.terminal_nodes_count:<18} |",
            "+----------------------------------------------------------------------+",
        ]
        if self.timeline_nodes:
            lines.append("| CHRONOLOGICAL TOPOLOGICAL TIMELINE:                                  |")
            lines.append("+----------+----------------------+--------+---------------------------+");
            lines.append("| NODE ID  | EVENT TYPE           | PARENTS| EVENT TITLE               |")
            lines.append("+----------+----------------------+--------+---------------------------+");
            for n in self.timeline_nodes[-12:]:  # Show recent 12
                nid = (n.node_id[:8]).ljust(8)
                etype = (n.event_type[:20]).ljust(20)
                parents = f"{len(n.cause_ids)} in"[:6].ljust(6)
                title = (n.title[:25]).ljust(25)
                lines.append(f"| {nid} | {etype} | {parents} | {title} |")
            lines.append("+----------+----------------------+--------+---------------------------+");
        else:
            lines.append("| STATUS: CAUSAL MEMORY DAG EMPTY                                      |")
            lines.append("+----------------------------------------------------------------------+")
        return "\n".join(lines)


class CausalDAGMemoryEngine:
    """
    Directed Acyclic Graph (DAG) Epistemic Memory and Counterfactual Engine.
    Records causal lineage, resolves 'why' questions by tracing root causes,
    and simulates counterfactual interventions.
    """

    def __init__(
        self,
        project_root: Optional[Union[str, Path]] = None,
        runtime: Optional[Any] = None,
        receipt_ledger: Optional[Any] = None,
        data_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parent.parent.parent
        self.runtime = runtime
        self.receipt_ledger = receipt_ledger
        self.data_dir = Path(data_dir) if data_dir else (self.project_root / "data" / "lucy" / "causal_dag")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.data_dir / "causal_memory.json"
        self.nodes: Dict[str, CausalNode] = {}
        self._load_memory()

    def record_event(
        self,
        title: str,
        event_type: str = "SYSTEM_DECISION",
        details: str = "",
        cause_ids: Optional[List[str]] = None,
        context_state: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
    ) -> CausalNode:
        """
        Records a discrete event node in the Causal DAG, linking it to direct causal predecessors.
        Maintains forward and backward adjacency and prevents cycles.
        """
        now_ts = datetime.now(timezone.utc).isoformat()
        digest = hashlib.sha256((title + now_ts + str(time.perf_counter())).encode("utf-8")).hexdigest()[:8]
        node_id = f"cnode_{digest}"

        valid_causes: List[str] = []
        if cause_ids:
            for cid in cause_ids:
                if cid in self.nodes and cid != node_id and not self._is_ancestor(node_id, cid):
                    valid_causes.append(cid)

        node = CausalNode(
            node_id=node_id,
            event_type=event_type,
            title=title,
            details=details or title,
            timestamp=now_ts,
            cause_ids=valid_causes,
            consequence_ids=[],
            context_state=context_state or {},
            confidence=max(0.0, min(confidence, 1.0)),
        )

        self.nodes[node_id] = node

        # Update parent forward links
        for cid in valid_causes:
            if node_id not in self.nodes[cid].consequence_ids:
                self.nodes[cid].consequence_ids.append(node_id)

        self._save_memory()

        # Emit receipt
        self._record_receipt(
            "CAUSAL_MEMORY",
            "record_event",
            node_id,
            f"type={event_type}, title='{title[:30]}', parents={len(valid_causes)}",
        )

        return node

    def causal_why(self, target_query_or_id: str) -> CausalChain:
        """
        Explains why a decision, action, or failure occurred by tracing ancestors to root causes.
        Returns a structured CausalChain with step-by-step path and synthesis narrative.
        """
        target = self._find_node(target_query_or_id)
        if not target:
            return CausalChain(
                query=target_query_or_id,
                target_node=None,
                path_nodes=[],
                root_causes=[],
                depth=0,
                explanation=f"No matching event found in Causal DAG memory for query: '{target_query_or_id}'.",
            )

        # Trace all ancestors via BFS
        ancestors: Dict[str, CausalNode] = {}
        queue: collections.deque[str] = collections.deque(target.cause_ids)
        visited: Set[str] = set(target.cause_ids)

        while queue:
            cid = queue.popleft()
            if cid in self.nodes:
                cnode = self.nodes[cid]
                ancestors[cid] = cnode
                for parent_id in cnode.cause_ids:
                    if parent_id not in visited and parent_id in self.nodes:
                        visited.add(parent_id)
                        queue.append(parent_id)

        # Identify root causes (nodes with no causes)
        root_causes = [n for n in ancestors.values() if not n.cause_ids]
        if not root_causes and not ancestors:
            root_causes = [target]  # Target itself is root cause

        # Build chronological path from earliest root cause to target
        path_nodes = sorted(list(ancestors.values()), key=lambda x: x.timestamp)
        path_nodes.append(target)
        depth = len(path_nodes)

        # Synthesize narrative explanation
        if len(path_nodes) == 1:
            narrative = f"'{target.title}' is a self-originating root event with no antecedent causal dependencies recorded."
        else:
            steps = [f"Step {i}: [{n.event_type}] {n.title}" for i, n in enumerate(path_nodes, 1)]
            narrative = (
                f"Lineage for '{target.title}':\n"
                f"Originated from {len(root_causes)} primary root cause(s).\n"
                + " -> \n".join(steps)
            )

        return CausalChain(
            query=target_query_or_id,
            target_node=target,
            path_nodes=path_nodes,
            root_causes=root_causes,
            depth=depth,
            explanation=narrative,
        )

    def counterfactual_replay(self, node_id_or_title: str, intervention: str) -> CounterfactualTimelineResult:
        """
        Simulates an alternative timeline under hypothetical intervention at a given event node.
        Traces which downstream events would be averted or altered.
        """
        node = self._find_node(node_id_or_title)
        if not node:
            return CounterfactualTimelineResult(
                original_node_id=node_id_or_title,
                original_event_title=node_id_or_title,
                intervention=intervention,
                branch_timeline_id="branch_none",
                averted_consequences=[],
                divergence_score=0.0,
                narrative=f"Event '{node_id_or_title}' not found in causal memory to branch counterfactual timeline.",
            )

        # Trace all downstream consequences recursively
        downstream: List[CausalNode] = []
        queue = collections.deque(node.consequence_ids)
        visited = set(node.consequence_ids)

        while queue:
            cid = queue.popleft()
            if cid in self.nodes:
                child = self.nodes[cid]
                downstream.append(child)
                for next_id in child.consequence_ids:
                    if next_id not in visited and next_id in self.nodes:
                        visited.add(next_id)
                        queue.append(next_id)

        averted = [f"[{d.event_type}] {d.title}" for d in downstream]
        total_graph_size = max(len(self.nodes), 1)
        divergence = len(downstream) / total_graph_size

        timeline_id = f"cf_{hashlib.sha256((node.node_id + intervention).encode('utf-8')).hexdigest()[:8]}"
        narrative = (
            f"Counterfactual Branch '{timeline_id}':\n"
            f"Intervention: '{intervention}' applied at '{node.title}' ({node.node_id}).\n"
            f"Result: {len(downstream)} downstream consequence(s) averted or fundamentally altered."
        )

        return CounterfactualTimelineResult(
            original_node_id=node.node_id,
            original_event_title=node.title,
            intervention=intervention,
            branch_timeline_id=timeline_id,
            averted_consequences=averted,
            divergence_score=round(divergence, 3),
            narrative=narrative,
        )

    def dag_timeline(self, limit: int = 15) -> str:
        """Renders CP1252-safe ASCII timeline table of the Causal DAG."""
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.timestamp)
        roots = sum(1 for n in sorted_nodes if not n.cause_ids)
        terminals = sum(1 for n in sorted_nodes if not n.consequence_ids)
        total_edges = sum(len(n.consequence_ids) for n in sorted_nodes)

        summary = DAGTimelineSummary(
            total_nodes=len(sorted_nodes),
            total_edges=total_edges,
            root_nodes_count=roots,
            terminal_nodes_count=terminals,
            timeline_nodes=sorted_nodes[-limit:],
        )
        return summary.format_terminal_summary()

    def prune_dag(self, max_nodes: int = 500, preserve_roots: bool = True) -> int:
        """
        Prunes older nodes beyond max_nodes while preserving transitive causal connectivity.
        Connects grandparents directly to grandchildren to maintain root-cause reachability.
        """
        if len(self.nodes) <= max_nodes:
            return 0

        excess = len(self.nodes) - max_nodes
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.timestamp)

        pruned_count = 0
        for n in sorted_nodes:
            if pruned_count >= excess:
                break
            if preserve_roots and not n.cause_ids:
                continue

            # Shortcut edges
            for pid in n.cause_ids:
                if pid in self.nodes:
                    parent = self.nodes[pid]
                    if n.node_id in parent.consequence_ids:
                        parent.consequence_ids.remove(n.node_id)
                    for cid in n.consequence_ids:
                        if cid not in parent.consequence_ids:
                            parent.consequence_ids.append(cid)

            for cid in n.consequence_ids:
                if cid in self.nodes:
                    child = self.nodes[cid]
                    if n.node_id in child.cause_ids:
                        child.cause_ids.remove(n.node_id)
                    for pid in n.cause_ids:
                        if pid not in child.cause_ids:
                            child.cause_ids.append(pid)

            del self.nodes[n.node_id]
            pruned_count += 1

        self._save_memory()
        return pruned_count

    def status(self) -> Dict[str, Any]:
        """Returns diagnostic status dictionary of the Causal DAG engine."""
        nodes = list(self.nodes.values())
        return {
            "stage": STAGE,
            "total_causal_nodes": len(nodes),
            "total_causal_edges": sum(len(n.consequence_ids) for n in nodes),
            "root_nodes": sum(1 for n in nodes if not n.cause_ids),
            "memory_file": str(self.memory_file),
        }

    # --- Internal Helpers ---

    def _find_node(self, query: str) -> Optional[CausalNode]:
        clean = query.strip()
        if clean in self.nodes:
            return self.nodes[clean]
        low = clean.lower()
        # Search by exact node ID or partial title match
        for n in reversed(list(self.nodes.values())):
            if low == n.node_id.lower() or low in n.title.lower():
                return n
        return None

    def _is_ancestor(self, potential_ancestor: str, start_node: str) -> bool:
        """Returns True if potential_ancestor is reachable by following cause_ids from start_node."""
        visited: Set[str] = set()
        queue = collections.deque([start_node])
        while queue:
            curr = queue.popleft()
            if curr == potential_ancestor:
                return True
            if curr in self.nodes:
                for parent_id in self.nodes[curr].cause_ids:
                    if parent_id not in visited:
                        visited.add(parent_id)
                        queue.append(parent_id)
        return False

    def _record_receipt(
        self,
        action_category: str,
        operation: str,
        target: str,
        verified_outcome: str,
    ) -> Optional[Dict[str, Any]]:
        ledger = self.receipt_ledger or (getattr(self.runtime, "receipt_ledger", None) if self.runtime else None)
        if ledger:
            try:
                if hasattr(ledger, "issue_receipt"):
                    return ledger.issue_receipt(action_category, operation, target, verified_outcome)
                elif hasattr(ledger, "record_receipt"):
                    return ledger.record_receipt(action_category, operation, target, verified_outcome)
            except Exception:
                pass
        return None

    def _save_memory(self) -> None:
        try:
            data = {nid: n.to_dict() for nid, n in self.nodes.items()}
            self.memory_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_memory(self) -> None:
        if not self.memory_file.exists():
            return
        try:
            data = json.loads(self.memory_file.read_text(encoding="utf-8"))
            for nid, d in data.items():
                self.nodes[nid] = CausalNode(
                    node_id=d["node_id"],
                    event_type=d["event_type"],
                    title=d["title"],
                    details=d.get("details", d["title"]),
                    timestamp=d["timestamp"],
                    cause_ids=d.get("cause_ids", []),
                    consequence_ids=d.get("consequence_ids", []),
                    context_state=d.get("context_state", {}),
                    confidence=d.get("confidence", 1.0),
                    counterfactual_notes=d.get("counterfactual_notes", ""),
                    is_synthetic=d.get("is_synthetic", False),
                )
        except Exception:
            pass
