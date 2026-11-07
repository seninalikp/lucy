"""
Unit Tests for Stage 298: Superstring Target Space T-Duality & Buscher Transformation Fabric
Sovereign Architect: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.superstring_t_duality_invariance import (
    SuperstringTDualityInvarianceFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
)


class TestStage298SuperstringTDualityInvariance(unittest.TestCase):

    def setUp(self):
        self.fabric = SuperstringTDualityInvarianceFabric(alpha_prime=1.0)

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 298)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["alpha_prime"], 1.0)
        self.assertEqual(st["self_dual_radius"], 1.0)
        self.assertEqual(st["status"], "OPERATIONAL")

    def test_02_self_dual_radius(self):
        # At R = sqrt(alpha') = 1.0, dual radius R' is also 1.0
        r_dual = self.fabric.compute_dual_radius(1.0)
        self.assertAlmostEqual(r_dual, 1.0, places=7)

    def test_03_inversion_of_radius(self):
        # R = 2.0 -> R' = 0.5
        r_dual = self.fabric.compute_dual_radius(2.0)
        self.assertAlmostEqual(r_dual, 0.5, places=7)

    def test_04_exact_t_duality_mass_spectrum_invariance(self):
        # M^2(R=3.0, n=2, w=5) must match M^2(R'=1/3, n=5, w=2)
        metrics = self.fabric.verify_t_duality_invariance(radius_r=3.0, momentum_n=2, winding_w=5)
        self.assertTrue(metrics.is_t_dual_invariant)
        self.assertAlmostEqual(metrics.t_duality_mass_difference, 0.0, places=9)
        self.assertAlmostEqual(metrics.mass_squared, metrics.dual_mass_squared, places=9)

    def test_05_pure_momentum_dual_to_pure_winding(self):
        # Pure KK state (n=4, w=0) at R=2 has mass (4/2)^2 = 4
        # Dual state (n=0, w=4) at R'=0.5 has mass (4 * 0.5 / 1)^2 = 4
        m = self.fabric.verify_t_duality_invariance(radius_r=2.0, momentum_n=4, winding_w=0)
        self.assertTrue(m.is_t_dual_invariant)
        self.assertAlmostEqual(m.mass_squared, 4.0, places=7)
        self.assertAlmostEqual(m.dual_mass_squared, 4.0, places=7)

    def test_06_buscher_metric_inversion(self):
        # G'_00 = 1 / G_00
        res = self.fabric.apply_buscher_transform(
            g_00=4.0, g_0i=0.0, g_ij=1.0, b_0i=0.0, b_ij=0.0, dilaton_phi=0.0
        )
        self.assertAlmostEqual(res["g_00_prime"], 0.25, places=7)

    def test_07_buscher_dilaton_shift(self):
        # Phi' = Phi - 0.5 * ln(G_00)
        # G_00 = 4.0 -> ln(4.0) = 2*ln(2) -> Phi' = 0.0 - ln(2)
        res = self.fabric.apply_buscher_transform(
            g_00=4.0, g_0i=0.0, g_ij=1.0, b_0i=0.0, b_ij=0.0, dilaton_phi=0.0
        )
        self.assertAlmostEqual(res["dilaton_phi_prime"], - math.log(2.0), places=6)

    def test_08_invalid_radius_raises(self):
        with self.assertRaises(ValueError):
            self.fabric.compute_dual_radius(-1.0)
        with self.assertRaises(ValueError):
            self.fabric.compute_string_mass_squared(radius_r=0.0, momentum_n=1, winding_w=1)

    def test_09_multithreaded_concurrency(self):
        results = []

        def worker():
            m = self.fabric.verify_t_duality_invariance(2.5, 3, 1)
            results.append(m.is_t_dual_invariant)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)
        self.assertTrue(all(results))

    def test_10_invalid_alpha_prime_raises(self):
        with self.assertRaises(ValueError):
            SuperstringTDualityInvarianceFabric(alpha_prime=-0.5)


if __name__ == "__main__":
    unittest.main()
