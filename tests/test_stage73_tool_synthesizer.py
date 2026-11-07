"""
tests/test_stage73_tool_synthesizer.py
Unit tests for Stage 73: Dynamic Local Tool Synthesizer & Ephemeral Sandbox
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.tool_synthesizer import (
    DynamicToolSynthesizer,
    EphemeralSandboxResult,
    SynthesizedTool,
    STAGE,
)


class DummyReceiptLedger:
    def __init__(self):
        self.receipts = []

    def issue_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        self.receipts.append({
            "category": action_category,
            "operation": operation,
            "target": target,
            "outcome": verified_outcome,
        })


class TestStage73ToolSynthesizer(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage73_test_"))
        self.sandbox_dir = self.test_dir / "sandbox"
        self.registry_file = self.test_dir / "data" / "tools.json"
        self.ledger = DummyReceiptLedger()
        self.synth = DynamicToolSynthesizer(
            sandbox_dir=self.sandbox_dir,
            registry_file=self.registry_file,
            receipt_ledger=self.ledger,
            project_root=self.test_dir,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 73)

    def test_02_syntax_validation(self):
        # Valid code
        err = self.synth.validate_code_syntax("print('hello world')")
        self.assertIsNone(err)

        # Syntax error
        err_bad = self.synth.validate_code_syntax("def broken(:")
        self.assertIsNotNone(err_bad)
        self.assertIn("Syntax error", err_bad)

        # Destructive pattern
        err_destruct = self.synth.validate_code_syntax("import shutil\nshutil.rmtree('/')")
        self.assertIsNotNone(err_destruct)
        self.assertIn("Disallowed destructive pattern", err_destruct)

    def test_03_synthesize_tool_and_persistence(self):
        code = (
            "import sys\n"
            "name = sys.argv[1] if len(sys.argv) > 1 else 'world'\n"
            "print(f'Hello {name}')\n"
        )
        tool = self.synth.synthesize_tool("greeter", code, description="Greets target", tags=["test", "utility"])
        self.assertEqual(tool.name, "greeter")
        self.assertTrue(Path(tool.script_path).exists())
        self.assertEqual(len(self.ledger.receipts), 1)
        self.assertEqual(self.ledger.receipts[0]["operation"], "synthesize_tool")

        # Verify new instance loads from registry
        new_synth = DynamicToolSynthesizer(
            sandbox_dir=self.sandbox_dir,
            registry_file=self.registry_file,
            project_root=self.test_dir,
        )
        loaded = new_synth.get_tool("greeter")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "greeter")
        self.assertIn("test", loaded.tags)

    def test_04_execute_registered_tool(self):
        code = (
            "import sys\n"
            "nums = [int(x) for x in sys.argv[1:]]\n"
            "print(sum(nums))\n"
        )
        self.synth.synthesize_tool("sum_tool", code)
        result = self.synth.execute_tool("sum_tool", args=["10", "25", "5"])

        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), "40")
        self.assertGreater(result.duration_ms, 0.0)

        # Check tool execution stats updated
        tool = self.synth.get_tool("sum_tool")
        self.assertEqual(tool.execution_count, 1)
        self.assertEqual(tool.last_status, "SUCCESS")
        self.assertIsNotNone(tool.last_executed)

    def test_05_execute_tool_failure_and_exit_code(self):
        code = (
            "import sys\n"
            "sys.stderr.write('Something blew up\\n')\n"
            "sys.exit(42)\n"
        )
        self.synth.synthesize_tool("failing_tool", code)
        res = self.synth.execute_tool("failing_tool")
        self.assertFalse(res.success)
        self.assertEqual(res.exit_code, 42)
        self.assertIn("Something blew up", res.stderr)
        self.assertEqual(self.synth.get_tool("failing_tool").last_status, "FAIL(exit=42)")

    def test_06_run_ephemeral_code_cleanup(self):
        code = "print(2 ** 10)"
        res = self.synth.run_ephemeral_code(code)
        self.assertTrue(res.success)
        self.assertEqual(res.stdout.strip(), "1024")
        # Ensure temporary files were cleaned up
        remaining = [f.name for f in self.sandbox_dir.iterdir() if f.name.startswith("_ephemeral_")]
        self.assertEqual(len(remaining), 0)

    def test_07_timeout_handling(self):
        code = "import time\ntime.sleep(2.0)\nprint('finished')"
        res = self.synth.run_ephemeral_code(code, timeout_sec=0.5)
        self.assertFalse(res.success)
        self.assertIn("timed out", res.error_message)

    def test_08_delete_tool(self):
        code = "print('temp')"
        tool = self.synth.synthesize_tool("to_delete", code)
        script_file = Path(tool.script_path)
        self.assertTrue(script_file.exists())

        deleted = self.synth.delete_tool("to_delete")
        self.assertTrue(deleted)
        self.assertIsNone(self.synth.get_tool("to_delete"))
        self.assertFalse(script_file.exists())

        # Second delete returns False
        self.assertFalse(self.synth.delete_tool("to_delete"))

    def test_09_purge_sandbox(self):
        # Create a registered tool
        self.synth.synthesize_tool("keep_me", "print('keep')")

        # Create stray scratch files
        stray1 = self.sandbox_dir / "stray1.txt"
        stray1.write_text("random")
        # Backdate stray file
        past_time = 1000000000.0  # long ago
        os.utime(stray1, (past_time, past_time))

        purge_report = self.synth.purge_sandbox(max_age_hours=1.0)
        self.assertGreaterEqual(purge_report["purged_count"], 1)
        self.assertFalse(stray1.exists())
        # Registered tool script still exists
        self.assertTrue(Path(self.synth.get_tool("keep_me").script_path).exists())

    def test_10_terminal_summary_ascii_safe(self):
        self.synth.synthesize_tool("tool_a", "print('A')", tags=["worker"])
        self.synth.synthesize_tool("tool_b", "print('B')", tags=["analyzer"])
        summary = self.synth.format_terminal_summary()

        # Must only contain standard ASCII characters
        summary.encode("ascii")
        self.assertIn("DYNAMIC LOCAL TOOL SYNTHESIZER", summary)
        self.assertIn("tool_a", summary)
        self.assertIn("tool_b", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)


if __name__ == "__main__":
    unittest.main()
