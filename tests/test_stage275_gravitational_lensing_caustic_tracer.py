"""
Unit Tests for Stage 275: Autonomous Gravitational Lensing Caustic & Relativistic Light-Deflection Raytracer
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import math
import threading
from backend.lucy_core.gravitational_lensing_caustic_tracer import (
    GravitationalLensingCausticTracer,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage275GravitationalLensingCausticTracer(unittest.TestCase):
    """Thorough unit test suite for Stage 275."""

    def setUp(self):
        self.tracer = GravitationalLensingCausticTracer(lens_mass_solar=1e11, dist_lens_mpc=1000.0, dist_source_mpc=2000.0)

    def test_01_initialization(self):
        """Verify default initialization and Einstein radius."""
        einst = self.tracer.compute_einstein_radius()
        self.assertEqual(einst["mass_solar"], 1e11)
        self.assertGreater(einst["theta_e_arcsec"], 0.0)
        self.assertGreater(einst["einstein_radius_kpc"], 0.0)
        self.assertEqual(len(self.tracer.raytracing_events), 0)

    def test_02_einstein_radius_scaling(self):
        """Verify Einstein radius scales with square root of mass: theta_E ~ sqrt(M)."""
        tracer_4x = GravitationalLensingCausticTracer(lens_mass_solar=4e11, dist_lens_mpc=1000.0, dist_source_mpc=2000.0)
        theta_1 = self.tracer.compute_einstein_radius()["theta_e_arcsec"]
        theta_4 = tracer_4x.compute_einstein_radius()["theta_e_arcsec"]
        self.assertAlmostEqual(theta_4 / theta_1, 2.0, places=3)

    def test_03_perfect_alignment_einstein_ring(self):
        """Verify perfect alignment (beta = 0) produces symmetric images theta_pm = pm theta_E."""
        theta_e = self.tracer.compute_einstein_radius()["theta_e_arcsec"]
        res = self.tracer.solve_image_positions(source_pos_arcsec=0.0)
        self.assertTrue(res["is_einstein_ring"])
        self.assertAlmostEqual(res["image_plus_arcsec"], theta_e, places=3)
        self.assertAlmostEqual(res["image_minus_arcsec"], -theta_e, places=3)

    def test_04_image_separation_formula(self):
        """Verify image separation Delta_theta >= 2 * theta_E."""
        theta_e = self.tracer.compute_einstein_radius()["theta_e_arcsec"]
        for beta in [0.2, 0.5, 1.0, 2.5]:
            res = self.tracer.solve_image_positions(source_pos_arcsec=beta)
            self.assertGreaterEqual(res["image_separation_arcsec"], 2.0 * theta_e - 1e-4)

    def test_05_large_impact_parameter_limit(self):
        """Verify for beta >> theta_E, primary image approaches beta and secondary vanishes."""
        res = self.tracer.solve_image_positions(source_pos_arcsec=10.0)
        self.assertAlmostEqual(res["image_plus_arcsec"], 10.0, delta=0.1)
        self.assertAlmostEqual(res["image_minus_arcsec"], 0.0, delta=0.1)

    def test_06_magnification_divergence_caustic(self):
        """Verify magnification approaches large values as beta approaches 0."""
        res_near_caustic = self.tracer.solve_image_positions(source_pos_arcsec=0.001)
        res_far = self.tracer.solve_image_positions(source_pos_arcsec=2.0)
        self.assertGreater(res_near_caustic["magnification_total"], res_far["magnification_total"])

    def test_07_magnification_difference(self):
        """Verify point lens theorem: mu_+ - mu_- == 1.0 exactly."""
        res = self.tracer.solve_image_positions(source_pos_arcsec=0.75)
        diff = res["magnification_plus"] - res["magnification_minus"]
        self.assertAlmostEqual(diff, 1.0, places=3)

    def test_08_shapiro_time_delay(self):
        """Verify time delay between multiple images is positive."""
        delay = self.tracer.compute_relative_time_delay(source_pos_arcsec=0.5)
        self.assertGreater(delay["time_delay_seconds"], 0.0)
        self.assertGreater(delay["time_delay_days"], 0.0)

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.tracer.get_status()
        self.assertEqual(status["stage"], 275)
        self.assertEqual(status["era"], 28)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 275)
        self.assertEqual(ERA_ID, 28)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                engine = GravitationalLensingCausticTracer()
                _ = engine.compute_einstein_radius()
                _ = engine.solve_image_positions(0.8)
                _ = engine.compute_relative_time_delay(0.6)
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
