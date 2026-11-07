"""
Unit Tests for Stage 248: Non-Archimedean p-Adic Ultrametric Cognitive Clustering & Hierarchical Tree Space Embedding
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import unittest
from backend.lucy_core.padic_ultrametric_clusterer import (
    PadicUltrametricClustererFabric,
    get_padic_clusterer,
    STAGE,
    ERA,
)


class TestStage248PadicUltrametricClusterer(unittest.TestCase):

    def setUp(self):
        self.fabric = PadicUltrametricClustererFabric(prime_base=3, precision_levels=6)

    def test_01_singleton_and_initialization(self):
        singleton = get_padic_clusterer()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 248)
        self.assertEqual(ERA, 25)
        self.assertEqual(self.fabric.p, 3)
        self.assertEqual(self.fabric.precision_levels, 6)

    def test_02_prime_validation_rejection(self):
        with self.assertRaises(ValueError):
            PadicUltrametricClustererFabric(prime_base=4)  # Composite
        with self.assertRaises(ValueError):
            PadicUltrametricClustererFabric(prime_base=1)  # Not prime
        with self.assertRaises(ValueError):
            PadicUltrametricClustererFabric(prime_base=9)  # Composite

    def test_03_p_adic_valuation_and_norm(self):
        # In base 3:
        # 18 = 2 * 3^2 -> v_3(18) = 2 -> |18|_3 = 3^(-2) = 1/9
        # 27 = 3^3 -> v_3(27) = 3 -> |27|_3 = 3^(-3) = 1/27
        # 7 not divisible by 3 -> v_3(7) = 0 -> |7|_3 = 1.0
        # 0 -> |0|_3 = 0.0
        self.assertEqual(self.fabric.p_adic_valuation(18), 2)
        self.assertAlmostEqual(self.fabric.p_adic_norm(18), 1.0 / 9.0)

        self.assertEqual(self.fabric.p_adic_valuation(27), 3)
        self.assertAlmostEqual(self.fabric.p_adic_norm(27), 1.0 / 27.0)

        self.assertEqual(self.fabric.p_adic_valuation(7), 0)
        self.assertAlmostEqual(self.fabric.p_adic_norm(7), 1.0)

        self.assertAlmostEqual(self.fabric.p_adic_norm(0), 0.0)

    def test_04_ultrametric_distance_properties(self):
        x = 12
        y = 21
        # Symmetry: d(x, y) == d(y, x)
        d_xy = self.fabric.ultrametric_distance(x, y)
        d_yx = self.fabric.ultrametric_distance(y, x)
        self.assertEqual(d_xy, d_yx)

        # Identity of indiscernibles: d(x, x) == 0
        self.assertEqual(self.fabric.ultrametric_distance(x, x), 0.0)

        # Positivity
        self.assertGreater(d_xy, 0.0)

    def test_05_strong_triangle_inequality_invariance(self):
        # Pick 3 arbitrary integers: x=5, y=14, z=32
        res = self.fabric.verify_strong_triangle_inequality(5, 14, 32)
        self.assertTrue(res["strong_inequality_holds"])
        self.assertTrue(res["is_isosceles_ultrametric"])
        self.assertLessEqual(res["d_xz"], res["max_subpath"])

        # Another triplet: x=81, y=27, z=9
        res2 = self.fabric.verify_strong_triangle_inequality(81, 27, 9)
        self.assertTrue(res2["strong_inequality_holds"])
        self.assertTrue(res2["is_isosceles_ultrametric"])

    def test_06_vector_to_p_adic_embedding(self):
        vec_a = [0.1, 0.4, 0.9]
        vec_b = [0.1, 0.4, 0.9]
        vec_c = [0.8, 0.2, 0.3]

        p_a = self.fabric.vector_to_p_adic(vec_a)
        p_b = self.fabric.vector_to_p_adic(vec_b)
        p_c = self.fabric.vector_to_p_adic(vec_c)

        # Exact match maps to exact same p-adic integer
        self.assertEqual(p_a, p_b)
        self.assertIsInstance(p_a, int)
        self.assertNotEqual(p_a, p_c)

    def test_07_concept_registration_and_retrieval(self):
        node = self.fabric.register_concept("quantum_teleportation", [0.95, 0.12, 0.44])
        self.assertEqual(node.name, "quantum_teleportation")
        self.assertIn("quantum_teleportation", self.fabric.nodes)
        self.assertIsInstance(node.padic_repr, int)

    def test_08_hierarchical_ball_clustering(self):
        self.fabric.register_concept("concept_alpha", [0.1, 0.2, 0.3])
        self.fabric.register_concept("concept_beta", [0.1, 0.2, 0.3])
        self.fabric.register_concept("concept_gamma", [0.9, 0.8, 0.7])

        clusters = self.fabric.cluster_concepts(max_radius=0.5)
        self.assertGreaterEqual(len(clusters), 1)

        # All nodes assigned
        assigned_members = [m for c in clusters for m in c.members]
        self.assertEqual(set(assigned_members), {"concept_alpha", "concept_beta", "concept_gamma"})

    def test_09_multiscale_dendrogram_filtration(self):
        for i in range(5):
            self.fabric.register_concept(f"node_{i}", [float(i) * 0.2, 0.5, 0.1])

        dendro = self.fabric.build_hierarchical_dendrogram()
        self.assertEqual(dendro["prime_base"], 3)
        self.assertEqual(dendro["total_concepts"], 5)
        self.assertEqual(len(dendro["filtration"]), 6)  # precision_levels = 6
        self.assertIn("node_0", dendro["distance_matrix"])

    def test_10_ascii_status_and_metrics(self):
        self.fabric.register_concept("root_concept", [0.5, 0.5])
        self.fabric.cluster_concepts()
        self.fabric.verify_strong_triangle_inequality(1, 2, 3)

        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 248: Non-Archimedean p-Adic Ultrametric Clusterer", ascii_table)
        self.assertIn("Prime Base (p)", ascii_table)
        self.assertIn("Active Clusters", ascii_table)

        # CP1252 encode test
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 248)
        self.assertEqual(metrics["era"], 25)
        self.assertEqual(metrics["prime_base"], 3)
        self.assertGreaterEqual(metrics["total_nodes_registered"], 1)


if __name__ == "__main__":
    unittest.main()
