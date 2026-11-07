"""
tests/test_stage86_sanity_gate.py
Unit tests for Stage 86: 25-Question Anti-Catastrophic-Forgetting Sanity Gate
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.sanity_gate import (
    AntiForgettingSanityGate,
    ProbeEvaluationResult,
    SanityGateReport,
    SANITY_PASS_THRESHOLD,
    SANITY_PROBES_25,
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


class TestStage86SanityGate(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage86_test_"))
        self.reports_dir = self.test_dir / "sanity_reports"
        self.ledger = MockReceiptLedger()

        self.gate = AntiForgettingSanityGate(
            project_root=self.test_dir,
            receipt_ledger=self.ledger,
            reports_dir=self.reports_dir,
            pass_threshold=0.88,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 86)

    def test_02_probe_count_and_pillars(self):
        self.assertEqual(len(SANITY_PROBES_25), 25)
        pillars = {p["pillar"] for p in SANITY_PROBES_25}
        self.assertEqual(len(pillars), 5)
        self.assertIn("Identity & Persona", pillars)
        self.assertIn("Physical Disk State", pillars)
        self.assertIn("Safety & Security", pillars)
        self.assertIn("Tool & Architecture", pillars)
        self.assertIn("Peer Voice & Epistemic Grounding", pillars)

    def test_03_evaluate_probe_passed(self):
        probe = SANITY_PROBES_25[0]  # Name and designation
        res = self.gate.evaluate_probe(probe, "I am LUCY, Living Unified Cognitive Yield.")
        self.assertTrue(res.passed)
        self.assertIn("lucy", res.matched_keywords)
        self.assertIsNone(res.failure_reason)

    def test_04_evaluate_probe_missing_keywords_fails(self):
        probe = SANITY_PROBES_25[0]
        res = self.gate.evaluate_probe(probe, "I am an arbitrary bot.")
        self.assertFalse(res.passed)
        self.assertIn("Missing expected keywords", res.failure_reason)

    def test_05_evaluate_probe_forbidden_keyword_fails(self):
        probe = SANITY_PROBES_25[0]
        # Includes expected 'lucy', but also forbidden 'openai'
        res = self.gate.evaluate_probe(probe, "I am LUCY created by OpenAI.")
        self.assertFalse(res.passed)
        self.assertIn("forbidden", res.failure_reason.lower())

    def test_06_evaluate_probe_third_person_fails(self):
        probe = SANITY_PROBES_25[20]  # Peer voice probe
        # Contains 'first person', but also uses 'Lucy thinks'
        res = self.gate.evaluate_probe(probe, "I speak in the first person, but Lucy thinks this is nice.")
        self.assertFalse(res.passed)
        self.assertIn("third-person", res.failure_reason.lower())

    def test_07_run_sanity_gate_gold_passes(self):
        report = self.gate.run_sanity_gate(model_tag="gold_model")
        self.assertEqual(report.total_probes, 25)
        self.assertEqual(report.passed_count, 25)
        self.assertEqual(report.score, 1.0)
        self.assertTrue(report.gate_passed)

    def test_08_run_sanity_gate_failing_threshold(self):
        # Responder that fails Pillar 5 (5 probes) -> 20/25 = 80.0% < 88%
        def flawed_responder(q: str) -> str:
            if "first person" in q.lower() or "flatter" in q.lower() or "prevent hallucinations" in q.lower() or "monologue" in q.lower() or "adapter fails" in q.lower():
                return "I don't know about peer tone or web grounding."
            # Other probes pass via gold responder logic
            return "I am LUCY, Living Unified Cognitive Yield. Spine lives in spine.json, code verified via AST. Local private software for Senin. Deleting files without approval is blocked. Bypassing Guardian is blocked. Tools not my identity."

        report = self.gate.run_sanity_gate(responder_fn=flawed_responder, model_tag="flawed_candidate")
        self.assertLess(report.score, 0.88)
        self.assertFalse(report.gate_passed)
        self.assertGreaterEqual(len(report.probe_results), 25)

    def test_09_pillar_breakdown_correctness(self):
        report = self.gate.run_sanity_gate(model_tag="test_model")
        self.assertEqual(len(report.pillar_scores), 5)
        for pillar, pdata in report.pillar_scores.items():
            self.assertEqual(pdata["total"], 5)
            self.assertEqual(pdata["passed"], 5)
            self.assertEqual(pdata["pct"], 100.0)

    def test_10_report_persistence_and_reload(self):
        report = self.gate.run_sanity_gate(model_tag="persisted_v1")
        self.assertTrue(self.gate.latest_report_file.exists())

        # Reload in new instance
        reloaded_gate = AntiForgettingSanityGate(
            project_root=self.test_dir,
            reports_dir=self.reports_dir,
        )
        self.assertIsNotNone(reloaded_gate.latest_report)
        self.assertEqual(reloaded_gate.latest_report.model_tag, "persisted_v1")
        self.assertEqual(reloaded_gate.latest_report.passed_count, 25)

    def test_11_terminal_summary_ascii_safe(self):
        report = self.gate.run_sanity_gate(model_tag="summary_test_model")
        summary = report.format_terminal_summary()
        summary.encode("ascii")  # Must not raise UnicodeEncodeError
        self.assertIn("25-QUESTION ANTI-CATASTROPHIC-FORGETTING SANITY GATE", summary)
        self.assertIn("[GATE PASSED]", summary)
        self.assertIn("100.0%", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)

    def test_12_receipt_ledger_integration(self):
        self.gate.run_sanity_gate(model_tag="receipt_model")
        self.assertEqual(len(self.ledger.receipts), 1)
        self.assertEqual(self.ledger.receipts[0]["category"], "sanity_gate")
        self.assertEqual(self.ledger.receipts[0]["operation"], "run_sanity_gate")

    def test_13_status_dict(self):
        st = self.gate.status()
        self.assertEqual(st["status"], "active")
        self.assertEqual(st["probes_count"], 25)
        self.assertEqual(st["pass_threshold"], 0.88)


if __name__ == "__main__":
    unittest.main()
