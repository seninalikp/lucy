"""
tests/test_stage77_code_reviewer.py
Unit tests for Stage 77: Autonomous Git Branch & Code Review Companion
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.code_reviewer import (
    AutonomousCodeReviewer,
    CodeReviewReport,
    ReviewFinding,
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


class TestStage77CodeReviewer(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage77_test_"))
        self.ledger = MockReceiptLedger()
        self.reviewer = AutonomousCodeReviewer(
            project_root=self.test_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 77)

    def test_02_clean_diff_review(self):
        report = self.reviewer.review_diff("")
        self.assertEqual(report.lines_added, 0)
        self.assertEqual(report.lines_removed, 0)
        self.assertEqual(report.risk_level, "LOW")
        self.assertEqual(len(report.findings), 0)

    def test_03_detect_secret_leak(self):
        diff = (
            "diff --git a/backend/config.py b/backend/config.py\n"
            "--- a/backend/config.py\n"
            "+++ b/backend/config.py\n"
            "@@ -10,1 +10,2 @@\n"
            "+api_key = 'sk_live_9876543210abcdef'\n"
        )
        report = self.reviewer.review_diff(diff)
        self.assertEqual(report.risk_level, "HIGH")
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].severity, "HIGH")
        self.assertIn("secret or token", report.findings[0].message)

    def test_04_detect_debug_leak(self):
        diff = (
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -5,1 +5,2 @@\n"
            "+print('DEBUG: checking value')\n"
        )
        report = self.reviewer.review_diff(diff)
        self.assertEqual(report.risk_level, "LOW")
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].severity, "LOW")
        self.assertIn("Leftover debug", report.findings[0].message)

    def test_05_detect_removed_public_symbol(self):
        diff = (
            "diff --git a/backend/api.py b/backend/api.py\n"
            "--- a/backend/api.py\n"
            "+++ b/backend/api.py\n"
            "@@ -20,2 +20,1 @@\n"
            "-def authenticate_client(token):\n"
            "-    pass\n"
        )
        report = self.reviewer.review_diff(diff)
        self.assertEqual(report.risk_level, "LOW")  # 1 medium finding keeps risk low
        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].severity, "MEDIUM")
        self.assertIn("Removed public symbol", report.findings[0].message)

    def test_06_commit_message_generation(self):
        msg_feat = self.reviewer.generate_commit_message(["backend/auth.py"], 50, 5, [])
        self.assertTrue(msg_feat.startswith("feat(auth):"))

        msg_test = self.reviewer.generate_commit_message(["tests/test_auth.py"], 30, 0, [])
        self.assertTrue(msg_test.startswith("test(auth):"))

        msg_fix = self.reviewer.generate_commit_message(["backend/bugfix.py"], 10, 10, [])
        self.assertTrue(msg_fix.startswith("fix(bugfix):"))

    def test_07_receipt_issuance(self):
        diff = (
            "diff --git a/main.py b/main.py\n"
            "--- a/main.py\n"
            "+++ b/main.py\n"
            "@@ -1,1 +1,2 @@\n"
            "+x = 10\n"
        )
        self.reviewer.review_diff(diff)
        self.assertEqual(len(self.ledger.receipts), 1)
        self.assertEqual(self.ledger.receipts[0]["operation"], "review_diff")

    def test_08_terminal_summary_ascii_safe(self):
        diff = (
            "diff --git a/main.py b/main.py\n"
            "--- a/main.py\n"
            "+++ b/main.py\n"
            "@@ -1,1 +1,2 @@\n"
            "+print('DEBUG: test')\n"
        )
        report = self.reviewer.review_diff(diff)
        summary = report.format_terminal_summary()

        summary.encode("ascii")
        self.assertIn("AUTONOMOUS LOCAL CODE REVIEW REPORT", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)

    def test_09_changelog_fallback_safety(self):
        # Even with nonexistent git repo, generate_changelog should not throw
        cl = self.reviewer.generate_changelog()
        cl.encode("ascii")
        self.assertIn("SEMANTIC CHANGELOG", cl)

    def test_10_multiple_files_metrics(self):
        diff = (
            "diff --git a/f1.py b/f1.py\n"
            "--- a/f1.py\n"
            "+++ b/f1.py\n"
            "@@ -1,1 +1,3 @@\n"
            "+a = 1\n"
            "+b = 2\n"
            "diff --git a/f2.py b/f2.py\n"
            "--- a/f2.py\n"
            "+++ b/f2.py\n"
            "@@ -1,2 +1,1 @@\n"
            "-c = 3\n"
        )
        report = self.reviewer.review_diff(diff)
        self.assertEqual(len(report.files_reviewed), 2)
        self.assertEqual(report.lines_added, 2)
        self.assertEqual(report.lines_removed, 1)


if __name__ == "__main__":
    unittest.main()
