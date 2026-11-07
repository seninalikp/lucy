"""
test_stage41_self_refinement.py
Unit tests for Stage 41: Self-Refinement & Regression Testing Harness.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.code_synthesis import CodeSynthesisPipeline
from backend.lucy_core.self_refinement import SelfRefinementHarness, STAGE
from backend.lucy_core.training_queue import TrainingQueue
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stage41SelfRefinementTests(unittest.TestCase):
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

        self.harness = SelfRefinementHarness(
            project_root=self.root_path,
            lucy_data=self.lucy_data,
            pipeline=self.pipeline,
            dispatcher=None,
            verifier=None,
            training_queue=self.training_queue,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_initial_status(self) -> None:
        st = self.harness.status()
        self.assertEqual(st["stage"], STAGE)
        self.assertEqual(st["self_refinement"], "active")
        self.assertEqual(st["total_refinements_attempted"], 0)
        self.assertEqual(st["resolved_count"], 0)
        self.assertEqual(st["unresolved_count"], 0)
        self.assertEqual(st["regression_testing"], "active")

    def test_02_parse_error_diagnostics(self) -> None:
        traceback_text = """Traceback (most recent call last):
  File "calculator.py", line 14, in <module>
    run_calc()
  File "calculator.py", line 8, in run_calc
    result = math.sqrt(16)
NameError: name 'math' is not defined"""

        diag = self.harness.parse_error_diagnostics(traceback_text)
        self.assertEqual(diag["error_type"], "NameError")
        self.assertIn("math", diag["message"])
        self.assertEqual(diag["line"], 8)

    def test_03_rule_healer_missing_import(self) -> None:
        broken_code = "print(sys.version)\n"
        diag = {
            "error_type": "NameError",
            "message": "name 'sys' is not defined",
            "line": 1,
        }
        healed = self.harness.rule_based_repair(broken_code, diag)
        self.assertTrue(healed.startswith("import sys\n"))
        self.assertIn("print(sys.version)", healed)

    def test_04_rule_healer_missing_colon(self) -> None:
        broken_code = "def add(a, b)\n    return a + b\n"
        diag = {
            "error_type": "SyntaxError",
            "message": "expected ':'",
            "line": 1,
        }
        healed = self.harness.rule_based_repair(broken_code, diag)
        self.assertIn("def add(a, b):", healed)

    def test_05_multi_attempt_repair_and_promotion(self) -> None:
        initial_queue_count = self.training_queue.count()

        # Code with a missing colon that will be repaired and then pass execution
        broken_code = """def main()
    print("Self-healing successful")
    return 0

if __name__ == '__main__':
    main()
"""
        initial_error = "SyntaxError at line 1: expected ':'"

        report = self.harness.refine_code(
            code=broken_code,
            error_context=initial_error,
            filename="auto_healed.py",
            max_attempts=3,
            instruction="Create an auto-healed worker",
        )

        self.assertTrue(report["resolved"])
        self.assertEqual(report["attempts_count"], 1)
        self.assertIn("def main():", report["final_code"])
        self.assertIn("[SELF_REFINED: PASS", report["badge"])
        self.assertTrue(report["lora_queue_admitted"])

        # Check queue incremented
        self.assertEqual(self.training_queue.count(), initial_queue_count + 1)

    def test_06_unresolvable_error_stops_cleanly(self) -> None:
        # Deliberate unrepairable nonsense
        nonsense_code = "@@@ #### $$$$ !!!!"
        initial_error = "SyntaxError: invalid syntax"

        report = self.harness.refine_code(
            code=nonsense_code,
            error_context=initial_error,
            filename="unfixable.py",
            max_attempts=2,
        )

        self.assertFalse(report["resolved"])
        self.assertEqual(report["attempts_count"], 2)
        self.assertIn("FAILED", report["badge"])


class Stage41RuntimeAndRouterIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runtime = LucyRuntime(project_root=Path(__file__).resolve().parent.parent)
        cls.router = CommandRouter(cls.runtime)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.runtime.graceful_shutdown("Stage 41 test suite finished")

    def test_07_runtime_refinement_status(self) -> None:
        st = self.runtime.self_refinement_status()
        self.assertEqual(st["stage"], STAGE)
        self.assertEqual(st["self_refinement"], "active")

    def test_08_runtime_regression_suite(self) -> None:
        reg_res = self.runtime.run_regression_suite()
        self.assertTrue(reg_res["regression_passed"])
        self.assertEqual(reg_res["returncode"], 0)

    def test_09_router_refinement_commands(self) -> None:
        # Refinement status command
        resp_status = self.router.handle("refinement status")
        self.assertIn("Self-Refinement Harness status:", resp_status.message)
        self.assertIn("Stage: 41 self-refinement", resp_status.message)

        # Regression suite command
        resp_reg = self.router.handle("run regression suite")
        self.assertIn("Regression Testing Result:", resp_reg.message)
        self.assertIn("passed: true", resp_reg.message.lower())

        # Refinement history command
        resp_hist = self.router.handle("refinement history")
        self.assertTrue(len(resp_hist.message) > 0)


if __name__ == "__main__":
    unittest.main()
