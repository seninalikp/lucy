"""
Unit Tests for Stage 254: Continuous Symplectic Geometric Integrator & Lie-Poisson Hamiltonian Momentum Preserver
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.symplectic_hamiltonian_integrator import (
    SymplecticHamiltonianIntegratorFabric,
    get_symplectic_integrator,
    STAGE,
    ERA,
)


class TestStage254SymplecticHamiltonianIntegrator(unittest.TestCase):

    def setUp(self):
        self.fabric = SymplecticHamiltonianIntegratorFabric(default_mass=1.0)

    def test_01_singleton_and_initialization(self):
        singleton = get_symplectic_integrator()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 254)
        self.assertEqual(ERA, 26)
        self.assertEqual(self.fabric.mass, 1.0)
        self.assertEqual(self.fabric.total_steps_integrated, 0)

    def test_02_harmonic_energy_and_gradient(self):
        # q = [2.0], p = [3.0], m = 1.0, k = 1.0
        # E = 3^2 / 2 + 1/2 * 2^2 = 4.5 + 2.0 = 6.5
        e = self.fabric.harmonic_energy([2.0], [3.0], k=1.0)
        self.assertAlmostEqual(e, 6.5)

        grad = self.fabric.harmonic_grad_v([2.0], k=1.0)
        self.assertEqual(grad, [2.0])

    def test_03_single_step_stormer_verlet(self):
        q0 = [1.0]
        p0 = [0.0]
        dt = 0.1
        q1, p1 = self.fabric.step_stormer_verlet(q0, p0, dt, self.fabric.harmonic_grad_v)

        # Analytic leapfrog check:
        # p_half = 0 - 0.5 * 0.1 * 1.0 = -0.05
        # q1 = 1.0 + 0.1 * (-0.05) = 0.995
        # p1 = -0.05 - 0.5 * 0.1 * 0.995 = -0.09975
        self.assertAlmostEqual(q1[0], 0.995)
        self.assertAlmostEqual(p1[0], -0.09975)

    def test_04_long_term_energy_conservation_no_secular_drift(self):
        # 1000 steps without dissipative decay
        sim = self.fabric.simulate_harmonic_trajectory(
            q0=[1.0],
            p0=[0.0],
            dt=0.02,
            steps=1000,
            k=1.0
        )
        self.assertEqual(sim["steps"], 1000)
        # Relative energy fluctuation must be small (< 0.1%)
        self.assertLess(sim["relative_energy_fluctuation"], 0.001)

    def test_05_reversible_trajectory_time_symmetry(self):
        # Step forward 20 steps
        q = [1.5]
        p = [0.8]
        dt = 0.05
        for _ in range(20):
            q, p = self.fabric.step_stormer_verlet(q, p, dt, self.fabric.harmonic_grad_v)

        # Step backward 20 steps with -dt
        for _ in range(20):
            q, p = self.fabric.step_stormer_verlet(q, p, -dt, self.fabric.harmonic_grad_v)

        self.assertAlmostEqual(q[0], 1.5, places=6)
        self.assertAlmostEqual(p[0], 0.8, places=6)

    def test_06_symplectic_jacobian_determinant_unity(self):
        res = self.fabric.verify_symplectic_jacobian(q0=[1.0], p0=[0.5], dt=0.05)
        self.assertTrue(res["is_symplectic_invariant"])
        self.assertAlmostEqual(res["det_jacobian"], 1.0, places=3)
        self.assertLess(res["det_discrepancy"], 1e-3)

    def test_07_multidimensional_harmonic_system(self):
        q0 = [1.0, -0.5, 2.0]
        p0 = [0.0, 1.2, -0.8]
        sim = self.fabric.simulate_harmonic_trajectory(q0, p0, dt=0.01, steps=200)
        self.assertLess(sim["relative_energy_fluctuation"], 0.001)
        self.assertEqual(len(sim["final_q"]), 3)
        self.assertEqual(len(sim["final_p"]), 3)

    def test_08_lie_poisson_rigid_body_casimir_preservation(self):
        # Euler rigid body with initial angular momentum L = [1.0, 2.0, 3.0]
        l_curr = [1.0, 2.0, 3.0]
        i_diag = [1.0, 2.0, 5.0]
        c_initial = math.sqrt(sum(x**2 for x in l_curr))

        for _ in range(100):
            l_curr, c_curr = self.fabric.step_lie_poisson_rigid_body(l_curr, i_diag, dt=0.01)

        c_final = math.sqrt(sum(x**2 for x in l_curr))
        self.assertAlmostEqual(c_initial, c_final, places=6)

    def test_09_thread_safe_concurrent_integration(self):
        def worker():
            for _ in range(10):
                self.fabric.simulate_harmonic_trajectory([1.0], [0.0], dt=0.05, steps=50)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(self.fabric.total_steps_integrated, 2000)

    def test_10_ascii_status_and_metrics(self):
        self.fabric.simulate_harmonic_trajectory([1.0], [0.0], dt=0.05, steps=10)
        self.fabric.verify_symplectic_jacobian([1.0], [0.0], dt=0.05)

        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 254: Symplectic Integrator & Lie-Poisson Momentum Preserver", ascii_table)
        self.assertIn("Canonical Mass", ascii_table)
        self.assertIn("Symplectic Steps", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 254)
        self.assertEqual(metrics["era"], 26)
        self.assertGreater(metrics["total_steps_integrated"], 0)


if __name__ == "__main__":
    unittest.main()
