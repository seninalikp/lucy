"""
Unit Tests for Stage 272: Non-Commutative Moyal-Weyl Spacetime Star-Product Algebra & Quantum Gravity Uncertainty Engine
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import math
import threading
from backend.lucy_core.noncommutative_moyal_star_algebra import (
    NoncommutativeMoyalStarAlgebra,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage272NoncommutativeMoyalStarAlgebra(unittest.TestCase):
    """Thorough unit test suite for Stage 272."""

    def setUp(self):
        # Use a non-zero test theta for numerical tests
        self.algebra = NoncommutativeMoyalStarAlgebra(theta_param_m2=1e-4, gup_beta=1e-10)

    def test_01_initialization(self):
        """Verify initialization constants and parameters."""
        self.assertEqual(self.algebra.theta, 1e-4)
        self.assertEqual(self.algebra.beta, 1e-10)
        self.assertEqual(len(self.algebra.algebra_history), 0)

    def test_02_star_product_zeroth_order(self):
        """Verify standard product recovery when derivatives vanish."""
        res = self.algebra.compute_moyal_star_product_2d(
            f_val=3.0, df_dx=0.0, df_dy=0.0, d2f_dxdy=0.0,
            g_val=4.0, dg_dx=0.0, dg_dy=0.0, d2g_dxdy=0.0
        )
        self.assertAlmostEqual(res["star_product_real"], 12.0, places=6)
        self.assertAlmostEqual(res["star_product_imag"], 0.0, places=6)
        self.assertEqual(res["poisson_bracket"], 0.0)

    def test_03_star_product_imaginary_linear_term(self):
        """Verify linear non-commutative imaginary contribution."""
        # f = x, g = y => df/dx = 1, dg/dy = 1 -> {f, g}_P = 1
        res = self.algebra.compute_moyal_star_product_2d(
            f_val=2.0, df_dx=1.0, df_dy=0.0, d2f_dxdy=0.0,
            g_val=5.0, dg_dx=0.0, dg_dy=1.0, d2g_dxdy=0.0
        )
        expected_imag = 0.5 * 1e-4 * 1.0  # 5e-5
        self.assertAlmostEqual(res["star_product_imag"], expected_imag, places=8)
        self.assertEqual(res["poisson_bracket"], 1.0)

    def test_04_star_product_anticommutativity(self):
        """Verify non-commutative ordering: (f*g).imag == - (g*f).imag."""
        res_fg = self.algebra.compute_moyal_star_product_2d(
            f_val=1.0, df_dx=1.0, df_dy=0.0, d2f_dxdy=0.0,
            g_val=1.0, dg_dx=0.0, dg_dy=1.0, d2g_dxdy=0.0
        )
        res_gf = self.algebra.compute_moyal_star_product_2d(
            f_val=1.0, df_dx=0.0, df_dy=1.0, d2f_dxdy=0.0,
            g_val=1.0, dg_dx=1.0, dg_dy=0.0, d2g_dxdy=0.0
        )
        self.assertAlmostEqual(res_fg["star_product_imag"], -res_gf["star_product_imag"], places=8)

    def test_05_heisenberg_limit_low_momentum(self):
        """Verify low momentum reproduces standard Heisenberg bound."""
        dp = 1e-20
        res = self.algebra.compute_gup_uncertainty(dp)
        self.assertAlmostEqual(res["gup_dx_m"] / res["heisenberg_dx_m"], 1.0, places=5)

    def test_06_gup_minimal_length_bound(self):
        """Verify absolute minimal length bound: dx_min = hbar * sqrt(beta)."""
        res = self.algebra.compute_gup_uncertainty(1e-5)
        expected_min = self.algebra.hbar * math.sqrt(self.algebra.beta)
        self.assertAlmostEqual(res["minimal_observable_length_m"], expected_min, delta=1e-45)
        # GUP dx must be greater than or equal to minimal length
        self.assertGreaterEqual(res["gup_dx_m"], expected_min)

    def test_07_gup_quadratic_increase_high_momentum(self):
        """Verify high momentum uncertainty increases linearly with dp."""
        dp_opt = 1.0 / math.sqrt(self.algebra.beta)  # 1e5
        res_opt = self.algebra.compute_gup_uncertainty(dp_opt)
        res_high = self.algebra.compute_gup_uncertainty(dp_opt * 100.0)
        self.assertGreater(res_high["gup_dx_m"], res_opt["gup_dx_m"])

    def test_08_uv_ir_mixing_dispersion(self):
        """Verify UV/IR mixing scale calculation."""
        res_low_p = self.algebra.compute_uv_ir_mixing_scale(external_momentum_p=1e-15, uv_cutoff_lambda=1e6)
        res_high_p = self.algebra.compute_uv_ir_mixing_scale(external_momentum_p=1e5, uv_cutoff_lambda=1e6)
        self.assertGreater(res_low_p["effective_cutoff_lambda_eff"], res_high_p["effective_cutoff_lambda_eff"])

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.algebra.get_status()
        self.assertEqual(status["stage"], 272)
        self.assertEqual(status["era"], 28)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 272)
        self.assertEqual(ERA_ID, 28)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                engine = NoncommutativeMoyalStarAlgebra()
                _ = engine.compute_moyal_star_product_2d(1.0, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0)
                _ = engine.compute_gup_uncertainty(1e-10)
                _ = engine.compute_uv_ir_mixing_scale(10.0)
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
