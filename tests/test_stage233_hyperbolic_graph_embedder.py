r"""
tests/test_stage233_hyperbolic_graph_embedder.py
Stage 233 Unit Tests: Autonomous Non-Euclidean Hyperbolic Knowledge Graph Embedding
"""

import threading
import unittest

from backend.lucy_core.hyperbolic_graph_embedder import (
    HyperbolicGraphEmbedderFabric,
    clip_to_ball,
    euclidean_norm,
    mobius_addition,
    poincare_geodesic_distance,
    STAGE,
    STAGE_NAME,
)


class TestStage233HyperbolicGraphEmbedder(unittest.TestCase):
    def setUp(self):
        self.fabric = HyperbolicGraphEmbedderFabric(dimension=5)

    def test_01_initialization_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 233)
        self.assertEqual(s["stage_name"], STAGE_NAME)
        self.assertEqual(s["dimension"], 5)
        self.assertEqual(s["total_nodes"], 5)
        self.assertIn("RootEntity", self.fabric.nodes)

    def test_02_clip_to_poincare_ball(self):
        outside = [2.0, 3.0, 0.0, 0.0, 0.0]
        clipped = clip_to_ball(outside)
        norm = euclidean_norm(clipped)
        self.assertLess(norm, 1.0)
        self.assertGreater(norm, 0.99)

    def test_03_geodesic_distance_properties(self):
        p1 = [0.1, 0.2, 0.0, 0.0, 0.0]
        p2 = [-0.1, 0.3, 0.1, 0.0, 0.0]
        # Identity
        self.assertAlmostEqual(poincare_geodesic_distance(p1, p1), 0.0, places=4)
        # Symmetry
        d12 = poincare_geodesic_distance(p1, p2)
        d21 = poincare_geodesic_distance(p2, p1)
        self.assertAlmostEqual(d12, d21, places=4)
        self.assertGreater(d12, 0.0)

    def test_04_exponential_hyperbolic_expansion_near_boundary(self):
        # Two pairs separated by identical Euclidean distance 0.05
        # Pair A near origin: [0.0, 0.0] and [0.05, 0.0]
        # Pair B near boundary: [0.90, 0.0] and [0.95, 0.0]
        p_origin_1 = [0.0] * 5
        p_origin_2 = [0.05] + [0.0] * 4
        dist_origin = poincare_geodesic_distance(p_origin_1, p_origin_2)

        p_bound_1 = [0.90] + [0.0] * 4
        p_bound_2 = [0.95] + [0.0] * 4
        dist_boundary = poincare_geodesic_distance(p_bound_1, p_bound_2)

        # In hyperbolic geometry, distance near the boundary is exponentially larger!
        self.assertGreater(dist_boundary, dist_origin * 4.0)

    def test_05_mobius_addition(self):
        u = [0.1, 0.0, 0.0, 0.0, 0.0]
        v = [0.2, 0.0, 0.0, 0.0, 0.0]
        sum_uv = mobius_addition(u, v)
        # Mobius sum of collinear vectors: (0.1 + 0.2) / (1 + 0.1*0.2) = 0.3 / 1.02 ~ 0.2941
        self.assertAlmostEqual(sum_uv[0], 0.3 / 1.02, places=3)
        self.assertLess(euclidean_norm(sum_uv), 1.0)

    def test_06_hierarchical_norm_embedding(self):
        root = self.fabric.nodes["RootEntity"]
        sovereign_agi = self.fabric.nodes["SovereignAGI"]
        # Root is at level 0 (near origin: norm == 0)
        self.assertEqual(root.norm, 0.0)
        # SovereignAGI is at level 2 (norm ~ 0.70)
        self.assertGreater(sovereign_agi.norm, 0.6)

    def test_07_add_custom_node_and_edge(self):
        node = self.fabric.add_node("DeepSpaceSatellite", level=3, parent_id="OrbitalStation")
        self.assertEqual(node.node_id, "DeepSpaceSatellite")
        self.assertEqual(node.level, 3)
        self.assertIn(("OrbitalStation", "DeepSpaceSatellite", 1.0), self.fabric.edges)

    def test_08_nearest_neighbor_search(self):
        nn = self.fabric.find_nearest_neighbors("CognitiveAgent", top_k=2)
        self.assertEqual(len(nn), 2)
        # Closest nodes should include parent or child
        neighbors = [x[0] for x in nn]
        self.assertTrue("RootEntity" in neighbors or "SovereignAGI" in neighbors)

    def test_09_riemannian_optimization_step(self):
        initial_dist = self.fabric.compute_distance("CognitiveAgent", "SovereignAGI")
        loss = self.fabric.optimize_embedding_step(lr=0.1)
        self.assertGreater(loss, 0.0)
        new_dist = self.fabric.compute_distance("CognitiveAgent", "SovereignAGI")
        self.assertLessEqual(new_dist, initial_dist)

    def test_10_cp1252_safe_ascii_and_concurrency(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 233", tbl)
        self.assertIn("HYPERBOLIC KNOWLEDGE GRAPH", tbl)
        tbl.encode("cp1252")
        self.assertTrue(tbl.startswith("+--"))

        def worker(wid: int):
            for i in range(3):
                nid = f"hyp_node_{wid}_{i}"
                self.fabric.add_node(nid, level=1, parent_id="RootEntity")
                _ = self.fabric.find_nearest_neighbors(nid, top_k=1)
            _ = self.fabric.status()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertGreaterEqual(self.fabric.total_embeddings, 10)


if __name__ == "__main__":
    unittest.main()
