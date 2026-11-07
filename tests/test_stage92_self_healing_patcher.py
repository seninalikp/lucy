"""
tests/test_stage92_self_healing_patcher.py
Stage 92 = Self-Healing Runtime Patch Engine

Verifies:
1. STAGE constant is 92.
2. Diagnosis parses Python traceback extracting error type, file, and line number.
3. Diagnosis analyzes file syntax errors via AST.
4. Candidate patch synthesizer generates surgical zero-division guard.
5. Candidate patch synthesizer generates missing typing import for NameError.
6. Pre-flight sandbox verification checks AST compile validity.
7. Atomic patch application writes to disk and creates PatchRecord.
8. Rollback mechanism reverts file to exact original content.
9. Execution receipt ledger records receipts for both apply and rollback.
10. Patch ledger persistence and reload from disk.
11. CP1252-safe ASCII table formatting for diffs and ledger summaries.
12. Status reporting dictionary.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.self_healing_patcher import (
    STAGE,
    HealingDiagnosis,
    PatchRecord,
    SelfHealingPatchEngine,
)


class MockReceiptLedger:
    def __init__(self) -> None:
        self.issued_receipts = []

    def issue_receipt(
        self,
        action_category: str,
        operation: str,
        target: str,
        verified_outcome: str = "",
        details: dict | None = None,
    ) -> dict:
        receipt = {
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self.issued_receipts.append(receipt)
        return receipt


class TestStage92SelfHealingPatcher(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.patch_dir = self.root / "data" / "lucy" / "patches"
        self.patch_dir.mkdir(parents=True, exist_ok=True)

        self.ledger = MockReceiptLedger()
        self.patcher = SelfHealingPatchEngine(
            project_root=self.root,
            receipt_ledger=self.ledger,
            patch_dir=self.patch_dir,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_stage_constant(self) -> None:
        self.assertEqual(STAGE, 92)

    def test_02_diagnose_traceback_string(self) -> None:
        tb = (
            "Traceback (most recent call last):\n"
            '  File "math_calc.py", line 12, in compute_ratio\n'
            "    res = total / count\n"
            "ZeroDivisionError: division by zero\n"
        )
        diag = self.patcher.diagnose_error(tb)
        self.assertEqual(diag.error_type, "ZeroDivisionError")
        self.assertEqual(diag.error_message, "division by zero")
        self.assertEqual(diag.file_path, "math_calc.py")
        self.assertEqual(diag.line_number, 12)
        self.assertIn("guard", diag.suggested_action.lower())

    def test_03_diagnose_syntax_error_file(self) -> None:
        broken_file = self.root / "broken_syntax.py"
        broken_file.write_text("def hello()\n    return 'world'\n", encoding="utf-8")

        diag = self.patcher.diagnose_error(str(broken_file))
        self.assertEqual(diag.error_type, "SyntaxError")
        self.assertEqual(diag.line_number, 1)
        self.assertIn("syntax", diag.suggested_action.lower())

    def test_04_synthesize_zero_division_guard(self) -> None:
        calc_file = self.root / "calculator.py"
        calc_file.write_text(
            "def divide(a, b):\n"
            "    res = a / b\n"
            "    return res\n",
            encoding="utf-8",
        )

        diag = HealingDiagnosis(
            error_type="ZeroDivisionError",
            error_message="division by zero",
            file_path=str(calc_file),
            line_number=2,
            code_context="res = a / b",
        )
        patch = self.patcher.generate_candidate_patch(calc_file, diag)
        self.assertIsNotNone(patch)
        self.assertIn("if b != 0 else 0", patch.patched_content)
        self.assertIn("-    res = a / b", patch.diff)
        self.assertIn("+    res = (a / b if b != 0 else 0)", patch.diff)

    def test_05_synthesize_typing_name_error(self) -> None:
        type_file = self.root / "models.py"
        type_file.write_text(
            "from typing import List, Optional\n"
            "def get_items() -> Tuple[str, int]:\n"
            "    return ('item', 1)\n",
            encoding="utf-8",
        )

        diag = HealingDiagnosis(
            error_type="NameError",
            error_message="name 'Tuple' is not defined",
            file_path=str(type_file),
            line_number=2,
        )
        patch = self.patcher.generate_candidate_patch(type_file, diag)
        self.assertIsNotNone(patch)
        self.assertIn("Tuple", patch.patched_content)
        self.assertIn("from typing import Tuple, List, Optional", patch.patched_content)

    def test_06_preflight_verification(self) -> None:
        patch = PatchRecord(
            patch_id="patch_test_01",
            target_file="test.py",
            error_signature="SyntaxError",
            diff="",
            status="VERIFIED",
            original_content="x = 1\n",
            patched_content="x = (1 + 2)\n",
        )
        ok, msg = self.patcher.verify_candidate_patch(patch)
        self.assertTrue(ok)
        self.assertTrue(patch.verified)

        # Invalid syntax fails verification
        bad_patch = PatchRecord(
            patch_id="patch_bad_01",
            target_file="bad.py",
            error_signature="SyntaxError",
            diff="",
            status="VERIFIED",
            original_content="x = 1\n",
            patched_content="x = ((1 +\n",
        )
        bad_ok, bad_msg = self.patcher.verify_candidate_patch(bad_patch)
        self.assertFalse(bad_ok)
        self.assertIn("compilation failed", bad_msg)

    def test_07_atomic_apply_and_receipt(self) -> None:
        target_file = self.root / "service.py"
        target_file.write_text("def run():\n    return 42\n", encoding="utf-8")

        new_code = "def run():\n    return 100\n"
        rec = self.patcher.apply_patch(target_file, new_code, error_signature="Logic upgrade")

        self.assertEqual(rec.status, "APPLIED")
        self.assertEqual(target_file.read_text(encoding="utf-8"), new_code)
        self.assertIn(rec.patch_id, self.patcher.patches)

        # Check receipt
        receipts = [r for r in self.ledger.issued_receipts if r["operation"] == "apply_patch"]
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["target"], rec.patch_id)

    def test_08_rollback_patch(self) -> None:
        target_file = self.root / "workflow.py"
        original_code = "def step_one():\n    return 'original'\n"
        target_file.write_text(original_code, encoding="utf-8")

        patched_code = "def step_one():\n    return 'healed'\n"
        rec = self.patcher.apply_patch(target_file, patched_code, error_signature="Fix step")
        self.assertEqual(target_file.read_text(encoding="utf-8"), patched_code)

        # Rollback
        success, msg = self.patcher.rollback_patch(rec.patch_id)
        self.assertTrue(success)
        self.assertEqual(target_file.read_text(encoding="utf-8"), original_code)
        self.assertEqual(self.patcher.patches[rec.patch_id].status, "ROLLED_BACK")

        # Check rollback receipt
        rb_receipts = [r for r in self.ledger.issued_receipts if r["operation"] == "rollback_patch"]
        self.assertEqual(len(rb_receipts), 1)

    def test_09_ledger_persistence_and_reload(self) -> None:
        target_file = self.root / "db.py"
        target_file.write_text("db = 1\n", encoding="utf-8")
        rec = self.patcher.apply_patch(target_file, "db = 2\n", error_signature="Fix DB")

        # Reload into new instance
        patcher2 = SelfHealingPatchEngine(
            project_root=self.root,
            patch_dir=self.patch_dir,
        )
        self.assertIn(rec.patch_id, patcher2.patches)
        self.assertEqual(patcher2.patches[rec.patch_id].status, "APPLIED")
        self.assertEqual(patcher2.patches[rec.patch_id].target_file, "db.py")

    def test_10_terminal_summaries_ascii_safe(self) -> None:
        target_file = self.root / "api.py"
        target_file.write_text("x = 1\n", encoding="utf-8")
        rec = self.patcher.apply_patch(target_file, "x = 2\n", error_signature="API fix")

        diff_summary = self.patcher.get_patch_diff(rec.patch_id)
        self.assertIn("PATCH DIFF:", diff_summary)
        self.assertIn("+----------------------------------------------------------------------+", diff_summary)
        diff_summary.encode("cp1252")

        ledger_summary = self.patcher.format_ledger_summary()
        self.assertIn("AUTONOMOUS SELF-HEALING RUNTIME PATCH LEDGER", ledger_summary)
        self.assertIn("+----------------------------------------------------------------------+", ledger_summary)
        ledger_summary.encode("cp1252")

    def test_11_status_dict(self) -> None:
        st = self.patcher.status()
        self.assertEqual(st["stage"], 92)
        self.assertEqual(st["status"], "active")
        self.assertIn("patch_directory", st)
        self.assertIn("total_patches", st)


if __name__ == "__main__":
    unittest.main()
