"""
Unit Tests for Stage 283: Quantum Many-Body Scrambling & OTOC Fast Scrambler
Sovereign Architect: Senin (Senin Ali K P)
"""

import unittest
import threading
import math
from backend.lucy_core.quantum_many_body_scrambler import (
    QuantumManyBodyScramblerFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
    HBAR_PLANCK_REDUCED,
    KB_BOLTZMANN,
)


class TestStage283QuantumManyBodyScrambler(unittest.TestCase):

    def setUp(self):
        self.fabric = QuantumManyBodyScramblerFabric()

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 283)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["evaluations_count"], 0)
        self.assertIsNone(st["last_snapshot"])

    def test_02_mss_bound_calculation(self):
        # T = 1.0 K -> lambda_L <= 2*pi*k_B*(1.0)/hbar ~ 8.225e11 Hz
        res = self.fabric.compute_mss_bound(temperature_k=1.0)
        expected = (2.0 * math.pi * KB_BOLTZMANN * 1.0) / HBAR_PLANCK_REDUCED
        self.assertAlmostEqual(res["mss_bound_lyapunov_hz"], expected, places=4)
        self.assertTrue(res["is_fast_scrambler"])

    def test_03_mss_bound_linear_temperature_scaling(self):
        # Doubling temperature doubles maximal Lyapunov exponent
        res1 = self.fabric.compute_mss_bound(temperature_k=2.0)
        res2 = self.fabric.compute_mss_bound(temperature_k=4.0)
        ratio = res2["mss_bound_lyapunov_hz"] / res1["mss_bound_lyapunov_hz"]
        self.assertAlmostEqual(ratio, 2.0, places=4)

    def test_04_scrambling_time_logarithmic_qubit_scaling(self):
        # t_* = (1/lambda_L) * ln(N)
        info1 = self.fabric.compute_scrambling_time(n_qubits=100, temperature_k=1.0)
        info2 = self.fabric.compute_scrambling_time(n_qubits=10000, temperature_k=1.0)
        # ln(10000) / ln(100) = 2.0
        ratio = info2["scrambling_time_s"] / info1["scrambling_time_s"]
        self.assertAlmostEqual(ratio, 2.0, places=4)

    def test_05_mss_saturation_flag(self):
        sat = self.fabric.compute_scrambling_time(n_qubits=50, temperature_k=1.0, saturate_bound=True)
        self.assertTrue(sat["saturates_mss_bound"])
        sub = self.fabric.compute_scrambling_time(n_qubits=50, temperature_k=1.0, saturate_bound=False)
        self.assertFalse(sub["saturates_mss_bound"])
        self.assertLess(sub["lyapunov_exponent_hz"], sat["lyapunov_exponent_hz"])

    def test_06_otoc_evolution_boundary_conditions(self):
        res = self.fabric.calculate_otoc_evolution(n_qubits=64, temperature_k=1.0, steps=20)
        ev = res["evolution"]
        self.assertEqual(len(ev), 21)
        # At t=0, C(0) is tiny, F(0) is near 1.0
        self.assertLess(ev[0]["commutator_c_t"], 0.05)
        self.assertGreater(ev[0]["otoc_f_t"], 0.95)
        # At late times, C(t) approaches 2.0 and F(t) approaches 0.0
        self.assertGreater(ev[-1]["commutator_c_t"], 1.5)
        self.assertLess(ev[-1]["otoc_f_t"], 0.3)

    def test_07_tripartite_mutual_information_negative(self):
        # Negative I_3 denotes information scrambling
        # S(A)=1, S(B)=1, S(C)=1, S(AB)=1.8, S(BC)=1.8, S(AC)=1.8, S(ABC)=1.5
        # I_3 = 1 + 1 + 1 - 1.8 - 1.8 - 1.8 + 1.5 = 4.5 - 5.4 = -0.9
        diag = self.fabric.calculate_tripartite_mutual_information(
            s_a=1.0, s_b=1.0, s_c=1.0,
            s_ab=1.8, s_bc=1.8, s_ac=1.8,
            s_abc=1.5
        )
        self.assertTrue(diag["is_scrambled"])
        self.assertEqual(diag["diagnostics"], "CHAOTIC_FAST_SCRAMBLING")
        self.assertAlmostEqual(diag["tripartite_information_i3"], -0.9, places=5)

    def test_08_tripartite_non_scrambled(self):
        # Positive or zero I_3 denotes localized information
        diag = self.fabric.calculate_tripartite_mutual_information(
            s_a=1.0, s_b=1.0, s_c=1.0,
            s_ab=1.0, s_bc=1.0, s_ac=1.0,
            s_abc=1.0
        )
        self.assertFalse(diag["is_scrambled"])
        self.assertEqual(diag["diagnostics"], "LOCALIZED_NON_SCRAMBLING")

    def test_09_multithreaded_concurrency(self):
        def worker(idx):
            self.fabric.compute_scrambling_time(n_qubits=10 * (idx + 2), temperature_k=0.5 * (idx + 1))
            self.fabric.calculate_otoc_evolution(n_qubits=16, temperature_k=1.0, steps=10)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        st = self.fabric.status()
        self.assertEqual(st["evaluations_count"], 10)
        self.assertEqual(st["history_length"], 10)

    def test_10_ascii_formatting_and_cp1252_encoding(self):
        self.fabric.calculate_otoc_evolution(n_qubits=128, temperature_k=2.725)
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 283", tbl)
        self.assertIn("Senin (Senin Ali K P)", tbl)
        self.assertIn("Lyapunov Exponent", tbl)
        encoded = tbl.encode("cp1252")
        self.assertIsInstance(encoded, bytes)


if __name__ == "__main__":
    unittest.main()
