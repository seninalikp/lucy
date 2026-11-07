"""
Unit Tests for Stage 258: Planetary Astro-Chronometric Relativistic Gravitational Time-Dilation Synchronizer
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import math
import unittest
from backend.lucy_core.relativistic_chrono_synchronizer import (
    RelativisticChronoSynchronizerFabric,
    get_chrono_synchronizer,
    SPEED_OF_LIGHT_C,
    G_GRAVITATIONAL,
    STAGE,
    ERA,
)


class TestStage258RelativisticChronoSynchronizer(unittest.TestCase):

    def setUp(self):
        self.fabric = RelativisticChronoSynchronizerFabric(reference_body="earth")

    def test_01_singleton_and_initialization(self):
        singleton = get_chrono_synchronizer()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 258)
        self.assertEqual(ERA, 26)
        self.assertEqual(self.fabric.reference_body, "earth")
        self.assertEqual(SPEED_OF_LIGHT_C, 299792458.0)

    def test_02_gravitational_dilation_factor_earth_surface(self):
        m = 5.9722e24
        r = 6378137.0
        factor = self.fabric.compute_gravitational_dilation_factor(m, r)
        self.assertLess(factor, 1.0)
        self.assertGreater(factor, 0.999999)

    def test_03_gravitational_dilation_event_horizon_rejection(self):
        # Earth's Schwarzschild radius is ~9 mm
        m = 5.9722e24
        with self.assertRaises(ValueError):
            self.fabric.compute_gravitational_dilation_factor(m, 0.005)

    def test_04_kinematic_dilation_lorentz_factor(self):
        # At v = 0 -> factor = 1.0
        f0 = self.fabric.compute_kinematic_dilation_factor(0.0)
        self.assertEqual(f0, 1.0)

        # At v = 0.6 * c -> factor = sqrt(1 - 0.36) = 0.8
        f_06 = self.fabric.compute_kinematic_dilation_factor(0.6 * SPEED_OF_LIGHT_C)
        self.assertAlmostEqual(f_06, 0.8)

    def test_05_kinematic_superluminal_rejection(self):
        with self.assertRaises(ValueError):
            self.fabric.compute_kinematic_dilation_factor(SPEED_OF_LIGHT_C)
        with self.assertRaises(ValueError):
            self.fabric.compute_kinematic_dilation_factor(1.5 * SPEED_OF_LIGHT_C)

    def test_06_gps_orbit_net_dilation_verification(self):
        # GPS orbit altitude ~ 20,180 km
        # Standard textbook relativistic result: +38.6 to +38.8 microseconds per day
        offset = self.fabric.compute_orbit_dilation(altitude_m=20180000.0, body="earth")
        self.assertAlmostEqual(offset.drift_microseconds_per_day, 38.7, delta=1.0)
        self.assertGreater(offset.gravitational_shift_ratio, 0.0)  # Runs faster
        self.assertLess(offset.kinematic_shift_ratio, 0.0)        # Runs slower

    def test_07_leo_orbit_net_dilation(self):
        # In Low Earth Orbit (e.g. 500 km), satellite velocity is higher (~7.6 km/s),
        # so kinematic slowing exceeds gravitational acceleration -> net negative drift!
        leo_offset = self.fabric.compute_orbit_dilation(altitude_m=500000.0, body="earth")
        self.assertLess(leo_offset.drift_microseconds_per_day, 0.0)

    def test_08_clock_synchronization_correction(self):
        # Over 5 days at GPS altitude, satellite runs ahead by ~5 * 38.7 us
        res = self.fabric.synchronize_clock(
            raw_satellite_time_sec=1000.0,
            altitude_m=20180000.0,
            elapsed_days=5.0,
        )
        self.assertGreater(res["accumulated_drift_us"], 180.0)
        self.assertLess(res["accumulated_drift_us"], 210.0)
        self.assertLess(res["corrected_time_sec"], 1000.0)
        self.assertEqual(self.fabric.total_clock_synchronizations, 1)

    def test_09_multibody_planetary_dilation(self):
        # Test Moon and Mars orbits
        moon_off = self.fabric.compute_orbit_dilation(altitude_m=100000.0, body="moon")
        mars_off = self.fabric.compute_orbit_dilation(altitude_m=200000.0, body="mars")

        self.assertEqual(moon_off.body, "moon")
        self.assertEqual(mars_off.body, "mars")
        self.assertIsInstance(moon_off.drift_microseconds_per_day, float)
        self.assertIsInstance(mars_off.drift_microseconds_per_day, float)

    def test_10_ascii_status_and_metrics(self):
        self.fabric.synchronize_clock(100.0, 20180000.0, 1.0)
        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 258: Relativistic Astro-Chronometric Synchronizer", ascii_table)
        self.assertIn("Net Relativistic Drift", ascii_table)
        self.assertIn("Gravitational Dilation", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 258)
        self.assertEqual(metrics["era"], 26)
        self.assertGreater(metrics["gps_daily_drift_us"], 35.0)


if __name__ == "__main__":
    unittest.main()
