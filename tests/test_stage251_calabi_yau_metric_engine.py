"""
Unit Tests for Stage 251: Holomorphic Modular Form & Calabi-Yau Compactification Metric Engine
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import cmath
import math
import unittest
from backend.lucy_core.calabi_yau_metric_engine import (
    CalabiYauMetricEngineFabric,
    get_calabi_yau_engine,
    STAGE,
    ERA,
)


class TestStage251CalabiYauMetricEngine(unittest.TestCase):

    def setUp(self):
        self.fabric = CalabiYauMetricEngineFabric(default_dim=3)

    def test_01_singleton_and_initialization(self):
        singleton = get_calabi_yau_engine()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 251)
        self.assertEqual(ERA, 26)
        self.assertEqual(self.fabric.complex_dim, 3)
        self.assertEqual(self.fabric.total_modular_evals, 0)

    def test_02_eisenstein_series_e4_and_e6(self):
        tau = 0.0 + 1.2j
        e4 = self.fabric.compute_eisenstein_e4(tau, n_terms=15)
        e6 = self.fabric.compute_eisenstein_e6(tau, n_terms=15)
        self.assertIsInstance(e4, complex)
        self.assertIsInstance(e6, complex)
        self.assertAlmostEqual(e4.imag, 0.0, places=3)
        self.assertAlmostEqual(e6.imag, 0.0, places=3)
        self.assertGreater(e4.real, 0.9)
        self.assertLess(e6.real, 1.1)

    def test_03_tau_lower_half_plane_rejection(self):
        with self.assertRaises(ValueError):
            self.fabric.compute_eisenstein_e4(1.0 - 0.5j)
        with self.assertRaises(ValueError):
            self.fabric.compute_eisenstein_e6(0.5 + 0.0j)

    def test_04_modular_discriminant(self):
        tau = 0.0 + 1.5j
        delta = self.fabric.compute_modular_discriminant(tau, n_terms=15)
        self.assertIsInstance(delta, complex)
        self.assertNotEqual(delta, 0.0)
        self.assertGreater(delta.real, 0.0)

    def test_05_klein_j_invariant_special_values(self):
        # At tau = 1.0j, E_6(i) = 0, so j(i) = 1728
        tau_i = 0.0 + 1.0j
        j_i = self.fabric.compute_klein_j_invariant(tau_i, n_terms=20)
        self.assertAlmostEqual(j_i.real, 1728.0, delta=1.0)
        self.assertAlmostEqual(j_i.imag, 0.0, delta=0.5)

    def test_06_sl2z_t_transformation_invariance(self):
        tau = 0.2 + 1.4j
        j_orig = self.fabric.compute_klein_j_invariant(tau, n_terms=20)
        j_t = self.fabric.compute_klein_j_invariant(tau + 1.0, n_terms=20)
        self.assertAlmostEqual(j_orig.real, j_t.real, places=2)
        self.assertAlmostEqual(j_orig.imag, j_t.imag, places=2)

    def test_07_sl2z_s_transformation_invariance(self):
        tau = 0.1 + 1.2j
        j_orig = self.fabric.compute_klein_j_invariant(tau, n_terms=25)
        j_s = self.fabric.compute_klein_j_invariant(-1.0 / tau, n_terms=25)
        self.assertAlmostEqual(j_orig.real, j_s.real, delta=2.0)

    def test_08_kahler_potential_and_metric_tensor(self):
        z_coords = [0.1 + 0.2j, 0.3 + 0.1j, 0.0 + 0.4j]
        k = self.fabric.compute_kahler_potential(z_coords)
        self.assertGreater(k, 0.0)

        g = self.fabric.calabi_yau_metric_tensor(z_coords)
        self.assertEqual(len(g), 3)
        self.assertEqual(len(g[0]), 3)
        for i in range(3):
            # Diagonal elements positive
            self.assertGreater(g[i][i].real, 0.0)

    def test_09_ricci_flatness_verification(self):
        z_coords = [0.1 + 0.1j, 0.2 + 0.0j, 0.0 + 0.1j]
        res = self.fabric.verify_ricci_flatness(z_coords, tol=1.0)
        self.assertEqual(res["dim"], 3)
        self.assertIn("det_metric", res)
        self.assertTrue(res["is_ricci_flat"])
        self.assertEqual(res["status"], "CALABI_YAU_RICCI_FLAT_COMPACTIFIED")

    def test_10_ascii_status_and_metrics(self):
        tau = 0.0 + 1.5j
        self.fabric.compute_klein_j_invariant(tau)
        self.fabric.calabi_yau_metric_tensor([0.1 + 0.1j, 0.2 + 0.2j])
        self.fabric.verify_ricci_flatness([0.1 + 0.1j, 0.2 + 0.2j])

        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 251: Holomorphic Calabi-Yau Metric & Modular Form Engine", ascii_table)
        self.assertIn("Manifold Structure", ascii_table)
        self.assertIn("Modular Evaluator", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 251)
        self.assertEqual(metrics["era"], 26)
        self.assertGreaterEqual(metrics["total_modular_evals"], 1)


if __name__ == "__main__":
    unittest.main()
