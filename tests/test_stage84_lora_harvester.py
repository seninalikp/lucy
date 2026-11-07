"""
tests/test_stage84_lora_harvester.py
Unit tests for Stage 84: High-Signal LoRA Interaction Harvester & Preference Dataset Curator
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lora_harvester import (
    CuratedInteraction,
    DPOPreferencePair,
    HighSignalLoRAHarvester,
    STAGE,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def issue_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        self.receipts.append({
            "category": action_category,
            "operation": operation,
            "target": target,
            "outcome": verified_outcome,
        })


class TestStage84LoRAHarvester(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage84_test_"))
        self.data_dir = self.test_dir / "lora"
        self.ledger = MockReceiptLedger()

        self.harvester = HighSignalLoRAHarvester(
            project_root=self.test_dir,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
            min_signal_threshold=0.70,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 84)

    def test_02_empty_interaction_rejected(self):
        score, info = self.harvester.evaluate_interaction("", "short")
        self.assertEqual(score, 0.0)
        curated = self.harvester.harvest_turn("", "short")
        self.assertIsNone(curated)

    def test_03_third_person_penalized(self):
        bad_response = "Lucy thinks this architecture is fine. Lucy will refactor the database connector tomorrow."
        score, info = self.harvester.evaluate_interaction("How should we refactor?", bad_response)
        self.assertFalse(info["first_person_pure"])
        self.assertLess(score, 0.70)

    def test_04_first_person_rewarded(self):
        good_response = "I checked the service connection. We should decouple the message queue handler from the main runtime thread."
        score, info = self.harvester.evaluate_interaction("How should we refactor?", good_response)
        self.assertTrue(info["first_person_pure"])
        self.assertGreaterEqual(score, 0.75)

    def test_05_sycophancy_penalized(self):
        sycophantic = "Certainly! As an AI language model, I would be happy to assist you! Great question! You are completely right."
        score, info = self.harvester.evaluate_interaction("Can you help?", sycophantic)
        self.assertTrue(info["has_sycophancy"])
        self.assertLess(score, 0.65)

    def test_06_pushback_rewarded(self):
        pushback_response = "Actually, that approach creates a race condition in the cache layer. A better approach is using an atomic CAS primitive."
        score, info = self.harvester.evaluate_interaction("Let's just use global variables", pushback_response)
        self.assertTrue(info["has_pushback"])
        self.assertGreaterEqual(score, 0.80)

    def test_07_epistemic_grounding_rewarded(self):
        grounded_response = """I verified the AST syntax and executed the handler:
```python
def safe_parse(payload: str) -> dict:
    import json
    return json.loads(payload)
```
All unit assertions hold."""
        score, info = self.harvester.evaluate_interaction(
            "Write a parser",
            grounded_response,
            metadata={"ast_valid": True, "verified_receipt": True},
        )
        self.assertTrue(info["is_grounded"])
        self.assertGreaterEqual(score, 0.85)

    def test_08_harvest_turn_creates_alpaca_and_dpo(self):
        instruction = "How should we handle unhandled exceptions in the daemon?"
        response = "I recommend wrapping the loop in an isolated supervisor pattern. Let's catch specific IO errors and log full tracebacks to disk."
        curated = self.harvester.harvest_turn(
            instruction=instruction,
            response=response,
            category="system_ops",
            metadata={"pushback_enforced": False},
        )
        self.assertIsNotNone(curated)
        self.assertEqual(len(self.harvester.curated_interactions), 1)
        self.assertEqual(len(self.harvester.preference_pairs), 1)

        dpo = self.harvester.preference_pairs[0]
        self.assertEqual(dpo.prompt, instruction)
        self.assertEqual(dpo.chosen, response)
        self.assertIn("Lucy", dpo.rejected)
        self.assertIn("As an AI", dpo.rejected)

    def test_09_storage_persistence_and_reload(self):
        self.harvester.harvest_turn(
            instruction="Optimize SQL query",
            response="I added an index on user_id and timestamp. Execution dropped from 320ms to 4ms.",
            category="coding",
        )
        self.assertTrue(self.harvester.golden_file.exists())
        self.assertTrue(self.harvester.dpo_file.exists())
        self.assertTrue(self.harvester.manifest_file.exists())

        # Reload in new instance
        new_harvester = HighSignalLoRAHarvester(
            project_root=self.test_dir,
            data_dir=self.data_dir,
        )
        self.assertEqual(len(new_harvester.curated_interactions), 1)
        self.assertEqual(len(new_harvester.preference_pairs), 1)
        self.assertEqual(new_harvester.curated_interactions[0].category, "coding")

    def test_10_terminal_summary_ascii_safe(self):
        self.harvester.harvest_turn(
            instruction="Check unit test",
            response="I ran the test suite and confirmed all 10 tests passed without errors.",
            category="coding",
        )
        summary = self.harvester.format_terminal_summary()
        summary.encode("ascii")  # Must not throw UnicodeEncodeError
        self.assertIn("HIGH-SIGNAL LORA HARVESTER", summary)
        self.assertIn("Golden Exemplars", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)

    def test_11_prune_low_signal(self):
        # Manually append an interaction with score 0.60
        self.harvester.curated_interactions.append(
            CuratedInteraction(
                interaction_id="low_1",
                instruction="Hi",
                response="Hey there.",
                category="casual",
                signal_score=0.60,
                epistemic_grounding=False,
                pushback_detected=False,
                first_person_pure=True,
            )
        )
        self.assertEqual(len(self.harvester.curated_interactions), 1)
        pruned = self.harvester.prune_low_signal(threshold=0.70)
        self.assertEqual(pruned, 1)
        self.assertEqual(len(self.harvester.curated_interactions), 0)

    def test_12_receipt_ledger_integration(self):
        self.harvester.harvest_turn(
            instruction="Review code",
            response="I analyzed the commit. The connection pool timeout needs to be increased.",
            category="coding",
        )
        self.assertEqual(len(self.ledger.receipts), 1)
        self.assertEqual(self.ledger.receipts[0]["category"], "lora_harvest")
        self.assertEqual(self.ledger.receipts[0]["operation"], "curate_interaction")

    def test_13_status_dict(self):
        st = self.harvester.status()
        self.assertEqual(st["status"], "active")
        self.assertIn("golden_exemplars_count", st)
        self.assertIn("preference_pairs_count", st)
        self.assertIn("average_signal_score", st)


if __name__ == "__main__":
    unittest.main()
