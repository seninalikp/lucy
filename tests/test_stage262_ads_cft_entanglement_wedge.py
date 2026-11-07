"""
Unit Tests for Stage 262: Holographic AdS/CFT Conformal Boundary-to-Bulk Dictionary & Ryu-Takayanagi Entanglement Wedge
Era 27: Cosmological Gauge Invariance, Non-Abelian Yang-Mills Fiber Bundles & Sovereign Trans-Planetary Unified Field Synthesis

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import math
import threading
import unittest
from backend.lucy_core.ads_cft_entanglement_wedge import (
    AdSCFTEntanglementWedgeFabric,
    get_entanglement_wedge_fabric,
    STAGE,
    ERA,
)


class TestStage262AdSCFTEntanglementWedge(unittest.TestCase):

    def setUp(self):
        self.fabric = AdSCFTEntanglementWedgeFabric(
            ads_radius_l=1.0,
            newton_constant_gn=0.25,
            default_uv_cutoff_eps=1e-3,
        )

    def test_01_singleton_and_initialization(self):
        singleton = get_entanglement_wedge_fabric()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 262)
        self.assertEqual(ERA, 27)
        # c = 3 * 1.0 / (2 * 0.25) = 6.0
        self.assertEqual(self.fabric.central_charge, 6.0)

    def test_02_ryu_takayanagi_logarithmic_scaling(self):
        # S_A = (c / 3) * ln(l / eps) = 2.0 * ln(l / eps)
        l_val = 10.0
        eps = 1e-3
        res = self.fabric.compute_ryu_takayanagi_entropy(l_val, uv_cutoff=eps)
        expected = 2.0 * math.log(l_val / eps)
        self.assertAlmostEqual(res["entanglement_entropy"], expected, places=5)
        self.assertEqual(res["max_bulk_penetration_z"], 5.0)

    def test_03_subsystem_below_uv_cutoff(self):
        res = self.fabric.compute_ryu_takayanagi_entropy(0.0005, uv_cutoff=0.001)
        self.assertEqual(res["entanglement_entropy"], 0.0)

    def test_04_bulk_geodesic_coordinates_semicircle(self):
        # Subsystem from x=-2.0 to x=2.0 (length l=4.0, radius=2.0, center=0.0)
        coords = self.fabric.compute_bulk_geodesic_coordinates(-2.0, 2.0, num_points=20)
        self.assertEqual(len(coords), 21)
        # Apex is at midpoint (theta = pi/2) -> (0.0, 2.0)
        mid_idx = 10
        mid_x, mid_z = coords[mid_idx]
        self.assertAlmostEqual(mid_x, 0.0, delta=0.01)
        self.assertAlmostEqual(mid_z, 2.0, delta=0.01)

    def test_05_point_inside_entanglement_wedge(self):
        # Subsystem [-2, 2] -> dome is x^2 + z^2 <= 4
        # Point (0.5, 1.0): 0.25 + 1.0 = 1.25 <= 4 -> inside!
        inside = self.fabric.is_in_entanglement_wedge(0.5, 1.0, -2.0, 2.0)
        self.assertTrue(inside)

    def test_06_point_outside_entanglement_wedge(self):
        # Point (1.5, 2.0): 2.25 + 4.0 = 6.25 > 4 -> outside!
        outside = self.fabric.is_in_entanglement_wedge(1.5, 2.0, -2.0, 2.0)
        self.assertFalse(outside)

        # Negative z outside physical bulk
        neg_z = self.fabric.is_in_entanglement_wedge(0.0, -0.5, -2.0, 2.0)
        self.assertFalse(neg_z)

    def test_07_holographic_mutual_information_connected_phase(self):
        # Subsystems A and B very close together: l_a = 5.0, l_b = 5.0, d = 0.1
        res = self.fabric.compute_holographic_mutual_information(5.0, 5.0, 0.1)
        self.assertEqual(res["holographic_phase"], "CONNECTED_ENTANGLED")
        self.assertGreater(res["mutual_information"], 0.0)

    def test_08_holographic_mutual_information_phase_transition_disconnected(self):
        # Subsystems A and B far apart: l_a = 1.0, l_b = 1.0, d = 20.0
        res = self.fabric.compute_holographic_mutual_information(1.0, 1.0, 20.0)
        self.assertEqual(res["holographic_phase"], "DISCONNECTED_DISENTANGLED")
        self.assertEqual(res["mutual_information"], 0.0)

    def test_09_thread_safe_concurrent_evaluations(self):
        def worker():
            for _ in range(25):
                self.fabric.compute_ryu_takayanagi_entropy(4.0)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(self.fabric.total_entropy_evaluations, 100)

    def test_10_ascii_status_and_metrics(self):
        self.fabric.compute_ryu_takayanagi_entropy(3.0)
        self.fabric.compute_bulk_geodesic_coordinates(0.0, 4.0)

        ascii_table = self.fabric.format_ascii_status()
        self.assertIn("STAGE 262: Holographic AdS/CFT Ryu-Takayanagi Entanglement Wedge", ascii_table)
        self.assertIn("Conformal Central Charge", ascii_table)
        self.assertIn("Entanglement Entropy", ascii_table)

        # CP1252 verification
        ascii_table.encode("cp1252")

        metrics = self.fabric.get_metrics()
        self.assertEqual(metrics["stage"], 262)
        self.assertEqual(metrics["era"], 27)
        self.assertEqual(metrics["central_charge"], 6.0)
        self.assertGreater(metrics["total_entropy_evaluations"], 0)


if __name__ == "__main__":
    unittest.main()
