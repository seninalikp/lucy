r"""
tests/test_stage208_multimodal_symbolic_grounding.py
Stage 208: Real-Time Multi-Modal Audio-Visual Symbolic Grounding Fabric
Era 21: Autonomous Hyper-Scale Multi-Kernel Federation, Quantum-Resistant Keys & Post-Singularity Architecture
"""

import unittest
from backend.lucy_core.multimodal_symbolic_grounding import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    ModalityType,
    SceneEntity,
    SceneRelation,
    MultimodalSymbolicGroundingFabric,
)


class TestStage208MultimodalSymbolicGrounding(unittest.TestCase):
    """10 Unit Tests for Stage 208 Multimodal Symbolic Grounding Fabric."""

    def setUp(self):
        self.fabric = MultimodalSymbolicGroundingFabric(embedding_dim=16)

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric.embedding_dim, 16)
        self.assertEqual(len(self.fabric.entities), 0)
        self.assertEqual(len(self.fabric.relations), 0)
        self.assertEqual(self.fabric.status()["stage"], 208)
        self.assertEqual(self.fabric.status()["era"], 21)

    def test_02_register_scene_entity(self):
        ent = self.fabric.register_entity(
            label="operator_workstation",
            modality=ModalityType.VISUAL,
            embedding=[0.1] * 16,
            bbox_3d=(1.0, 2.0, 0.5, 0.8, 1.2, 0.7),
            confidence=0.98,
        )
        self.assertIn(ent.entity_id, self.fabric.entities)
        self.assertEqual(ent.label, "operator_workstation")
        self.assertEqual(ent.modality, ModalityType.VISUAL)
        self.assertEqual(len(ent.embedding), 16)

    def test_03_register_audio_entity(self):
        ent = self.fabric.register_entity(
            label="senin_vocal_command",
            modality=ModalityType.AUDIO,
            embedding=[0.5] * 16,
            bbox_3d=(1.0, 2.0, 1.6, 0.3, 0.3, 0.3),
            confidence=0.99,
        )
        self.assertEqual(ent.modality, ModalityType.AUDIO)
        self.assertEqual(ent.label, "senin_vocal_command")

    def test_04_embedding_dimension_padding_and_truncation(self):
        # Short embedding (5 elements) -> padded to 16
        e_short = self.fabric.register_entity("short", ModalityType.SYMBOLIC, [1.0, 2.0, 3.0, 4.0, 5.0])
        self.assertEqual(len(e_short.embedding), 16)
        self.assertEqual(e_short.embedding[5:], [0.0] * 11)

        # Long embedding (25 elements) -> truncated to 16
        e_long = self.fabric.register_entity("long", ModalityType.SYMBOLIC, [0.9] * 25)
        self.assertEqual(len(e_long.embedding), 16)

    def test_05_add_spatial_relation(self):
        e1 = self.fabric.register_entity("human_operator", ModalityType.VISUAL, [0.1] * 16)
        e2 = self.fabric.register_entity("terminal_screen", ModalityType.VISUAL, [0.2] * 16)

        rel = self.fabric.add_relation(e1.entity_id, e2.entity_id, "facing", weight=0.95)
        self.assertEqual(len(self.fabric.relations), 1)
        self.assertEqual(rel.source_id, e1.entity_id)
        self.assertEqual(rel.target_id, e2.entity_id)
        self.assertEqual(rel.relation, "facing")

    def test_06_add_relation_invalid_entities_raise(self):
        with self.assertRaises(ValueError):
            self.fabric.add_relation("ghost_1", "ghost_2", "adjacent_to")

    def test_07_fuse_audio_visual_features(self):
        audio = [0.8] * 16
        visual = [0.4] * 16
        fused = self.fabric.fuse_audio_visual(audio, visual)
        self.assertEqual(len(fused), 16)
        for val in fused:
            self.assertGreaterEqual(val, -1.0)
            self.assertLessEqual(val, 1.0)
        self.assertEqual(self.fabric._fusions_computed, 1)

    def test_08_query_grounded_symbol(self):
        e1 = self.fabric.register_entity("senin_primary_desktop", ModalityType.VISUAL, [0.3] * 16)
        e2 = self.fabric.register_entity("microphone_mic_0", ModalityType.AUDIO, [0.7] * 16)
        self.fabric.add_relation(e1.entity_id, e2.entity_id, "contains_sensor")

        res = self.fabric.query_grounded_symbol("desktop")
        self.assertEqual(len(res), 1)
        ent, rels = res[0]
        self.assertEqual(ent.entity_id, e1.entity_id)
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0].relation, "contains_sensor")

    def test_09_query_grounded_symbol_no_match(self):
        self.fabric.register_entity("existing_object", ModalityType.SYMBOLIC, [0.0] * 16)
        res = self.fabric.query_grounded_symbol("unrelated_spaceship")
        self.assertEqual(len(res), 0)

    def test_10_ascii_status_and_metadata(self):
        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 208: MULTIMODAL AUDIO-VISUAL SYMBOLIC GROUNDING FABRIC", ascii_out)
        self.assertIn("Era 21 (Post-Singularity Multimodal Grounding)", ascii_out)


if __name__ == "__main__":
    unittest.main()
