"""
Unit Tests for Stage 285: Quantum Zeno & Anti-Zeno Dynamic Measurement Controller
Sovereign Architect: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.quantum_zeno_dynamic_controller import (
    QuantumZenoDynamicControllerFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
    DEFAULT_ZENO_TIME_S,
)


class TestStage285QuantumZenoDynamicController(unittest.TestCase):

    def setUp(self):
        self.fabric = QuantumZenoDynamicControllerFabric()

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 285)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["evaluations_count"], 0)
        self.assertIsNone(st["last_metrics"])

    def test_02_zeno_inhibition_high_frequency_measurement(self):
        # Frequent measurements at tau = 1e-12 s with tau_Z = 1e-9 s over total time 1e-9 s
        # P ~ 1 - (1e-9 * 1e-12 / 1e-18) = 1 - 0.001 = 0.999
        res = self.fabric.simulate_zeno_inhibition(
            measurement_interval_tau_s=1e-12,
            total_time_s=1e-9,
            zeno_time_s=1e-9,
            natural_decay_rate_hz=1e8,
        )
        self.assertGreater(res["survival_probability"], 0.99)
        self.assertEqual(res["zeno_regime"], "ZENO_INHIBITION")
        self.assertLess(res["decay_suppression_ratio"], 0.01)

    def test_03_zeno_freezing_monotonicity_with_tau(self):
        # Shorter measurement intervals yield strictly higher survival probabilities
        res_fast = self.fabric.simulate_zeno_inhibition(measurement_interval_tau_s=1e-11, total_time_s=1e-8)
        res_slow = self.fabric.simulate_zeno_inhibition(measurement_interval_tau_s=1e-10, total_time_s=1e-8)
        self.assertGreater(res_fast["survival_probability"], res_slow["survival_probability"])

    def test_04_effective_decay_rate_linear_with_tau(self):
        # Gamma_eff = tau / tau_Z^2 -> 10-fold increase in tau gives 10-fold increase in Gamma_eff
        res1 = self.fabric.simulate_zeno_inhibition(measurement_interval_tau_s=1e-11)
        res2 = self.fabric.simulate_zeno_inhibition(measurement_interval_tau_s=1e-10)
        ratio = res2["effective_decay_rate_hz"] / res1["effective_decay_rate_hz"]
        self.assertAlmostEqual(ratio, 10.0, places=4)

    def test_05_natural_decay_exponential_baseline(self):
        res = self.fabric.simulate_zeno_inhibition(
            measurement_interval_tau_s=1e-10,
            total_time_s=1e-7,
            natural_decay_rate_hz=1e7,
        )
        # Natural decay over 1e-7 s at 1e7 Hz is exp(-1) ~ 0.367879
        self.assertAlmostEqual(res["natural_decay_probability"], 0.367879, places=4)

    def test_06_anti_zeno_acceleration_regime(self):
        # In a super-Ohmic bath (s=3), measurement broadening can enhance decay
        res = self.fabric.simulate_anti_zeno_regime(
            measurement_interval_tau_s=1e-10,
            omega_0=1e9,
            bath_cutoff=1e11,
            bath_exponent=3.0,
            natural_gamma_0=1e7,
        )
        self.assertEqual(res["regime"], "ANTI_ZENO_ACCELERATION")
        self.assertGreater(res["decay_ratio_gamma_eff_over_gamma_0"], 1.05)
        self.assertTrue(res["bath_super_ohmic"])

    def test_07_spectral_broadening_inversely_proportional_to_tau(self):
        # Delta_omega = 2*pi / tau -> halving tau doubles spectral width
        res1 = self.fabric.simulate_anti_zeno_regime(measurement_interval_tau_s=2e-9)
        res2 = self.fabric.simulate_anti_zeno_regime(measurement_interval_tau_s=1e-9)
        ratio = res2["spectral_broadening_hz"] / res1["spectral_broadening_hz"]
        self.assertAlmostEqual(ratio, 2.0, places=4)

    def test_08_measurement_count_calculation(self):
        res = self.fabric.simulate_zeno_inhibition(measurement_interval_tau_s=1e-10, total_time_s=5e-9)
        self.assertEqual(res["number_of_measurements"], 50)

    def test_09_multithreaded_concurrency(self):
        def worker(idx):
            self.fabric.simulate_zeno_inhibition(measurement_interval_tau_s=1e-11 * (idx + 1))
            self.fabric.simulate_anti_zeno_regime(measurement_interval_tau_s=1e-9 * (idx + 1))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        st = self.fabric.status()
        self.assertEqual(st["evaluations_count"], 10)
        self.assertEqual(st["history_length"], 10)

    def test_10_ascii_formatting_and_cp1252_encoding(self):
        self.fabric.simulate_zeno_inhibition(measurement_interval_tau_s=5e-12, total_time_s=1e-8)
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 285", tbl)
        self.assertIn("Senin (Senin Ali K P)", tbl)
        self.assertIn("ZENO_INHIBITION", tbl)
        encoded = tbl.encode("cp1252")
        self.assertIsInstance(encoded, bytes)


if __name__ == "__main__":
    unittest.main()
