r"""
tests/test_stage121_neural_knowledge_graph.py
Unit tests for Stage 121: Causal Neural Knowledge Graph & Property Graph Nexus (Era 13).
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.neural_knowledge_graph import (
    NeuralKnowledgeGraphNexus,
    KnowledgeNode,
    KnowledgeEdge,
    STAGE,
    ERA,
    ERA_NAME,
    STAGE_NAME,
    CREATOR_NAME,
    CREATOR_FULL_NAME,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def record_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        self.receipts.append({
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        })


class TestStage121NeuralKnowledgeGraph(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_test_stage121_"))
        self.data_dir = self.test_dir / "data" / "lucy" / "graph"
        self.ledger = MockReceiptLedger()
        self.nexus = NeuralKnowledgeGraphNexus(
            project_root=self.test_dir,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 121)
        self.assertEqual(ERA, 13)
        self.assertEqual(STAGE_NAME, "Causal Neural Knowledge Graph & Property Graph Nexus")
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")

        st = self.nexus.status()
        self.assertEqual(st["stage"], 121)
        self.assertEqual(st["era"], 13)
        self.assertEqual(st["creator"], "Senin")
        self.assertGreaterEqual(st["total_nodes"], 4)
        self.assertGreaterEqual(st["total_edges"], 3)

    def test_02_foundational_identity_anchoring(self):
        op_node = self.nexus.get_node("node:operator:senin")
        self.assertIsNotNone(op_node)
        self.assertEqual(op_node.node_type, "OPERATOR")
        self.assertIn("Senin Ali K P", op_node.label)

        core_node = self.nexus.get_node("node:core:lucy_os")
        self.assertIsNotNone(core_node)
        self.assertEqual(core_node.node_type, "CORE")

        # Verify Lucy OS AUTHORED_BY Senin relation
        edges = self.nexus.get_edges(source_id="node:core:lucy_os", target_id="node:operator:senin")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].relation, "AUTHORED_BY")

    def test_03_node_mutation_and_receipts(self):
        node = self.nexus.add_node(
            node_id="concept:transformer_attention",
            node_type="CONCEPT",
            label="Multi-Head Self-Attention",
            properties={"complexity": "O(N^2)", "domain": "deep_learning"},
            weight=0.95,
        )
        self.assertEqual(node.node_id, "concept:transformer_attention")
        self.assertEqual(node.weight, 0.95)

        # Check receipt
        rec_cats = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("KG_NODE_ADDED", rec_cats)

        # Retrieve
        fetched = self.nexus.get_node("concept:transformer_attention")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.label, "Multi-Head Self-Attention")

    def test_04_edge_mutation_and_adjacency(self):
        self.nexus.add_node("mod:a", "MODULE", "Module A")
        self.nexus.add_node("mod:b", "MODULE", "Module B")
        edge = self.nexus.add_edge("mod:a", "mod:b", "DEPENDS_ON", weight=0.8)

        self.assertEqual(edge.source_id, "mod:a")
        self.assertEqual(edge.target_id, "mod:b")
        self.assertEqual(edge.relation, "DEPENDS_ON")

        out_edges = self.nexus.get_edges(source_id="mod:a")
        self.assertEqual(len(out_edges), 1)
        self.assertEqual(out_edges[0].target_id, "mod:b")

        in_edges = self.nexus.get_edges(target_id="mod:b")
        self.assertEqual(len(in_edges), 1)

    def test_05_shortest_path_bfs(self):
        # A -> B -> C -> D
        self.nexus.add_edge("A", "B", "LINK")
        self.nexus.add_edge("B", "C", "LINK")
        self.nexus.add_edge("C", "D", "LINK")
        self.nexus.add_edge("A", "X", "LINK")  # alternate branch

        path = self.nexus.find_shortest_path("A", "D")
        self.assertEqual(path, ["A", "B", "C", "D"])

        # Disconnected target
        self.nexus.add_node("Z", "ISOLATED", "Isolated Node")
        self.assertIsNone(self.nexus.find_shortest_path("A", "Z"))

    def test_06_causal_chain_backtracking(self):
        # RootCause -> BugFix -> Deployment -> UserDelight
        self.nexus.add_edge("RootCause", "BugFix", "CAUSES")
        self.nexus.add_edge("BugFix", "Deployment", "CAUSES")
        self.nexus.add_edge("Deployment", "UserDelight", "CAUSES")

        chain = self.nexus.find_causal_chain("UserDelight")
        self.assertGreaterEqual(len(chain), 3)
        sources = [e.source_id for e in chain]
        self.assertIn("Deployment", sources)
        self.assertIn("BugFix", sources)
        self.assertIn("RootCause", sources)

    def test_07_contradiction_detection(self):
        self.nexus.add_node("claim:p", "ASSERTION", "System is completely offline")
        self.nexus.add_node("claim:not_p", "ASSERTION", "System requires cloud connection")
        self.nexus.add_edge("claim:p", "claim:not_p", "CONTRADICTS")

        contras = self.nexus.detect_contradictions()
        self.assertEqual(len(contras), 1)
        self.assertEqual(contras[0][0], "claim:p")
        self.assertEqual(contras[0][1], "claim:not_p")

        rec_cats = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("KG_CONTRADICTION_DETECTED", rec_cats)

    def test_08_query_filtering(self):
        self.nexus.add_node("algo:hnsw", "ALGORITHM", "Hierarchical Navigable Small World")
        self.nexus.add_node("algo:dijkstra", "ALGORITHM", "Shortest Path Search")
        self.nexus.add_node("doc:readme", "DOCUMENT", "System Architecture README")

        algos = self.nexus.query(node_type="ALGORITHM")
        self.assertEqual(len(algos), 2)

        matched = self.nexus.query(keyword="navigable")
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0].node_id, "algo:hnsw")

    def test_09_persistence_and_reload(self):
        self.nexus.add_node("persist:node1", "TEST", "Persistent Entity")
        self.nexus.add_edge("persist:node1", "node:core:lucy_os", "REPORTS_TO")

        # Instantiate fresh nexus on same data directory
        fresh = NeuralKnowledgeGraphNexus(
            project_root=self.test_dir,
            data_dir=self.data_dir,
        )
        self.assertIsNotNone(fresh.get_node("persist:node1"))
        edges = fresh.get_edges(source_id="persist:node1", target_id="node:core:lucy_os")
        self.assertEqual(len(edges), 1)

    def test_10_ascii_status_table(self):
        tbl = self.nexus.format_kg_status_table()
        self.assertIn("LUCY OS - CAUSAL NEURAL KNOWLEDGE GRAPH NEXUS", tbl)
        self.assertIn("Total Property Graph Nodes", tbl)
        self.assertIn("Total Multi-Relational Edges", tbl)
        self.assertIn("Senin (Senin Ali K P)", tbl)


if __name__ == "__main__":
    unittest.main()
