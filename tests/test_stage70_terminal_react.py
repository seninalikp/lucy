"""
test_stage70_terminal_react.py
Stage 70: Autonomous Terminal ReAct Loop & Self-Healing Execution Engine Unit Tests.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.terminal_react import (
    TerminalReActEngine,
    ReActResult,
    ReActStep,
    DIAG_PYTHON_STUB,
    DIAG_MODULE_NOT_FOUND,
    DIAG_FILE_NOT_FOUND,
    STAGE as STAGE_70,
)
from backend.lucy_core.lucy_runtime import LucyRuntime


class TestStage70TerminalReAct(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        self.engine = TerminalReActEngine(project_root=self.project_root)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_successful_clean_execution(self) -> None:
        cmd = f'"{sys.executable}" -c "print(\'lucy_react_ok\')"'
        res = self.engine.execute_with_self_healing(cmd, goal="Test clean command")

        self.assertEqual(res.status, "success")
        self.assertEqual(res.attempts_count, 1)
        self.assertFalse(res.healed)
        self.assertIn("lucy_react_ok", res.stdout)
        self.assertEqual(len(res.steps), 1)

    def test_02_diagnose_python_stub_alias(self) -> None:
        fake_stderr = "Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Apps > Advanced app settings > App execution aliases."
        diag = self.engine.diagnose_failure(exit_code=1, stdout="", stderr=fake_stderr, command="python script.py")

        self.assertEqual(diag.get("error_type"), DIAG_PYTHON_STUB)
        self.assertEqual(diag.get("remedy_type"), "substitute_executable")
        self.assertEqual(diag.get("target_executable"), sys.executable)

    def test_03_diagnose_module_not_found(self) -> None:
        fake_stderr = "Traceback (most recent call last):\n  File 'test.py', line 1\nModuleNotFoundError: No module named 'backend'"
        diag = self.engine.diagnose_failure(exit_code=1, stdout="", stderr=fake_stderr, command="python test.py")

        self.assertEqual(diag.get("error_type"), DIAG_MODULE_NOT_FOUND)
        self.assertEqual(diag.get("missing_module"), "backend")
        self.assertEqual(diag.get("remedy_type"), "set_pythonpath")

    def test_04_diagnose_file_not_found(self) -> None:
        fake_stderr = "FileNotFoundError: [Errno 2] No such file or directory: 'nonexistent_file.txt'"
        diag = self.engine.diagnose_failure(exit_code=1, stdout="", stderr=fake_stderr, command="python read.py")

        self.assertEqual(diag.get("error_type"), DIAG_FILE_NOT_FOUND)
        self.assertEqual(diag.get("missing_file"), "nonexistent_file.txt")

    def test_05_self_healing_module_import_retry(self) -> None:
        # Create a mock module inside project_root
        pkg_dir = self.project_root / "my_mock_pkg"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "__init__.py").write_text("MAGIC_VAL = 42\n", encoding="utf-8")

        # Run python code without PYTHONPATH in a separate directory so it fails first
        cmd = f'"{sys.executable}" -c "import my_mock_pkg; print(\'val=\', my_mock_pkg.MAGIC_VAL)"'

        # Without PYTHONPATH set in environment, the engine will diagnose and inject project_root
        res = self.engine.execute_with_self_healing(
            cmd,
            goal="Import mock package",
            max_attempts=3,
        )

        self.assertEqual(res.status, "success")
        self.assertIn("val= 42", res.stdout)

    def test_06_self_healing_python_alias_retry(self) -> None:
        # Mock diagnosis adaptation directly
        diag = {
            "error_type": DIAG_PYTHON_STUB,
            "remedy_type": "substitute_executable",
        }
        cmd = "python -c 'print(123)'"
        adapted, _, desc = self.engine.adapt_command(cmd, diag, {})

        self.assertNotIn("python -c", adapted)
        self.assertIn(sys.executable, adapted)
        self.assertIn("Substituted active Python binary", desc)

    def test_07_attempt_budget_exhaustion(self) -> None:
        cmd = f'"{sys.executable}" -c "import sys; sys.exit(42)"'
        res = self.engine.execute_with_self_healing(cmd, goal="Intentional failure", max_attempts=2)

        self.assertEqual(res.status, "failed")
        self.assertEqual(res.attempts_count, 2)
        self.assertFalse(res.healed)

    def test_08_format_terminal_summary(self) -> None:
        steps = [
            ReActStep(attempt=1, thought="Run command", command="python fail.py", exit_code=1, stderr="ModuleNotFoundError: No module named 'foo'"),
            ReActStep(attempt=2, thought="Retry with fix", command="python pass.py", exit_code=0, stdout="Success output!"),
        ]
        res = ReActResult(
            goal="Verify formatting",
            initial_command="python fail.py",
            final_command="python pass.py",
            status="success",
            attempts_count=2,
            steps=steps,
            stdout="Success output!",
            healed=True,
            receipt_id="rcpt_test_123",
        )
        output = res.format_terminal_summary()

        self.assertIn("[Autonomous ReAct Execution: [OK: HEALED]]", output)
        self.assertIn("Total Iterations: 2", output)
        self.assertIn("Cryptographic Receipt: rcpt_test_123", output)
        self.assertIn("Success output!", output)

    def test_09_runtime_autonomous_exec_and_status(self) -> None:
        runtime = LucyRuntime()
        status = runtime.react_status()
        self.assertEqual(status.get("stage"), STAGE_70)
        self.assertEqual(status.get("react_engine"), "active")

        # Execute a clean command via runtime
        clean_cmd = f'"{sys.executable}" -c "print(\'lucy_runtime_react_ok\')"'
        exec_res = runtime.autonomous_exec(clean_cmd, goal="Test runtime exec")
        self.assertEqual(exec_res.get("status"), "success")
        self.assertEqual(exec_res.get("stage"), STAGE_70)

    def test_10_runtime_lucy_respond_react_command(self) -> None:
        runtime = LucyRuntime()
        cmd = f"/react \"{sys.executable}\" -c \"print('react_repl_test')\""
        out = runtime.lucy_respond(cmd)

        self.assertIn("[Autonomous ReAct Execution:", out)
        self.assertIn("react_repl_test", out)


if __name__ == "__main__":
    unittest.main()
