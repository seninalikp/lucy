"""
Unit Tests for Stage 296: Quantum Hall Skyrmion Spin Texture & Topological Soliton Engine
Sovereign Architect: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.quantum_hall_skyrmion_crystal import (
    QuantumHallSkyrmionCrystalFabric,
    STAGE,
    STAGE_NAME,
    SOVEREIGN_OPERATOR,
    E_CHARGE,
)


class TestStage296QuantumHallSkyrmionCrystal(unittest.TestCase):

    def setUp(self):
        self.fabric = QuantumHallSkyrmionCrystalFabric(filling_factor=1.0, magnetic_field_tesla=10.0)

    def test_01_initialization_and_metadata(self):
        st = self.fabric.status()
        self.assertEqual(st["stage"], 296)
        self.assertEqual(st["stage_name"], STAGE_NAME)
        self.assertEqual(st["sovereign_operator"], SOVEREIGN_OPERATOR)
        self.assertEqual(st["filling_factor_nu"], 1.0)
        self.assertEqual(st["magnetic_field_tesla"], 10.0)
        self.assertEqual(st["status"], "OPERATIONAL")

    def test_02_hedgehog_profile_unit_sphere_norm(self):
        # All vector points in hedgehog profile must lie on S^2 (norm = 1.0)
        grid = self.fabric.generate_hedgehog_spin_profile(grid_size=15, radius_lb=2.0, winding=1)
        for row in grid:
            for nx, ny, nz in row:
                norm_sq = nx**2 + ny**2 + nz**2
                self.assertAlmostEqual(norm_sq, 1.0, places=5)

    def test_03_core_spin_reversal(self):
        # Core at center must be pointing down (-1.0 in nz)
        grid = self.fabric.generate_hedgehog_spin_profile(grid_size=15, radius_lb=2.0, winding=1)
        center = len(grid) // 2
        core = grid[center][center]
        self.assertAlmostEqual(core[0], 0.0, places=6)
        self.assertAlmostEqual(core[1], 0.0, places=6)
        self.assertAlmostEqual(core[2], -1.0, places=6)

    def test_04_pontryagin_index_winding_sign(self):
        # Q = +1 skyrmion vs Q = -1 antiskyrmion
        grid_pos = self.fabric.generate_hedgehog_spin_profile(grid_size=25, radius_lb=3.0, winding=1)
        q_pos = self.fabric.compute_pontryagin_topological_charge(grid_pos)

        grid_neg = self.fabric.generate_hedgehog_spin_profile(grid_size=25, radius_lb=3.0, winding=-1)
        q_neg = self.fabric.compute_pontryagin_topological_charge(grid_neg)

        # Discrete lattice sum has opposite signs for opposite winding
        self.assertNotEqual(math.copysign(1.0, q_pos), math.copysign(1.0, q_neg))

    def test_05_effective_electric_charge_quantization(self):
        # e* = - nu * Q * e
        m1 = self.fabric.calculate_skyrmion_energy(winding_q=1, radius_lb=3.0)
        self.assertAlmostEqual(m1.effective_electric_charge_coulombs, - 1.0 * E_CHARGE, places=22)

        f_half = QuantumHallSkyrmionCrystalFabric(filling_factor=0.3333333333333333)
        m_half = f_half.calculate_skyrmion_energy(winding_q=1, radius_lb=3.0)
        self.assertAlmostEqual(m_half.effective_electric_charge_coulombs, - (1.0 / 3.0) * E_CHARGE, delta=1e-22)

    def test_06_exchange_energy_proportional_to_winding(self):
        # E_ex = 4*pi*rho_s * |Q|
        m1 = self.fabric.calculate_skyrmion_energy(winding_q=1, radius_lb=2.0)
        m2 = self.fabric.calculate_skyrmion_energy(winding_q=2, radius_lb=2.0)
        self.assertAlmostEqual(m2.exchange_energy_mev / m1.exchange_energy_mev, 2.0, places=5)

    def test_07_zeeman_energy_scales_with_b_field(self):
        # E_Z is proportional to B field
        f1 = QuantumHallSkyrmionCrystalFabric(filling_factor=1.0, magnetic_field_tesla=5.0)
        f2 = QuantumHallSkyrmionCrystalFabric(filling_factor=1.0, magnetic_field_tesla=10.0)
        m1 = f1.calculate_skyrmion_energy(winding_q=1, radius_lb=3.0)
        m2 = f2.calculate_skyrmion_energy(winding_q=1, radius_lb=3.0)
        self.assertAlmostEqual(m2.zeeman_energy_mev / m1.zeeman_energy_mev, 2.0, places=5)

    def test_08_invalid_parameters_raise(self):
        with self.assertRaises(ValueError):
            QuantumHallSkyrmionCrystalFabric(filling_factor=-0.5)
        with self.assertRaises(ValueError):
            QuantumHallSkyrmionCrystalFabric(magnetic_field_tesla=0.0)

    def test_09_multithreaded_concurrency(self):
        results = []

        def worker():
            m = self.fabric.calculate_skyrmion_energy(1, 2.5)
            results.append(m.total_energy_mev)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 10)
        self.assertTrue(all(e > 0 for e in results))

    def test_10_topological_protection_flag(self):
        m_prot = self.fabric.calculate_skyrmion_energy(winding_q=1)
        self.assertTrue(m_prot.is_topologically_protected)
        m_triv = self.fabric.calculate_skyrmion_energy(winding_q=0)
        self.assertFalse(m_triv.is_topologically_protected)


if __name__ == "__main__":
    unittest.main()
