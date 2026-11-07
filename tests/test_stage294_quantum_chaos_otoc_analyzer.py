"""
Unit Tests for Stage 294: Quantum Chaos OTOC Analyzer & Maldacena-Shenker-Stanford (MSS) Bound Engine
Sovereign Architect: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.quantum_chaos_otoc_analyzer import (
    QuantumChaosOTOCAnalyzerFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
)


class TestStage294QuantumChaosOTOCAnalyzer(unittest.TestCase):

    def setUp(self):
        self.fabric = QuantumChaosOTOCAnalyzerFabric(default_temp_k=1.0, degrees_of_freedom=100)

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 294)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["temperature_kelvin"], 1.0)
        self.assertEqual(st["degrees_of_freedom_N"], 100)
        self.assertGreater(st["mss_bound_limit"], 1e11)
        self.assertEqual(st["status"], "OPERATIONAL")

    def test_02_mss_bound_calculation(self):
        # lambda_MSS = 2 * pi * kB * T / hbar
        # At T = 1.0 K: ~ 8.226e11 s^-1
        mss = self.fabric.compute_mss_bound(temp_k=1.0)
        self.assertGreater(mss, 8.0e11)
        self.assertLess(mss, 8.5e11)

    def test_03_mss_linear_temperature_scaling(self):
        # Doubling temperature must exactly double the MSS bound limit
        b1 = self.fabric.compute_mss_bound(temp_k=2.0)
        b2 = self.fabric.compute_mss_bound(temp_k=4.0)
        self.assertAlmostEqual(b2 / b1, 2.0, places=6)

    def test_04_otoc_decay_trajectory(self):
        lambda_test = 1.0e6
        times = [0.0, 1.0e-6, 1.0e-5]
        traj = self.fabric.evaluate_otoc_trajectory(lambda_test, times)
        self.assertEqual(len(traj), 3)
        # At t=0, F(0) = 1.0
        self.assertAlmostEqual(traj[0][1], 1.0, places=6)
        # Later time must show decay
        self.assertLess(traj[2][1], traj[0][1])

    def test_05_scrambling_time_logarithmic_n_scaling(self):
        # t_* = (1 / lambda) * ln(N^2) = (2 / lambda) * ln(N)
        lambda_test = 1.0e6
        t_star = self.fabric.compute_scrambling_time(lambda_test)
        expected = (1.0 / lambda_test) * math.log(100**2)
        self.assertAlmostEqual(t_star, expected, places=8)

    def test_06_maximally_chaotic_detection(self):
        mss = self.fabric.compute_mss_bound()
        metrics = self.fabric.analyze_scrambler(lambda_L=mss)
        self.assertTrue(metrics.is_maximally_chaotic)
        self.assertAlmostEqual(metrics.bound_ratio, 1.0, places=4)

    def test_07_sub_maximal_scrambler(self):
        mss = self.fabric.compute_mss_bound()
        metrics = self.fabric.analyze_scrambler(lambda_L=0.5 * mss)
        self.assertFalse(metrics.is_maximally_chaotic)
        self.assertAlmostEqual(metrics.bound_ratio, 0.5, places=4)

    def test_08_mss_bound_violation_raises(self):
        mss = self.fabric.compute_mss_bound()
        with self.assertRaises(ValueError):
            self.fabric.analyze_scrambler(lambda_L=1.5 * mss)

    def test_09_multithreaded_concurrency(self):
        results = []

        def worker():
            m = self.fabric.compute_mss_bound()
            results.append(m)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)
        self.assertTrue(all(r > 1e11 for r in results))

    def test_10_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            QuantumChaosOTOCAnalyzerFabric(default_temp_k=-5.0)
        with self.assertRaises(ValueError):
            QuantumChaosOTOCAnalyzerFabric(degrees_of_freedom=1)


if __name__ == "__main__":
    unittest.main()
