"""
memory_walker.py
Stage 72: Memory Graph Associative Edge Walker & Spreading Activation.

Provides multi-hop associative recall across the Temporal Memory Graph.
When a user refers to a project, tool, or topic, spreading activation walks weighted
relational edges (co-occurrence, shared domain, entity linkage, causal lineage)
to retrieve deeply connected memory context even without exact keyword overlap.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

STAGE = "72 memory graph associative edge walker and spreading activation"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokenize(text: str) -> Set[str]:
    return set(re.findall(r"[a-z0-9_]{3,}", text.lower()))


class AssociativeEdge:
    """Represents a weighted connection between two memory nodes."""

    def __init__(
        self,
        source_id: str,
        target_id: str,
        weight: float,
        relation: str,  # "shared_slot", "entity_link", "temporal_session", "causal_lineage"
    ) -> None:
        self.source_id = source_id
        self.target_id = target_id
        self.weight = round(min(1.0, max(0.05, weight)), 3)
        self.relation = relation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "weight": self.weight,
            "relation": self.relation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AssociativeEdge:
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            weight=data["weight"],
            relation=data["relation"],
        )


class SpreadingActivationWalker:
    """
    Constructs relational memory edges and performs spreading activation graph walks.
    """

    def __init__(
        self,
        memory_dir: Optional[Path] = None,
        memory_graph: Any = None,
    ) -> None:
        self.memory_dir = Path(memory_dir).resolve() if memory_dir else Path.cwd() / "data" / "lucy" / "memory"
        self.memory_graph = memory_graph
        self.edges_file = self.memory_dir / "memory_edges.json"

        self.edges: List[AssociativeEdge] = []
        self._adjacency: Dict[str, List[Tuple[str, float, str]]] = {}
        self.total_walks = 0

        self.load_edges()

    def load_edges(self) -> None:
        """Loads edges from disk if present."""
        if not self.edges_file.exists():
            return
        try:
            data = json.loads(self.edges_file.read_text(encoding="utf-8"))
            raw_edges = data.get("edges", [])
            self.edges = [AssociativeEdge.from_dict(e) for e in raw_edges]
            self._rebuild_adjacency()
        except Exception:
            self.edges = []
            self._adjacency = {}

    def save_edges(self) -> None:
        """Saves edges to disk."""
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "stage": STAGE,
                "updated_at": _now_iso(),
                "total_edges": len(self.edges),
                "edges": [e.to_dict() for e in self.edges],
            }
            self.edges_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def _rebuild_adjacency(self) -> None:
        self._adjacency.clear()
        for e in self.edges:
            self._adjacency.setdefault(e.source_id, []).append((e.target_id, e.weight, e.relation))
            self._adjacency.setdefault(e.target_id, []).append((e.source_id, e.weight, e.relation))

    def add_edge(self, source_id: str, target_id: str, weight: float, relation: str) -> None:
        """Adds an associative edge between two nodes if not already present."""
        if source_id == target_id:
            return
        for e in self.edges:
            if (e.source_id == source_id and e.target_id == target_id) or (e.source_id == target_id and e.target_id == source_id):
                # Update weight to highest
                if weight > e.weight:
                    e.weight = weight
                    e.relation = relation
                    self._rebuild_adjacency()
                return

        edge = AssociativeEdge(source_id, target_id, weight, relation)
        self.edges.append(edge)
        self._adjacency.setdefault(source_id, []).append((target_id, weight, relation))
        self._adjacency.setdefault(target_id, []).append((source_id, weight, relation))

    def build_edges_from_nodes(self, nodes: List[Dict[str, Any]]) -> int:
        """
        Infers associative edges from memory nodes based on:
        1. Shared slot domain (e.g. active_project, stack, editor) -> weight 0.85
        2. Entity overlap (token intersection >= 2) -> weight 0.70
        3. Causal lineage (supersedes) -> weight 0.90
        """
        active_nodes = [n for n in nodes if n.get("status", "active") == "active" and not n.get("deleted")]
        initial_count = len(self.edges)

        # 1. Causal lineage edges
        for node in nodes:
            nid = node.get("id")
            for sup_id in node.get("supersedes", []):
                self.add_edge(nid, sup_id, weight=0.90, relation="causal_lineage")

        # 2. Pairwise attribute and token overlap
        for i in range(len(active_nodes)):
            n1 = active_nodes[i]
            id1 = n1.get("id")
            fact1 = str(n1.get("fact") or "")
            slot1 = n1.get("slot_key")
            toks1 = _tokenize(fact1)

            for j in range(i + 1, len(active_nodes)):
                n2 = active_nodes[j]
                id2 = n2.get("id")
                fact2 = str(n2.get("fact") or "")
                slot2 = n2.get("slot_key")
                toks2 = _tokenize(fact2)

                # Shared canonical slot
                if slot1 and slot2 and slot1 == slot2:
                    self.add_edge(id1, id2, weight=0.85, relation=f"shared_slot:{slot1}")
                    continue

                # Token intersection overlap
                common = toks1 & toks2
                if len(common) >= 2:
                    overlap_ratio = len(common) / float(min(len(toks1), len(toks2)))
                    weight = round(0.50 + 0.40 * overlap_ratio, 3)
                    self.add_edge(id1, id2, weight=weight, relation=f"entity_overlap:{len(common)}")

        self.save_edges()
        return len(self.edges) - initial_count

    def walk(
        self,
        seed_node_ids: List[str],
        max_hops: int = 2,
        decay: float = 0.65,
        threshold: float = 0.20,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Executes spreading activation:
        Starts with seed nodes at activation 1.0. Propagates outward across weighted edges,
        decaying with each hop. Returns connected nodes sorted by activation energy.
        """
        self.total_walks += 1
        if not seed_node_ids:
            return []

        # Map: node_id -> (max_activation, path_taken)
        activation_map: Dict[str, Tuple[float, List[str]]] = {}
        queue: List[Tuple[str, float, int, List[str]]] = []

        for sid in seed_node_ids:
            activation_map[sid] = (1.0, [sid])
            queue.append((sid, 1.0, 0, [sid]))

        while queue:
            curr_id, curr_act, hop, path = queue.pop(0)
            if hop >= max_hops:
                continue

            neighbors = self._adjacency.get(curr_id, [])
            for neighbor_id, weight, rel in neighbors:
                propagated = curr_act * weight * decay
                if propagated < threshold:
                    continue

                prev_best, _ = activation_map.get(neighbor_id, (0.0, []))
                if propagated > prev_best:
                    new_path = path + [f"->({rel}:{weight})->{neighbor_id}"]
                    activation_map[neighbor_id] = (propagated, new_path)
                    queue.append((neighbor_id, propagated, hop + 1, new_path))

        # Filter out seed nodes themselves from final results
        seeds_set = set(seed_node_ids)
        results: List[Dict[str, Any]] = []

        # Lookup node facts from memory_graph if available
        node_facts: Dict[str, str] = {}
        if self.memory_graph and hasattr(self.memory_graph, "_read"):
            try:
                g_data = self.memory_graph._read()
                for n in g_data.get("nodes", []):
                    node_facts[n.get("id")] = n.get("fact") or n.get("content", "")
            except Exception:
                pass

        for nid, (score, path) in activation_map.items():
            if nid not in seeds_set:
                results.append({
                    "node_id": nid,
                    "activation": round(score, 3),
                    "fact": node_facts.get(nid, f"Node {nid}"),
                    "path": path,
                })

        results.sort(key=lambda x: x["activation"], reverse=True)
        return results[:limit]

    def format_walk_trace(self, topic: str, walk_results: List[Dict[str, Any]]) -> str:
        """Renders a clean ASCII trace of the associative memory walk."""
        if not walk_results:
            return f"Associative walk for topic '{topic}' reached no connected nodes above threshold."

        lines = [
            f"+--- [Associative Memory Walk: '{topic}'] ---------------------------+",
            f"| Activated Seed Nodes: {len(walk_results)} connected nodes discovered",
        ]
        for idx, res in enumerate(walk_results, start=1):
            nid = res.get("node_id")
            score = res.get("activation")
            fact = res.get("fact", "")[:55]
            lines.append(f"| [{idx}] ({score:.2f}) {nid}: \"{fact}\"")

            path_trace = res.get("path", [])
            if len(path_trace) > 1:
                trace_str = " ".join(path_trace[1:])[:60]
                lines.append(f"|     Trace: {trace_str}")

        lines.append("+------------------------------------------------------------------+")
        return "\n".join(lines)

    def status(self) -> Dict[str, Any]:
        return {
            "stage": STAGE,
            "memory_walker": "active",
            "total_edges": len(self.edges),
            "connected_nodes": len(self._adjacency),
            "total_walks": self.total_walks,
            "edges_file": str(self.edges_file),
        }
