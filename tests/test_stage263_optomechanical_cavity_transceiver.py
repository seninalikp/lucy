"""
Unit Tests for Stage 263: Superconducting Optomechanical Cavity Radiation Pressure & Phonon-Photon Squeezing Transceiver
Era 27: Cosmological Gauge Invariance, Non-Abelian Yang-Mills Fiber Bundles & Sovereign Trans-Planetary Unified Field Synthesis

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.optomechanical_cavity_transceiver import (
    OptomechanicalCavityTransceiverFabric,
    get_optomechanical_transceiver,
    HBAR,
    STAGE,
    ERA,
)


class TestStage263OptomechanicalCavityTransceiver(unittest.TestCase):

    def setUp(self):
        self.fabric = OptomechanicalCavityTransceiverFabric(
            cavity_freq_hz=1.93e14,
            mech_freq_hz=1.0e7,
            mech_mass_kg=1.0e-14,
            cavity_decay_rate_hz=1.0e6,
            single_photon_coupling_g0=200.0,
        )

    def test_01_singleton_and_initialization(self):
        singleton = get_optomechanical_transceiver()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 263)
        self.assertEqual(ERA, 27)
        self.assertAlmostEqual(self.fabric.mass, 1e-14)
        self.assertEqual(self.fabric.total_cooling_cycles, 0)

    def test_02_zero_point_fluctuation_amplitude(self):
        # x_zpf = sqrt(hbar / (2 * m * omega_m))
        # For m=1e-14 kg, omega_m = 2*pi*1e7 rad/s: x_zpf ~ 9.15e-16 m (~0.9 femtometers)
        x_calc = math.sqrt(HBAR / (2.0 * self.fabric.mass * self.fabric.omega_m))
        self.assertAlmostEqual(self.fabric.x_zpf, x_calc)
        self.assertGreater(self.fabric.x_zpf, 1e-16)
        self.assertLess(self.fabric.x_zpf, 1e-14)

    def test_03_intracavity_photon_number_scaling(self):
        delta = -self.fabric.omega_m
        n1 = self.fabric.compute_intracavity_photons(1e-4, delta)
        n2 = self.fabric.compute_intracavity_photons(2e-4, delta)
        # Power doubles -> photons double
        self.assertAlmostEqual(n2, 2.0 * n1, places=1)
        self.assertGreater(n1, 0.0)

    def test_04_linearized_coupling_g(self):
        # G = g0 * sqrt(n_c)
        g_lin = self.fabric.compute_linearized_coupling(1e6)
        expected = self.fabric.g0 * 1000.0
        self.assertAlmostEqual(g_lin, expected)

    def test_05_ground_state_cooling_sub_unity_occupancy(self):
        # High power (1 mW) and low bath temperature (50 mK) drives n_eff < 1.0
        res = self.fabric.evaluate_ground_state_cooling(laser_power_w=1e-3, bath_temperature_k=0.05)
        self.assertTrue(res["is_quantum_ground_state"])
        self.assertLess(res["final_cooled_occupancy"], 1.0)
        self.assertGreater(res["optomechanical_cooling_rate_s"], 0.0)

    def test_06_thermal_bath_occupancy(self):
        # Room temperature 300K -> thermal occupancy n_th ~ k_B * T / (hbar * omega_m) ~ 6.2e5 phonons
        res = self.fabric.evaluate_ground_state_cooling(laser_power_w=1e-5, bath_temperature_k=300.0)
        self.assertGreater(res["initial_thermal_occupancy"], 1e5)

    def test_07_ponderomotive_squeezing_sub_shot_noise(self):
        sqz = self.fabric.compute_ponderomotive_squeezing(laser_power_w=1e-3)
        self.assertTrue(sqz["is_sub_shot_noise"])
        self.assertGreater(sqz["squeezing_db"], 0.0)
        self.assertLess(sqz["noise_variance_ratio"], 1.0)

    def test_08_ponderomotive_squeezing_power_dependence(self):
        sqz_low = self.fabric.compute_ponderomotive_squeezing(laser_power_w=1e-4)
        sqz_high = self.fabric.compute_ponderomotive_squeezing(laser_power_w=1e-3)

        self.assertGreater(sqz_high["squeezing_db"], sqz_low["squeezing_db"])
        self.assertGreater(sqz_high["cooperativity_C"], sqz_low["cooperativity_C"])

    def test_09_thread_safe_concurrent_cooling_and_squeezing(self):
        def worker():
            for _ in range(20):
                self.fabric.evaluate_ground_state_cooling(1e-4, 0.1)
                self.fabric.compute_ponderomotive_squeezing(1e-4)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(self.fabric.total_cooling_cycles, 80)
        self.assertEqual(self.fabric.total_squeezing_operations, 80)

    def test_10_ascii_status_and_metrics(self):
        self.fabric.evaluate_ground_state_cooling(1e-4, 0.1)
        self.fabric.compute_ponderomotive_squeezing(1e-4)

        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 263: Optomechanical Radiation Pressure Transceiver", ascii_table)
        self.assertIn("Resonance Frequencies", ascii_table)
        self.assertIn("Zero-Point Amplitude", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 263)
        self.assertEqual(metrics["era"], 27)
        self.assertGreater(metrics["zero_point_fluctuation_m"], 0.0)


if __name__ == "__main__":
    unittest.main()
