"""
tests/test_stage243_cellular_cohomology_sheaf.py
Unit tests for Stage 243: Deep Sheaf-Theoretic Distributed Multi-Sensor Consistency & Cellular Cohomology Engine
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials
"""

import os
import sys
import unittest

sys.path.insert(0, os.getcwd())

from backend.lucy_core.cellular_cohomology_sheaf import (
    STAGE,
    STAGE_NAME,
    ERA,
    CellularCohomologySheafFabric
)


class TestStage243CellularCohomologySheaf(unittest.TestCase):

    def test_01_sheaf_complex_initialization(self):
        """Test default 4-node sensor sheaf complex initialization."""
        sheaf = CellularCohomologySheafFabric(stalk_dim=1)
        self.assertEqual(len(sheaf.vertices), 4)
        self.assertEqual(len(sheaf.edges), 4)
        self.assertEqual(sheaf.stalk_dim, 1)

    def test_02_global_section_zero_energy(self):
        """Test that identical sensor sections form a global section in H^0 with zero Dirichlet energy."""
        sheaf = CellularCohomologySheafFabric(stalk_dim=1)
        for v in sheaf.vertices:
            sheaf.set_sensor_value(v, [42.0])

        self.assertAlmostEqual(sheaf.compute_sheaf_dirichlet_energy(), 0.0, places=6)
        self.assertTrue(sheaf.is_globally_consistent())

    def test_03_coboundary_residual_non_zero_on_discrepancy(self):
        """Test non-zero coboundary 1-cochains on discrepant sensor nodes."""
        sheaf = CellularCohomologySheafFabric(stalk_dim=1)
        sheaf.set_sensor_value("sensor_alpha", [10.0])
        sheaf.set_sensor_value("sensor_beta", [15.0]) # 5.0 discrepancy

        res = sheaf.compute_coboundary_residual()
        self.assertIn("e_sensor_alpha_sensor_beta", res)
        diff = res["e_sensor_alpha_sensor_beta"]
        self.assertAlmostEqual(diff[0], 5.0, places=4)

    def test_04_dirichlet_energy_quadratic_scaling(self):
        """Test Dirichlet energy scales with the square of the discrepancy delta."""
        sheaf = CellularCohomologySheafFabric(stalk_dim=1)
        # Baseline identical
        for v in sheaf.vertices:
            sheaf.set_sensor_value(v, [10.0])

        sheaf.set_sensor_value("sensor_alpha", [12.0]) # delta = 2.0
        e1 = sheaf.compute_sheaf_dirichlet_energy()

        sheaf.set_sensor_value("sensor_alpha", [14.0]) # delta = 4.0 (2x delta)
        e2 = sheaf.compute_sheaf_dirichlet_energy()

        # E scales as delta^2 -> e2 / e1 ~ 4.0
        self.assertAlmostEqual(e2 / e1, 4.0, places=4)

    def test_05_h1_obstruction_detection(self):
        """Test topological audit detects H^1 obstruction on inconsistent data."""
        sheaf = CellularCohomologySheafFabric(stalk_dim=1)
        for v in sheaf.vertices:
            sheaf.set_sensor_value(v, [10.0])
        sheaf.set_sensor_value("sensor_gamma", [99.0]) # Major anomaly

        audit = sheaf.audit_topological_obstruction()
        self.assertTrue(audit["h1_obstruction_detected"])
        self.assertFalse(audit["is_global_section_h0"])
        self.assertGreater(audit["dirichlet_energy"], 100.0)
        self.assertEqual(sheaf.total_audits, 1)

    def test_06_harmonic_diffusion_convergence(self):
        """Test gradient descent on Sheaf Laplacian converges monotonically toward consensus."""
        sheaf = CellularCohomologySheafFabric(stalk_dim=1)
        sheaf.set_sensor_value("sensor_alpha", [10.0])
        sheaf.set_sensor_value("sensor_beta", [20.0])
        sheaf.set_sensor_value("sensor_gamma", [30.0])
        sheaf.set_sensor_value("sensor_delta", [40.0])

        e_initial = sheaf.compute_sheaf_dirichlet_energy()
        energies = []
        for _ in range(25):
            e = sheaf.diffuse_harmonic_consensus_step(step_size=0.1)
            energies.append(e)

        self.assertLess(energies[-1], e_initial)
        self.assertLess(energies[-1], 1.0)
        self.assertEqual(sheaf.total_diffusions, 25)

    def test_07_multi_dimensional_vector_stalks(self):
        """Test higher-dimensional vector stalks (R^3)."""
        sheaf = CellularCohomologySheafFabric(stalk_dim=3)
        sheaf.set_sensor_value("sensor_alpha", [1.0, 2.0, 3.0])
        sheaf.set_sensor_value("sensor_beta", [1.0, 2.0, 3.0])
        sheaf.set_sensor_value("sensor_gamma", [1.0, 2.0, 3.0])
        sheaf.set_sensor_value("sensor_delta", [1.0, 2.0, 3.0])

        self.assertAlmostEqual(sheaf.compute_sheaf_dirichlet_energy(), 0.0, places=6)
        self.assertTrue(sheaf.is_globally_consistent())

    def test_08_dynamic_vertex_and_edge_addition(self):
        """Test adding new vertices and edges dynamically to cell complex."""
        sheaf = CellularCohomologySheafFabric(stalk_dim=1)
        sheaf.add_vertex("sensor_epsilon", [10.0])
        eid = sheaf.add_edge("sensor_delta", "sensor_epsilon", weight=2.0)

        self.assertIn("sensor_epsilon", sheaf.vertices)
        self.assertIn(eid, sheaf.edges)
        self.assertEqual(sheaf.edges[eid].weight, 2.0)

    def test_09_sheaf_status_dictionary(self):
        """Test status dictionary output."""
        sheaf = CellularCohomologySheafFabric(stalk_dim=2)
        st = sheaf.status()
        self.assertEqual(st["stage"], 243)
        self.assertEqual(st["era"], 25)
        self.assertEqual(st["stalk_dimension"], 2)
        self.assertIn("dirichlet_energy", st)

    def test_10_ascii_status_table(self):
        """Test CP1252-safe ASCII table formatting."""
        sheaf = CellularCohomologySheafFabric()
        tbl = sheaf.format_ascii_status()
        self.assertIn("STAGE 243", tbl)
        self.assertIn("Cell Complex", tbl)
        self.assertIn("Cohomology Status", tbl)
        self.assertTrue(tbl.startswith("+--"))
        self.assertTrue(tbl.endswith("--+"))


if __name__ == "__main__":
    unittest.main()
