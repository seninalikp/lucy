"""
Unit Tests for Stage 253: Hyper-Dimensional Clifford Geometric Algebra (Cl_{p,q,r}) Multivector Wave Processor
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import math
import unittest
from backend.lucy_core.clifford_geometric_algebra import (
    CliffordGeometricAlgebraFabric,
    Multivector,
    get_clifford_processor,
    STAGE,
    ERA,
)


class TestStage253CliffordGeometricAlgebra(unittest.TestCase):

    def setUp(self):
        self.fabric = CliffordGeometricAlgebraFabric(p=3, q=0, r=0)

    def test_01_singleton_and_initialization(self):
        singleton = get_clifford_processor()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 253)
        self.assertEqual(ERA, 26)
        self.assertEqual(self.fabric.p, 3)
        self.assertEqual(self.fabric.q, 0)
        self.assertEqual(self.fabric.r, 0)
        self.assertEqual(1 << (self.fabric.p + self.fabric.q + self.fabric.r), 8)

    def test_02_basis_blade_multiplication_signs(self):
        # In Cl(3,0): e1 (blade 1), e2 (blade 2)
        e1 = self.fabric.create_vector([1.0, 0.0, 0.0])
        e2 = self.fabric.create_vector([0.0, 1.0, 0.0])

        e12 = self.fabric.geometric_product(e1, e2)
        e21 = self.fabric.geometric_product(e2, e1)

        # e1 * e2 = e12 (blade 3), e2 * e1 = -e12
        self.assertAlmostEqual(e12.coeffs[3], 1.0)
        self.assertAlmostEqual(e21.coeffs[3], -1.0)

        # e1^2 = +1 (scalar component)
        e1_sq = self.fabric.geometric_product(e1, e1)
        self.assertAlmostEqual(e1_sq.scalar(), 1.0)

    def test_03_minkowski_spacetime_signature(self):
        # Spacetime Algebra Cl(1, 3): e0^2 = +1, e1^2 = -1
        sta = CliffordGeometricAlgebraFabric(p=1, q=3, r=0)
        e0 = sta.create_vector([1.0, 0.0, 0.0, 0.0])
        e1 = sta.create_vector([0.0, 1.0, 0.0, 0.0])

        e0_sq = sta.geometric_product(e0, e0)
        e1_sq = sta.geometric_product(e1, e1)

        self.assertAlmostEqual(e0_sq.scalar(), 1.0)
        self.assertAlmostEqual(e1_sq.scalar(), -1.0)

    def test_04_geometric_product_decomposition(self):
        # ab = a . b + a ^ b for arbitrary vectors
        v1 = self.fabric.create_vector([2.0, -1.0, 3.0])
        v2 = self.fabric.create_vector([0.5, 4.0, 1.5])

        decomp = self.fabric.verify_geometric_decomposition(v1, v2)
        self.assertTrue(decomp["decomposition_holds"])
        self.assertLess(decomp["max_discrepancy"], 1e-9)

    def test_05_orthogonal_vectors_anticommute(self):
        # v1 and v2 orthogonal -> a . b = 0, ab = a ^ b = -ba
        v1 = self.fabric.create_vector([1.0, 0.0, 0.0])
        v2 = self.fabric.create_vector([0.0, 1.0, 0.0])

        prod12 = self.fabric.geometric_product(v1, v2)
        prod21 = self.fabric.geometric_product(v2, v1)
        ip = self.fabric.inner_product(v1, v2)

        self.assertAlmostEqual(ip.scalar(), 0.0)
        for b in range(prod12.dim):
            self.assertAlmostEqual(prod12.coeffs[b], -prod21.coeffs[b])

    def test_06_collinear_vectors_commute(self):
        # v1 and v2 parallel -> a ^ b = 0, ab = a . b = ba
        v1 = self.fabric.create_vector([2.0, 0.0, 0.0])
        v2 = self.fabric.create_vector([3.0, 0.0, 0.0])

        wp = self.fabric.wedge_product(v1, v2)
        self.assertAlmostEqual(wp.norm(), 0.0)

        gp = self.fabric.geometric_product(v1, v2)
        ip = self.fabric.inner_product(v1, v2)
        self.assertAlmostEqual(gp.scalar(), 6.0)
        self.assertAlmostEqual(ip.scalar(), 6.0)

    def test_07_rotor_90_degree_rotation(self):
        # Rotor in e12 plane (blade 3) by pi/2: R = cos(pi/4) - e12 * sin(pi/4)
        rotor = self.fabric.create_rotor(plane_bivector_idx=3, theta_rad=math.pi / 2.0)
        v = self.fabric.create_vector([1.0, 0.0, 0.0])  # Along x (e1)

        v_rotated = self.fabric.rotate_vector(v, rotor)

        # After +90 deg rotation in xy plane, vector should be along y (e2 = blade 2)
        self.assertAlmostEqual(v_rotated.coeffs[1], 0.0, places=6)  # e1
        self.assertAlmostEqual(v_rotated.coeffs[2], 1.0, places=6)  # e2
        self.assertAlmostEqual(v_rotated.coeffs[4], 0.0, places=6)  # e3

    def test_08_rotor_norm_preservation(self):
        rotor = self.fabric.create_rotor(plane_bivector_idx=3, theta_rad=0.785)
        v = self.fabric.create_vector([3.0, -4.0, 5.0])
        v_orig_norm = v.norm()

        v_rot = self.fabric.rotate_vector(v, rotor)
        v_rot_norm = v_rot.norm()

        self.assertAlmostEqual(v_orig_norm, v_rot_norm, places=6)

    def test_09_multivector_reversion_grade_invariance(self):
        mv = self.fabric.create_multivector([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        rev1 = mv.reverse()
        rev2 = rev1.reverse()

        for b in range(mv.dim):
            self.assertAlmostEqual(mv.coeffs[b], rev2.coeffs[b])

    def test_10_ascii_status_and_metrics(self):
        self.fabric.create_vector([1.0, 2.0, 3.0])
        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 253: Clifford Geometric Algebra Multivector Wave Processor", ascii_table)
        self.assertIn("Algebra Signature", ascii_table)
        self.assertIn("Blade Space Dimension", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 253)
        self.assertEqual(metrics["era"], 26)
        self.assertEqual(metrics["signature"], "Cl(3,0,0)")
        self.assertEqual(metrics["total_blades"], 8)


if __name__ == "__main__":
    unittest.main()
