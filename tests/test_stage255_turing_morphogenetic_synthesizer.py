"""
Unit Tests for Stage 255: Sovereign Bio-Mimetic Morphogenetic Reaction-Diffusion Turing Pattern Synthesizer
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import threading
import unittest
from backend.lucy_core.turing_morphogenetic_synthesizer import (
    TuringMorphogeneticSynthesizerFabric,
    get_turing_synthesizer,
    MorphogeneticRegime,
    STAGE,
    ERA,
)


class TestStage255TuringMorphogeneticSynthesizer(unittest.TestCase):

    def setUp(self):
        self.fabric = TuringMorphogeneticSynthesizerFabric(
            grid_width=16,
            grid_height=16,
            diff_u=0.16,
            diff_v=0.08,
            feed_f=0.035,
            kill_k=0.065,
        )

    def test_01_singleton_and_initialization(self):
        singleton = get_turing_synthesizer()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 255)
        self.assertEqual(ERA, 26)
        self.assertEqual(self.fabric.w, 16)
        self.assertEqual(self.fabric.h, 16)
        self.assertEqual(self.fabric.u[0][0], 1.0)
        self.assertEqual(self.fabric.v[0][0], 0.0)

    def test_02_homogeneous_equilibrium_stability(self):
        # Stepping homogeneous grid should remain homogeneous at u=1, v=0
        self.fabric.step_reaction_diffusion(steps=5, dt=1.0)
        stats = self.fabric.compute_morphogenetic_statistics()
        self.assertEqual(stats["regime"], "HOMOGENEOUS")
        self.assertAlmostEqual(stats["variance_v"], 0.0)

    def test_03_seed_central_spot(self):
        self.fabric.seed_central_spot(radius=2, u_val=0.5, v_val=0.25)
        self.assertEqual(self.fabric.total_perturbations_injected, 1)
        cx, cy = 8, 8
        self.assertEqual(self.fabric.u[cy][cx], 0.5)
        self.assertEqual(self.fabric.v[cy][cx], 0.25)

    def test_04_reaction_diffusion_step_bounds(self):
        self.fabric.seed_central_spot(radius=2)
        self.fabric.step_reaction_diffusion(steps=10, dt=1.0)

        for y in range(self.fabric.h):
            for x in range(self.fabric.w):
                self.assertGreaterEqual(self.fabric.u[y][x], 0.0)
                self.assertLessEqual(self.fabric.u[y][x], 1.0)
                self.assertGreaterEqual(self.fabric.v[y][x], 0.0)
                self.assertLessEqual(self.fabric.v[y][x], 1.0)

    def test_05_turing_instability_mathematical_conditions(self):
        # Activator-inhibitor Jacobian at steady state
        # fu > 0 (self-activation), fv < 0 (inhibition)
        # gu > 0 (activation of inhibitor), gv < 0 (inhibitor self-decay)
        # Differential diffusion: Dv >> Du
        fu, fv = 1.0, -1.0
        gu, gv = 2.0, -1.5
        du, dv = 0.01, 0.20

        res = self.fabric.evaluate_turing_instability(fu, fv, gu, gv, du, dv)
        self.assertTrue(res["cond1_stable_homogeneous"])
        self.assertTrue(res["cond2_det_positive"])
        self.assertTrue(res["cond3_diffusion_destabilizing"])
        self.assertTrue(res["cond4_bifurcation_positive"])
        self.assertTrue(res["is_turing_instability"])
        self.assertGreater(res["pattern_wavelength"], 0.0)

    def test_06_turing_stability_when_diffusion_equal(self):
        # Equal diffusion Du == Dv prevents Turing instability
        fu, fv = 1.0, -1.0
        gu, gv = 2.0, -1.5
        du, dv = 0.1, 0.1

        res = self.fabric.evaluate_turing_instability(fu, fv, gu, gv, du, dv)
        self.assertFalse(res["is_turing_instability"])

    def test_07_morphogenetic_statistics_variance_tracking(self):
        self.fabric.seed_central_spot(radius=3)
        self.fabric.step_reaction_diffusion(steps=5, dt=1.0)
        stats = self.fabric.compute_morphogenetic_statistics()
        self.assertGreater(stats["variance_u"], 0.0)
        self.assertGreater(stats["variance_v"], 0.0)

    def test_08_periodic_toroidal_boundary_continuity(self):
        # Seed perturbation on corner (0, 0)
        self.fabric.u[0][0] = 0.5
        self.fabric.v[0][0] = 0.5
        self.fabric.step_reaction_diffusion(steps=2, dt=1.0)
        # Should execute cleanly across periodic boundaries
        self.assertGreater(self.fabric.v[15][15], 0.0)

    def test_09_thread_safe_concurrent_simulation(self):
        def worker():
            for _ in range(5):
                self.fabric.step_reaction_diffusion(steps=2)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(self.fabric.total_simulation_steps, 40)

    def test_10_ascii_status_and_metrics(self):
        self.fabric.seed_central_spot(radius=2)
        self.fabric.step_reaction_diffusion(steps=2)

        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 255: Bio-Mimetic Turing Reaction-Diffusion Synthesizer", ascii_table)
        self.assertIn("Grid Stencil Topology", ascii_table)
        self.assertIn("Chemical Parameters", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 255)
        self.assertEqual(metrics["era"], 26)
        self.assertGreater(metrics["total_simulation_steps"], 0)


if __name__ == "__main__":
    unittest.main()
