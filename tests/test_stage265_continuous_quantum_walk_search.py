"""
Unit Tests for Stage 265: Continuous-Time Quantum Walk & Graph-Topological Spatial Search Accelerator
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.continuous_quantum_walk_search import (
    ContinuousQuantumWalkSearch,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage265ContinuousQuantumWalkSearch(unittest.TestCase):
    """Thorough unit test suite for Stage 265."""

    def setUp(self):
        self.qw = ContinuousQuantumWalkSearch(num_nodes=12, hopping_rate_gamma=1.0)

    def test_01_initialization(self):
        """Verify default initialization and cycle graph topology."""
        self.assertEqual(self.qw.num_nodes, 12)
        st = self.qw.get_status()
        self.assertEqual(st["num_edges"], 12)  # Cycle C_12 has 12 edges
        self.assertIsNone(self.qw.marked_target)

    def test_02_unitary_norm_conservation(self):
        """Verify probability conservation sum |psi|^2 = 1.0 across evolution times."""
        times = [0.1, 0.5, 1.5, 3.0, 5.0]
        for t in times:
            res = self.qw.propagate_quantum_state(evolution_time=t)
            self.assertAlmostEqual(res["state_norm"], 1.0, places=4)
            self.assertEqual(len(res["probabilities"]), 12)

    def test_03_topology_complete_graph(self):
        """Verify complete graph K_N topology and propagation."""
        self.qw.set_topology_complete()
        st = self.qw.get_status()
        expected_edges = 12 * 11 // 2  # 66
        self.assertEqual(st["num_edges"], expected_edges)
        res = self.qw.propagate_quantum_state(evolution_time=1.0)
        self.assertAlmostEqual(res["state_norm"], 1.0, places=4)

    def test_04_topology_star_graph(self):
        """Verify star graph S_N topology."""
        self.qw.set_topology_star(center=0)
        st = self.qw.get_status()
        self.assertEqual(st["num_edges"], 11)  # Star S_12 has 11 edges
        # Initial localized state at center
        psi_0 = [complex(1.0 if i == 0 else 0.0) for i in range(12)]
        res = self.qw.propagate_quantum_state(initial_state=psi_0, evolution_time=0.5)
        # Probability must have diffused from center to leaves
        self.assertLess(res["probabilities"][0], 1.0)
        self.assertGreater(sum(res["probabilities"][1:]), 0.0)

    def test_05_topology_2d_grid(self):
        """Verify 2D grid graph topology configuration."""
        self.qw.set_topology_grid_2d(rows=3, cols=4)
        self.assertEqual(self.qw.num_nodes, 12)
        res = self.qw.propagate_quantum_state(evolution_time=1.2)
        self.assertAlmostEqual(res["state_norm"], 1.0, places=4)

    def test_06_oracle_depth_marking(self):
        """Verify construction of search Hamiltonian with marked oracle potential."""
        H = self.qw.build_hamiltonian(marked_node=4, oracle_depth=3.5)
        self.assertEqual(len(H), 12)
        # Node 4 should have diagonal potential shifted by -3.5
        self.assertAlmostEqual(H[4][4], -3.5, places=5)
        self.assertAlmostEqual(H[0][0], 0.0, places=5)

    def test_07_spatial_search_peak(self):
        """Verify spatial search discovers probability concentration above classical 1/N."""
        self.qw.set_topology_complete()
        res = self.qw.execute_spatial_search(target_node=3, oracle_depth=2.0, time_samples=30, max_time=6.0)
        self.assertEqual(res["target_node"], 3)
        self.assertGreater(res["peak_success_probability"], 1.0 / 12)
        self.assertGreater(res["optimal_time_t"], 0.0)

    def test_08_quantum_speedup_scaling(self):
        """Verify quadratic complexity advantage metric."""
        self.qw.set_topology_complete()
        res = self.qw.execute_spatial_search(target_node=5, oracle_depth=2.0)
        self.assertLess(res["quantum_complexity"], res["classical_complexity"])
        self.assertGreater(res["quantum_advantage_factor"], 0.0)

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.qw.get_status()
        self.assertEqual(status["stage"], 265)
        self.assertEqual(status["era"], 27)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 265)
        self.assertEqual(ERA_ID, 27)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safe execution across concurrent worker threads."""
        threads = []
        errors = []

        def worker():
            try:
                engine = ContinuousQuantumWalkSearch(num_nodes=8)
                engine.set_topology_cycle()
                res = engine.propagate_quantum_state(evolution_time=0.8)
                if abs(res["state_norm"] - 1.0) > 1e-3:
                    errors.append("Norm drift in thread")
                _ = engine.execute_spatial_search(target_node=2, oracle_depth=1.5, time_samples=10, max_time=3.0)
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
