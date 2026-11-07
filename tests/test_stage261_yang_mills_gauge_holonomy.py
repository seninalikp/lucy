"""
Unit Tests for Stage 261: Non-Abelian SU(N) Yang-Mills Gauge Connection & Wilson Loop Holonomy Engine
Era 27: Cosmological Gauge Invariance, Non-Abelian Yang-Mills Fiber Bundles & Sovereign Trans-Planetary Unified Field Synthesis

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import cmath
import math
import threading
import unittest
from backend.lucy_core.yang_mills_gauge_holonomy import (
    YangMillsGaugeHolonomyFabric,
    get_yang_mills_engine,
    _mat_mul,
    _mat_trace,
    STAGE,
    ERA,
)


class TestStage261YangMillsGaugeHolonomy(unittest.TestCase):

    def setUp(self):
        self.fabric = YangMillsGaugeHolonomyFabric(gauge_group="SU(2)", coupling_g=1.0)

    def test_01_singleton_and_initialization(self):
        singleton = get_yang_mills_engine()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 261)
        self.assertEqual(ERA, 27)
        self.assertEqual(self.fabric.gauge_group, "SU(2)")
        self.assertEqual(self.fabric.g, 1.0)
        self.assertEqual(self.fabric.total_wilson_loops_computed, 0)

    def test_02_su2_generator_commutation_relations(self):
        # [T1, T2] = i * T3
        t1, t2, t3 = self.fabric.generators_su2
        comm12 = self.fabric.matrix_commutator(t1, t2)
        # Check comm12 == i * t3
        for i in range(2):
            for j in range(2):
                expected = 1j * t3[i][j]
                self.assertAlmostEqual(comm12[i][j].real, expected.real, places=6)
                self.assertAlmostEqual(comm12[i][j].imag, expected.imag, places=6)

        # [T2, T3] = i * T1
        comm23 = self.fabric.matrix_commutator(t2, t3)
        for i in range(2):
            for j in range(2):
                expected = 1j * t1[i][j]
                self.assertAlmostEqual(comm23[i][j].real, expected.real, places=6)
                self.assertAlmostEqual(comm23[i][j].imag, expected.imag, places=6)

    def test_03_generator_normalization_traces(self):
        # Tr(Ta * Tb) = 0.5 * delta_ab
        for a in range(3):
            for b in range(3):
                ta = self.fabric.generators_su2[a]
                tb = self.fabric.generators_su2[b]
                prod = _mat_mul(ta, tb)
                tr = _mat_trace(prod)
                expected = 0.5 if a == b else 0.0
                self.assertAlmostEqual(tr.real, expected, places=6)
                self.assertAlmostEqual(tr.imag, 0.0, places=6)

    def test_04_zero_field_trivial_holonomy(self):
        # For A = 0, plaquette holonomy is identity matrix I
        u_p = self.fabric.compute_plaquette_holonomy([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
        self.assertAlmostEqual(u_p[0][0].real, 1.0, places=6)
        self.assertAlmostEqual(u_p[1][1].real, 1.0, places=6)
        self.assertAlmostEqual(u_p[0][1].real, 0.0, places=6)
        self.assertAlmostEqual(u_p[1][0].real, 0.0, places=6)

        w_res = self.fabric.compute_wilson_loop([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
        self.assertEqual(w_res["wilson_loop_value"], 1.0)

    def test_05_field_strength_non_abelian_commutator(self):
        # Ax along T1, Ay along T2
        # -i * g * [T1, T2] = -i * g * (i * T3) = g * T3
        ax = [1.0, 0.0, 0.0]
        ay = [0.0, 1.0, 0.0]
        f_strength = self.fabric.compute_field_strength(ax, ay)
        # Expected = 1.0 * T3 = [[0.5, 0], [0, -0.5]]
        self.assertAlmostEqual(f_strength[0][0].real, 0.5, places=5)
        self.assertAlmostEqual(f_strength[1][1].real, -0.5, places=5)

    def test_06_wilson_loop_plaquette_trace_bounded(self):
        ax = [0.8, -0.3, 0.5]
        ay = [0.2, 0.9, -0.4]
        res = self.fabric.compute_wilson_loop(ax, ay, dx=0.2, dy=0.2)
        self.assertTrue(res["is_unitary"])
        self.assertLessEqual(abs(res["wilson_loop_value"]), 1.0001)

    def test_07_wilson_loop_gauge_invariance(self):
        ax = [0.5, 0.2, -0.4]
        ay = [-0.1, 0.6, 0.3]
        gauge_test = self.fabric.verify_gauge_invariance(ax, ay, gauge_rotation_rad=1.2)
        self.assertTrue(gauge_test["is_gauge_invariant"])
        self.assertLess(gauge_test["discrepancy"], 1e-6)

    def test_08_coupling_scaling_effect(self):
        fabric_low = YangMillsGaugeHolonomyFabric(coupling_g=0.1)
        fabric_high = YangMillsGaugeHolonomyFabric(coupling_g=5.0)

        ax = [1.0, 0.0, 0.0]
        ay = [0.0, 1.0, 0.0]

        res_low = fabric_low.compute_wilson_loop(ax, ay, dx=0.1, dy=0.1)
        res_high = fabric_high.compute_wilson_loop(ax, ay, dx=0.1, dy=0.1)

        # Stronger coupling causes larger phase rotation away from 1.0
        diff_low = abs(1.0 - res_low["wilson_loop_value"])
        diff_high = abs(1.0 - res_high["wilson_loop_value"])
        self.assertGreater(diff_high, diff_low)

    def test_09_thread_safe_concurrent_computations(self):
        def worker():
            for _ in range(20):
                self.fabric.compute_wilson_loop([0.5, 0.0, 0.0], [0.0, 0.5, 0.0])

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(self.fabric.total_wilson_loops_computed, 80)

    def test_10_ascii_status_and_metrics(self):
        self.fabric.compute_wilson_loop([0.1, 0.2, 0.3], [0.4, 0.5, 0.6])
        self.fabric.verify_gauge_invariance([0.1, 0.2, 0.3], [0.4, 0.5, 0.6])

        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 261: Non-Abelian SU(N) Yang-Mills Gauge Holonomy Engine", ascii_table)
        self.assertIn("Gauge Symmetry Group", ascii_table)
        self.assertIn("Wilson Loop Holonomy", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 261)
        self.assertEqual(metrics["era"], 27)
        self.assertEqual(metrics["gauge_group"], "SU(2)")
        self.assertGreater(metrics["total_wilson_loops_computed"], 0)


if __name__ == "__main__":
    unittest.main()
