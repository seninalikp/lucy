"""
Unit Tests for Stage 281: Black Hole Holographic Thermodynamics & Bekenstein-Hawking Entropy Engine
Sovereign Architect: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.black_hole_thermodynamics import (
    BlackHoleThermodynamicsFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
    SOLAR_MASS_KG,
)


class TestStage281BlackHoleThermodynamics(unittest.TestCase):

    def setUp(self):
        self.fabric = BlackHoleThermodynamicsFabric()

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 281)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["evaluations_count"], 0)
        self.assertIsNone(st["last_metrics"])

    def test_02_schwarzschild_solar_mass_precision(self):
        # 1 Solar Mass: r_s ~ 2953.25 m, T_H ~ 6.17e-8 K
        res = self.fabric.calculate_schwarzschild(mass_solar=1.0)
        self.assertAlmostEqual(res["mass_solar"], 1.0, places=4)
        self.assertAlmostEqual(res["mass_kg"], SOLAR_MASS_KG, delta=1e20)
        self.assertGreater(res["schwarzschild_radius_m"], 2940.0)
        self.assertLess(res["schwarzschild_radius_m"], 2960.0)
        self.assertGreater(res["hawking_temperature_k"], 6.0e-8)
        self.assertLess(res["hawking_temperature_k"], 6.3e-8)
        self.assertGreater(res["dimensionless_entropy"], 1e76)

    def test_03_entropy_quadratic_mass_scaling(self):
        # S_BH proportional to M^2: doubling mass quadruples entropy
        m1 = self.fabric.calculate_schwarzschild(mass_solar=2.0)
        m2 = self.fabric.calculate_schwarzschild(mass_solar=4.0)
        ratio = m2["dimensionless_entropy"] / m1["dimensionless_entropy"]
        self.assertAlmostEqual(ratio, 4.0, places=3)

    def test_04_hawking_temp_inverse_mass_scaling(self):
        # T_H proportional to 1/M: doubling mass halves temperature
        m1 = self.fabric.calculate_schwarzschild(mass_solar=3.0)
        m2 = self.fabric.calculate_schwarzschild(mass_solar=6.0)
        ratio = m1["hawking_temperature_k"] / m2["hawking_temperature_k"]
        self.assertAlmostEqual(ratio, 2.0, places=3)

    def test_05_evaporation_cubic_lifetime_scaling(self):
        # t_evap proportional to M^3: doubling mass octuples lifetime
        m1 = self.fabric.calculate_schwarzschild(mass_solar=1.5)
        m2 = self.fabric.calculate_schwarzschild(mass_solar=3.0)
        ratio = m2["evaporation_lifetime_s"] / m1["evaporation_lifetime_s"]
        self.assertAlmostEqual(ratio, 8.0, places=3)

    def test_06_kerr_spinning_black_hole_horizons(self):
        # Kerr horizon radius r_+ is strictly smaller than Schwarzschild radius for a* > 0
        sch = self.fabric.calculate_schwarzschild(mass_solar=5.0)
        kerr = self.fabric.calculate_kerr(mass_solar=5.0, spin_param=0.8)
        self.assertLess(kerr["horizon_radius_m"], sch["schwarzschild_radius_m"])
        self.assertLess(kerr["horizon_area_m2"], sch["horizon_area_m2"])
        self.assertEqual(kerr["spin_parameter"], 0.8)

    def test_07_kerr_near_extremal_temperature_drop(self):
        # In Kerr metric, as a* -> 1 (extremal), Hawking temperature T_H -> 0
        kerr_mid = self.fabric.calculate_kerr(mass_solar=2.0, spin_param=0.5)
        kerr_near_ext = self.fabric.calculate_kerr(mass_solar=2.0, spin_param=0.999)
        self.assertLess(kerr_near_ext["hawking_temperature_k"], kerr_mid["hawking_temperature_k"])
        self.assertGreater(kerr_near_ext["hawking_temperature_k"], 0.0)

    def test_08_page_curve_unitary_information_recovery(self):
        # Simulate Page curve and verify radiation entropy peaks then descends (Page curve behavior)
        page_sim = self.fabric.simulate_page_curve(mass_solar=1.0, steps=40)
        self.assertTrue(page_sim["unitary_preserved"])
        curve = page_sim["curve"]
        self.assertEqual(len(curve), 41)
        # Verify initial entropy is zero for radiation
        self.assertEqual(curve[0]["entropy_radiation_page"], 0.0)
        # Verify Page curve rises to a maximum and returns to zero at tau=1.0
        rad_entropies = [p["entropy_radiation_page"] for p in curve]
        max_rad = max(rad_entropies)
        self.assertGreater(max_rad, 0.0)
        self.assertAlmostEqual(curve[-1]["entropy_radiation_page"], 0.0, places=3)

    def test_09_multithreaded_concurrency(self):
        def worker(idx):
            self.fabric.calculate_schwarzschild(mass_solar=float(idx + 1))
            self.fabric.calculate_kerr(mass_solar=float(idx + 1), spin_param=0.2 * (idx % 4))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        st = self.fabric.status()
        self.assertEqual(st["evaluations_count"], 20)
        self.assertEqual(st["history_length"], 20)

    def test_10_ascii_formatting_and_cp1252_encoding(self):
        self.fabric.calculate_kerr(mass_solar=10.0, spin_param=0.65)
        table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 281", table)
        self.assertIn("Senin (Senin Ali K P)", table)
        self.assertIn("Kerr Spin", table)
        # CP1252 compatibility test: must encode cleanly without exception
        encoded = table.encode("cp1252")
        self.assertIsInstance(encoded, bytes)


if __name__ == "__main__":
    unittest.main()
