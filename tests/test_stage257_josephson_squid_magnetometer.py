"""
Unit Tests for Stage 257: Quantum Superconducting Josephson Junction SQUID Flux-State Quantum Magnetometer
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.josephson_squid_magnetometer import (
    JosephsonSquidMagnetometerFabric,
    get_squid_magnetometer,
    FLUX_QUANTUM_PHI0,
    STAGE,
    ERA,
)


class TestStage257JosephsonSquidMagnetometer(unittest.TestCase):

    def setUp(self):
        self.fabric = JosephsonSquidMagnetometerFabric(
            critical_current_junction=1e-6,
            loop_area_m2=1e-6,
            shunt_resistance_ohms=10.0,
        )

    def test_01_singleton_and_initialization(self):
        singleton = get_squid_magnetometer()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 257)
        self.assertEqual(ERA, 26)
        self.assertAlmostEqual(FLUX_QUANTUM_PHI0, 2.067833848e-15, delta=1e-20)
        self.assertEqual(self.fabric.i_c0, 1e-6)

    def test_02_dc_josephson_sinusoidal_relation(self):
        # I = I_c * sin(phi)
        i_0 = self.fabric.compute_dc_josephson_current(0.0)
        self.assertAlmostEqual(i_0, 0.0)

        i_half_pi = self.fabric.compute_dc_josephson_current(math.pi / 2.0)
        self.assertAlmostEqual(i_half_pi, 1e-6)

        i_pi = self.fabric.compute_dc_josephson_current(math.pi)
        self.assertAlmostEqual(i_pi, 0.0)

        i_neg_half_pi = self.fabric.compute_dc_josephson_current(-math.pi / 2.0)
        self.assertAlmostEqual(i_neg_half_pi, -1e-6)

    def test_03_ac_josephson_frequency_exact_ratio(self):
        # 1 mV = 1e-3 V -> f = 1e-3 / Phi_0 ~= 4.835979e11 Hz (483.6 GHz)
        f = self.fabric.compute_ac_josephson_frequency(1e-3)
        self.assertAlmostEqual(f * 1e-9, 483.5979, places=2)

    def test_04_squid_flux_periodicity(self):
        flux = 0.3 * FLUX_QUANTUM_PHI0
        ic_1 = self.fabric.compute_squid_critical_current(flux)
        ic_2 = self.fabric.compute_squid_critical_current(flux + FLUX_QUANTUM_PHI0)
        ic_3 = self.fabric.compute_squid_critical_current(flux + 5.0 * FLUX_QUANTUM_PHI0)

        self.assertAlmostEqual(ic_1, ic_2, places=12)
        self.assertAlmostEqual(ic_1, ic_3, places=12)

    def test_05_squid_constructive_interference_integer_flux(self):
        # At Phi = n * Phi_0 -> I_c = 2 * I_c0
        ic_0 = self.fabric.compute_squid_critical_current(0.0)
        ic_1 = self.fabric.compute_squid_critical_current(FLUX_QUANTUM_PHI0)
        ic_2 = self.fabric.compute_squid_critical_current(2.0 * FLUX_QUANTUM_PHI0)

        self.assertAlmostEqual(ic_0, 2e-6)
        self.assertAlmostEqual(ic_1, 2e-6)
        self.assertAlmostEqual(ic_2, 2e-6)

    def test_06_squid_destructive_interference_half_integer_flux(self):
        # At Phi = (n + 0.5) * Phi_0 -> I_c = 0
        ic_half = self.fabric.compute_squid_critical_current(0.5 * FLUX_QUANTUM_PHI0)
        ic_one_half = self.fabric.compute_squid_critical_current(1.5 * FLUX_QUANTUM_PHI0)

        self.assertAlmostEqual(ic_half, 0.0, places=12)
        self.assertAlmostEqual(ic_one_half, 0.0, places=12)

    def test_07_flux_to_voltage_transfer(self):
        readout_constructive = self.fabric.flux_to_voltage_readout(0.0)
        readout_destructive = self.fabric.flux_to_voltage_readout(0.5 * FLUX_QUANTUM_PHI0)

        # Destructive interference reduces critical current to 0, maximizing voltage across shunt
        self.assertGreater(readout_destructive["voltage_output_volts"], readout_constructive["voltage_output_volts"])
        self.assertAlmostEqual(readout_destructive["critical_current_amps"], 0.0, places=15)

    def test_08_external_field_measurement(self):
        # 1 microtesla field across 1 mm^2 loop
        # Phi = 1e-6 T * 1e-6 m^2 = 1e-12 Wb
        b_input = 1e-6
        meas = self.fabric.measure_external_field(b_input)
        self.assertEqual(meas["applied_b_tesla"], b_input)
        self.assertAlmostEqual(meas["flux_webers"], 1e-12)
        self.assertGreater(meas["flux_quanta"], 0.0)

    def test_09_thread_safe_concurrent_measurements(self):
        def worker():
            for _ in range(25):
                self.fabric.measure_external_field(5e-6)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(self.fabric.total_flux_measurements, 100)

    def test_10_ascii_status_and_metrics(self):
        self.fabric.measure_external_field(2e-6)
        self.fabric.compute_ac_josephson_frequency(5e-4)

        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 257: Quantum Superconducting Josephson SQUID Magnetometer", ascii_table)
        self.assertIn("Flux Quantum (Phi_0)", ascii_table)
        self.assertIn("SQUID Loop Area", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 257)
        self.assertEqual(metrics["era"], 26)
        self.assertGreater(metrics["total_flux_measurements"], 0)


if __name__ == "__main__":
    unittest.main()
