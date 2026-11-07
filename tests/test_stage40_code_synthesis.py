"""
test_stage40_code_synthesis.py
Unit tests for Stage 40: Code Synthesis & Real Terminal AST / Pytest Verification Pipeline.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.code_synthesis import CodeSynthesisPipeline, STAGE
from backend.lucy_core.training_queue import TrainingQueue
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stage40CodeSynthesisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.lucy_data = self.root_path / "data" / "lucy"
        self.training_queue = TrainingQueue(self.lucy_data)

        self.pipeline = CodeSynthesisPipeline(
            project_root=self.root_path,
            lucy_data=self.lucy_data,
            dispatcher=None,
            verifier=None,
            daemon=None,
            training_queue=self.training_queue,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_initial_status(self) -> None:
        st = self.pipeline.status()
        self.assertEqual(st["stage"], STAGE)
        self.assertEqual(st["code_synthesis"], "active")
        self.assertEqual(st["total_syntheses"], 0)
        self.assertEqual(st["promoted_count"], 0)
        self.assertEqual(st["failed_count"], 0)
        self.assertIn("ACTIVE", st["lora_queue_protection"])

    def test_02_ast_verification(self) -> None:
        # Valid code
        valid_res = self.pipeline.verify_ast("def calculate(x, y):\n    return x * y\n")
        self.assertTrue(valid_res["ast_passed"])
        self.assertTrue(valid_res["syntax_valid"])
        self.assertIn("calculate", valid_res["functions"])

        # Syntax error
        syntax_res = self.pipeline.verify_ast("def broken(x\n    return x")
        self.assertFalse(syntax_res["ast_passed"])
        self.assertFalse(syntax_res["syntax_valid"])
        self.assertEqual(syntax_res["line"], 1)

        # Dangerous eval call
        dangerous_res = self.pipeline.verify_ast("def execute(code):\n    return eval(code)\n")
        self.assertFalse(dangerous_res["ast_passed"])
        self.assertIn("eval", dangerous_res["dangerous_calls"])

    def test_03_physical_py_compile(self) -> None:
        valid_file = self.pipeline.staging_dir / "valid_test.py"
        valid_file.write_text("print('compiled ok')", encoding="utf-8")

        res = self.pipeline.verify_compile(valid_file)
        self.assertTrue(res["compile_passed"])
        self.assertIsNone(res["error"])

    def test_04_subprocess_execution(self) -> None:
        # File that runs cleanly
        clean_file = self.pipeline.staging_dir / "clean_runner.py"
        clean_file.write_text("import sys\nsys.stdout.write('clean output\\n')\nsys.exit(0)\n", encoding="utf-8")

        res_clean = self.pipeline.verify_execution(clean_file)
        self.assertTrue(res_clean["execution_passed"])
        self.assertEqual(res_clean["returncode"], 0)
        self.assertEqual(res_clean["stdout"], "clean output")

        # File that raises an exception / exits with error
        crash_file = self.pipeline.staging_dir / "crash_runner.py"
        crash_file.write_text("raise RuntimeError('Terminal crash')\n", encoding="utf-8")

        res_crash = self.pipeline.verify_execution(crash_file)
        self.assertFalse(res_crash["execution_passed"])
        self.assertNotEqual(res_crash["returncode"], 0)
        self.assertIn("RuntimeError", res_crash["stderr"])

    def test_05_full_synthesis_promotion_and_lora_queue(self) -> None:
        initial_queue_count = self.training_queue.count()

        # Provide mock api_tools returning real functional Python code
        class MockApiTools:
            def chat(self, prompt: str, system_prompt: str) -> dict:
                return {
                    "ok": True,
                    "provider": "mock_groq",
                    "text": (
                        "```python\n"
                        "import hashlib\n"
                        "import sys\n"
                        "class HashCalc:\n"
                        "    def __init__(self):\n"
                        "        pass\n"
                        "    def run(self):\n"
                        "        h = hashlib.sha256(b'test').hexdigest()\n"
                        "        return {'status': 'success', 'hash': h}\n"
                        "def main():\n"
                        "    hc = HashCalc()\n"
                        "    print(hc.run())\n"
                        "    return 0\n"
                        "if __name__ == '__main__':\n"
                        "    sys.exit(main())\n"
                        "```"
                    ),
                }

        self.pipeline.api_tools = MockApiTools()

        # Run synthesis with live model drafting
        report = self.pipeline.synthesize(
            instruction="Create a fast hash calculator",
            filename="hash_calc.py",
        )

        self.assertEqual(report["status"], "PROMOTED")
        self.assertTrue(report["promoted"])
        self.assertTrue(report["ast"]["ast_passed"])
        self.assertTrue(report["compile"]["compile_passed"])
        self.assertTrue(report["execution"]["execution_passed"])
        self.assertIn("[CODE_VERIFIED: PASS", report["badge"])
        self.assertTrue(report["lora_queue_admitted"])

        # Verify physical file was promoted to final path
        final_file = Path(report["final_path"])
        self.assertTrue(final_file.exists())

        # Verify admission into verified training queue
        new_queue_count = self.training_queue.count()
        self.assertEqual(new_queue_count, initial_queue_count + 1)

    def test_05b_fallback_stubs_never_admitted_to_lora_queue(self) -> None:
        initial_queue_count = self.training_queue.count()
        self.pipeline.api_tools = None
        self.pipeline.dispatcher = None
        self.pipeline.ollama_connector = None

        # Run synthesis in offline fallback mode
        report = self.pipeline.synthesize(
            instruction="Create an offline stub utility",
            filename="offline_stub.py",
        )

        self.assertEqual(report["status"], "PROMOTED")
        self.assertTrue(report["promoted"])
        self.assertEqual(report["source"], "deterministic_template_fallback")
        # STRICT ANTI-COLLAPSE GATE: Must never admit fallback template to training queue
        self.assertFalse(report["lora_queue_admitted"])
        self.assertEqual(self.training_queue.count(), initial_queue_count)

    def test_06_synthesis_blocked_on_broken_code(self) -> None:
        initial_queue_count = self.training_queue.count()

        broken_code = "def invalid_syntax(x\n    return x +"
        report = self.pipeline.synthesize(
            instruction="Broken code test",
            filename="broken_code.py",
            custom_code=broken_code,
        )

        self.assertEqual(report["status"], "FAILED_AST")
        self.assertFalse(report["promoted"])
        self.assertFalse(report["lora_queue_admitted"])
        self.assertIn("FAILED_AST", report["badge"])

        # Final destination does NOT contain broken file
        final_file = self.pipeline.promoted_dir / "broken_code.py"
        self.assertFalse(final_file.exists())

        # LoRA queue was protected from model collapse
        self.assertEqual(self.training_queue.count(), initial_queue_count)

    def test_07_verify_existing_file(self) -> None:
        test_file = self.pipeline.promoted_dir / "math_lib.py"
        test_file.write_text("def multiply(a, b):\n    return a * b\n\nif __name__ == '__main__':\n    print(multiply(3, 4))\n", encoding="utf-8")

        res = self.pipeline.verify_file(test_file)
        self.assertTrue(res["verified"])
        self.assertIn("[CODE_VERIFIED: PASS", res["badge"])


class Stage40RuntimeAndRouterIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = LucyRuntime(project_root=Path(__file__).resolve().parent.parent)
        cls.router = CommandRouter(cls.runtime)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime.graceful_shutdown("Stage 40 test suite finished")

    def test_08_runtime_synthesis_methods(self) -> None:
        st = self.runtime.code_synthesis_status()
        self.assertEqual(st["stage"], STAGE)
        self.assertEqual(st["code_synthesis"], "active")

        # Synthesize via runtime
        res = self.runtime.synthesize_code("Build an uptime calculator", filename="uptime_calc.py")
        self.assertEqual(res["status"], "PROMOTED")
        self.assertTrue(res["promoted"])

        # History check
        hist = self.runtime.code_synthesis_history()
        self.assertGreaterEqual(len(hist), 1)

    def test_09_router_synthesis_commands(self) -> None:
        # Synthesis status command
        resp_status = self.router.handle("synthesis status")
        self.assertIn("Code Synthesis Pipeline status:", resp_status.message)
        self.assertIn("Stage: 40 code synthesis", resp_status.message)

        # Synthesize code command
        resp_synth = self.router.handle("synthesize code create a token counter in python")
        self.assertIn("Code Synthesis:", resp_synth.message)
        self.assertIn("PROMOTED", resp_synth.message)

        # Synthesis history command
        resp_hist = self.router.handle("synthesis history")
        self.assertIn("Code Synthesis History:", resp_hist.message)


if __name__ == "__main__":
    unittest.main()
