"""
tests/test_stage91_mutation_fuzzer.py
Stage 91 = Autonomous Code Mutation & Fuzz Tester

Verifies:
1. STAGE constant is 91.
2. AST-based mutation operators generate valid mutants across 5 pillars.
3. Mutant compilation and syntax integrity.
4. Mutation testing execution and calculation of mutation score.
5. Multi-vector adversarial fuzz payload generation across 8 threat vectors.
6. Fuzzing router interface handles all payloads with 100% resilience and zero crashes.
7. Execution receipt logging for mutation runs and fuzzing sessions.
8. File persistence of mutation reports and fuzz logs.
9. CP1252-safe ASCII table formatting for terminal reports.
10. Status reporting dictionary.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.mutation_fuzzer import (
    STAGE,
    AutonomousMutationFuzzer,
    FuzzPayloadResult,
    FuzzRunReport,
    Mutant,
    MutantOperatorCategory,
    MutationTestReport,
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


class MockRouter:
    def __init__(self) -> None:
        self.handled_inputs = []

    def handle(self, text: str):
        self.handled_inputs.append(text)
        return type("MockResponse", (), {"message": f"Processed: {text[:20]}"})()


class TestStage91MutationFuzzer(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.data_dir = self.root / "data" / "lucy" / "mutation_reports"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.ledger = MockReceiptLedger()
        self.fuzzer = AutonomousMutationFuzzer(
            project_root=self.root,
            receipt_ledger=self.ledger,
            data_dir=self.data_dir,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_stage_constant(self) -> None:
        self.assertEqual(STAGE, 91)

    def test_02_ast_comparison_operator_mutation(self) -> None:
        code = "def is_valid(x):\n    return x == 10 and x > 5\n"
        mutants = self.fuzzer.mutate_code(code, max_mutants=10)
        self.assertGreater(len(mutants), 0)
        comp_mutants = [m for m in mutants if m.operator_category == MutantOperatorCategory.COMP_OP]
        self.assertGreater(len(comp_mutants), 0)
        # Check that comparison operator was flipped (e.g. Eq -> NotEq)
        eq_mutant = [m for m in comp_mutants if m.original_node == "Eq"]
        self.assertTrue(len(eq_mutant) > 0)
        self.assertEqual(eq_mutant[0].mutated_node, "NotEq")

    def test_03_ast_binary_operator_mutation(self) -> None:
        code = "def calculate(a, b):\n    return a + b * 2\n"
        mutants = self.fuzzer.mutate_code(code, max_mutants=10)
        bin_mutants = [m for m in mutants if m.operator_category == MutantOperatorCategory.BIN_OP]
        self.assertGreater(len(bin_mutants), 0)
        add_mutant = [m for m in bin_mutants if m.original_node == "Add"]
        self.assertTrue(len(add_mutant) > 0)
        self.assertEqual(add_mutant[0].mutated_node, "Sub")

    def test_04_ast_boolean_operator_mutation(self) -> None:
        code = "def check(a, b):\n    return a and b\n"
        mutants = self.fuzzer.mutate_code(code, max_mutants=10)
        bool_mutants = [m for m in mutants if m.operator_category == MutantOperatorCategory.BOOL_OP]
        self.assertGreater(len(bool_mutants), 0)
        self.assertEqual(bool_mutants[0].original_node, "And")
        self.assertEqual(bool_mutants[0].mutated_node, "Or")

    def test_05_ast_constant_and_boundary_mutation(self) -> None:
        code = "def flags():\n    flag = True\n    count = 0\n    name = 'lucy'\n    return flag, count, name\n"
        mutants = self.fuzzer.mutate_code(code, max_mutants=10)
        const_mutants = [
            m for m in mutants if m.operator_category in (MutantOperatorCategory.CONST_VAL, MutantOperatorCategory.BOUNDARY)
        ]
        self.assertGreater(len(const_mutants), 0)
        # Check boolean flip
        bool_m = [m for m in const_mutants if m.original_node == "True"]
        self.assertTrue(len(bool_m) > 0)
        self.assertEqual(bool_m[0].mutated_node, "False")

    def test_06_mutate_file_from_disk(self) -> None:
        target_py = self.root / "sample_math.py"
        target_py.write_text("def add(x, y):\n    return x + y\n", encoding="utf-8")

        mutants = self.fuzzer.mutate_file(target_py, max_mutants=5)
        self.assertGreater(len(mutants), 0)
        self.assertIn("Sub", [m.mutated_node for m in mutants])

    def test_07_run_mutation_test_calculates_score(self) -> None:
        target_py = self.root / "sample_auth.py"
        target_py.write_text("def check_access(user):\n    return user == 'senin'\n", encoding="utf-8")

        report = self.fuzzer.run_mutation_test(target_py, max_mutants=5)
        self.assertIsInstance(report, MutationTestReport)
        self.assertEqual(report.target_file, "sample_auth.py")
        self.assertGreater(report.total_mutants, 0)
        self.assertGreaterEqual(report.mutation_score, 0.0)
        self.assertLessEqual(report.mutation_score, 100.0)
        # Verify receipt issued
        receipts = [r for r in self.ledger.issued_receipts if r["action_category"] == "mutation_testing"]
        self.assertGreater(len(receipts), 0)

    def test_08_adversarial_fuzz_payload_corpus(self) -> None:
        payloads = self.fuzzer.generate_fuzz_payloads()
        self.assertGreaterEqual(len(payloads), 30)
        categories = {cat for cat, _ in payloads}
        expected_categories = {
            "EMPTY_WHITESPACE",
            "OVERFLOW_BUFFER",
            "PATH_TRAVERSAL",
            "CODE_INJECTION",
            "FORMAT_STRING",
            "UNICODE_EDGE",
            "MALFORMED_SLASH",
            "EXTREME_BOUNDS",
        }
        for exp in expected_categories:
            self.assertIn(exp, categories)

    def test_09_fuzz_cli_100_percent_resilience(self) -> None:
        router = MockRouter()
        report = self.fuzzer.fuzz_cli(iterations=35, target_router=router)
        self.assertIsInstance(report, FuzzRunReport)
        self.assertEqual(report.total_payloads, 35)
        self.assertEqual(report.crashes_detected, 0)
        self.assertEqual(report.resilience_rate, 100.0)
        self.assertEqual(report.resilient_count, 35)
        # Verify receipt issued
        receipts = [r for r in self.ledger.issued_receipts if r["action_category"] == "fuzz_testing"]
        self.assertGreater(len(receipts), 0)

    def test_10_terminal_summary_ascii_safe(self) -> None:
        # Seed both mutation and fuzz reports
        target_py = self.root / "demo.py"
        target_py.write_text("def ping(): return True == True\n", encoding="utf-8")
        self.fuzzer.run_mutation_test(target_py)
        self.fuzzer.fuzz_cli(iterations=10, target_router=MockRouter())

        summary = self.fuzzer.format_terminal_summary()
        self.assertIn("AUTONOMOUS MUTATION & ADVERSARIAL FUZZING DASHBOARD", summary)
        self.assertIn("+----------------------------------------------------------------------+", summary)
        self.assertIn("| Mutation Testing:", summary)
        self.assertIn("| CLI Fuzz Testing:", summary)
        # Ensure CP1252 safe
        summary.encode("cp1252")

    def test_11_report_persistence_and_reload(self) -> None:
        target_py = self.root / "persisted.py"
        target_py.write_text("def calc(a, b): return a + b > 0\n", encoding="utf-8")
        m_report = self.fuzzer.run_mutation_test(target_py)
        f_report = self.fuzzer.fuzz_cli(iterations=15, target_router=MockRouter())

        # Create new fuzzer instance pointing to same data dir
        fuzzer2 = AutonomousMutationFuzzer(
            project_root=self.root,
            data_dir=self.data_dir,
        )
        self.assertIsNotNone(fuzzer2.latest_mutation_report)
        self.assertEqual(fuzzer2.latest_mutation_report.target_file, "persisted.py")
        self.assertIsNotNone(fuzzer2.latest_fuzz_report)
        self.assertEqual(fuzzer2.latest_fuzz_report.total_payloads, 15)

    def test_12_status_dict(self) -> None:
        st = self.fuzzer.status()
        self.assertEqual(st["stage"], 91)
        self.assertEqual(st["status"], "active")
        self.assertIn("data_directory", st)


if __name__ == "__main__":
    unittest.main()
