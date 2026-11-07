"""
Unit Tests for Stage 267: Geometric Berry-Pancharatnam Phase & Non-Abelian Wilczek-Zee Holonomy Gate
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import math
import threading
from backend.lucy_core.berry_wilczek_zee_holonomy import (
    BerryWilczekZeeHolonomy,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage267BerryWilczekZeeHolonomy(unittest.TestCase):
    """Thorough unit test suite for Stage 267."""

    def setUp(self):
        self.bwz = BerryWilczekZeeHolonomy()

    def test_01_initialization(self):
        """Verify initialization and default state."""
        self.assertEqual(self.bwz.hbar, 1.0)
        self.assertEqual(len(self.bwz.gate_history), 0)

    def test_02_spin_berry_phase_half_solid_angle(self):
        """Verify Berry phase equals half the solid angle: gamma = -Omega / 2."""
        theta = math.pi / 2.0  # Equatorial cone
        res = self.bwz.compute_spin_berry_phase(cone_angle_theta_rad=theta, loops=1)
        expected_omega = 2.0 * math.pi * (1.0 - math.cos(theta))  # 2 * pi
        self.assertAlmostEqual(res["solid_angle_steradians"], expected_omega, places=4)
        expected_gamma = -0.5 * expected_omega  # -pi
        self.assertAlmostEqual(res["berry_phase_rad"], expected_gamma, places=4)

    def test_03_berry_phase_loops_scaling(self):
        """Verify linear scaling with multi-loop circuits."""
        res_1 = self.bwz.compute_spin_berry_phase(cone_angle_theta_rad=math.pi / 3.0, loops=1)
        res_3 = self.bwz.compute_spin_berry_phase(cone_angle_theta_rad=math.pi / 3.0, loops=3)
        self.assertAlmostEqual(res_3["berry_phase_rad"], res_1["berry_phase_rad"] * 3.0, places=4)

    def test_04_first_chern_number_monopole(self):
        """Verify first Chern number quantization C = -1."""
        res = self.bwz.compute_spin_berry_phase(cone_angle_theta_rad=math.pi / 4.0)
        self.assertEqual(res["first_chern_number"], -1)

    def test_05_pancharatnam_phase(self):
        """Verify Pancharatnam phase on Poincare sphere."""
        res = self.bwz.compute_pancharatnam_phase()
        self.assertIn("pancharatnam_phase_rad", res)
        self.assertIn("pancharatnam_phase_deg", res)
        self.assertIn("enclosed_solid_angle", res)

    def test_06_wilczek_zee_not_gate(self):
        """Verify Wilczek-Zee holonomic NOT gate synthesis and unitarity."""
        res = self.bwz.synthesize_wilczek_zee_gate(gate_type="NOT")
        self.assertEqual(res["gate_type"], "NOT")
        self.assertTrue(res["is_unitary"])
        self.assertAlmostEqual(res["holonomy_angle_rad"], math.pi, places=4)

    def test_07_wilczek_zee_phase_gate(self):
        """Verify Wilczek-Zee holonomic Phase gate synthesis."""
        angle = math.pi / 4.0
        res = self.bwz.synthesize_wilczek_zee_gate(gate_type="PHASE", alpha_angle=angle)
        self.assertEqual(res["gate_type"], "PHASE")
        self.assertTrue(res["is_unitary"])
        self.assertAlmostEqual(res["holonomy_angle_rad"], angle, places=4)

    def test_08_wilczek_zee_hadamard_gate(self):
        """Verify Wilczek-Zee holonomic Hadamard gate synthesis."""
        res = self.bwz.synthesize_wilczek_zee_gate(gate_type="HADAMARD")
        self.assertEqual(res["gate_type"], "HADAMARD")
        self.assertTrue(res["is_unitary"])

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.bwz.get_status()
        self.assertEqual(status["stage"], 267)
        self.assertEqual(status["era"], 27)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 267)
        self.assertEqual(ERA_ID, 27)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                engine = BerryWilczekZeeHolonomy()
                _ = engine.compute_spin_berry_phase(math.pi / 3.0)
                _ = engine.compute_pancharatnam_phase()
                _ = engine.synthesize_wilczek_zee_gate("NOT")
                _ = engine.synthesize_wilczek_zee_gate("PHASE", math.pi / 2.0)
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
