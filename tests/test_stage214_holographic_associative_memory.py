r"""
tests/test_stage214_holographic_associative_memory.py
Stage 214: Holographic Memory Associative Content-Addressable Storage (H-CAM)
Era 22: Autonomous Galactic Hyper-Mesh, Hardware-Accelerated Photonic Emulation & Trans-Universal Reasoning Fabrics
"""

import unittest
from backend.lucy_core.holographic_associative_memory import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    HolographicPage,
    HolographicAssociativeMemoryFabric,
)


class TestStage214HolographicAssociativeMemory(unittest.TestCase):
    """10 Unit Tests for Stage 214 Holographic Associative Memory Fabric."""

    def setUp(self):
        self.fabric = HolographicAssociativeMemoryFabric(dimension=32)

    def test_01_fabric_initialization(self):
        self.assertEqual(STAGE, 214)
        self.assertEqual(ERA, 22)
        self.assertEqual(self.fabric.dimension, 32)
        self.assertEqual(len(self.fabric.pages), 0)
        self.assertEqual(self.fabric.status()["stage"], 214)

    def test_02_encode_key_to_phase_deterministic(self):
        p1 = self.fabric._encode_key_to_phase("sovereign_concept_alpha")
        p2 = self.fabric._encode_key_to_phase("sovereign_concept_alpha")
        self.assertEqual(len(p1), 32)
        self.assertEqual(p1, p2)
        # Unit magnitude check
        for c in p1:
            self.assertAlmostEqual(abs(c), 1.0, places=4)

    def test_03_store_page_superimposition(self):
        page = self.fabric.store_page("kernel_state_1", {"ram_mb": 4096})
        self.assertIsNotNone(page)
        self.assertEqual(len(self.fabric.pages), 1)
        self.assertEqual(self.fabric.stores_count, 1)
        # Non-zero interference volume
        total_mag = sum(abs(v) for v in self.fabric.interference_volume)
        self.assertGreater(total_mag, 0.0)

    def test_04_associative_recall_exact_match(self):
        self.fabric.store_page("beacon_alpha", "DATA_ALPHA")
        matches = self.fabric.associative_recall("beacon_alpha", correlation_threshold=0.9)
        self.assertEqual(len(matches), 1)
        matched_page, corr = matches[0]
        self.assertEqual(matched_page.key, "beacon_alpha")
        self.assertAlmostEqual(corr, 1.0, places=3)

    def test_05_associative_recall_orthogonal_keys(self):
        self.fabric.store_page("key_apple", "FRUIT")
        # Querying an unrelated key with high threshold yields 0 matches
        matches = self.fabric.associative_recall("key_submarine_nuclear", correlation_threshold=0.7)
        self.assertEqual(len(matches), 0)

    def test_06_associative_recall_threshold_filtering(self):
        self.fabric.store_page("target_memory", 12345)
        m_low = self.fabric.associative_recall("target_memory", correlation_threshold=0.1)
        m_high = self.fabric.associative_recall("target_memory", correlation_threshold=0.99)
        self.assertGreaterEqual(len(m_low), len(m_high))

    def test_07_reconstruct_from_degraded_partial_occlusion(self):
        self.fabric.store_page("resilient_archive", {"classified": True})
        # 40% occluded -> should retain ~60% correlation and still identify target page
        page, corr = self.fabric.reconstruct_from_degraded("resilient_archive", occlusion_fraction=0.4)
        self.assertIsNotNone(page)
        self.assertEqual(page.key, "resilient_archive")
        self.assertAlmostEqual(corr, 0.60, places=1)

    def test_08_reconstruct_from_degraded_heavy_damage(self):
        self.fabric.store_page("robust_beacon", "ALIVE")
        # 80% occluded -> retains ~20% correlation
        page, corr = self.fabric.reconstruct_from_degraded("robust_beacon", occlusion_fraction=0.8)
        self.assertIsNotNone(page)
        self.assertEqual(page.key, "robust_beacon")
        self.assertAlmostEqual(corr, 0.20, places=1)

    def test_09_multiple_page_superimposition(self):
        for i in range(5):
            self.fabric.store_page(f"key_{i}", f"payload_{i}")
        self.assertEqual(len(self.fabric.pages), 5)
        # Recall each of them
        for i in range(5):
            m = self.fabric.associative_recall(f"key_{i}", correlation_threshold=0.9)
            self.assertEqual(len(m), 1)
            self.assertEqual(m[0][0].key, f"key_{i}")

    def test_10_ascii_status_formatting(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 214: HOLOGRAPHIC ASSOCIATIVE CONTENT-ADDRESSABLE MEMORY", tbl)
        self.assertIn("Complex Optical Fourier Plane", tbl)
        self.assertIn("Volume Bragg Grating Emulation", tbl)


if __name__ == "__main__":
    unittest.main()
