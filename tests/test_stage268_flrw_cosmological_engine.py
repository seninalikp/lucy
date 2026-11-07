"""
Unit Tests for Stage 268: Autonomous Cosmological FLRW Metric Evolution & Dark Energy State Engine
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.flrw_cosmological_engine import (
    FLRWCosmologicalEngine,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage268FLRWCosmologicalEngine(unittest.TestCase):
    """Thorough unit test suite for Stage 268."""

    def setUp(self):
        self.cosmo = FLRWCosmologicalEngine()

    def test_01_initialization(self):
        """Verify default cosmological parameters."""
        self.assertEqual(self.cosmo.h0, 67.4)
        self.assertEqual(self.cosmo.omega_m0, 0.315)
        self.assertEqual(self.cosmo.omega_de0, 0.685)
        self.assertEqual(self.cosmo.w0, -1.0)
        self.assertEqual(self.cosmo.wa, 0.0)

    def test_02_hubble_time_calculation(self):
        """Verify Hubble time scale in Gigayears."""
        self.assertAlmostEqual(self.cosmo.hubble_time_gyr, 14.5, delta=0.5)

    def test_03_cosmic_acceleration_today(self):
        """Verify cosmic expansion is accelerating today (q_0 < 0)."""
        res = self.cosmo.compute_cosmic_acceleration_q(z=0.0)
        self.assertEqual(res["redshift_z"], 0.0)
        self.assertTrue(res["is_accelerating"])
        # Standard LambdaCDM q_0 ~ 1/2 * (0.315 - 2*0.685) ~ -0.527
        self.assertAlmostEqual(res["deceleration_parameter_q"], -0.527, delta=0.05)

    def test_04_matter_dominated_deceleration_past(self):
        """Verify cosmic expansion was decelerating at high redshift (z=3)."""
        res = self.cosmo.compute_cosmic_acceleration_q(z=3.0)
        self.assertFalse(res["is_accelerating"])
        self.assertGreater(res["deceleration_parameter_q"], 0.0)

    def test_05_cpl_dark_energy_eos(self):
        """Verify Chevallier-Polarski-Linder dynamic dark energy equation of state."""
        dynamic_engine = FLRWCosmologicalEngine(w0=-0.9, wa=-0.2)
        res_z1 = dynamic_engine.compute_cosmic_acceleration_q(z=1.0) # a = 0.5
        # w(a=0.5) = -0.9 + (-0.2)*(1 - 0.5) = -1.0
        self.assertAlmostEqual(res_z1["dark_energy_eos_w"], -1.0, places=3)

    def test_06_distance_ladder_monotonicity(self):
        """Verify luminosity distance monotonically increases with redshift."""
        d1 = self.cosmo.compute_distance_ladder(z=0.5)
        d2 = self.cosmo.compute_distance_ladder(z=1.0)
        self.assertGreater(d2["luminosity_dist_mpc"], d1["luminosity_dist_mpc"])
        self.assertGreater(d2["lookback_time_gyr"], d1["lookback_time_gyr"])

    def test_07_etherington_reciprocity_relation(self):
        """Verify Etherington duality theorem: d_L(z) = (1+z)^2 * d_A(z)."""
        z = 1.5
        d = self.cosmo.compute_distance_ladder(z=z)
        expected_ratio = (1.0 + z) ** 2
        actual_ratio = d["luminosity_dist_mpc"] / d["angular_diam_dist_mpc"]
        self.assertAlmostEqual(actual_ratio, expected_ratio, places=3)

    def test_08_age_of_universe_standard(self):
        """Verify computed age of universe ~ 13.8 Gyr."""
        age = self.cosmo.compute_age_of_universe()
        self.assertAlmostEqual(age, 13.8, delta=0.5)

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.cosmo.get_status()
        self.assertEqual(status["stage"], 268)
        self.assertEqual(status["era"], 27)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 268)
        self.assertEqual(ERA_ID, 27)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                engine = FLRWCosmologicalEngine()
                _ = engine.compute_cosmic_acceleration_q(0.8)
                _ = engine.compute_distance_ladder(1.2)
                _ = engine.compute_age_of_universe(num_steps=100)
            except Exception as e:
                errors.append(str(e))

        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")


if __name__ == "__main__":
    unittest.main()
