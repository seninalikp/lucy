"""
tests/test_stage133_static_constraint_solver.py
Verification suite for Stage 133: Type-Inference & Static Constraint Solver
Era 14: Autonomous Code Evolution, Semantic Mutation & Static Synthesis
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.static_constraint_solver import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    StaticConstraintSolver,
    ConstraintSolveResult,
    InferredVariableType,
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


class TestStage133StaticConstraintSolver(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        self.data_dir = self.project_root / "data" / "lucy" / "constraints"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = MockReceiptLedger()
        self.solver = StaticConstraintSolver(
            project_root=self.project_root,
            data_dir=self.data_dir,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata(self):
        """Verifies sovereign operator identity and stage/era metadata."""
        self.assertEqual(STAGE, 133)
        self.assertEqual(ERA, 14)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        status = self.solver.status()
        self.assertEqual(status["stage"], 133)
        self.assertEqual(status["era"], 14)
        self.assertEqual(status["creator"], "Senin")
        self.assertEqual(status["creator_full_name"], "Senin Ali K P")

    def test_02_infer_primitive_types(self):
        """Verifies static type inference across primitives and collections."""
        code = """a = 42
b = 3.14
c = "lucy_kernel"
d = True
e = [1, 2, 3]
f = {"key": "val"}
"""
        res = self.solver.solve_constraints(code, "Primitives")
        self.assertTrue(res.is_satisfiable)
        types = res.inferred_types
        self.assertEqual(types["a"], "int")
        self.assertEqual(types["b"], "float")
        self.assertEqual(types["c"], "str")
        self.assertEqual(types["d"], "bool")
        self.assertEqual(types["e"], "list")
        self.assertEqual(types["f"], "dict")

    def test_03_detect_type_conflict_reassignment(self):
        """Verifies detection of conflicting variable reassignments."""
        code = """x = 100
x = "not_an_integer"
"""
        res = self.solver.solve_constraints(code, "ConflictingReassign")
        self.assertFalse(res.is_satisfiable)
        self.assertGreaterEqual(len(res.conflicts_detected), 1)
        self.assertIn("reassigned from int to str", res.conflicts_detected[0])

    def test_04_detect_invalid_binary_operation(self):
        """Verifies detection of invalid binary type combinations (e.g. int + str)."""
        code = """a = 10
b = "text"
c = a + b
"""
        res = self.solver.solve_constraints(code, "InvalidBinOp")
        self.assertFalse(res.is_satisfiable)
        self.assertTrue(any("Invalid binary operation" in c for c in res.conflicts_detected))

    def test_05_detect_unsat_dead_branches(self):
        """Verifies detection of statically unreachable/dead branches."""
        code = """if False:
    dead_code = 1
if 1 == 2:
    impossible_code = 2
"""
        res = self.solver.solve_constraints(code, "DeadBranches")
        self.assertEqual(res.unsat_branches_count, 2)

    def test_06_check_branch_sat_symbolic_bound(self):
        """Verifies symbolic evaluation of bound constraints (SAT vs UNSAT)."""
        res_unsat = self.solver.check_branch_sat("x > 10 and x < 5")
        self.assertEqual(res_unsat["status"], "UNSAT")

        res_sat = self.solver.check_branch_sat("x > 5 and x < 10")
        self.assertEqual(res_sat["status"], "SATISFIABLE")

        res_taut = self.solver.check_branch_sat("True")
        self.assertEqual(res_taut["status"], "TAUTOLOGY_SAT")

    def test_07_creator_identity_invariants(self):
        """Verifies that creator identity must be statically typed as str."""
        code = 'CREATOR_NAME = 12345\n'
        res = self.solver.solve_constraints(code, "CreatorInvariant")
        self.assertFalse(res.is_satisfiable)
        self.assertTrue(any("CREATOR_NAME must be statically typed as str" in c for c in res.conflicts_detected))

    def test_08_receipt_ledger_integration(self):
        """Verifies execution receipts for type constraint solving."""
        code = "val = 500\n"
        self.solver.solve_constraints(code, "LedgerTest")
        actions = [r["action_category"] for r in self.ledger.receipts]
        self.assertIn("TYPE_CONSTRAINTS_SOLVED", actions)

    def test_09_ascii_constraint_status_table(self):
        """Verifies CP1252-safe ASCII table formatting."""
        code = "x = 10\n"
        self.solver.solve_constraints(code, "TableTest")
        table = self.solver.format_constraint_status_table()
        self.assertIn("STATIC CONSTRAINT SOLVER", table)
        self.assertIn("TableTest", table)
        self.assertIn("Senin", table)
        # Strict CP1252 compatibility test
        table.encode("cp1252")

    def test_10_runtime_integration(self):
        """Verifies LucyRuntime binds and executes constraint solver commands."""
        from backend.lucy_core.lucy_runtime import LucyRuntime

        runtime = LucyRuntime(project_root=self.project_root)
        self.assertTrue(hasattr(runtime, "constraint_solver"))
        self.assertIsInstance(runtime.constraint_solver, StaticConstraintSolver)

        # Test CLI commands via lucy_respond
        res = runtime.lucy_respond("/constraint-status")
        self.assertIn("STATIC CONSTRAINT SOLVER", res)

        res_solve = runtime.lucy_respond("/solve-constraints a = 10; b = 20")
        self.assertIn("Constraints Solved", res_solve)

        res_sat = runtime.lucy_respond("/check-branch-sat x > 20 and x < 10")
        self.assertIn("UNSAT", res_sat)


if __name__ == "__main__":
    unittest.main()
