"""
tests/test_stage89_hypothesis_engine.py
Unit tests for Stage 89: Autonomous Hypothesis Generation & Pre-Response Counterfactual Verifier
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.hypothesis_engine import (
    CognitiveHypothesis,
    CounterfactualHypothesisEngine,
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


class TestStage89HypothesisEngine(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage89_test_"))
        self.journal_dir = self.test_dir / "reasoning"
        self.ledger = MockReceiptLedger()

        self.engine = CounterfactualHypothesisEngine(
            project_root=self.test_dir,
            receipt_ledger=self.ledger,
            journal_dir=self.journal_dir,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 89)

    def test_02_formulate_syntax_hypothesis(self):
        desc = "The service crashed with SyntaxError: unexpected EOF while parsing at line 42."
        hypotheses = self.engine.formulate_hypotheses(desc)
        self.assertGreaterEqual(len(hypotheses), 1)
        h = hypotheses[0]
        self.assertIn("syntax", h.statement.lower())
        self.assertIn("ast.parse", h.falsification_condition.lower())

    def test_03_formulate_concurrency_hypothesis(self):
        desc = "The worker threads experience a deadlock when waiting on the shared message queue."
        hypotheses = self.engine.formulate_hypotheses(desc)
        self.assertGreaterEqual(len(hypotheses), 1)
        h = hypotheses[0]
        self.assertIn("concurrency", h.statement.lower())
        self.assertIn("synchronous", h.counterfactual_check.lower())

    def test_04_formulate_import_hypothesis(self):
        desc = "Script failed with ModuleNotFoundError: No module named 'fastapi'."
        hypotheses = self.engine.formulate_hypotheses(desc)
        self.assertGreaterEqual(len(hypotheses), 1)
        h = hypotheses[0]
        self.assertIn("import", h.statement.lower())
        self.assertIn("pathlib", h.counterfactual_check.lower())

    def test_05_formulate_general_hypothesis(self):
        desc = "The pricing calculation outputs negative values under unexpected conditions."
        hypotheses = self.engine.formulate_hypotheses(desc)
        self.assertGreaterEqual(len(hypotheses), 1)
        self.assertIn("boundary", hypotheses[0].counterfactual_check.lower())

    def test_06_counterfactual_verification_syntax_refuted(self):
        hyp = CognitiveHypothesis(
            hypothesis_id="test_hyp_1",
            statement="Malformed syntax in Python source.",
            confidence=0.80,
            status="FORMULATED",
        )
        clean_code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        verified = self.engine.counterfactual_verify(hyp, code_context=clean_code)
        self.assertEqual(verified.status, "REFUTED")
        self.assertLess(verified.confidence, 0.25)
        self.assertGreaterEqual(len(verified.refuting_evidence), 1)

    def test_07_counterfactual_verification_syntax_confirmed(self):
        hyp = CognitiveHypothesis(
            hypothesis_id="test_hyp_2",
            statement="Malformed syntax in Python source.",
            confidence=0.50,
            status="FORMULATED",
        )
        broken_code = "def broken(a, b:\n    return a + b\n"
        verified = self.engine.counterfactual_verify(hyp, code_context=broken_code)
        self.assertEqual(verified.status, "VERIFIED")
        self.assertGreaterEqual(verified.confidence, 0.90)
        self.assertGreaterEqual(len(verified.supporting_evidence), 1)

    def test_08_evaluate_solution_safe(self):
        proposal = """I recommend refactoring the handler with clean exception boundaries:
```python
def safe_divide(x: float, y: float) -> float:
    if y == 0:
        raise ValueError("Division by zero")
    return x / y
```
This avoids unhandled ZeroDivisionErrors."""
        report = self.engine.evaluate_solution_candidate(proposal)
        self.assertTrue(report["syntax_valid"])
        self.assertTrue(report["recommended"])
        self.assertEqual(report["counterfactual_risk"], "LOW")
        self.assertEqual(len(report["detected_risks"]), 0)

    def test_09_evaluate_solution_syntax_error(self):
        proposal = """Here is the fix:
```python
def broken_fn(x:
    return x * 2
```"""
        report = self.engine.evaluate_solution_candidate(proposal)
        self.assertFalse(report["syntax_valid"])
        self.assertFalse(report["recommended"])
        self.assertEqual(report["counterfactual_risk"], "HIGH_SYNTAX_FAILURE")

    def test_10_evaluate_solution_dangerous_patterns(self):
        dangerous_proposal = "We can wipe the temp directory using os.system('rm -rf /tmp/data')."
        report = self.engine.evaluate_solution_candidate(dangerous_proposal)
        self.assertFalse(report["recommended"])
        self.assertEqual(report["counterfactual_risk"], "CRITICAL_SECURITY_RISK")
        self.assertGreaterEqual(len(report["detected_risks"]), 1)

    def test_11_journal_persistence_and_reload(self):
        self.engine.formulate_hypotheses("Testing hypothesis persistence.")
        self.assertTrue(self.engine.journal_file.exists())

        # Reload in new instance
        reloaded = CounterfactualHypothesisEngine(
            project_root=self.test_dir,
            journal_dir=self.journal_dir,
        )
        self.assertGreaterEqual(len(reloaded.hypotheses_history), 1)

    def test_12_terminal_summary_ascii_safe(self):
        self.engine.formulate_hypotheses("Check summary formatting.")
        summary = self.engine.format_terminal_summary()
        summary.encode("ascii")  # Must not raise UnicodeEncodeError
        self.assertIn("AUTONOMOUS HYPOTHESIS & COUNTERFACTUAL REASONING", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)

    def test_13_receipt_ledger_integration(self):
        self.engine.formulate_hypotheses("Auditing receipt logging.")
        self.assertEqual(len(self.ledger.receipts), 1)
        self.assertEqual(self.ledger.receipts[0]["category"], "counterfactual_reasoning")
        self.assertEqual(self.ledger.receipts[0]["operation"], "formulate_hypotheses")


if __name__ == "__main__":
    unittest.main()
