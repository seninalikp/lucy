"""
Unit Tests for Stage 264: Autonomous Topological Soliton Skyrmion Lattice Dynamics & Chiral Domain Wall Weaver
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.topological_skyrmion_weaver import (
    TopologicalSkyrmionWeaver,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage264TopologicalSkyrmionWeaver(unittest.TestCase):
    """Thorough unit test suite for Stage 264."""

    def setUp(self):
        self.weaver = TopologicalSkyrmionWeaver(grid_width=32, grid_height=32)

    def test_01_initialization(self):
        """Verify default initialization and ferromagnetic vacuum."""
        self.assertEqual(self.weaver.grid_width, 32)
        self.assertEqual(self.weaver.grid_height, 32)
        q = self.weaver.compute_topological_charge()
        self.assertAlmostEqual(q, 0.0, places=3)
        self.assertEqual(len(self.weaver.soliton_registry), 0)

    def test_02_inject_single_skyrmion(self):
        """Verify single skyrmion injection produces topological charge Q ~ -1.0."""
        res = self.weaver.inject_skyrmion(center_x=16.0, center_y=16.0, radius=4.5)
        self.assertIn("topological_charge", res)
        # Numerical discretization on 32x32 yields Q near -1.0 (+/- 0.2 due to finite mesh boundary)
        self.assertAlmostEqual(res["topological_charge"], -1.0, delta=0.25)

    def test_03_antiskyrmion_or_polarity_flip(self):
        """Verify polarity flip reverses core magnetization and topological sign."""
        self.weaver.reset_lattice(initial_mz=-1.0)
        res = self.weaver.inject_skyrmion(center_x=16.0, center_y=16.0, radius=4.5, core_polarity=+1)
        self.assertIn("topological_charge", res)
        # Reversing core polarity reverses winding sign
        self.assertGreater(res["topological_charge"], 0.5)

    def test_04_energy_breakdown(self):
        """Verify computation of exchange, DMI, PMA and Zeeman energies."""
        self.weaver.inject_skyrmion(center_x=16.0, center_y=16.0, radius=4.0)
        energies = self.weaver.compute_energy_breakdown(b_ext_z=0.05)
        self.assertIn("exchange_energy_j", energies)
        self.assertIn("dmi_energy_j", energies)
        self.assertIn("anisotropy_energy_j", energies)
        self.assertIn("zeeman_energy_j", energies)
        self.assertIn("total_energy_j", energies)
        # Exchange energy must be strictly positive for non-trivial texture
        self.assertGreater(energies["exchange_energy_j"], 0.0)

    def test_05_thiele_dynamics_ferromagnet(self):
        """Verify uniform ferromagnet (Q=0) has zero gyrovector and zero Hall angle."""
        thiele = self.weaver.compute_thiele_dynamics()
        self.assertEqual(thiele["gyrovector_gz"], 0.0)
        self.assertEqual(thiele["skyrmion_hall_angle_deg"], 0.0)
        self.assertEqual(thiele["speed_m_s"], 0.0)

    def test_06_thiele_dynamics_skyrmion(self):
        """Verify skyrmion exhibits non-zero gyrovector and finite Skyrmion Hall angle."""
        self.weaver.inject_skyrmion(center_x=16.0, center_y=16.0, radius=4.5)
        thiele = self.weaver.compute_thiele_dynamics(current_density_j_a_m2=2e11, spin_polarization=0.4)
        self.assertNotEqual(thiele["gyrovector_gz"], 0.0)
        self.assertGreater(thiele["speed_m_s"], 0.0)
        # Skyrmion Hall angle is non-zero
        self.assertNotEqual(thiele["skyrmion_hall_angle_deg"], 0.0)

    def test_07_encode_racetrack_track(self):
        """Verify binary racetrack memory track encoding."""
        res = self.weaver.encode_racetrack_track("101", slot_width=8)
        self.assertEqual(res["encoded_bits"], "101")
        self.assertEqual(res["num_bits"], 3)
        self.assertEqual(len(res["slots"]), 3)
        # Two '1's should yield ~ -2.0 total charge
        self.assertAlmostEqual(res["total_topological_charge"], -2.0, delta=0.5)

    def test_08_skyrmion_crystal_lattice(self):
        """Verify creation of a multi-soliton crystal lattice."""
        weaver = TopologicalSkyrmionWeaver(grid_width=48, grid_height=48)
        res = weaver.weave_skyrmion_crystal_lattice(rows=2, cols=3, spacing=12.0)
        self.assertEqual(res["skyrmions_created"], 6)
        self.assertAlmostEqual(res["total_topological_charge"], -6.0, delta=1.5)

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and status output."""
        status = self.weaver.get_status()
        self.assertEqual(status["stage"], 264)
        self.assertEqual(status["era"], 27)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 264)
        self.assertEqual(ERA_ID, 27)

    def test_10_concurrency_and_reset(self):
        """Verify thread-safety and reset functionality."""
        threads = []
        errors = []

        def worker():
            try:
                w = TopologicalSkyrmionWeaver(grid_width=16, grid_height=16)
                w.inject_skyrmion(8.0, 8.0, 3.0)
                _ = w.compute_topological_charge()
                _ = w.compute_thiele_dynamics()
                w.reset_lattice()
                q = w.compute_topological_charge()
                if abs(q) > 1e-3:
                    errors.append("Reset failed to zero charge")
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
