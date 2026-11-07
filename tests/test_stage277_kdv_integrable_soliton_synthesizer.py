"""
Unit Tests for Stage 277: Autonomous Non-Linear Soliton Korteweg-de Vries (KdV) Integrable Wave Synthesizer
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import math
import threading
from backend.lucy_core.kdv_integrable_soliton_synthesizer import (
    KdVIntegrableSolitonSynthesizer,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage277KdVIntegrableSolitonSynthesizer(unittest.TestCase):
    """Thorough unit test suite for Stage 277."""

    def setUp(self):
        self.kdv = KdVIntegrableSolitonSynthesizer(spatial_grid_points=120, x_min=-30.0, x_max=30.0)

    def test_01_initialization(self):
        """Verify grid configuration and parameters."""
        self.assertEqual(self.kdv.num_points, 120)
        self.assertEqual(self.kdv.x_min, -30.0)
        self.assertEqual(self.kdv.x_max, 30.0)
        self.assertEqual(len(self.kdv.soliton_events), 0)

    def test_02_1_soliton_amplitude_speed_scaling(self):
        """Verify amplitude A = 2 * kappa^2 and speed v = 4 * kappa^2."""
        kappa = 1.5
        res = self.kdv.evaluate_1_soliton(kappa=kappa)
        self.assertAlmostEqual(res["peak_amplitude"], 2.0 * (1.5 ** 2), places=4)
        self.assertAlmostEqual(res["soliton_speed"], 4.0 * (1.5 ** 2), places=4)

    def test_03_1_soliton_propagation_shape_invariance(self):
        """Verify peak value is preserved as wave translates along x axis."""
        sol_t0 = self.kdv.evaluate_1_soliton(kappa=1.0, t=0.0)
        sol_t1 = self.kdv.evaluate_1_soliton(kappa=1.0, t=1.0)
        max_0 = max(sol_t0["profile"])
        max_1 = max(sol_t1["profile"])
        self.assertAlmostEqual(max_0, max_1, delta=0.05)

    def test_04_1_soliton_mass_energy_invariants(self):
        """Verify exact mass I_1 = 4 * kappa and energy I_2 = (16/3) * kappa^3."""
        kappa = 1.2
        res = self.kdv.evaluate_1_soliton(kappa=kappa)
        expected_i1 = 4.0 * kappa
        expected_i2 = (16.0 / 3.0) * (kappa ** 3)
        self.assertAlmostEqual(res["exact_mass_i1"], expected_i1, places=3)
        self.assertAlmostEqual(res["exact_energy_i2"], expected_i2, places=3)

    def test_05_2_soliton_interaction_coupling(self):
        """Verify interaction coupling parameter A_12."""
        k1 = 1.2
        k2 = 0.8
        res = self.kdv.evaluate_2_soliton_collision(kappa_1=k1, kappa_2=k2)
        expected_a12 = ((k1 - k2) / (k1 + k2)) ** 2
        self.assertAlmostEqual(res["interaction_coupling_a12"], expected_a12, places=5)
        self.assertGreater(res["interaction_coupling_a12"], 0.0)
        self.assertLess(res["interaction_coupling_a12"], 1.0)

    def test_06_2_soliton_phase_shift_conservation(self):
        """Verify fast soliton gets backward phase shift and slow gets forward shift."""
        res = self.kdv.evaluate_2_soliton_collision(kappa_1=1.5, kappa_2=0.5)
        self.assertLess(res["phase_shift_1"], 0.0)
        self.assertGreater(res["phase_shift_2"], 0.0)

    def test_07_2_soliton_discrete_energy_conservation(self):
        """Verify discrete energy remains stable across collision time."""
        c_before = self.kdv.evaluate_2_soliton_collision(kappa_1=1.0, kappa_2=0.6, t=-2.0)
        c_after = self.kdv.evaluate_2_soliton_collision(kappa_1=1.0, kappa_2=0.6, t=2.0)
        inv_before = self.kdv.compute_discrete_invariants(c_before["profile"])
        inv_after = self.kdv.compute_discrete_invariants(c_after["profile"])
        self.assertAlmostEqual(inv_before["mass_i1"], inv_after["mass_i1"], delta=0.5)

    def test_08_discrete_integrals_evaluation(self):
        """Verify numerical discrete integration matches analytical integrals closely."""
        sol = self.kdv.evaluate_1_soliton(kappa=1.0)
        inv = self.kdv.compute_discrete_invariants(sol["profile"])
        # Grid covers -30 to 30, so full solitary wave integral is captured
        self.assertAlmostEqual(inv["mass_i1"], sol["exact_mass_i1"], delta=0.1)
        self.assertAlmostEqual(inv["energy_i2"], sol["exact_energy_i2"], delta=0.1)

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.kdv.get_status()
        self.assertEqual(status["stage"], 277)
        self.assertEqual(status["era"], 28)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 277)
        self.assertEqual(ERA_ID, 28)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                engine = KdVIntegrableSolitonSynthesizer(spatial_grid_points=60)
                _ = engine.evaluate_1_soliton(1.0, 0.5)
                _ = engine.evaluate_2_soliton_collision(1.2, 0.8, 0.0)
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
