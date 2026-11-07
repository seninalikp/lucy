"""
tests/test_stage132_test_oracle_synthesizer.py
Verification suite for Stage 132: Autonomous Test Oracle Synthesizer
Era 14: Autonomous Code Evolution, Semantic Mutation & Static Synthesis
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.test_oracle_synthesizer import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    AutonomousTestOracleSynthesizer,
    SynthesizedTestSuiteRecord,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def record_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        self.receipts.append({
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        })


class TestStage132TestOracleSynthesizer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        self.data_dir = self.project_root / "data" / "lucy" / "oracles"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = MockReceiptLedger()
        self.synthesizer = AutonomousTestOracleSynthesizer(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata(self):
        """Verifies sovereign operator identity and stage/era metadata."""
        self.assertEqual(STAGE, 132)
        self.assertEqual(ERA, 14)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        status = self.synthesizer.status()
        self.assertEqual(status["stage"], 132)
        self.assertEqual(status["era"], 14)
        self.assertEqual(status["creator"], "Senin")
        self.assertEqual(status["creator_full_name"], "Senin Ali K P")

    def test_02_synthesize_standalone_function_tests(self):
        """Verifies test oracle generation for standalone top-level functions."""
        code = "def calculate_tax(income: float, rate_pct: float) -> float:\n    return income * rate_pct\n"
        suite = self.synthesizer.synthesize_test_suite(code, target_name="TaxCalculator")
        self.assertTrue(suite.is_compilable)
        self.assertGreaterEqual(suite.assertions_count, 1)
        self.assertIn("TestTaxcalculatorSynthesizedOracle", suite.test_code)
        self.assertIn("calculate_tax", suite.test_code)
        self.assertIn("Senin", suite.test_code)

    def test_03_synthesize_class_method_tests(self):
        """Verifies test oracle generation for class definitions and methods."""
        code = """class VectorIndex:
    def __init__(self):
        self.items = []

    def insert(self, item_id: str, vector_data: list) -> bool:
        return True

    def query(self, query_val: str, limit_count: int) -> list:
        return []
"""
        suite = self.synthesizer.synthesize_test_suite(code, target_name="VectorIndexEngine")
        self.assertTrue(suite.is_compilable)
        self.assertGreaterEqual(suite.assertions_count, 2)
        self.assertIn("TestVectorindexengineSynthesizedOracle", suite.test_code)
        self.assertIn("VectorIndex_insert_invocation", suite.test_code)
        self.assertIn("VectorIndex_query_invocation", suite.test_code)

    def test_04_synthesize_empty_module_fallback(self):
        """Verifies fallback test synthesis for code with no top-level functions."""
        code = "GLOBAL_CONST = 100\nMESSAGE = 'hello'\n"
        suite = self.synthesizer.synthesize_test_suite(code, target_name="Constants")
        self.assertTrue(suite.is_compilable)
        self.assertGreaterEqual(suite.assertions_count, 1)
        self.assertIn("test_01_module_load", suite.test_code)

    def test_05_validate_test_suite_compilation(self):
        """Verifies validation check evaluates compilation cleanly."""
        code = "def ping() -> str:\n    return 'pong'\n"
        suite = self.synthesizer.synthesize_test_suite(code, target_name="PingModule")
        val_result = self.synthesizer.validate_test_suite(suite.suite_id)
        self.assertEqual(val_result["status"], "success")
        self.assertTrue(val_result["is_compilable"])

    def test_06_sample_argument_heuristic_types(self):
        """Verifies heuristic sample argument resolution."""
        synth = self.synthesizer
        self.assertEqual(synth._generate_sample_arg("user_id"), "1")
        self.assertEqual(synth._generate_sample_arg("batch_size"), "1")
        self.assertEqual(synth._generate_sample_arg("discount_rate"), "0.5")
        self.assertEqual(synth._generate_sample_arg("is_active"), "True")
        self.assertEqual(synth._generate_sample_arg("items_list"), "[]")
        self.assertEqual(synth._generate_sample_arg("config_dict"), "{}")

    def test_07_persistence_manifest(self):
        """Verifies test suites persist to disk and reload across instances."""
        code = "def echo(x):\n    return x\n"
        suite = self.synthesizer.synthesize_test_suite(code, target_name="Echoer")

        synth2 = AutonomousTestOracleSynthesizer(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )
        self.assertIn(suite.suite_id, synth2._test_suites)
        self.assertEqual(synth2.status()["total_synthesized"], 1)

    def test_08_receipt_ledger_integration(self):
        """Verifies execution receipts emitted for oracle synthesis and validation."""
        code = "def square(n):\n    return n * n\n"
        suite = self.synthesizer.synthesize_test_suite(code, target_name="Math")
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("TEST_ORACLE_SYNTHESIZED", actions)

        self.synthesizer.validate_test_suite(suite.suite_id)
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("TEST_SUITE_VALIDATED", actions)

    def test_09_ascii_oracle_status_table(self):
        """Verifies CP1252-safe ASCII table formatting."""
        code = "def f(): return True\n"
        self.synthesizer.synthesize_test_suite(code, target_name="Sample")
        table = self.synthesizer.format_oracle_status_table()
        self.assertIn("AUTONOMOUS TEST ORACLE SYNTHESIZER", table)
        self.assertIn("Sample", table)
        self.assertIn("Senin", table)
        # Strict CP1252 compatibility test
        table.encode("cp1252")

    def test_10_runtime_integration(self):
        """Verifies LucyRuntime binds and executes test oracle synthesizer commands."""
        from backend.lucy_core.lucy_runtime import LucyRuntime

        runtime = LucyRuntime(project_root=self.project_root)
        self.assertTrue(hasattr(runtime, "test_oracle"))
        self.assertIsInstance(runtime.test_oracle, AutonomousTestOracleSynthesizer)

        # Test CLI commands via lucy_respond
        res = runtime.lucy_respond("/test-oracle-status")
        self.assertIn("AUTONOMOUS TEST ORACLE SYNTHESIZER", res)

        res_synth = runtime.lucy_respond("/synthesize-tests def add(a, b): return a + b")
        self.assertIn("Test Suite Synthesized", res_synth)

        res_val = runtime.lucy_respond("/validate-test-suite oracle_")
        self.assertTrue(len(res_val) > 0)


if __name__ == "__main__":
    unittest.main()
