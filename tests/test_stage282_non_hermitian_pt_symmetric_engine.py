"""
Unit Tests for Stage 282: Non-Hermitian Parity-Time (PT) Symmetric Open Quantum Engine & Exceptional Point Sensor
Sovereign Architect: Senin (Senin Ali K P)
"""

import unittest
import threading
import math
from backend.lucy_core.non_hermitian_pt_symmetric_engine import (
    NonHermitianPTSymmetricFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
)


class TestStage282NonHermitianPTSymmetricEngine(unittest.TestCase):

    def setUp(self):
        self.fabric = NonHermitianPTSymmetricFabric()

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 282)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["evaluations_count"], 0)
        self.assertIsNone(st["last_result"])

    def test_02_unbroken_pt_phase_real_eigenvalues(self):
        # gamma = 0.6, g = 1.0 -> diff = 1.0 - 0.36 = 0.64 -> sqrt = 0.8
        res = self.fabric.solve_dim2_spectrum(gain_loss_gamma=0.6, coupling_g=1.0, omega_0=0.0)
        self.assertEqual(res.pt_phase, "UNBROKEN_REAL")
        self.assertAlmostEqual(res.eigenvalues[0].imag, 0.0, places=9)
        self.assertAlmostEqual(res.eigenvalues[1].imag, 0.0, places=9)
        self.assertAlmostEqual(res.eigenvalues[0].real, 0.8, places=9)
        self.assertAlmostEqual(res.eigenvalues[1].real, -0.8, places=9)

    def test_03_exceptional_point_coalescence(self):
        # gamma = 1.0, g = 1.0 -> EP2 -> lambda_1 = lambda_2 = omega_0
        res = self.fabric.solve_dim2_spectrum(gain_loss_gamma=1.0, coupling_g=1.0, omega_0=2.5)
        self.assertEqual(res.pt_phase, "EXCEPTIONAL_POINT")
        self.assertAlmostEqual(res.ep_distance, 0.0, places=9)
        self.assertAlmostEqual(res.eigenvalues[0].real, 2.5, places=9)
        self.assertAlmostEqual(res.eigenvalues[1].real, 2.5, places=9)
        self.assertAlmostEqual(res.eigenvalues[0].imag, 0.0, places=9)
        self.assertAlmostEqual(res.eigenvalues[1].imag, 0.0, places=9)

    def test_04_broken_pt_phase_complex_conjugate(self):
        # gamma = 1.25, g = 0.75 -> diff = 0.5625 - 1.5625 = -1.0 -> imaginary part = +- 1.0
        res = self.fabric.solve_dim2_spectrum(gain_loss_gamma=1.25, coupling_g=0.75, omega_0=1.0)
        self.assertEqual(res.pt_phase, "BROKEN_COMPLEX")
        self.assertAlmostEqual(res.eigenvalues[0].real, 1.0, places=9)
        self.assertAlmostEqual(res.eigenvalues[1].real, 1.0, places=9)
        self.assertAlmostEqual(res.eigenvalues[0].imag, 1.0, places=9)
        self.assertAlmostEqual(res.eigenvalues[1].imag, -1.0, places=9)

    def test_05_omega0_shift_invariance(self):
        res1 = self.fabric.solve_dim2_spectrum(gain_loss_gamma=0.3, coupling_g=0.5, omega_0=0.0)
        res2 = self.fabric.solve_dim2_spectrum(gain_loss_gamma=0.3, coupling_g=0.5, omega_0=5.0)
        self.assertAlmostEqual(res2.eigenvalues[0].real - res1.eigenvalues[0].real, 5.0, places=9)
        self.assertAlmostEqual(res2.eigenvalues[1].real - res1.eigenvalues[1].real, 5.0, places=9)

    def test_06_ep2_sensor_square_root_scaling(self):
        # For order 2 EP: eps = 1e-6 -> delta_lambda = (1e-6)^(1/2) = 1e-3
        sensor = self.fabric.evaluate_ep_sensor(perturbation_epsilon=1e-6, order=2, coupling_g=1.0)
        self.assertAlmostEqual(sensor["ep_eigenvalue_splitting"], 1e-3, places=6)
        self.assertAlmostEqual(sensor["amplification_factor"], 1000.0, places=3)
        self.assertEqual(sensor["sensitivity_order"], "O(eps^(1/2))")

    def test_07_ep3_sensor_cube_root_scaling(self):
        # For order 3 EP: eps = 1e-9 -> delta_lambda = (1e-9)^(1/3) = 1e-3
        sensor = self.fabric.evaluate_ep_sensor(perturbation_epsilon=1e-9, order=3, coupling_g=1.0)
        self.assertAlmostEqual(sensor["ep_eigenvalue_splitting"], 1e-3, places=6)
        self.assertAlmostEqual(sensor["amplification_factor"], 1e6, places=1)
        self.assertEqual(sensor["sensitivity_order"], "O(eps^(1/3))")

    def test_08_trimer_spectrum_and_critical_gamma(self):
        # For 3-site trimer: critical gamma = sqrt(2) * g
        g = 2.0
        crit_gamma = math.sqrt(2.0) * g
        # Subcritical
        res_sub = self.fabric.solve_dim3_spectrum(gain_loss_gamma=crit_gamma * 0.5, coupling_g=g)
        self.assertEqual(res_sub["pt_phase"], "UNBROKEN_REAL")
        # Supercritical
        res_super = self.fabric.solve_dim3_spectrum(gain_loss_gamma=crit_gamma * 1.5, coupling_g=g)
        self.assertEqual(res_super["pt_phase"], "BROKEN_COMPLEX")

    def test_09_multithreaded_concurrency(self):
        def worker(idx):
            self.fabric.solve_dim2_spectrum(gain_loss_gamma=0.1 * idx, coupling_g=1.0)
            self.fabric.evaluate_ep_sensor(perturbation_epsilon=1e-5 * (idx + 1))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        st = self.fabric.status()
        self.assertEqual(st["evaluations_count"], 10)
        self.assertEqual(st["history_length"], 10)

    def test_10_ascii_formatting_and_cp1252_encoding(self):
        self.fabric.solve_dim2_spectrum(gain_loss_gamma=0.999999, coupling_g=1.0)
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 282", tbl)
        self.assertIn("Senin (Senin Ali K P)", tbl)
        self.assertIn("PT Phase State", tbl)
        encoded = tbl.encode("cp1252")
        self.assertIsInstance(encoded, bytes)


if __name__ == "__main__":
    unittest.main()
