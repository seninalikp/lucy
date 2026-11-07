"""
tests/test_stage242_exceptional_point_resonance.py
Unit tests for Stage 242: Non-Hermitian Exceptional Point Dynamical Resonance Engine
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.getcwd())

from backend.lucy_core.exceptional_point_resonance import (
    STAGE,
    STAGE_NAME,
    ERA,
    PTPhase,
    ExceptionalPointResonanceFabric
)


class TestStage242ExceptionalPointResonance(unittest.TestCase):

    def test_01_pt_exact_phase_real_eigenvalues(self):
        """Test PT-exact phase (gamma < kappa): real eigenvalues with zero imaginary part."""
        fabric = ExceptionalPointResonanceFabric(omega_0=10.0, kappa=3.0, gamma=1.0)
        st = fabric.compute_eigenspectrum()
        self.assertEqual(st.phase, PTPhase.EXACT_SYMMETRIC)
        self.assertAlmostEqual(st.eigenvalue_plus.imag, 0.0, places=6)
        self.assertAlmostEqual(st.eigenvalue_minus.imag, 0.0, places=6)
        # Expected: 10 +/- sqrt(9 - 1) = 10 +/- sqrt(8) ~ 10 +/- 2.8284
        self.assertAlmostEqual(st.eigenvalue_plus.real, 10.0 + math.sqrt(8.0), places=4)
        self.assertAlmostEqual(st.eigenvalue_minus.real, 10.0 - math.sqrt(8.0), places=4)

    def test_02_exceptional_point_coalescence(self):
        """Test Exceptional Point (gamma == kappa): eigenvalue coalescence to omega_0 and fidelity=1.0."""
        fabric = ExceptionalPointResonanceFabric(omega_0=10.0, kappa=2.5, gamma=2.5)
        st = fabric.compute_eigenspectrum()
        self.assertEqual(st.phase, PTPhase.EXCEPTIONAL_POINT)
        self.assertAlmostEqual(st.eigenvalue_plus.real, 10.0, places=5)
        self.assertAlmostEqual(st.eigenvalue_minus.real, 10.0, places=5)
        self.assertAlmostEqual(abs(st.splitting), 0.0, places=5)
        self.assertEqual(st.eigenvector_coalescence_fidelity, 1.0)

    def test_03_pt_broken_phase_complex_conjugates(self):
        """Test PT-broken phase (gamma > kappa): complex conjugate eigenvalues with non-zero imaginary parts."""
        fabric = ExceptionalPointResonanceFabric(omega_0=10.0, kappa=1.0, gamma=3.0)
        st = fabric.compute_eigenspectrum()
        self.assertEqual(st.phase, PTPhase.BROKEN_SYMMETRIC)
        # Expected: 10 +/- i * sqrt(9 - 1) = 10 +/- i * sqrt(8)
        self.assertAlmostEqual(st.eigenvalue_plus.real, 10.0, places=4)
        self.assertAlmostEqual(st.eigenvalue_minus.real, 10.0, places=4)
        self.assertAlmostEqual(abs(st.eigenvalue_plus.imag), math.sqrt(8.0), places=4)
        self.assertAlmostEqual(abs(st.eigenvalue_minus.imag), math.sqrt(8.0), places=4)
        self.assertAlmostEqual(st.eigenvalue_plus.imag, -st.eigenvalue_minus.imag, places=4)

    def test_04_square_root_scaling_sensitivity(self):
        """Test square-root perturbation scaling gives huge sensitivity enhancement at EP."""
        fabric = ExceptionalPointResonanceFabric(omega_0=10.0, kappa=2.0, gamma=2.0)
        res = fabric.measure_perturbation_enhancement(epsilon=1e-4)
        # For eps = 1e-4, sqrt(eps) = 1e-2. Enhancement ~ 1e-2 / (2 * 1e-4) ~ 50x to 100x
        self.assertGreater(res["sensitivity_enhancement_factor"], 50.0)
        self.assertEqual(fabric.total_sensings, 1)

    def test_05_extreme_sub_micro_perturbation_scaling(self):
        """Test extreme perturbation eps = 1e-6 exhibits enhancement > 500x."""
        fabric = ExceptionalPointResonanceFabric(omega_0=10.0, kappa=2.0, gamma=2.0)
        res = fabric.measure_perturbation_enhancement(epsilon=1e-6)
        # sqrt(1e-6) = 1e-3. 1e-3 / 1e-6 ~ 1000x enhancement
        self.assertGreater(res["sensitivity_enhancement_factor"], 500.0)

    def test_06_non_trivial_parametric_encircling(self):
        """Test clockwise encircling of the Exceptional Point in parameter space."""
        fabric = ExceptionalPointResonanceFabric(omega_0=10.0, kappa=2.0, gamma=2.0)
        res = fabric.encircle_exceptional_point(num_steps=50, clockwise=True)
        self.assertEqual(res["direction"], "CLOCKWISE")
        self.assertTrue(res["chiral_topological_state_transferred"])
        self.assertEqual(fabric.total_encirclings, 1)

    def test_07_counter_clockwise_encircling(self):
        """Test counter-clockwise encircling of the Exceptional Point."""
        fabric = ExceptionalPointResonanceFabric(omega_0=10.0, kappa=2.0, gamma=2.0)
        res = fabric.encircle_exceptional_point(num_steps=50, clockwise=False)
        self.assertEqual(res["direction"], "COUNTER_CLOCKWISE")
        self.assertTrue(res["chiral_topological_state_transferred"])

    def test_08_invalid_epsilon_raises_error(self):
        """Test negative or zero epsilon raises ValueError."""
        fabric = ExceptionalPointResonanceFabric()
        with self.assertRaises(ValueError):
            fabric.measure_perturbation_enhancement(-0.01)
        with self.assertRaises(ValueError):
            fabric.measure_perturbation_enhancement(0.0)

    def test_09_fabric_status_dictionary(self):
        """Test status dictionary keys and values."""
        fabric = ExceptionalPointResonanceFabric(omega_0=12.0, kappa=2.0, gamma=2.0)
        st = fabric.status()
        self.assertEqual(st["stage"], 242)
        self.assertEqual(st["era"], 25)
        self.assertEqual(st["pt_phase"], "EXCEPTIONAL_POINT")
        self.assertEqual(st["coalescence_fidelity"], 1.0)

    def test_10_ascii_status_table(self):
        """Test CP1252-safe ASCII table formatting."""
        fabric = ExceptionalPointResonanceFabric()
        tbl = fabric.format_ascii_status()
        self.assertIn("STAGE 242", tbl)
        self.assertIn("PT Symmetry Phase", tbl)
        self.assertIn("EP State Coalescence", tbl)
        self.assertTrue(tbl.startswith("+--"))
        self.assertTrue(tbl.endswith("--+"))


if __name__ == "__main__":
    unittest.main()
