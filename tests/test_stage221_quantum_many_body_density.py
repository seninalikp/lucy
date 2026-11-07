r"""
tests/test_stage221_quantum_many_body_density.py
Stage 221: Quantum Many-Body Density Matrix Simulator & Mixed-State Dephasing Fabric
Era 23: Universal Multi-Verse State Synthesis, Sub-Atomic Hyper-Computing & Sovereign Holographic Swarm Intelligence
"""

import math
import unittest
from backend.lucy_core.quantum_many_body_density import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    DensityMatrix,
    QuantumManyBodyDensityFabric,
)


class TestStage221QuantumManyBodyDensity(unittest.TestCase):
    """10 Unit Tests for Stage 221 Quantum Density Matrix Fabric."""

    def setUp(self):
        self.fabric = QuantumManyBodyDensityFabric(default_dim=2)

    def test_01_fabric_initialization(self):
        self.assertEqual(STAGE, 221)
        self.assertEqual(ERA, 23)
        self.assertEqual(self.fabric.default_dim, 2)
        self.assertEqual(self.fabric.simulations_count, 0)
        self.assertEqual(self.fabric.status()["stage"], 221)

    def test_02_prepare_pure_state_trace_and_purity(self):
        # Pure state |+> = (|0> + |1>)/sqrt(2)
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        dm = self.fabric.prepare_pure_state([inv_sqrt2, inv_sqrt2])
        self.assertAlmostEqual(dm.trace().real, 1.0, places=4)
        self.assertAlmostEqual(dm.purity(), 1.0, places=4)
        # Off-diagonal elements should be 0.5
        self.assertAlmostEqual(dm.data[0][1].real, 0.5, places=4)

    def test_03_prepare_maximally_mixed(self):
        dm = self.fabric.prepare_maximally_mixed(dim=2)
        self.assertAlmostEqual(dm.trace().real, 1.0, places=4)
        # Purity for 2x2 maximally mixed is 1/2 = 0.5
        self.assertAlmostEqual(dm.purity(), 0.5, places=4)
        self.assertAlmostEqual(dm.data[0][0].real, 0.5, places=4)
        self.assertAlmostEqual(dm.data[0][1].real, 0.0, places=4)

    def test_04_phase_damping_preserves_diagonals(self):
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        dm = self.fabric.prepare_pure_state([inv_sqrt2, inv_sqrt2])
        damped = self.fabric.apply_phase_damping(dm, lambda_rate=0.5)

        # Diagonals preserved at 0.5
        self.assertAlmostEqual(damped.data[0][0].real, 0.5, places=4)
        self.assertAlmostEqual(damped.data[1][1].real, 0.5, places=4)
        # Off-diagonals decayed: 0.5 * (1 - 0.5) = 0.25
        self.assertAlmostEqual(damped.data[0][1].real, 0.25, places=4)
        # Purity reduced (mixed state)
        self.assertLess(damped.purity(), 1.0)

    def test_05_amplitude_damping_full_relaxation(self):
        # Excited state |1> -> [0, 1]
        dm = self.fabric.prepare_pure_state([0.0, 1.0])
        # Full decay gamma = 1.0 -> relaxes to ground state |0>
        relaxed = self.fabric.apply_amplitude_damping(dm, gamma=1.0)
        self.assertAlmostEqual(relaxed.data[0][0].real, 1.0, places=4)
        self.assertAlmostEqual(relaxed.data[1][1].real, 0.0, places=4)

    def test_06_von_neumann_entropy_pure_state(self):
        dm = self.fabric.prepare_pure_state([1.0, 0.0])  # |0>
        entropy = self.fabric.compute_von_neumann_entropy(dm)
        self.assertAlmostEqual(entropy, 0.0, places=4)

    def test_07_von_neumann_entropy_maximally_mixed(self):
        dm = self.fabric.prepare_maximally_mixed(dim=2)
        entropy = self.fabric.compute_von_neumann_entropy(dm)
        # For d=2, log2(2) = 1.0
        self.assertAlmostEqual(entropy, 1.0, places=4)

    def test_08_partial_trace_bell_state(self):
        # Bell state (|00> + |11>) / sqrt(2) in 4D basis: |00>=0, |01>=1, |10>=2, |11>=3
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        bell_vec = [inv_sqrt2, 0.0, 0.0, inv_sqrt2]
        dm_bell = self.fabric.prepare_pure_state(bell_vec)

        # Trace out subsystem B (leaves 2x2 subsystem A)
        dm_a = self.fabric.partial_trace_b(dm_bell, dim_a=2, dim_b=2)
        self.assertEqual(dm_a.dim, 2)
        # Subsystem A should be maximally mixed (entropy = 1.0)
        self.assertAlmostEqual(dm_a.data[0][0].real, 0.5, places=4)
        self.assertAlmostEqual(dm_a.data[1][1].real, 0.5, places=4)
        self.assertAlmostEqual(dm_a.data[0][1].real, 0.0, places=4)
        self.assertAlmostEqual(self.fabric.compute_von_neumann_entropy(dm_a), 1.0, places=4)

    def test_09_partial_trace_dimension_mismatch(self):
        dm = self.fabric.prepare_pure_state([1.0, 0.0])  # dim 2
        with self.assertRaises(ValueError):
            self.fabric.partial_trace_b(dm, dim_a=2, dim_b=2)  # expects dim 4

    def test_10_ascii_status_formatting(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 221: QUANTUM DENSITY MATRIX & MIXED-STATE DEPHASING FABRIC", tbl)
        self.assertIn("Hilbert Space Basis", tbl)
        self.assertIn("T1 Energy Relaxation & T2 Phase Damping", tbl)


if __name__ == "__main__":
    unittest.main()
