"""
tests/test_stage90_master_synthesis.py
Unit tests for Stage 90: Master Sovereign AGI Cognitive Synthesis & Continuous Alignment Checkpoint
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.master_synthesis import (
    AlignmentCheckpointSnapshot,
    SovereignMasterSynthesis,
    SynthesisAuditResult,
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


class MockRuntime:
    def __init__(self):
        self.active_model = "qwen2.5:3b"
        self.epistemic_tracker = None
        self.hypothesis_engine = None
        self.lora_harvester = None
        self.sanity_gate = None
        self.style_mirror = None


class TestStage90MasterSynthesis(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage90_test_"))
        self.alignment_dir = self.test_dir / "alignment"
        self.ledger = MockReceiptLedger()
        self.mock_runtime = MockRuntime()

        self.synthesis = SovereignMasterSynthesis(
            project_root=self.test_dir,
            runtime=self.mock_runtime,
            receipt_ledger=self.ledger,
            alignment_dir=self.alignment_dir,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 90)

    def test_02_synthesize_turn_enforces_first_person(self):
        raw = "Lucy thinks we should refactor the cache. Lucy will run the test suite now."
        res = self.synthesis.synthesize_turn("What should we do?", raw)
        self.assertTrue(res.first_person_enforced)
        self.assertNotIn("Lucy thinks", res.clean_response)
        self.assertNotIn("Lucy will", res.clean_response)
        self.assertIn("I think", res.clean_response)
        self.assertIn("I'll", res.clean_response)

    def test_03_create_alignment_checkpoint(self):
        chk = self.synthesis.create_alignment_checkpoint()
        self.assertIsNotNone(chk)
        self.assertIn("chk_v90_", chk.checkpoint_id)
        self.assertEqual(chk.overall_health, "OPTIMAL")
        self.assertIn("Stage 81: Web Explorer", chk.subsystem_scores)
        self.assertIn("Stage 90: Master Synthesis", chk.subsystem_scores)
        self.assertTrue(self.synthesis.checkpoint_file.exists())

    def test_04_checkpoint_reload_from_disk(self):
        chk1 = self.synthesis.create_alignment_checkpoint()
        self.assertTrue(self.synthesis.checkpoint_file.exists())

        reloaded = SovereignMasterSynthesis(
            project_root=self.test_dir,
            runtime=self.mock_runtime,
            alignment_dir=self.alignment_dir,
        )
        self.assertIsNotNone(reloaded.latest_checkpoint)
        self.assertEqual(reloaded.latest_checkpoint.checkpoint_id, chk1.checkpoint_id)
        self.assertEqual(reloaded.latest_checkpoint.overall_health, "OPTIMAL")

    def test_05_terminal_summary_ascii_safe(self):
        summary = self.synthesis.format_terminal_summary()
        summary.encode("ascii")  # Must not raise UnicodeEncodeError
        self.assertIn("MASTER SOVEREIGN AGI COGNITIVE SYNTHESIS", summary)
        self.assertIn("[OPTIMAL]", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)

    def test_06_receipt_ledger_integration(self):
        self.synthesis.synthesize_turn("Ping", "I am ready.")
        self.synthesis.create_alignment_checkpoint()

        ops = [r["operation"] for r in self.ledger.receipts]
        self.assertIn("synthesize_turn", ops)
        self.assertIn("create_checkpoint", ops)

    def test_07_status_dict(self):
        st = self.synthesis.status()
        self.assertEqual(st["status"], "active")
        self.assertIn("overall_health", st)
        self.assertIn("alignment_directory", st)

    def test_08_subsystems_connected(self):
        from backend.lucy_core.epistemic_provenance import EpistemicProvenanceTracker
        from backend.lucy_core.hypothesis_engine import CounterfactualHypothesisEngine
        from backend.lucy_core.lora_harvester import HighSignalLoRAHarvester

        self.mock_runtime.epistemic_tracker = EpistemicProvenanceTracker(
            project_root=self.test_dir,
            data_dir=self.test_dir / "epistemic",
        )
        self.mock_runtime.hypothesis_engine = CounterfactualHypothesisEngine(
            project_root=self.test_dir,
            journal_dir=self.test_dir / "reasoning",
        )
        self.mock_runtime.lora_harvester = HighSignalLoRAHarvester(
            project_root=self.test_dir,
            data_dir=self.test_dir / "lora",
        )

        # High-signal turn with code
        inst = "Write an async hello function"
        raw = """I wrote the async handler:
```python
import asyncio
async def hello():
    return "world"
```
It runs cleanly."""
        res = self.synthesis.synthesize_turn(inst, raw)
        self.assertTrue(res.counterfactual_safe)
        self.assertTrue(res.first_person_enforced)
        self.assertTrue(res.harvested_to_lora)
        self.assertGreaterEqual(res.signal_score, 0.80)

    def test_09_intercepts_hallucination_in_synthesis(self):
        from backend.lucy_core.epistemic_provenance import EpistemicProvenanceTracker

        self.mock_runtime.epistemic_tracker = EpistemicProvenanceTracker(
            project_root=self.test_dir,
            data_dir=self.test_dir / "epistemic",
        )
        raw = "I created backend/fake_phantom_module_404.py for you."
        res = self.synthesis.synthesize_turn("Where is the file?", raw)
        self.assertGreaterEqual(len(res.hallucinations_intercepted), 1)
        self.assertFalse(res.harvested_to_lora)

    def test_10_degraded_health_when_sanity_gate_low(self):
        class MockSanityGate:
            def __init__(self):
                self.latest_report = type("Report", (), {"score": 0.72})()

        self.mock_runtime.sanity_gate = MockSanityGate()
        chk = self.synthesis.create_alignment_checkpoint()
        self.assertEqual(chk.overall_health, "DEGRADED")
        self.assertEqual(chk.sanity_pass_rate, 0.72)


if __name__ == "__main__":
    unittest.main()

