r"""
tests/test_stage125_latent_concept_miner.py
Unit tests for Stage 125: Self-Supervised Latent Concept Miner (Era 13).
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.latent_concept_miner import (
    LatentConceptMiner,
    MinedConcept,
    STAGE,
    ERA,
    ERA_NAME,
    STAGE_NAME,
    CREATOR_NAME,
    CREATOR_FULL_NAME,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def record_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        self.receipts.append({
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        })


class MockKnowledgeGraph:
    def __init__(self):
        self.nodes = {}

    def add_node(self, node_id: str, node_type: str, label: str, properties: dict = None, weight: float = 1.0):
        self.nodes[node_id] = {
            "node_type": node_type,
            "label": label,
            "properties": properties,
            "weight": weight,
        }


class TestStage125LatentConceptMiner(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_test_stage125_"))
        self.data_dir = self.test_dir / "data" / "lucy" / "concepts"
        self.ledger = MockReceiptLedger()
        self.miner = LatentConceptMiner(
            project_root=self.test_dir,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 125)
        self.assertEqual(ERA, 13)
        self.assertEqual(STAGE_NAME, "Self-Supervised Latent Concept Miner")
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")

        st = self.miner.status()
        self.assertEqual(st["stage"], 125)
        self.assertEqual(st["era"], 13)
        self.assertEqual(st["creator"], "Senin")
        self.assertGreaterEqual(st["total_concepts"], 3)
        self.assertEqual(st["total_mining_cycles"], 0)

    def test_02_foundational_concepts_seeded(self):
        op_concept = self.miner.get_concept("concept_invariant_operator_identity")
        self.assertIsNotNone(op_concept)
        self.assertEqual(op_concept.category, "SYSTEM_INVARIANT")
        self.assertEqual(op_concept.confidence, 1.0)
        self.assertIn("Senin", op_concept.description)

        sov_concept = self.miner.get_concept("concept_invariant_offline_sovereignty")
        self.assertIsNotNone(sov_concept)
        self.assertIn("offline", sov_concept.description.lower())

    def test_03_mine_concepts_cycle(self):
        new_concepts = self.miner.mine_concepts(min_support=2)
        self.assertGreaterEqual(len(new_concepts), 2)

        # Check mining metrics updated
        st = self.miner.status()
        self.assertEqual(st["total_mining_cycles"], 1)
        self.assertGreater(st["total_concepts"], 3)

        # Verify receipt
        rec_cats = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("CONCEPTS_MINED", rec_cats)

    def test_04_export_to_knowledge_graph(self):
        kg = MockKnowledgeGraph()
        count = self.miner.export_to_knowledge_graph(kg)
        self.assertGreaterEqual(count, 3)

        # Check node in mock KG
        self.assertIn("concept:concept_invariant_operator_identity", kg.nodes)
        node = kg.nodes["concept:concept_invariant_operator_identity"]
        self.assertEqual(node["node_type"], "CONCEPT")
        self.assertEqual(node["weight"], 1.0)

        # Verify receipt
        rec_cats = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("TAXONOMY_UPDATED", rec_cats)

    def test_05_list_concepts_by_category(self):
        invariants = self.miner.list_concepts("SYSTEM_INVARIANT")
        self.assertGreaterEqual(len(invariants), 2)
        for c in invariants:
            self.assertEqual(c.category, "SYSTEM_INVARIANT")

        motifs = self.miner.list_concepts("WORKFLOW_MOTIF")
        self.assertGreaterEqual(len(motifs), 1)

    def test_06_persistence_and_reload(self):
        self.miner.mine_concepts()

        # Fresh instance pointing to same storage
        fresh_miner = LatentConceptMiner(
            project_root=self.test_dir,
            data_dir=self.data_dir,
        )
        st = fresh_miner.status()
        self.assertGreaterEqual(st["total_concepts"], 5)
        self.assertIsNotNone(fresh_miner.get_concept("concept_invariant_operator_identity"))

    def test_07_ascii_status_and_taxonomy_tree(self):
        tbl = self.miner.format_concept_status_table()
        self.assertIn("LUCY OS - SELF-SUPERVISED LATENT CONCEPT MINER", tbl)
        self.assertIn("Total Mined Concepts in Taxonomy", tbl)
        self.assertIn("Senin (Senin Ali K P)", tbl)

        tree = self.miner.format_concept_taxonomy_tree()
        self.assertIn("LUCY OS - LATENT CONCEPT TAXONOMY TREE", tree)
        self.assertIn("# [SYSTEM_INVARIANT]", tree)
        self.assertIn("+-- Operator Authority Permanence", tree)

    def test_08_dataclass_methods(self):
        c = MinedConcept(
            concept_id="c_test",
            name="Test Concept",
            category="STRUCTURAL_PATTERN",
            description="A test pattern",
            confidence=0.88,
            support_count=12,
            exemplars=["sample 1"],
            derived_rules=["rule 1"],
        )
        d = c.to_dict()
        self.assertEqual(d["concept_id"], "c_test")
        self.assertEqual(d["confidence"], 0.88)
        self.assertEqual(len(d["exemplars"]), 1)


if __name__ == "__main__":
    unittest.main()
