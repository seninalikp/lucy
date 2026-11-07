"""
test_stage72_memory_walker.py
Stage 72: Memory Graph Associative Edge Walker & Spreading Activation Unit Tests.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.memory_walker import (
    AssociativeEdge,
    SpreadingActivationWalker,
    STAGE as STAGE_72,
)
from backend.lucy_core.memory_graph import TemporalMemoryGraph
from backend.lucy_core.conversational_memory import ConversationalMemoryEngine
from backend.lucy_core.lucy_runtime import LucyRuntime


class TestStage72MemoryWalker(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mem_dir = Path(self.temp_dir.name)
        self.walker = SpreadingActivationWalker(memory_dir=self.mem_dir)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_edge_representation_and_serialization(self) -> None:
        edge = AssociativeEdge(
            source_id="mnode_0001",
            target_id="mnode_0002",
            weight=0.85,
            relation="shared_slot:active_project",
        )
        d = edge.to_dict()
        self.assertEqual(d["weight"], 0.85)
        self.assertEqual(d["relation"], "shared_slot:active_project")

        reloaded = AssociativeEdge.from_dict(d)
        self.assertEqual(reloaded.source_id, "mnode_0001")
        self.assertEqual(reloaded.target_id, "mnode_0002")

    def test_02_add_edge_and_adjacency_rebuild(self) -> None:
        self.walker.add_edge("n1", "n2", 0.75, "entity_link")
        self.walker.add_edge("n2", "n3", 0.60, "shared_slot")

        self.assertEqual(len(self.walker.edges), 2)
        self.assertIn("n1", self.walker._adjacency)
        self.assertIn("n2", self.walker._adjacency)
        self.assertIn("n3", self.walker._adjacency)

    def test_03_build_edges_from_memory_nodes(self) -> None:
        nodes = [
            {"id": "n1", "fact": "my primary focus is Drift Music audio pipeline", "slot_key": "focus", "status": "active"},
            {"id": "n2", "fact": "Drift Music uses FastAPI on port 8000", "slot_key": "stack", "status": "active"},
            {"id": "n3", "fact": "I prefer Neovim for Python coding", "slot_key": "editor", "status": "active"},
        ]
        count = self.walker.build_edges_from_nodes(nodes)
        self.assertGreater(count, 0)
        # n1 and n2 share "Drift Music" and should have an entity_overlap edge
        neighbors_n1 = [t[0] for t in self.walker._adjacency.get("n1", [])]
        self.assertIn("n2", neighbors_n1)

    def test_04_spreading_activation_multi_hop_decay(self) -> None:
        # Build chain: n1 --(0.8)--> n2 --(0.8)--> n3
        self.walker.add_edge("n1", "n2", 0.80, "link_1")
        self.walker.add_edge("n2", "n3", 0.80, "link_2")

        # Walk starting at n1 with decay 0.65
        # Hop 1 (n2): 1.0 * 0.8 * 0.65 = 0.52
        # Hop 2 (n3): 0.52 * 0.8 * 0.65 = 0.2704
        results = self.walker.walk(["n1"], max_hops=2, decay=0.65, threshold=0.20)

        self.assertEqual(len(results), 2)
        node_ids = [r["node_id"] for r in results]
        self.assertEqual(node_ids, ["n2", "n3"])
        self.assertAlmostEqual(results[0]["activation"], 0.52, places=2)
        self.assertAlmostEqual(results[1]["activation"], 0.27, places=2)

    def test_05_threshold_filtering(self) -> None:
        self.walker.add_edge("n1", "n2", 0.20, "weak_link")
        # 1.0 * 0.20 * 0.65 = 0.13, below 0.20 threshold
        results = self.walker.walk(["n1"], threshold=0.20)
        self.assertEqual(len(results), 0)

    def test_06_format_walk_trace(self) -> None:
        self.walker.add_edge("n1", "n2", 0.85, "entity_overlap")
        results = self.walker.walk(["n1"], threshold=0.20)
        trace = self.walker.format_walk_trace("Drift Music", results)

        self.assertIn("[Associative Memory Walk: 'Drift Music']", trace)
        self.assertIn("n2", trace)

    def test_07_conversational_memory_associative_injection(self) -> None:
        # Build memory graph with connected nodes
        mg = TemporalMemoryGraph(self.mem_dir)
        mg.upsert_fact("my primary focus is Drift Music")
        mg.upsert_fact("Drift Music backend is built with FastAPI")

        # Build walker edges
        self.walker.memory_graph = mg
        self.walker.build_edges_from_nodes(mg._read()["nodes"])

        engine = ConversationalMemoryEngine(
            lucy_data=self.mem_dir,
            memory_system=mg,
        )
        engine.memory_graph = mg
        engine.memory_walker = self.walker

        # Query "Drift Music"
        mems = engine.get_relevant_memories("Drift Music", limit=4)
        self.assertGreaterEqual(len(mems), 1)

    def test_08_runtime_memory_walker_status(self) -> None:
        runtime = LucyRuntime()
        status = runtime.memory_walker_status()
        self.assertEqual(status.get("stage"), STAGE_72)
        self.assertEqual(status.get("memory_walker"), "active")
        self.assertIn("total_edges", status)

    def test_09_runtime_walk_command(self) -> None:
        runtime = LucyRuntime()
        out = runtime.lucy_respond("/walk Lucy")
        self.assertIn("Associative", out)

    def test_10_persistence_roundtrip(self) -> None:
        self.walker.add_edge("a1", "b2", 0.88, "persistence_test")
        self.walker.save_edges()

        # Load fresh instance pointing to same file
        walker2 = SpreadingActivationWalker(memory_dir=self.mem_dir)
        self.assertEqual(len(walker2.edges), 1)
        self.assertEqual(walker2.edges[0].source_id, "a1")
        self.assertEqual(walker2.edges[0].weight, 0.88)


if __name__ == "__main__":
    unittest.main()
