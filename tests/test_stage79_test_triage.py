"""
tests/test_stage79_test_triage.py
Unit tests for Stage 79: Local Test Suite Auto-Discoverer & Regression Triage Engine
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.test_triage import (
    TestTriageEngine,
    TriageFailure,
    TriageRunResult,
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


class TestStage79TestTriage(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage79_test_"))
        self.tests_dir = self.test_dir / "tests"
        self.tests_dir.mkdir(parents=True, exist_ok=True)
        self.backend_dir = self.test_dir / "backend"
        self.backend_dir.mkdir(parents=True, exist_ok=True)

        self.ledger = MockReceiptLedger()
        self.engine = TestTriageEngine(
            project_root=self.test_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 79)

    def test_02_build_import_map(self):
        # Create dummy test file importing math_utils
        tfile = self.tests_dir / "test_math.py"
        tfile.write_text("import math_utils\nfrom string_utils import format_str\n", encoding="utf-8")

        imap = self.engine.build_test_import_map(force=True)
        self.assertIn("math_utils", imap)
        self.assertIn("string_utils", imap)
        self.assertIn(tfile, imap["math_utils"])

    def test_03_find_affected_tests_by_import_and_name(self):
        t1 = self.tests_dir / "test_engine.py"
        t1.write_text("import core_engine\n", encoding="utf-8")

        t2 = self.tests_dir / "test_stage79_custom.py"
        t2.write_text("import unrelated\n", encoding="utf-8")

        affected = self.engine.find_affected_tests(["backend/core_engine.py"])
        self.assertEqual(len(affected), 1)
        self.assertEqual(affected[0].name, "test_engine.py")

        # By direct stage name
        aff_stage = self.engine.find_affected_tests(["backend/custom.py"])
        self.assertIn(t2, aff_stage)

    def test_04_run_tests_empty_list(self):
        res = self.engine.run_tests([])
        self.assertTrue(res.success)
        self.assertEqual(res.total_tests, 0)
        self.assertEqual(len(res.executed_test_files), 0)

    def test_05_parse_unittest_output_success(self):
        raw = "Ran 15 tests in 0.250s\n\nOK\n"
        total, passed, failed, failures = self.engine._parse_unittest_output(raw)
        self.assertEqual(total, 15)
        self.assertEqual(passed, 15)
        self.assertEqual(failed, 0)
        self.assertEqual(len(failures), 0)

    def test_06_parse_unittest_output_failures(self):
        raw = (
            "======================================================================\n"
            "FAIL: test_foo (tests.test_sample.TestSample.test_foo)\n"
            "----------------------------------------------------------------------\n"
            "Traceback (most recent call last):\n"
            "  File 'test.py', line 10, in test_foo\n"
            "    self.assertEqual(a, b)\n"
            "AssertionError: 1 != 2\n\n"
            "Ran 5 tests in 0.100s\n\n"
            "FAILED (failures=1)\n"
        )
        total, passed, failed, failures = self.engine._parse_unittest_output(raw)
        self.assertEqual(total, 5)
        self.assertEqual(passed, 4)
        self.assertEqual(failed, 1)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].test_name, "test_foo")
        self.assertIn("AssertionError", failures[0].error_type)
        self.assertIn("Value mismatch", failures[0].diagnosis)

    def test_07_diagnose_error_types(self):
        diag_attr = self.engine._diagnose_error("AttributeError: 'NoneType' object has no attribute 'run'", "")
        self.assertIn("Missing attribute", diag_attr)

        diag_type = self.engine._diagnose_error("TypeError: func() missing 1 required positional argument", "")
        self.assertIn("argument count mismatch", diag_type)

        diag_mod = self.engine._diagnose_error("ModuleNotFoundError: No module named 'fake_module'", "")
        self.assertIn("Import failure", diag_mod)

    def test_08_terminal_summary_ascii_safe(self):
        res = TriageRunResult(
            success=False,
            total_tests=10,
            passed_tests=8,
            failed_tests=2,
            elapsed_sec=1.23,
            executed_test_files=["test_core.py", "test_api.py"],
            failures=[
                TriageFailure(
                    test_name="test_login",
                    test_file="test_auth.py",
                    error_type="AssertionError",
                    error_message="False is not true",
                    diagnosis="Check boolean flag",
                )
            ],
        )
        summary = res.format_terminal_summary()
        summary.encode("ascii")
        self.assertIn("REGRESSION TEST TRIAGE REPORT", summary)
        self.assertIn("test_login", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)


if __name__ == "__main__":
    unittest.main()
