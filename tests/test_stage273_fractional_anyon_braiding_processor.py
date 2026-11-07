"""
Unit Tests for Stage 273: Topological Anyon Fractional Exchange Statistics & Braiding Matrix Fusion Processor
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import math
import threading
from backend.lucy_core.fractional_anyon_braiding_processor import (
    FractionalAnyonBraidingProcessor,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage273FractionalAnyonBraidingProcessor(unittest.TestCase):
    """Thorough unit test suite for Stage 273."""

    def setUp(self):
        self.processor = FractionalAnyonBraidingProcessor()

    def test_01_initialization(self):
        """Verify initialization constants and golden ratio."""
        expected_phi = (1.0 + math.sqrt(5.0)) / 2.0
        self.assertAlmostEqual(self.processor.golden_ratio, expected_phi, places=6)
        self.assertEqual(len(self.processor.braiding_log), 0)

    def test_02_laughlin_fractional_phase(self):
        """Verify fractional statistical exchange phase for Laughlin state (nu = 1/3)."""
        res = self.processor.compute_abelian_exchange_phase(filling_fraction_nu=1.0 / 3.0, exchange_count=1)
        self.assertAlmostEqual(res["half_exchange_phase_deg"], 60.0, places=2)
        self.assertAlmostEqual(res["full_loop_braid_phase_deg"], 120.0, places=2)

    def test_03_fibonacci_f_matrix_unitarity(self):
        """Verify F-matrix is real, symmetric, and orthogonal (F @ F == I)."""
        f = self.processor.get_fibonacci_f_matrix()
        self.assertAlmostEqual(f[0][1], f[1][0], places=6) # Symmetric
        # F @ F = I
        i00 = f[0][0]*f[0][0] + f[0][1]*f[1][0]
        i11 = f[1][0]*f[0][1] + f[1][1]*f[1][1]
        i01 = f[0][0]*f[0][1] + f[0][1]*f[1][1]
        self.assertAlmostEqual(i00, 1.0, places=5)
        self.assertAlmostEqual(i11, 1.0, places=5)
        self.assertAlmostEqual(i01, 0.0, places=5)

    def test_04_fibonacci_r_matrix_eigenvalues(self):
        """Verify R-matrix diagonal entries have absolute value 1 (pure phases)."""
        r = self.processor.get_fibonacci_r_matrix()
        self.assertAlmostEqual(abs(r[0][0]), 1.0, places=6)
        self.assertAlmostEqual(abs(r[1][1]), 1.0, places=6)
        self.assertEqual(r[0][1], complex(0.0, 0.0))
        self.assertEqual(r[1][0], complex(0.0, 0.0))

    def test_05_yang_baxter_braid_relation(self):
        """Verify Artin braid equation sigma_1 @ sigma_2 @ sigma_1 == sigma_2 @ sigma_1 @ sigma_2."""
        res = self.processor.verify_yang_baxter_braid_relation()
        self.assertTrue(res["is_satisfied"])
        self.assertLess(res["max_deviation"], 1e-6)

    def test_06_braid_sequence_execution(self):
        """Verify execution of braid word produces unitary gate."""
        res = self.processor.execute_braid_sequence([1, 2, 1])
        self.assertEqual(res["length"], 3)
        self.assertTrue(res["is_unitary"])

    def test_07_braid_inverse_cancellation(self):
        """Verify [1, -1] yields identity matrix."""
        res = self.processor.execute_braid_sequence([1, -1])
        self.assertTrue(res["is_unitary"])
        # Check elements ~ identity
        self.assertIn("1.0000+0.0000j", res["matrix"][0][0])
        self.assertIn("1.0000+0.0000j", res["matrix"][1][1])

    def test_08_quantum_dimension_golden_ratio(self):
        """Verify quantum dimension d_tau ~ 1.618034."""
        st = self.processor.get_status()
        self.assertAlmostEqual(st["quantum_dimension_tau"], 1.618034, places=5)

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.processor.get_status()
        self.assertEqual(status["stage"], 273)
        self.assertEqual(status["era"], 28)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 273)
        self.assertEqual(ERA_ID, 28)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                p = FractionalAnyonBraidingProcessor()
                _ = p.compute_abelian_exchange_phase(1.0 / 3.0)
                _ = p.verify_yang_baxter_braid_relation()
                _ = p.execute_braid_sequence([1, 2, -1, -2])
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
