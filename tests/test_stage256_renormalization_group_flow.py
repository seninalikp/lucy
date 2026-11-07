"""
Unit Tests for Stage 256: Deep Renormalization Group Flow & Wilsonian Effective Field Theory Coarse-Grainer
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import math
import unittest
from backend.lucy_core.renormalization_group_flow import (
    RenormalizationGroupFlowFabric,
    get_rg_flow_fabric,
    STAGE,
    ERA,
)


class TestStage256RenormalizationGroupFlow(unittest.TestCase):

    def setUp(self):
        self.fabric = RenormalizationGroupFlowFabric(block_factor=2)

    def test_01_singleton_and_initialization(self):
        singleton = get_rg_flow_fabric()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 256)
        self.assertEqual(ERA, 26)
        self.assertEqual(self.fabric.block_factor, 2)
        self.assertEqual(self.fabric.total_blocking_operations, 0)

    def test_02_beta_function_phi4_zero_coupling(self):
        # beta(0) = 0 for Gaussian free theory
        beta_0 = self.fabric.beta_function_phi4(0.0, epsilon=1.0)
        self.assertEqual(beta_0, 0.0)

    def test_03_beta_function_wilson_fisher_fixed_point(self):
        # At g* = 16 * pi^2 * eps / 3, beta(g*) must equal 0
        eps = 1.0
        g_wf = (16.0 * (math.pi ** 2) * eps) / 3.0
        beta_wf = self.fabric.beta_function_phi4(g_wf, epsilon=eps)
        self.assertAlmostEqual(beta_wf, 0.0, places=5)

    def test_04_rg_flow_trajectory_convergence(self):
        # Integrate RG flow from near the fixed point
        eps = 0.5
        g_wf = (16.0 * (math.pi ** 2) * eps) / 3.0
        flow = self.fabric.integrate_rg_flow(g_initial=g_wf * 0.95, epsilon=eps, steps=30, d_ln_mu=-0.05)
        self.assertEqual(flow["steps"], 30)
        self.assertAlmostEqual(flow["wilson_fisher_target"], g_wf, places=2)

    def test_05_kadanoff_spin_block_dimensions_halved(self):
        lat = self.fabric.generate_random_ising_lattice(width=16, height=16, seed=42)
        coarse = self.fabric.kadanoff_spin_block_2d(lat)
        self.assertEqual(len(coarse), 8)
        self.assertEqual(len(coarse[0]), 8)
        self.assertEqual(self.fabric.total_blocking_operations, 1)

    def test_06_kadanoff_all_spins_up_majority_invariance(self):
        # All +1 spins
        lat = [[1 for _ in range(8)] for _ in range(8)]
        coarse = self.fabric.kadanoff_spin_block_2d(lat)
        self.assertEqual(len(coarse), 4)
        for row in coarse:
            for s in row:
                self.assertEqual(s, 1)

    def test_07_kadanoff_all_spins_down_majority_invariance(self):
        # All -1 spins
        lat = [[-1 for _ in range(8)] for _ in range(8)]
        coarse = self.fabric.kadanoff_spin_block_2d(lat)
        self.assertEqual(len(coarse), 4)
        for row in coarse:
            for s in row:
                self.assertEqual(s, -1)

    def test_08_magnetization_and_nn_correlation(self):
        # Ferromagnetic state
        lat_ferro = [[1 for _ in range(4)] for _ in range(4)]
        stats_ferro = self.fabric.calculate_magnetization_and_correlation(lat_ferro)
        self.assertEqual(stats_ferro["magnetization"], 1.0)
        self.assertEqual(stats_ferro["nn_correlation"], 1.0)

        # Antiferromagnetic checkerboard
        lat_af = [[1 if (x + y) % 2 == 0 else -1 for x in range(4)] for y in range(4)]
        stats_af = self.fabric.calculate_magnetization_and_correlation(lat_af)
        self.assertEqual(stats_af["magnetization"], 0.0)
        self.assertEqual(stats_af["nn_correlation"], -1.0)

    def test_09_multiscale_iterated_blocking(self):
        lat = self.fabric.generate_random_ising_lattice(width=16, height=16, p_up=0.8, seed=10)
        # Block 16x16 -> 8x8 -> 4x4 -> 2x2
        b1 = self.fabric.kadanoff_spin_block_2d(lat)
        b2 = self.fabric.kadanoff_spin_block_2d(b1)
        b3 = self.fabric.kadanoff_spin_block_2d(b2)

        self.assertEqual(len(b1), 8)
        self.assertEqual(len(b2), 4)
        self.assertEqual(len(b3), 2)
        self.assertEqual(self.fabric.total_blocking_operations, 3)

    def test_10_ascii_status_and_metrics(self):
        lat = self.fabric.generate_random_ising_lattice(width=8, height=8, seed=1)
        self.fabric.kadanoff_spin_block_2d(lat)
        self.fabric.integrate_rg_flow(g_initial=5.0, steps=5)

        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 256: Deep Renormalization Group Flow & Wilsonian EFT", ascii_table)
        self.assertIn("Block Transformation", ascii_table)
        self.assertIn("RG Trajectories Run", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 256)
        self.assertEqual(metrics["era"], 26)
        self.assertEqual(metrics["block_factor"], 2)
        self.assertGreater(metrics["total_blocking_operations"], 0)


if __name__ == "__main__":
    unittest.main()
