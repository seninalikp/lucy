r"""
backend/lucy_core/neural_knowledge_graph.py
Stage 121: Causal Neural Knowledge Graph & Property Graph Nexus
Era 13: Self-Reflective Symbolic Mesh & Cognitive Graph Synthesizer

100% offline, sovereign multi-relational property knowledge graph and causal reasoning nexus for Lucy OS:
1. Multi-Relational Directed Property Graph:
   - Stores typed nodes (OPERATOR, CORE, CONCEPT, FILE, ACTION, AXIOM, SUBSYSTEM).
   - Stores directed weighted relations (CAUSES, DEPENDS_ON, AUTHORED_BY, DERIVED_FROM, CONTRADICTS, REGULATES, EXTENDS).
2. Graph Algorithmic Capabilities:
   - Multi-hop shortest path search (Dijkstra / BFS).
   - Root-cause causal chain backward tracking.
   - Epistemic contradiction detection across assertion edges.
   - Subgraph neighborhood extraction with customizable hop depth.
3. Persistent Knowledge Base:
   - Persists graph topology to data/lucy/graph/knowledge_graph.json.
   - Seeds foundational axiomatic graph: Operator identity permanently anchored to Senin (Senin Ali K P).
4. Telemetry & Cryptographic Receipts:
   - Emits KG_NODE_ADDED, KG_EDGE_ADDED, KG_CONTRADICTION_DETECTED receipts.
   - CP1252-safe ASCII graph matrices and CLI commands:
     * /kg-status
     * /kg-query [keyword]
     * /kg-path [source] [target]
     * /kg-contradictions
"""

from __future__ import annotations

import collections
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

STAGE: int = 121
ERA: int = 13
ERA_NAME: str = "Self-Reflective Symbolic Mesh & Cognitive Graph Synthesizer"
STAGE_NAME: str = "Causal Neural Knowledge Graph & Property Graph Nexus"

CREATOR_NAME: str = "Senin"
CREATOR_FULL_NAME: str = "Senin Ali K P"


# =============================================================================
# Graph Primitives
# =============================================================================

@dataclass
class KnowledgeNode:
    node_id: str
    node_type: str
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label,
            "properties": self.properties,
            "weight": round(self.weight, 4),
            "created_at": self.created_at,
        }


@dataclass
class KnowledgeEdge:
    edge_id: str
    source_id: str
    target_id: str
    relation: str
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "weight": round(self.weight, 4),
            "properties": self.properties,
            "created_at": self.created_at,
        }


# =============================================================================
# Neural Knowledge Graph Nexus Core
# =============================================================================

