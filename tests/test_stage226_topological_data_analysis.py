r"""
tests/test_stage226_topological_data_analysis.py
Stage 226 Unit Tests: Self-Supervised Topological Data Analysis & Persistent Homology Engine
"""

import threading
import unittest

from backend.lucy_core.topological_data_analysis import (
    DisjointSet,
    PersistenceInterval,
    TopologicalDataAnalysisFabric,
    STAGE,
    STAGE_NAME,
)


class TestStage226TopologicalDataAnalysis(unittest.TestCase):
    def setUp(self):
        self.fabric = TopologicalDataAnalysisFabric()

    def test_01_initialization_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 226)
        self.assertEqual(s["stage_name"], STAGE_NAME)
        self.assertEqual(s["total_clouds"], 0)
        self.assertEqual(s["total_analyses"], 0)

    def test_02_add_point_cloud_and_validation(self):
        pts = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
        self.fabric.add_point_cloud("cloud1", pts)
        self.assertIn("cloud1", self.fabric.point_clouds)
        with self.assertRaises(ValueError):
            self.fabric.add_point_cloud("invalid", [])
        with self.assertRaises(ValueError):
            self.fabric.add_point_cloud("invalid_dim", [[0.0, 0.0], [1.0]])

    def test_03_disjoint_set_elder_rule(self):
        uf = DisjointSet(3)
        # Components at eps=0: {0}, {1}, {2}
        m1 = uf.union(0, 1, current_eps=1.5)
        self.assertIsNotNone(m1)
        # Elder 0 survives, 1 dies
        self.assertEqual(uf.find(1), 0)

    def test_04_h0_persistent_homology_two_clusters(self):
        # Two distinct points far apart
        pts = [[0.0, 0.0], [10.0, 0.0]]
        self.fabric.add_point_cloud("two_pts", pts)
        intervals = self.fabric.compute_vietoris_rips_homology("two_pts")
        h0_intervals = [it for it in intervals if it.dimension == 0]
        self.assertEqual(len(h0_intervals), 2)
        # One dies at dist 10.0, one survives forever
        finite_h0 = [it for it in h0_intervals if it.death != float("inf")][0]
        self.assertAlmostEqual(finite_h0.death, 10.0, places=2)

    def test_05_synthetic_circle_generation(self):
        self.fabric.generate_circle_sample("unit_circle", num_points=12, radius=1.0)
        self.assertIn("unit_circle", self.fabric.point_clouds)
        self.assertEqual(len(self.fabric.point_clouds["unit_circle"]), 12)

    def test_06_detect_1_cycle_in_circle(self):
        self.fabric.generate_circle_sample("circle_loop", num_points=16, radius=2.0)
        intervals = self.fabric.compute_vietoris_rips_homology("circle_loop")
        h1_intervals = [it for it in intervals if it.dimension == 1]
        self.assertGreater(len(h1_intervals), 0)
        # Prominent persistent 1-hole with non-trivial lifespan
        max_lifespan = max(it.lifespan for it in h1_intervals)
        self.assertGreater(max_lifespan, 0.1)

    def test_07_compute_betti_numbers(self):
        pts = [[0.0, 0.0], [1.0, 0.0], [5.0, 0.0]]
        self.fabric.add_point_cloud("betti_test", pts)
        # At eps=0.5: 3 distinct components (beta_0 = 3)
        b_early = self.fabric.compute_betti_numbers("betti_test", epsilon=0.5)
        self.assertEqual(b_early["beta_0"], 3)
        # At eps=2.0: points 0 and 1 merged, 2 separate (beta_0 = 2)
        b_mid = self.fabric.compute_betti_numbers("betti_test", epsilon=2.0)
        self.assertEqual(b_mid["beta_0"], 2)

    def test_08_persistence_interval_serialization(self):
        it = PersistenceInterval(dimension=1, birth=0.5, death=1.8, feature_id="h1_loop")
        d = it.to_dict()
        self.assertEqual(d["dimension"], 1)
        self.assertEqual(d["birth"], 0.5)
        self.assertEqual(d["death"], 1.8)
        self.assertAlmostEqual(d["lifespan"], 1.3, places=2)

    def test_09_bottleneck_distance(self):
        self.fabric.generate_circle_sample("c1", num_points=10, radius=1.0)
        self.fabric.generate_circle_sample("c2", num_points=10, radius=1.0)
        self.fabric.generate_circle_sample("c3", num_points=10, radius=5.0)

        # Identical circles have ~0 bottleneck distance
        dist_c1_c2 = self.fabric.compute_bottleneck_distance("c1", "c2")
        self.assertAlmostEqual(dist_c1_c2, 0.0, places=1)

        # Scaled circle has larger distance
        dist_c1_c3 = self.fabric.compute_bottleneck_distance("c1", "c3")
        self.assertGreater(dist_c1_c3, dist_c1_c2)

    def test_10_cp1252_safe_ascii_and_concurrency(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 226", tbl)
        self.assertIn("TOPOLOGICAL DATA ANALYSIS", tbl)
        tbl.encode("cp1252")
        self.assertTrue(tbl.startswith("+--"))

        def worker(wid: int):
            c_name = f"c_{wid}"
            self.fabric.generate_circle_sample(c_name, num_points=8, radius=float(wid + 1))
            self.fabric.compute_vietoris_rips_homology(c_name)
            _ = self.fabric.status()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertGreaterEqual(self.fabric.total_analyses, 4)


if __name__ == "__main__":
    unittest.main()
