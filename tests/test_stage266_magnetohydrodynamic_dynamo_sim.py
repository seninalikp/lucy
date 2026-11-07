"""
Unit Tests for Stage 266: Planetary Magnetohydrodynamic (MHD) Dynamo Alfven Wave Plasma Core Simulator
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.magnetohydrodynamic_dynamo_sim import (
    MagnetohydrodynamicDynamoSim,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage266MagnetohydrodynamicDynamoSim(unittest.TestCase):
    """Thorough unit test suite for Stage 266."""

    def setUp(self):
        self.dynamo = MagnetohydrodynamicDynamoSim()

    def test_01_initialization(self):
        """Verify default core dimensions, parameters, and seed field."""
        self.assertEqual(self.dynamo.r_core, 3.48e6)
        self.assertEqual(self.dynamo.rho, 1.1e4)
        self.assertGreater(self.dynamo.b_poloidal, 0.0)
        self.assertEqual(self.dynamo.b_toroidal, 0.0)
        self.assertEqual(len(self.dynamo.step_history), 0)

    def test_02_dimensionless_numbers(self):
        """Verify calculation of Rm, Ek, Pm, and Elsasser numbers."""
        dim = self.dynamo.compute_dimensionless_numbers()
        self.assertIn("magnetic_reynolds_Rm", dim)
        self.assertIn("ekman_number_Ek", dim)
        self.assertIn("magnetic_prandtl_Pm", dim)
        self.assertIn("elsasser_number_Lambda", dim)
        # Liquid core Rm should be >> 1 (e.g. 58,000)
        self.assertGreater(dim["magnetic_reynolds_Rm"], 100.0)
        # Ekman number is extremely small in planetary core
        self.assertLess(dim["ekman_number_Ek"], 1e-10)

    def test_03_critical_rm_threshold(self):
        """Verify dynamo self-excitation regime determination."""
        dim = self.dynamo.compute_dimensionless_numbers()
        self.assertEqual(dim["critical_Rm_threshold"], 40.0)

    def test_04_alfven_velocity_formula(self):
        """Verify Alfven speed formula v_A = |B| / sqrt(mu_0 * rho)."""
        res = self.dynamo.compute_alfven_velocity(b_field_tesla=0.005) # 50 Gauss
        expected_v = 0.005 / ((4.0 * 3.141592653589793 * 1e-7 * 1.1e4) ** 0.5)
        self.assertAlmostEqual(res["alfven_velocity_m_s"], expected_v, places=2)
        self.assertGreater(res["core_transit_time_years"], 0.0)

    def test_05_step_dynamo_evolution(self):
        """Verify evolution step produces toroidal shearing and updates time."""
        rec = self.dynamo.step_dynamo_evolution(dt_years=50.0)
        self.assertEqual(rec["step_dt_years"], 50.0)
        self.assertEqual(rec["current_time_years"], 50.0)
        # Omega shear must amplify toroidal field from poloidal seed
        self.assertNotEqual(self.dynamo.b_toroidal, 0.0)
        self.assertIn("dipole_moment_a_m2", rec)
        self.assertGreater(abs(rec["dipole_moment_a_m2"]), 0.0)

    def test_06_lorentz_force_saturation(self):
        """Verify alpha-quenching prevents infinite exponential explosion."""
        for _ in range(20):
            self.dynamo.step_dynamo_evolution(dt_years=100.0)
        b_tot = (self.dynamo.b_poloidal**2 + self.dynamo.b_toroidal**2)**0.5
        # Field should remain physically bounded under saturation
        self.assertLess(b_tot, 10.0)

    def test_07_magnetic_reversal(self):
        """Verify simulation of polarity reversal excursion."""
        res = self.dynamo.simulate_magnetic_reversal(duration_years=10000.0, dt_step_years=500.0)
        self.assertEqual(res["duration_years"], 10000.0)
        self.assertIn("polarity_flips", res)
        self.assertIn("final_poloidal_b_tesla", res)

    def test_08_transit_time_scaling(self):
        """Verify transit time increases as field decreases."""
        res_strong = self.dynamo.compute_alfven_velocity(b_field_tesla=0.01)
        res_weak = self.dynamo.compute_alfven_velocity(b_field_tesla=0.001)
        self.assertLess(res_strong["core_transit_time_years"], res_weak["core_transit_time_years"])

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.dynamo.get_status()
        self.assertEqual(status["stage"], 266)
        self.assertEqual(status["era"], 27)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 266)
        self.assertEqual(ERA_ID, 27)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                sim = MagnetohydrodynamicDynamoSim()
                _ = sim.compute_dimensionless_numbers()
                _ = sim.compute_alfven_velocity()
                _ = sim.step_dynamo_evolution(dt_years=25.0)
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
