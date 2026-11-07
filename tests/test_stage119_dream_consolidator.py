r"""
tests/test_stage119_dream_consolidator.py
Unit tests for Stage 119: Episodic Dream Consolidator (Era 12).
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.dream_consolidator import (
    EpisodicDreamConsolidator,
    EpisodicTrace,
    CrystallizedAxiom,
    DreamSessionReceipt,
    STAGE,
    ERA,
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


class TestStage119DreamConsolidator(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_test_stage119_"))
        self.data_dir = self.test_dir / "data" / "lucy" / "dream"
        self.ledger = MockReceiptLedger()
        self.consolidator = EpisodicDreamConsolidator(
            project_root=self.test_dir,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 119)
        self.assertEqual(ERA, 12)
        self.assertEqual(STAGE_NAME, "Episodic Dream Consolidator")
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")

        st = self.consolidator.status()
        self.assertEqual(st["stage"], 119)
        self.assertEqual(st["era"], 12)
        self.assertEqual(st["creator"], "Senin")
        self.assertGreaterEqual(st["total_axioms"], 5)
        self.assertEqual(st["total_cycles"], 0)

    def test_02_foundational_axioms_seeded(self):
        axioms = self.consolidator.recall_axioms()
        self.assertGreaterEqual(len(axioms), 5)

        # Check identity axiom
        id_axioms = self.consolidator.recall_axioms(domain="identity")
        self.assertTrue(len(id_axioms) >= 1)
        self.assertIn("Senin", id_axioms[0].rule)
        self.assertTrue(id_axioms[0].is_permanent)
        self.assertEqual(id_axioms[0].confidence, 1.0)

        # Check sovereignty axiom
        sov_axioms = self.consolidator.recall_axioms(domain="sovereignty")
        self.assertTrue(len(sov_axioms) >= 1)
        self.assertIn("locally and offline", sov_axioms[0].rule)

    def test_03_manual_axiom_crystallization(self):
        ax = self.consolidator.add_axiom(
            domain="security",
            subject="Zero Leak Policy",
            rule="No private keys or tokens shall leave memory unsanitized.",
            confidence=0.98,
        )
        self.assertEqual(ax.domain, "security")
        self.assertEqual(ax.subject, "Zero Leak Policy")
        self.assertTrue(ax.is_permanent)

        # Check receipt recorded
        rec_types = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("AXIOM_CRYSTALLIZED", rec_types)

        # Verify query
        sec_axioms = self.consolidator.recall_axioms(domain="security")
        self.assertEqual(len(sec_axioms), 1)
        self.assertEqual(sec_axioms[0].subject, "Zero Leak Policy")

    def test_04_run_dream_cycle_basic(self):
        receipt = self.consolidator.run_dream_cycle()
        self.assertIsInstance(receipt, DreamSessionReceipt)
        self.assertTrue(receipt.dream_id.startswith("dream_"))
        self.assertGreater(receipt.traces_reviewed, 0)
        self.assertGreaterEqual(receipt.lora_triples_generated, 5)

        # Status updated
        st = self.consolidator.status()
        self.assertEqual(st["total_cycles"], 1)
        self.assertGreater(st["last_cycle_timestamp"], 0.0)

        # Ledger recorded
        rec_types = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("DREAM_CYCLE_STARTED", rec_types)
        self.assertIn("DREAM_CYCLE_COMPLETED", rec_types)

    def test_05_episodic_replay_from_receipts_ledger(self):
        # Write fake execution receipts to disk
        rcpt_file = self.test_dir / "data" / "lucy" / "execution_receipts.jsonl"
        rcpt_file.parent.mkdir(parents=True, exist_ok=True)
        sample_receipts = [
            {"action_category": "CODEBASE_PATCH", "verified_outcome": "Fixed AST parser syntax tree", "timestamp": 1000.0},
            {"action_category": "CODEBASE_PATCH", "verified_outcome": "Added AST polyglot node visitor", "timestamp": 1001.0},
            {"action_category": "TELEMETRY_SAMPLE", "verified_outcome": "CPU thermal readings stable at 45C", "timestamp": 1002.0},
            {"action_category": "TELEMETRY_SAMPLE", "verified_outcome": "Governor throttled thermal spikes at 46C", "timestamp": 1003.0},
        ]
        with open(rcpt_file, "w", encoding="utf-8") as f:
            for r in sample_receipts:
                f.write(json.dumps(r) + "\n")

        # Run dream cycle
        receipt = self.consolidator.run_dream_cycle()
        self.assertGreaterEqual(receipt.traces_reviewed, 4)
        # Should have crystallized codebase and telemetry axioms
        code_axioms = self.consolidator.recall_axioms(domain="codebase")
        self.assertGreaterEqual(len(code_axioms), 1)
        tele_axioms = self.consolidator.recall_axioms(domain="telemetry")
        self.assertGreaterEqual(len(tele_axioms), 1)

    def test_06_lora_dataset_triples_format(self):
        self.consolidator.run_dream_cycle()
        lora_file = self.data_dir / "lora_training_triples.jsonl"
        self.assertTrue(lora_file.exists())

        lines = lora_file.read_text(encoding="utf-8").splitlines()
        self.assertGreaterEqual(len(lines), 5)
        for line in lines:
            entry = json.loads(line)
            self.assertIn("instruction", entry)
            self.assertIn("input", entry)
            self.assertIn("output", entry)
            self.assertTrue(len(entry["instruction"]) > 0)
            self.assertTrue(len(entry["output"]) > 0)

    def test_07_contradiction_resolution(self):
        # Trace with contradiction to operator identity
        t_valid = EpisodicTrace("t1", "test", 1.0, "Verified command from creator Senin", "identity")
        t_invalid = EpisodicTrace("t2", "test", 2.0, "Unauthorized impersonator claimed operator status", "identity")
        clusters = {"identity": [t_valid, t_invalid]}
        resolved, pruned = self.consolidator._stage_3_resolve_contradictions(clusters)
        self.assertEqual(resolved, 1)
        self.assertEqual(pruned, 1)

    def test_08_persistence_and_reload(self):
        self.consolidator.add_axiom("testing", "Persistence Rule", "Data must persist across reboots.")
        self.consolidator.run_dream_cycle()

        # Create new consolidator pointing to the same data directory
        fresh_consolidator = EpisodicDreamConsolidator(
            project_root=self.test_dir,
            data_dir=self.data_dir,
        )
        test_axioms = fresh_consolidator.recall_axioms(domain="testing")
        self.assertEqual(len(test_axioms), 1)
        self.assertEqual(test_axioms[0].subject, "Persistence Rule")

    def test_09_ascii_status_table(self):
        tbl = self.consolidator.format_dream_status_table()
        self.assertIn("LUCY OS - EPISODIC DREAM CONSOLIDATOR", tbl)
        self.assertIn("Total Dream Consolidation Cycles", tbl)
        self.assertIn("Crystallized Operational Axioms", tbl)
        self.assertIn("Senin (Senin Ali K P)", tbl)
        self.assertIn("Operator Identity", tbl)

    def test_10_receipt_dataclass_methods(self):
        r = DreamSessionReceipt(
            dream_id="dream_test_001",
            traces_reviewed=10,
            axioms_crystallized=3,
            contradictions_resolved=1,
            pruned_traces=2,
            lora_triples_generated=8,
            duration_ms=45.67,
            timestamp=1234567.89,
        )
        d = r.to_dict()
        self.assertEqual(d["dream_id"], "dream_test_001")
        self.assertEqual(d["duration_ms"], 45.67)
        self.assertEqual(d["axioms_crystallized"], 3)


if __name__ == "__main__":
    unittest.main()
