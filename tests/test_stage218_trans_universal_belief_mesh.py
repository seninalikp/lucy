r"""
tests/test_stage218_trans_universal_belief_mesh.py
Stage 218: Trans-Universal Multi-Agent Recursive Reasoning & Belief Propagation Mesh
Era 22: Autonomous Galactic Hyper-Mesh, Hardware-Accelerated Photonic Emulation & Trans-Universal Reasoning Fabrics
"""

import unittest
from backend.lucy_core.trans_universal_belief_mesh import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    FactorNode,
    TransUniversalBeliefMeshFabric,
    VariableNode,
)


class TestStage218TransUniversalBeliefMesh(unittest.TestCase):
    """10 Unit Tests for Stage 218 Trans-Universal Belief Mesh Fabric."""

    def setUp(self):
        self.fabric = TransUniversalBeliefMeshFabric()

    def test_01_fabric_initialization(self):
        self.assertEqual(STAGE, 218)
        self.assertEqual(ERA, 22)
        self.assertEqual(len(self.fabric.variables), 0)
        self.assertEqual(len(self.fabric.factors), 0)
        self.assertEqual(self.fabric.inference_runs, 0)
        self.assertEqual(self.fabric.status()["stage"], 218)

    def test_02_add_variable_default_uniform_prior(self):
        var = self.fabric.add_variable("X1", cardinality=2)
        self.assertEqual(var.var_id, "X1")
        self.assertEqual(var.cardinality, 2)
        self.assertEqual(var.prior, [0.5, 0.5])

    def test_03_add_factor_and_channel_initialization(self):
        self.fabric.add_variable("A", 2)
        self.fabric.add_variable("B", 2)
        table = {(0, 0): 0.9, (0, 1): 0.1, (1, 0): 0.1, (1, 1): 0.9}
        f = self.fabric.add_factor("f_AB", ["A", "B"], table)
        self.assertEqual(f.factor_id, "f_AB")
        self.assertIn(("A", "f_AB"), self.fabric.messages)
        self.assertIn(("f_AB", "A"), self.fabric.messages)
        self.assertIn(("B", "f_AB"), self.fabric.messages)
        self.assertIn(("f_AB", "B"), self.fabric.messages)

    def test_04_step_belief_propagation_delta(self):
        self.fabric.add_variable("A", 2)
        self.fabric.add_variable("B", 2)
        self.fabric.add_factor("f1", ["A", "B"], {(0, 0): 1.0, (1, 1): 1.0})
        delta = self.fabric.step_belief_propagation()
        self.assertIsInstance(delta, float)
        self.assertGreaterEqual(delta, 0.0)

    def test_05_single_variable_evidence_propagation(self):
        # Biased prior on X
        self.fabric.add_variable("X", 2, prior=[0.9, 0.1])
        beliefs = self.fabric.run_inference(max_iterations=5)
        self.assertAlmostEqual(beliefs["X"][0], 0.9, places=2)
        self.assertAlmostEqual(beliefs["X"][1], 0.1, places=2)

    def test_06_two_variable_correlated_inference(self):
        # Variable A has evidence [0.95, 0.05], Variable B has uniform prior [0.5, 0.5]
        # Strong equality potential between A and B
        self.fabric.add_variable("A", 2, prior=[0.95, 0.05])
        self.fabric.add_variable("B", 2, prior=[0.5, 0.5])
        self.fabric.add_factor("f_agree", ["A", "B"], {(0, 0): 0.9, (0, 1): 0.1, (1, 0): 0.1, (1, 1): 0.9})

        beliefs = self.fabric.run_inference(max_iterations=10)
        # B should be persuaded towards state 0
        self.assertGreater(beliefs["B"][0], 0.70)

    def test_07_loopy_triangle_convergence(self):
        # 3 variables in a ring
        self.fabric.add_variable("V1", 2)
        self.fabric.add_variable("V2", 2)
        self.fabric.add_variable("V3", 2)
        table = {(0, 0): 0.8, (0, 1): 0.2, (1, 0): 0.2, (1, 1): 0.8}
        self.fabric.add_factor("f12", ["V1", "V2"], table)
        self.fabric.add_factor("f23", ["V2", "V3"], table)
        self.fabric.add_factor("f31", ["V3", "V1"], table)

        beliefs = self.fabric.run_inference(max_iterations=15)
        self.assertEqual(len(beliefs), 3)
        for v in ["V1", "V2", "V3"]:
            self.assertAlmostEqual(sum(beliefs[v]), 1.0, places=3)

    def test_08_run_inference_posterior_normalization(self):
        self.fabric.add_variable("M1", 3)
        self.fabric.add_variable("M2", 3)
        table = {(i, j): 1.0 for i in range(3) for j in range(3)}
        self.fabric.add_factor("f_m", ["M1", "M2"], table)
        beliefs = self.fabric.run_inference(max_iterations=5)
        self.assertAlmostEqual(sum(beliefs["M1"]), 1.0, places=3)
        self.assertAlmostEqual(sum(beliefs["M2"]), 1.0, places=3)

    def test_09_message_ticks_and_runs_counter(self):
        self.fabric.add_variable("Z", 2)
        self.fabric.run_inference(max_iterations=3)
        s = self.fabric.status()
        self.assertEqual(s["inference_runs"], 1)
        self.assertGreater(s["message_ticks"], 0)

    def test_10_ascii_status_formatting(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 218: TRANS-UNIVERSAL RECURSIVE BELIEF PROPAGATION MESH", tbl)
        self.assertIn("Variable Nodes (State)", tbl)
        self.assertIn("Loopy Damped Sum-Product Belief Propagation", tbl)


if __name__ == "__main__":
    unittest.main()
