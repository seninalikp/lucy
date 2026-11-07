"""
Unit Tests for Stage 287: Pulsar Magnetosphere Relativistic Force-Free Electrodynamics (FFE) Simulator
Sovereign Architect: Senin (Senin Ali K P)
"""

import unittest
import threading
import math
from backend.lucy_core.pulsar_magnetosphere_ffe import (
    PulsarMagnetosphereFFEFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
    C_SPEED_OF_LIGHT,
)


class TestStage287PulsarMagnetosphereFFE(unittest.TestCase):

    def setUp(self):
        self.fabric = PulsarMagnetosphereFFEFabric()

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 287)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["evaluations_count"], 0)
        self.assertIsNone(st["last_metrics"])

    def test_02_crab_pulsar_light_cylinder(self):
        # Crab pulsar period P ~ 0.03339 s -> R_LC = c * P / (2 * pi) ~ 1.59e6 m (~1590 km)
        res = self.fabric.calculate_pulsar_parameters(period_s=0.03339, period_derivative=4.21e-13)
        expected_rlc = (C_SPEED_OF_LIGHT * 0.03339) / (2.0 * math.pi)
        self.assertAlmostEqual(res["light_cylinder_radius_m"], expected_rlc, places=1)
        self.assertGreater(res["light_cylinder_radius_m"], 1.5e6)
        self.assertLess(res["light_cylinder_radius_m"], 1.7e6)
        self.assertTrue(res["ffe_conditions_satisfied"])

    def test_03_light_cylinder_linear_period_scaling(self):
        # Doubling pulsar period doubles the light cylinder radius
        res1 = self.fabric.calculate_pulsar_parameters(period_s=0.05)
        res2 = self.fabric.calculate_pulsar_parameters(period_s=0.10)
        ratio = res2["light_cylinder_radius_m"] / res1["light_cylinder_radius_m"]
        self.assertAlmostEqual(ratio, 2.0, places=4)

    def test_04_goldreich_julian_charge_density(self):
        res = self.fabric.calculate_pulsar_parameters(period_s=0.03339, period_derivative=4.21e-13)
        self.assertLess(res["goldreich_julian_density_c_m3"], 0.0) # Negative at north pole
        self.assertGreater(res["goldreich_julian_number_density_m3"], 1e15)

    def test_05_crab_characteristic_age(self):
        # P = 0.03339 s, P_dot = 4.21e-13 -> tau_c ~ 1250 - 1260 years
        res = self.fabric.calculate_pulsar_parameters(period_s=0.03339, period_derivative=4.21e-13)
        self.assertGreater(res["characteristic_age_years"], 1200.0)
        self.assertLess(res["characteristic_age_years"], 1300.0)

    def test_06_spindown_luminosity_quartic_period_scaling(self):
        # E_dot scales as Omega^4 ~ (1/P)^4 -> Halving period increases luminosity by 2^4 = 16x
        res1 = self.fabric.calculate_pulsar_parameters(period_s=0.04, b_surface_gauss=1e12)
        res2 = self.fabric.calculate_pulsar_parameters(period_s=0.02, b_surface_gauss=1e12)
        ratio = res2["spindown_luminosity_watts"] / res1["spindown_luminosity_watts"]
        self.assertAlmostEqual(ratio, 16.0, places=3)

    def test_07_surface_field_derivation(self):
        # B_surf ~ 3.2e19 * sqrt(P * P_dot) Gauss
        p = 0.1
        p_dot = 1e-15
        expected_gauss = 3.2e19 * math.sqrt(p * p_dot) # ~ 3.2e19 * 1e-8 = 3.2e11 Gauss = 3.2e7 Tesla
        res = self.fabric.calculate_pulsar_parameters(period_s=p, period_derivative=p_dot)
        self.assertAlmostEqual(res["surface_b_field_tesla"], expected_gauss * 1e-4, places=1)

    def test_08_magnetosphere_profile_zones(self):
        sim = self.fabric.simulate_magnetosphere_radial_profile(period_s=0.03339, r_points=20)
        profile = sim["profile"]
        self.assertEqual(len(profile), 21)
        # First point is near NS surface in corotating magnetosphere
        self.assertEqual(profile[0]["zone"], "COROTATING_MAGNETOSPHERE")
        # Final point is beyond light cylinder in wind radiation zone
        self.assertEqual(profile[-1]["zone"], "WIND_RADIATION_ZONE")
        self.assertGreater(profile[-1]["radius_over_r_lc"], 1.0)

    def test_09_multithreaded_concurrency(self):
        def worker(idx):
            self.fabric.calculate_pulsar_parameters(period_s=0.01 * (idx + 1))
            self.fabric.simulate_magnetosphere_radial_profile(period_s=0.01 * (idx + 1), r_points=10)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        st = self.fabric.status()
        self.assertEqual(st["evaluations_count"], 10)
        self.assertEqual(st["history_length"], 10)

    def test_10_ascii_formatting_and_cp1252_encoding(self):
        self.fabric.calculate_pulsar_parameters(period_s=0.03339)
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 287", tbl)
        self.assertIn("Senin (Senin Ali K P)", tbl)
        self.assertIn("Light Cylinder", tbl)
        encoded = tbl.encode("cp1252")
        self.assertIsInstance(encoded, bytes)


if __name__ == "__main__":
    unittest.main()
