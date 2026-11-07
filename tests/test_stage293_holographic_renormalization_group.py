"""
Unit Tests for Stage 293: Holographic Renormalization Group (HRG) Flow & Boundary Ward Identity Fabric
Sovereign Architect: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.holographic_renormalization_group import (
    HolographicRenormalizationGroupFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
)


class TestStage293HolographicRenormalizationGroup(unittest.TestCase):

    def setUp(self):
        self.fabric = HolographicRenormalizationGroupFabric(boundary_dim=4, ads_radius=1.0)

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 293)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["boundary_dimension_d"], 4)
        self.assertEqual(st["bulk_dimension_d_plus_1"], 5)
        self.assertEqual(st["bf_stability_bound"], -4.0)
        self.assertEqual(st["status"], "OPERATIONAL")

    def test_02_massless_scalar_conformal_dimension(self):
        # In d=4, m^2=0 -> Delta = 4/2 + sqrt(4 + 0) = 4
        delta = self.fabric.compute_conformal_dimension(m_squared=0.0)
        self.assertAlmostEqual(delta, 4.0, places=6)

    def test_03_massive_scalar_dimension(self):
        # In d=4, m^2=5 -> Delta = 2 + sqrt(4 + 5) = 2 + 3 = 5
        delta = self.fabric.compute_conformal_dimension(m_squared=5.0)
        self.assertAlmostEqual(delta, 5.0, places=6)

    def test_04_bf_bound_violation_raises(self):
        # m^2 < -4.0 violates BF bound
        with self.assertRaises(ValueError):
            self.fabric.compute_conformal_dimension(m_squared=-4.5)

    def test_05_radial_profile_integration(self):
        profile = self.fabric.integrate_radial_profile(
            m_squared=0.0,
            source_phi0=1.0,
            vev_vev=0.5,
            steps=50,
            epsilon=0.01,
            z_max=1.0,
        )
        self.assertEqual(len(profile), 51)
        # At UV boundary z=0.01: phi ~ phi0 + vev * z^4 ~ 1.0
        z_uv, phi_uv = profile[0]
        self.assertAlmostEqual(z_uv, 0.01, places=5)
        self.assertAlmostEqual(phi_uv, 1.0, places=3)

    def test_06_holographic_1pt_function(self):
        # <O> = (2*Delta - d) * vev
        # For d=4, m^2=5 -> Delta=5 -> 2*Delta - d = 10 - 4 = 6
        # vev = 2.0 -> <O> = 12.0
        one_pt = self.fabric.compute_holographic_1pt_function(m_squared=5.0, source_phi0=1.0, vev_vev=2.0)
        self.assertAlmostEqual(one_pt, 12.0, places=6)

    def test_07_renormalized_action_finite_contact(self):
        # S_ren = -0.5 * phi0 * <O> = -0.5 * 1.0 * 12.0 = -6.0
        s_ren = self.fabric.compute_renormalized_action(m_squared=5.0, source_phi0=1.0, vev_vev=2.0)
        self.assertAlmostEqual(s_ren, -6.0, places=6)

    def test_08_conformal_ward_identity_verification(self):
        res = self.fabric.verify_conformal_ward_identity(m_squared=0.0, source_phi0=0.0, vev_vev=1.0)
        self.assertTrue(res["ward_identity_satisfied"])
        metrics = res["metrics"]
        self.assertAlmostEqual(metrics["trace_anomaly"], 0.0, places=6)

    def test_09_multithreaded_concurrency(self):
        results = []

        def worker():
            d = self.fabric.compute_conformal_dimension(m_squared=0.0)
            results.append(d)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)
        self.assertTrue(all(d == 4.0 for d in results))

    def test_10_invalid_boundary_dim_raises(self):
        with self.assertRaises(ValueError):
            HolographicRenormalizationGroupFabric(boundary_dim=1)


if __name__ == "__main__":
    unittest.main()