class NeuralKnowledgeGraphNexus:
    """
    Sovereign property knowledge graph and causal reasoning engine.
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
            self.data_dir = self.project_root / "data" / "lucy" / "graph"
        else:
            self.data_dir = Path(data_dir)

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.graph_file = self.data_dir / "knowledge_graph.json"
        self.receipt_ledger = receipt_ledger

        self._lock = threading.RLock()
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._edges: Dict[str, KnowledgeEdge] = {}
        self._adj_out: Dict[str, Set[str]] = collections.defaultdict(set)
        self._adj_in: Dict[str, Set[str]] = collections.defaultdict(set)

        self._load_graph()
        self._seed_foundational_graph()

    # =========================================================================
    # Foundational Graph Seeding
    # =========================================================================

    def _seed_foundational_graph(self) -> None:
        """Injects non-negotiable core identity, system, and architectural axioms."""
        with self._lock:
            # Seed operator node
            op_id = "node:operator:senin"
            if op_id not in self._nodes:
                self.add_node(
                    node_id=op_id,
                    node_type="OPERATOR",
                    label=f"Operator {CREATOR_NAME} ({CREATOR_FULL_NAME})",
                    properties={"name": CREATOR_NAME, "full_name": CREATOR_FULL_NAME, "role": "Creator & Sovereign Authority"},
                    weight=1.0,
                )

            # Seed Lucy OS core node
            core_id = "node:core:lucy_os"
            if core_id not in self._nodes:
                self.add_node(
                    node_id=core_id,
                    node_type="CORE",
                    label="Lucy Autonomous OS Core",
                    properties={"stage": STAGE, "era": ERA, "mode": "100% Offline Sovereign"},
                    weight=1.0,
                )

            # Seed relation: Lucy OS AUTHORED_BY Senin
            edge_id = f"edge:{core_id}:AUTHORED_BY:{op_id}"
            if edge_id not in self._edges:
                self.add_edge(
                    source_id=core_id,
                    target_id=op_id,
                    relation="AUTHORED_BY",
                    weight=1.0,
                    properties={"status": "Permanent Invariant", "immutable": True},
                )

            # Seed Era 12 and Era 13 nodes
            era12_id = "node:era:12"
            if era12_id not in self._nodes:
                self.add_node(
                    node_id=era12_id,
                    node_type="ERA",
                    label="Era 12: Cognitive Matrix & IPC Fabric",
                    properties={"stages": "111-120", "status": "Sealed"},
                    weight=1.0,
                )
                self.add_edge(era12_id, core_id, "EXTENDS", 1.0)

            era13_id = "node:era:13"
            if era13_id not in self._nodes:
                self.add_node(
                    node_id=era13_id,
                    node_type="ERA",
                    label=f"Era 13: {ERA_NAME}",
                    properties={"stages": "121-130", "status": "Active"},
                    weight=1.0,
                )
                self.add_edge(era13_id, era12_id, "DERIVED_FROM", 1.0)
                self.add_edge(era13_id, core_id, "EXTENDS", 1.0)

    # =========================================================================
    # Node & Edge Mutation
    # =========================================================================

    def add_node(
        self,
        node_id: str,
        node_type: str,
        label: str,
        properties: Optional[Dict[str, Any]] = None,
        weight: float = 1.0,
    ) -> KnowledgeNode:
        """Adds or updates a typed property node in the knowledge graph."""
        clean_id = node_id.strip()
        with self._lock:
            node = KnowledgeNode(
                node_id=clean_id,
                node_type=node_type.strip().upper(),
                label=label.strip(),
                properties=properties or {},
                weight=max(0.0, min(weight, 1.0)),
                created_at=time.time(),
            )
            self._nodes[clean_id] = node
            self._persist_graph()

            self._emit_receipt(
                "KG_NODE_ADDED",
                clean_id,
                f"Added graph node [{node.node_type}] '{node.label}'",
            )
            return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeEdge:
        """Adds a directed relation between two nodes, creating placeholders if needed."""
        with self._lock:
            s_id = source_id.strip()
            t_id = target_id.strip()
            rel = relation.strip().upper()

            # Create placeholder nodes if not existent
            if s_id not in self._nodes:
                self.add_node(s_id, "ENTITY", s_id)
            if t_id not in self._nodes:
                self.add_node(t_id, "ENTITY", t_id)

            edge_id = f"edge:{s_id}:{rel}:{t_id}"
            edge = KnowledgeEdge(
                edge_id=edge_id,
                source_id=s_id,
                target_id=t_id,
                relation=rel,
                weight=max(0.0, min(weight, 1.0)),
                properties=properties or {},
                created_at=time.time(),
            )

            self._edges[edge_id] = edge
            self._adj_out[s_id].add(edge_id)
            self._adj_in[t_id].add(edge_id)
            self._persist_graph()

            self._emit_receipt(
                "KG_EDGE_ADDED",
                edge_id,
                f"Added edge ({s_id}) -[{rel}]-> ({t_id})",
            )

            if rel == "CONTRADICTS":
                self._emit_receipt(
                    "KG_CONTRADICTION_DETECTED",
                    edge_id,
                    f"Contradiction edge recorded between {s_id} and {t_id}",
                )

            return edge

    def remove_node(self, node_id: str) -> bool:
        clean_id = node_id.strip()
        with self._lock:
            if clean_id not in self._nodes:
                return False

            # Remove associated edges
            edges_to_remove = set(self._adj_out.get(clean_id, set())) | set(self._adj_in.get(clean_id, set()))
            for e_id in edges_to_remove:
                if e_id in self._edges:
                    edge = self._edges[e_id]
                    self._adj_out[edge.source_id].discard(e_id)
                    self._adj_in[edge.target_id].discard(e_id)
                    del self._edges[e_id]

            self._adj_out.pop(clean_id, None)
            self._adj_in.pop(clean_id, None)
            del self._nodes[clean_id]
            self._persist_graph()
            return True

    def remove_edge(self, edge_id: str) -> bool:
        with self._lock:
            if edge_id not in self._edges:
                return False
            edge = self._edges[edge_id]
            self._adj_out[edge.source_id].discard(edge_id)
            self._adj_in[edge.target_id].discard(edge_id)
            del self._edges[edge_id]
            self._persist_graph()
            return True

    # =========================================================================
    # Queries & Traversal
    # =========================================================================

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        with self._lock:
            return self._nodes.get(node_id.strip())

    def get_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation: Optional[str] = None,
    ) -> List[KnowledgeEdge]:
        with self._lock:
            res: List[KnowledgeEdge] = []
            rel_u = relation.strip().upper() if relation else None

            if source_id:
                candidate_eids = self._adj_out.get(source_id.strip(), set())
                candidates = [self._edges[eid] for eid in candidate_eids if eid in self._edges]
            elif target_id:
                candidate_eids = self._adj_in.get(target_id.strip(), set())
                candidates = [self._edges[eid] for eid in candidate_eids if eid in self._edges]
            else:
                candidates = list(self._edges.values())

            for e in candidates:
                if target_id and e.target_id != target_id.strip():
                    continue
                if source_id and e.source_id != source_id.strip():
                    continue
                if rel_u and e.relation != rel_u:
                    continue
                res.append(e)
            return res

    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Finds shortest unweighted path using Breadth-First Search."""
        s = source_id.strip()
        t = target_id.strip()
        with self._lock:
            if s not in self._nodes or t not in self._nodes:
                return None
            if s == t:
                return [s]

            queue = collections.deque([[s]])
            visited = {s}

            while queue:
                path = queue.popleft()
                curr = path[-1]

                for eid in self._adj_out.get(curr, set()):
                    edge = self._edges.get(eid)
                    if not edge:
                        continue
                    nxt = edge.target_id
                    if nxt == t:
                        return path + [nxt]
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(path + [nxt])

            return None

    def find_causal_chain(self, effect_node_id: str, max_depth: int = 5) -> List[KnowledgeEdge]:
        """
        Backtracks causal lineage upstream (edges of type CAUSES, DEPENDS_ON, DERIVED_FROM).
        """
        chain: List[KnowledgeEdge] = []
        visited_nodes: Set[str] = set()

        def _traverse(curr_id: str, depth: int):
            if depth >= max_depth or curr_id in visited_nodes:
                return
            visited_nodes.add(curr_id)

            # Inbound edges indicate what caused or was derived into curr_id
            for eid in self._adj_in.get(curr_id, set()):
                e = self._edges.get(eid)
                if not e:
                    continue
                if e.relation in {"CAUSES", "DEPENDS_ON", "DERIVED_FROM"}:
                    chain.append(e)
                    _traverse(e.source_id, depth + 1)

        with self._lock:
            _traverse(effect_node_id.strip(), 0)

        return chain

    def detect_contradictions(self) -> List[Tuple[str, str, str]]:
        """
        Returns list of (source_id, target_id, reason) for conflicting relations.
        """
        contradictions: List[Tuple[str, str, str]] = []
        with self._lock:
            for e in self._edges.values():
                if e.relation == "CONTRADICTS":
                    s_label = self._nodes.get(e.source_id, KnowledgeNode(e.source_id, "", e.source_id)).label
                    t_label = self._nodes.get(e.target_id, KnowledgeNode(e.target_id, "", e.target_id)).label
                    contradictions.append((e.source_id, e.target_id, f"Explicit contradiction: '{s_label}' vs '{t_label}'"))
        return contradictions

    def query(
        self,
        node_type: Optional[str] = None,
        relation: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> List[KnowledgeNode]:
        """Queries graph nodes by type, edge relation, or text keyword."""
        with self._lock:
            res: List[KnowledgeNode] = []
            type_u = node_type.strip().upper() if node_type else None
            kw_l = keyword.strip().lower() if keyword else None

            for n in self._nodes.values():
                if type_u and n.node_type != type_u:
                    continue
                if kw_l:
                    text_blob = f"{n.node_id} {n.label} {json.dumps(n.properties)}".lower()
                    if kw_l not in text_blob:
                        continue
                if relation:
                    # Node must be involved in an edge with this relation
                    has_rel = any(
                        self._edges[eid].relation == relation.strip().upper()
                        for eid in self._adj_out.get(n.node_id, set()) | self._adj_in.get(n.node_id, set())
                        if eid in self._edges
                    )
                    if not has_rel:
                        continue
                res.append(n)
            return res

    # =========================================================================
    # Persistence & Receipts
    # =========================================================================

    def _persist_graph(self) -> None:
        try:
            data = {
                "version": "1.0",
                "stage": STAGE,
                "era": ERA,
                "updated_at": time.time(),
                "nodes": [n.to_dict() for n in self._nodes.values()],
                "edges": [e.to_dict() for e in self._edges.values()],
            }
            tmp = self.graph_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp.replace(self.graph_file)
        except Exception:
            pass

    def _load_graph(self) -> None:
        if not self.graph_file.exists():
            return
        try:
            with open(self.graph_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for d in data.get("nodes", []):
                node = KnowledgeNode(
                    node_id=d["node_id"],
                    node_type=d["node_type"],
                    label=d["label"],
                    properties=d.get("properties", {}),
                    weight=d.get("weight", 1.0),
                    created_at=d.get("created_at", time.time()),
                )
                self._nodes[node.node_id] = node

            for d in data.get("edges", []):
                edge = KnowledgeEdge(
                    edge_id=d["edge_id"],
                    source_id=d["source_id"],
                    target_id=d["target_id"],
                    relation=d["relation"],
                    weight=d.get("weight", 1.0),
                    properties=d.get("properties", {}),
                    created_at=d.get("created_at", time.time()),
                )
                self._edges[edge.edge_id] = edge
                self._adj_out[edge.source_id].add(edge.edge_id)
                self._adj_in[edge.target_id].add(edge.edge_id)
        except Exception:
            pass

    def _emit_receipt(self, action_cat: str, target: str, outcome: str) -> None:
        if self.receipt_ledger and hasattr(self.receipt_ledger, "record_receipt"):
            try:
                self.receipt_ledger.record_receipt(
                    action_category=action_cat,
                    operation="neural_knowledge_graph",
                    target=target,
                    verified_outcome=outcome,
                )
            except Exception:
                pass

    # =========================================================================
    # ASCII Reports & Status
    # =========================================================================

    def format_kg_status_table(self) -> str:
        """Renders CP1252-safe ASCII table of knowledge graph metrics."""
        with self._lock:
            n_cnt = len(self._nodes)
            e_cnt = len(self._edges)
            density = (e_cnt / max(1, n_cnt * (n_cnt - 1))) if n_cnt > 1 else 0.0
            contras = len(self.detect_contradictions())

        lines = [
            "+--------------------------------------------------------------------------------+",
            "|                LUCY OS - CAUSAL NEURAL KNOWLEDGE GRAPH NEXUS                   |",
            "+--------------------------------------+-----------------------------------------+",
            "| Knowledge Graph Telemetry Metric     | Current Operational Value               |",
            "+--------------------------------------+-----------------------------------------+",
            f"| Total Property Graph Nodes           | {f'{n_cnt} entities & concepts'.ljust(39)} |",
            f"| Total Multi-Relational Edges         | {f'{e_cnt} directed relations'.ljust(39)} |",
            f"| Graph Topological Density            | {f'{density:.4f} edge/node ratio'.ljust(39)} |",
            f"| Epistemic Contradictions Flagged     | {f'{contras} conflicting assertions'.ljust(39)} |",
            f"| Sovereign Operator Identity          | {f'{CREATOR_NAME} ({CREATOR_FULL_NAME})'.ljust(39)} |",
            f"| Offline Symbolic Reasoning           | {'100% DETERMINISTIC LOCAL MESH'.ljust(39)} |",
            "+--------------------------------------+-----------------------------------------+",
            "",
            "+------------------------+--------------+----------------------------------------+",
            "| Node Identifier        | Type         | Label                                  |",
            "+------------------------+--------------+----------------------------------------+",
        ]

        with self._lock:
            sample_nodes = list(self._nodes.values())[:8]

        for n in sample_nodes:
            id_s = n.node_id[:22].ljust(22)
            typ_s = n.node_type[:12].ljust(12)
            lbl_s = (n.label[:36] + ".." if len(n.label) > 36 else n.label).ljust(38)
            lines.append(f"| {id_s} | {typ_s} | {lbl_s} |")

        lines.append("+------------------------+--------------+----------------------------------------+")
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
                "total_nodes": len(self._nodes),
                "total_edges": len(self._edges),
                "contradictions_count": len(self.detect_contradictions()),
            }
