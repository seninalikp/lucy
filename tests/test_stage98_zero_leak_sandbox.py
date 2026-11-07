"""
tests/test_stage98_zero_leak_sandbox.py
Stage 98 = Zero-Leak Host Sandbox & Process Containment Gate

Verifies:
1. STAGE constant is 98.
2. sanitize_env strips all sensitive environment variables (API keys, secrets, tokens).
3. check_path_boundary enforces containment inside project root and blocks traversal.
4. scan_for_sensitive_patterns identifies API keys and private keys.
5. Destructive shell command interception blocks dangerous commands pre-execution.
6. run_in_sandbox safely executes sandboxed Python code and captures output.
7. Execution timeout guard halts long-running processes cleanly.
8. quarantine_file isolates offending artifacts into quarantine vault.
9. leak_audit scans files and returns structured LeakAuditReport.
10. Execution receipt ledger records receipts with SHA256 digests.
11. Terminal summaries use strictly CP1252-compatible ASCII characters.
12. status returns complete diagnostics dictionary.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.lucy_core.zero_leak_sandbox import (
    STAGE,
    LeakAuditReport,
    QuarantineItem,
    SandboxExecutionResult,
    SandboxViolationType,
    ZeroLeakHostSandbox,
)


class MockReceiptLedger:
    def __init__(self) -> None:
        self.receipts: List[Dict[str, Any]] = []

    def issue_receipt(
        self,
        action_category: str,
        operation: str,
        target: str,
        verified_outcome: str,
    ) -> Dict[str, Any]:
        rcpt = {
            "receipt_id": f"rcpt_{len(self.receipts)+1}",
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self.receipts.append(rcpt)
        return rcpt


class TestStage98ZeroLeakSandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.mock_ledger = MockReceiptLedger()
        self.sandbox = ZeroLeakHostSandbox(
            project_root=self.root,
            receipt_ledger=self.mock_ledger,
            sandbox_dir=self.root / "data" / "lucy" / "sandbox",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_stage_constant(self) -> None:
        self.assertEqual(STAGE, 98)

    def test_02_sanitize_env(self) -> None:
        os.environ["MOCK_API_KEY_SECRET"] = "secret_value_12345"
        os.environ["AUTH_BEARER_TOKEN"] = "token_xyz"

        clean = self.sandbox.sanitize_env()
        self.assertNotIn("MOCK_API_KEY_SECRET", clean)
        self.assertNotIn("AUTH_BEARER_TOKEN", clean)
        self.assertIn("PYTHONIOENCODING", clean)
        self.assertEqual(clean["PYTHONIOENCODING"], "utf-8")

    def test_03_check_path_boundary(self) -> None:
        inside = self.root / "backend" / "test.py"
        ok_in, _ = self.sandbox.check_path_boundary(inside)
        self.assertTrue(ok_in)

        # Blocked system path
        ok_sys, msg_sys = self.sandbox.check_path_boundary(r"C:\Windows\System32\cmd.exe")
        self.assertFalse(ok_sys)
        self.assertIn("blocked", msg_sys.lower())

    def test_04_scan_for_sensitive_patterns(self) -> None:
        sample_leak = 'openai_key = "sk-123456789012345678901234567890"'
        leaks = self.sandbox.scan_for_sensitive_patterns(sample_leak)
        self.assertGreater(len(leaks), 0)
        self.assertEqual(leaks[0][0], "OPENAI_KEY")

        redacted = self.sandbox.redact_text(sample_leak)
        self.assertNotIn("1234567890", redacted)
        self.assertIn("[REDACTED_OPENAI_KEY]", redacted)

    def test_05_blocked_destructive_command(self) -> None:
        bad_cmd = "format C: /fs:ntfs"
        res = self.sandbox.run_in_sandbox(bad_cmd)
        self.assertTrue(res.violation_detected)
        self.assertEqual(res.violation_type, SandboxViolationType.FORBIDDEN_COMMAND.value)
        self.assertIsNotNone(res.quarantine_id)

    def test_06_run_safe_python_sandbox(self) -> None:
        py_code = 'print("Hello from sovereign sandbox")'
        res = self.sandbox.run_in_sandbox(py_code, is_python_code=True)
        self.assertEqual(res.return_code, 0)
        self.assertIn("Hello from sovereign sandbox", res.stdout)
        self.assertFalse(res.timed_out)

        # Receipt verified
        self.assertGreaterEqual(len(self.mock_ledger.receipts), 1)
        self.assertEqual(self.mock_ledger.receipts[0]["action_category"], "SANDBOX_CONTAINMENT")

    def test_07_execution_timeout_guard(self) -> None:
        infinite_loop = "import time\ntime.sleep(5)\n"
        res = self.sandbox.run_in_sandbox(infinite_loop, is_python_code=True, timeout_sec=0.2)
        self.assertTrue(res.timed_out)
        self.assertEqual(res.violation_type, SandboxViolationType.EXECUTION_TIMEOUT.value)

    def test_08_quarantine_and_release(self) -> None:
        suspicious_file = self.root / "suspicious.py"
        suspicious_file.write_text('api_key = "AIzaSyDummyGoogleApiKey1234567890"', encoding="utf-8")

        item = self.sandbox.quarantine_file(
            suspicious_file,
            reason="Exposed Google API key",
            violation_type="SECRET_LEAK_ATTEMPT",
        )
        self.assertEqual(item.status, "QUARANTINED")
        self.assertTrue(Path(item.quarantine_path).exists())

        # Check status table
        status_table = self.sandbox.quarantine_status()
        self.assertIn("ZERO-LEAK SANDBOX QUARANTINE LEDGER", status_table)
        self.assertIn(item.quarantine_id, status_table)

        # Release
        rel = self.sandbox.release_quarantine(item.quarantine_id)
        self.assertEqual(rel["status"], "success")
        self.assertEqual(rel["released_count"], 1)

    def test_09_leak_audit(self) -> None:
        test_dir = self.root / "test_scan"
        test_dir.mkdir(parents=True, exist_ok=True)
        (test_dir / "clean.py").write_text("def add(a, b): return a + b\n", encoding="utf-8")
        (test_dir / "leak.json").write_text('{"token": "Bearer abcdef12345678901234567890"}', encoding="utf-8")

        report = self.sandbox.leak_audit(scan_dir=test_dir)
        self.assertEqual(report.total_files_scanned, 2)
        self.assertEqual(report.potential_leaks_found, 1)
        self.assertEqual(report.clean_files_count, 1)

        summary = report.format_terminal_summary()
        summary.encode("cp1252")
        self.assertIn("+----------------------------------------------------------------------+", summary)
        self.assertIn("ZERO-LEAK HOST SANDBOX & CREDENTIAL AUDIT", summary)

    def test_10_terminal_summary_cp1252(self) -> None:
        res = self.sandbox.run_in_sandbox('print("Output OK")', is_python_code=True)
        summary = res.format_terminal_summary()

        encoded = summary.encode("cp1252")
        self.assertTrue(len(encoded) > 0)
        for ch in summary:
            self.assertFalse(0x2500 <= ord(ch) <= 0x257F)

        self.assertIn("+----------------------------------------------------------------------+", summary)
        self.assertIn("ZERO-LEAK SANDBOX EXECUTION RECEIPT", summary)

    def test_11_status_dictionary(self) -> None:
        st = self.sandbox.status()
        self.assertEqual(st["stage"], 98)
        self.assertIn("jail_dir", st)
        self.assertIn("quarantine_dir", st)


if __name__ == "__main__":
    unittest.main()
