"""
Unit Tests for Stage 297: Traversable Wormhole Protocol & Quantum Teleportation Engine
Sovereign Architect: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.wormhole_teleportation_protocol import (
    WormholeTeleportationProtocolFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
)


class TestStage297WormholeTeleportationProtocol(unittest.TestCase):

    def setUp(self):
        self.fabric = WormholeTeleportationProtocolFabric(throat_radius_m=1.0e3, default_coupling=0.1)

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 297)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["throat_radius_m"], 1.0e3)
        self.assertEqual(st["double_trace_coupling_h"], 0.1)
        self.assertTrue(st["is_traversable"])
        self.assertEqual(st["status"], "OPERATIONAL")

    def test_02_anec_violation_is_negative(self):
        # Average null energy must be negative for horizon opening
        anec = self.fabric.compute_anec_integral()
        self.assertLess(anec, 0.0)

    def test_03_null_shockwave_shift_is_negative(self):
        # Delta v < 0 (shifts null geodesic to arrive earlier -> traversable)
        shift = self.fabric.compute_shockwave_shift()
        self.assertLess(shift, 0.0)

    def test_04_shockwave_shift_linear_in_coupling(self):
        # Doubling coupling h must double the magnitude of negative shift
        s1 = self.fabric.compute_shockwave_shift(coupling_h=0.1)
        s2 = self.fabric.compute_shockwave_shift(coupling_h=0.2)
        self.assertAlmostEqual(s2 / s1, 2.0, places=6)

    def test_05_traversability_verification(self):
        m = self.fabric.evaluate_traversability(coupling_h=0.5)
        self.assertTrue(m.is_traversable)
        self.assertLess(m.null_shockwave_shift_delta_v, 0.0)
        self.assertGreater(m.teleportation_fidelity, 0.5)

    def test_06_throat_radius_inverse_square_scaling(self):
        # ANEC is proportional to 1 / r0^2
        f1 = WormholeTeleportationProtocolFabric(throat_radius_m=100.0)
        f2 = WormholeTeleportationProtocolFabric(throat_radius_m=200.0)
        a1 = f1.compute_anec_integral(coupling_h=1.0)
        a2 = f2.compute_anec_integral(coupling_h=1.0)
        self.assertAlmostEqual(a1 / a2, 4.0, places=4)

    def test_07_teleportation_fidelity_bounds(self):
        fid = self.fabric.calculate_teleportation_fidelity(num_qubits=1, coupling_h=1.0)
        self.assertGreaterEqual(fid, 0.5)
        self.assertLessEqual(fid, 1.0)

    def test_08_invalid_parameters_raise(self):
        with self.assertRaises(ValueError):
            WormholeTeleportationProtocolFabric(throat_radius_m=-10.0)
        with self.assertRaises(ValueError):
            WormholeTeleportationProtocolFabric(default_coupling=-0.5)

    def test_09_multithreaded_concurrency(self):
        results = []

        def worker():
            m = self.fabric.evaluate_traversability()
            results.append(m.is_traversable)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)
        self.assertTrue(all(results))

    def test_10_zero_or_negative_qubits_raises(self):
        with self.assertRaises(ValueError):
            self.fabric.calculate_teleportation_fidelity(num_qubits=0)


if __name__ == "__main__":
    unittest.main()
