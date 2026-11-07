"""
test_stage61_fact_state_verifier.py
Automated verification tests for Stage 61: Sentence-Scoped Fact & Runtime State Verifier.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.fact_state_verifier import FactStateVerifier, STAGE
from backend.lucy_core.lucy_runtime import LucyRuntime


class TestStage61FactStateVerifier(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "promoted_tools").mkdir(parents=True, exist_ok=True)
        self.verifier = FactStateVerifier(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_sentence_scoped_no_cross_paragraph_false_positive(self) -> None:
        # Paragraph 1 has affirmative verb with no file
        # Paragraph 2 mentions a file casually without creation claim
        text = (
            "I have successfully saved your profile.\n\n"
            "You can always view settings.json or README.md if you want to inspect configuration.\n\n"
            "Let me know if you need anything else."
        )
        claimed = self.verifier.extract_claimed_paths(text)
        self.assertEqual(claimed, [])

        report = self.verifier.verify_claim(text)
        self.assertTrue(report["verified"])
        self.assertFalse(report["hallucination_detected"])
        self.assertEqual(len(report["missing_paths"]), 0)

    def test_02_sentence_scoped_extracts_actual_affirmative_claim(self) -> None:
        text = (
            "Here is your daily update.\n\n"
            "I created the file backend/new_sensor.py on disk.\n\n"
            "You can review it anytime."
        )
        claimed = self.verifier.extract_claimed_paths(text)
        self.assertEqual(claimed, ["backend/new_sensor.py"])

        # File does not exist yet -> correctly flagged as missing
        report = self.verifier.verify_claim(text)
        self.assertFalse(report["verified"])
        self.assertTrue(report["hallucination_detected"])
        self.assertIn("backend/new_sensor.py", report["missing_paths"])

    def test_03_promoted_tools_and_staging_resolution(self) -> None:
        # Create physical file in promoted_tools
        tool_file = self.root / "promoted_tools" / "custom_tool.py"
        tool_file.write_text("print('hello')", encoding="utf-8")

        claim = "I have promoted custom_tool.py for your project."
        report = self.verifier.verify_claim(claim)
        self.assertTrue(report["verified"])
        self.assertFalse(report["hallucination_detected"])
        self.assertIn("custom_tool.py", report["verified_paths"])

    def test_04_verify_runtime_state_claims_accurate(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        try:
            actual_count = len(runtime.project_summary().get("open_tasks", []))
            claim = f"You have {actual_count} open tasks remaining."
            res = self.verifier.verify_runtime_state_claims(claim, runtime=runtime)
            self.assertTrue(res["verified"])
            self.assertFalse(res["hallucination_detected"])
            self.assertEqual(len(res["discrepancies"]), 0)
        finally:
            runtime.graceful_shutdown()

    def test_05_verify_runtime_state_claims_hallucination_caught(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        try:
            # Claiming 5 open tasks when there are 0
            claim = "You have 5 open tasks remaining."
            res = self.verifier.verify_runtime_state_claims(claim, runtime=runtime)
            self.assertFalse(res["verified"])
            self.assertTrue(res["hallucination_detected"])
            self.assertGreaterEqual(len(res["discrepancies"]), 1)
            self.assertIn("Claimed 5 open tasks", res["discrepancies"][0])
        finally:
            runtime.graceful_shutdown()


if __name__ == "__main__":
    unittest.main()
