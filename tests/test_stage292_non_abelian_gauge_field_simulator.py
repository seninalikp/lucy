"""
Unit Tests for Stage 292: Non-Abelian SU(2) Yang-Mills Lattice Gauge Field Simulator & Wilson Loop Fabric
Sovereign Architect: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.non_abelian_gauge_field_simulator import (
    NonAbelianGaugeFieldSimulatorFabric,
    SU2Element,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
)


class TestStage292NonAbelianGaugeFieldSimulator(unittest.TestCase):

    def setUp(self):
        self.fabric = NonAbelianGaugeFieldSimulatorFabric(size_x=4, size_y=4, beta=2.5)

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 292)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["lattice_dimensions"], (4, 4))
        self.assertEqual(st["total_links"], 32)
        self.assertEqual(st["gauge_coupling_beta"], 2.5)
        self.assertEqual(st["status"], "OPERATIONAL")

    def test_02_cold_vacuum_plaquettes_and_action(self):
        # Cold vacuum (all U = I) should have Tr(U_P)/2 = 1.0 and S_W = 0.0
        avg_p = self.fabric.average_plaquette()
        action = self.fabric.wilson_action()
        self.assertAlmostEqual(avg_p, 1.0, places=6)
        self.assertAlmostEqual(action, 0.0, places=6)

    def test_03_su2_element_multiplication_group_laws(self):
        # I * U = U
        u_ident = SU2Element(1.0, 0.0, 0.0, 0.0)
        # Pauli X generator: i * sigma_x -> a1 = 1.0
        u_x = SU2Element(0.0, 1.0, 0.0, 0.0)
        prod = u_ident.multiply(u_x)
        self.assertAlmostEqual(prod.a0, 0.0, places=6)
        self.assertAlmostEqual(prod.a1, 1.0, places=6)

        # U * U^\dagger = I
        prod_inv = u_x.multiply(u_x.dagger())
        self.assertAlmostEqual(prod_inv.a0, 1.0, places=6)
        self.assertAlmostEqual(prod_inv.a1, 0.0, places=6)

    def test_04_su2_quaternion_normalization(self):
        u_unnorm = SU2Element(2.0, 2.0, 2.0, 2.0)
        u_norm = u_unnorm.normalize()
        mag_sq = u_norm.a0**2 + u_norm.a1**2 + u_norm.a2**2 + u_norm.a3**2
        self.assertAlmostEqual(mag_sq, 1.0, places=6)

    def test_05_gauge_invariance_under_local_transformation(self):
        # Average plaquette and action must be strictly invariant under gauge transformations
        init_plaq = self.fabric.average_plaquette()
        init_act = self.fabric.wilson_action()

        # Apply random SU(2) rotation at site (1, 1)
        omega = SU2Element(0.6, 0.8, 0.0, 0.0)
        self.fabric.apply_local_gauge_transformation(1, 1, omega)

        new_plaq = self.fabric.average_plaquette()
        new_act = self.fabric.wilson_action()
        self.assertAlmostEqual(init_plaq, new_plaq, places=5)
        self.assertAlmostEqual(init_act, new_act, places=5)

    def test_06_wilson_loop_in_cold_vacuum(self):
        # 1x1, 2x2, and 3x3 Wilson loops in vacuum evaluate to 1.0
        w11 = self.fabric.compute_wilson_loop(1, 1)
        w22 = self.fabric.compute_wilson_loop(2, 2)
        self.assertAlmostEqual(w11, 1.0, places=5)
        self.assertAlmostEqual(w22, 1.0, places=5)

    def test_07_fluctuation_increases_action(self):
        # Perturb a single link away from identity
        perturbed = SU2Element(0.0, 1.0, 0.0, 0.0) # Tr = 0
        self.fabric.set_link(0, 0, 0, perturbed)
        avg_p = self.fabric.average_plaquette()
        action = self.fabric.wilson_action()
        self.assertLess(avg_p, 1.0)
        self.assertGreater(action, 0.0)

    def test_08_invalid_dimension_raises(self):
        with self.assertRaises(ValueError):
            NonAbelianGaugeFieldSimulatorFabric(size_x=1, size_y=4)

    def test_09_multithreaded_concurrency(self):
        results = []

        def worker():
            p = self.fabric.average_plaquette()
            results.append(p)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)

    def test_10_su2_trace_bounds(self):
        u = SU2Element(0.7071, 0.7071, 0.0, 0.0)
        self.assertAlmostEqual(u.trace(), 2 * 0.7071, places=4)
        self.assertAlmostEqual(u.normalized_trace(), 0.7071, places=4)


if __name__ == "__main__":
    unittest.main()
