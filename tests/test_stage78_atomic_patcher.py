"""
tests/test_stage78_atomic_patcher.py
Unit tests for Stage 78: Multi-File Refactor & Atomic Patch Orchestrator
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.atomic_patcher import (
    AtomicPatchOrchestrator,
    FilePatchOperation,
    PatchTransaction,
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


class TestStage78AtomicPatcher(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage78_test_"))
        self.journal_file = self.test_dir / "data" / "patch_journal.json"
        self.ledger = MockReceiptLedger()
        self.patcher = AtomicPatchOrchestrator(
            project_root=self.test_dir,
            journal_file=self.journal_file,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 78)

    def test_02_begin_transaction(self):
        tx = self.patcher.begin_transaction("Test refactor")
        self.assertTrue(tx.tx_id.startswith("tx_"))
        self.assertEqual(tx.status, "PENDING")
        self.assertEqual(self.patcher.active_tx.tx_id, tx.tx_id)

    def test_03_stage_and_commit_multi_file(self):
        # Existing file
        f1 = self.test_dir / "module_a.py"
        f1.write_text("x = 1\n", encoding="utf-8")

        # New file to create
        f2 = self.test_dir / "module_b.py"

        tx = self.patcher.begin_transaction("Update a and create b")
        self.patcher.stage_file_patch(f1, "x = 42\n")
        self.patcher.stage_file_patch(f2, "y = 99\n")

        valid, errors = self.patcher.validate_transaction(tx.tx_id)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

        ok, msg = self.patcher.commit_transaction(tx.tx_id)
        self.assertTrue(ok)
        self.assertIn("Committed transaction", msg)

        # Check disk states
        self.assertEqual(f1.read_text(encoding="utf-8"), "x = 42\n")
        self.assertEqual(f2.read_text(encoding="utf-8"), "y = 99\n")
        self.assertEqual(len(self.ledger.receipts), 1)

    def test_04_pre_validation_fails_on_syntax_error(self):
        f = self.test_dir / "bad.py"
        f.write_text("valid = True\n", encoding="utf-8")

        tx = self.patcher.begin_transaction("Bad syntax test")
        self.patcher.stage_file_patch(f, "def broken(:\n    pass\n")

        valid, errors = self.patcher.validate_transaction(tx.tx_id)
        self.assertFalse(valid)
        self.assertIn("SyntaxError", errors[0])

        ok, msg = self.patcher.commit_transaction(tx.tx_id)
        self.assertFalse(ok)
        self.assertIn("Pre-commit validation failed", msg)
        # Original content preserved
        self.assertEqual(f.read_text(encoding="utf-8"), "valid = True\n")

    def test_05_manual_rollback(self):
        f = self.test_dir / "service.py"
        f.write_text("def start(): pass\n", encoding="utf-8")

        f_new = self.test_dir / "extra.py"

        tx = self.patcher.begin_transaction("Service upgrade")
        self.patcher.stage_file_patch(f, "def start(): return True\n")
        self.patcher.stage_file_patch(f_new, "extra = 1\n")

        self.patcher.commit_transaction(tx.tx_id)
        self.assertEqual(f.read_text(encoding="utf-8"), "def start(): return True\n")
        self.assertTrue(f_new.exists())

        # Rollback
        rb_ok, rb_msg = self.patcher.rollback_transaction(tx.tx_id)
        self.assertTrue(rb_ok)
        self.assertIn("Rolled back", rb_msg)

        # Verified restoration
        self.assertEqual(f.read_text(encoding="utf-8"), "def start(): pass\n")
        self.assertFalse(f_new.exists())

    def test_06_stage_file_delete_and_rollback(self):
        target = self.test_dir / "obsolete.txt"
        target.write_text("delete me", encoding="utf-8")

        tx = self.patcher.begin_transaction("Delete obsolete")
        self.patcher.stage_file_delete(target)

        self.patcher.commit_transaction(tx.tx_id)
        self.assertFalse(target.exists())

        # Rollback restoration
        self.patcher.rollback_transaction(tx.tx_id)
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(encoding="utf-8"), "delete me")

    def test_07_journal_persistence(self):
        tx = self.patcher.begin_transaction("Persisted refactor")
        f = self.test_dir / "code.py"
        f.write_text("a = 1", encoding="utf-8")
        self.patcher.stage_file_patch(f, "a = 2")
        self.patcher.commit_transaction(tx.tx_id)

        # New instance reads journal
        new_patcher = AtomicPatchOrchestrator(
            project_root=self.test_dir,
            journal_file=self.journal_file,
        )
        self.assertIn(tx.tx_id, new_patcher.transactions)
        self.assertEqual(new_patcher.transactions[tx.tx_id].status, "COMMITTED")

    def test_08_terminal_summary_ascii_safe(self):
        tx = self.patcher.begin_transaction("Sample transaction")
        summary = self.patcher.format_terminal_summary()

        summary.encode("ascii")
        self.assertIn("ATOMIC PATCH ORCHESTRATOR", summary)
        self.assertIn(tx.tx_id, summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)


if __name__ == "__main__":
    unittest.main()
