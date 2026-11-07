"""
tests/test_stage131_ast_mutation_operator.py
Verification suite for Stage 131: Semantic Mutation Engine & AST Genetic Operator
Era 14: Autonomous Code Evolution, Semantic Mutation & Static Synthesis
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.ast_mutation_operator import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    ASTSemanticMutationOperator,
    MutantGenome,
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


class TestStage131ASTMutationOperator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        self.data_dir = self.project_root / "data" / "lucy" / "mutations"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = MockReceiptLedger()
        self.operator = ASTSemanticMutationOperator(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata(self):
        """Verifies sovereign operator identity and stage/era metadata."""
        self.assertEqual(STAGE, 131)
        self.assertEqual(ERA, 14)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        status = self.operator.status()
        self.assertEqual(status["stage"], 131)
        self.assertEqual(status["era"], 14)
        self.assertEqual(status["creator"], "Senin")
        self.assertEqual(status["creator_full_name"], "Senin Ali K P")

    def test_02_aor_arithmetic_mutation(self):
        """Verifies Arithmetic Operator Replacement (+ -> -)."""
        src = "def add(a, b):\n    return a + b\n"
        mutant = self.operator.mutate_code(src, operator_name="AOR")
        self.assertTrue(mutant.is_valid_syntax)
        self.assertIn("-", mutant.mutated_code)
        self.assertEqual(mutant.operator_applied, "AOR")

    def test_03_ror_relational_mutation(self):
        """Verifies Relational Operator Replacement (== -> !=)."""
        src = "def is_valid(x):\n    return x == 10\n"
        mutant = self.operator.mutate_code(src, operator_name="ROR")
        self.assertTrue(mutant.is_valid_syntax)
        self.assertIn("!=", mutant.mutated_code)
        self.assertEqual(mutant.operator_applied, "ROR")

    def test_04_cor_conditional_mutation(self):
        """Verifies Conditional Operator Replacement (and -> or)."""
        src = "def check(a, b):\n    return a and b\n"
        mutant = self.operator.mutate_code(src, operator_name="COR")
        self.assertTrue(mutant.is_valid_syntax)
        self.assertIn("or", mutant.mutated_code)
        self.assertEqual(mutant.operator_applied, "COR")

    def test_05_crcr_constant_mutation(self):
        """Verifies Constant Replacement (boundary shift n -> n + 1)."""
        src = "def compute():\n    return 42\n"
        mutant = self.operator.mutate_code(src, operator_name="CRCR")
        self.assertTrue(mutant.is_valid_syntax)
        self.assertIn("43", mutant.mutated_code)
        self.assertEqual(mutant.operator_applied, "CRCR")

    def test_06_safety_invariants_protection(self):
        """Verifies that creator identity strings are strictly preserved during mutation."""
        src = 'CREATOR = "Senin"\nAUTHOR = "Senin Ali K P"\ndef get_author():\n    return 100\n'
        mutant = self.operator.mutate_code(src, operator_name="CRCR")
        self.assertTrue(mutant.is_valid_syntax)
        self.assertIn("Senin", mutant.mutated_code)
        self.assertIn("Senin Ali K P", mutant.mutated_code)

    def test_07_evolve_code_multi_generation(self):
        """Verifies multi-generational evolutionary genetic code loops."""
        src = "def algorithm(x, y):\n    res = x + y\n    if res > 50 and x == 10:\n        return res * 2\n    return res\n"
        survivors = self.operator.evolve_code(src, generations=3, population_size=4)
        self.assertGreaterEqual(len(survivors), 3)
        self.assertGreaterEqual(self.operator.status()["total_generations"], 3)
        # All survivors should have valid syntax
        for s in survivors:
            self.assertTrue(s.is_valid_syntax)

    def test_08_receipt_ledger_integration(self):
        """Verifies execution receipts for AST mutation and genetic evolution."""
        src = "def sub(a, b):\n    return a - b\n"
        self.operator.mutate_code(src, "AOR")
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("AST_MUTATION_APPLIED", actions)

        self.operator.evolve_code(src, generations=1)
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("GENETIC_GENERATION_EVOLVED", actions)

    def test_09_ascii_mutation_status_table(self):
        """Verifies CP1252-safe ASCII table formatting."""
        src = "def f(x):\n    return x + 1\n"
        self.operator.mutate_code(src, "AOR")
        table = self.operator.format_mutation_status_table()
        self.assertIn("AST SEMANTIC MUTATION OPERATOR", table)
        self.assertIn("Senin", table)
        self.assertIn("AOR", table)
        # Strict CP1252 compatibility test
        table.encode("cp1252")

    def test_10_runtime_integration(self):
        """Verifies LucyRuntime binds and executes AST mutation operator commands."""
        from backend.lucy_core.lucy_runtime import LucyRuntime

        runtime = LucyRuntime(project_root=self.project_root)
        self.assertTrue(hasattr(runtime, "ast_mutator"))
        self.assertIsInstance(runtime.ast_mutator, ASTSemanticMutationOperator)

        # Test CLI commands via lucy_respond
        res = runtime.lucy_respond("/mutation-status")
        self.assertIn("AST SEMANTIC MUTATION OPERATOR", res)

        res_mut = runtime.lucy_respond("/mutate-code def test(a, b): return a + b")
        self.assertIn("Mutant Generated", res_mut)

        res_evolve = runtime.lucy_respond("/evolve-code def run(): return 10 + 20")
        self.assertIn("Evolution Complete", res_evolve)


if __name__ == "__main__":
    unittest.main()
