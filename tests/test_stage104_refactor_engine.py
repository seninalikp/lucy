"""
tests/test_stage104_refactor_engine.py
Stage 104: Autonomous Refactoring & Code Quality Enforcer Unit Tests
"""

import ast
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.refactor_engine import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    STAGE,
    AutonomousRefactorEngine,
    CodeSmell,
    FileQualityReport,
    RefactorProposal,
    _ComplexityVisitor,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def issue_receipt(self, action_category, operation, target, verified_outcome):
        rec = {
            "category": action_category,
            "operation": operation,
            "target": target,
            "outcome": verified_outcome,
        }
        self.receipts.append(rec)
        return rec


class TestStage104RefactorEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lucy_stage104_test_")
        self.temp_path = Path(self.temp_dir)
        self.project_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_constants_and_metadata(self):
        self.assertEqual(STAGE, 104)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")

    def test_02_cyclomatic_complexity_calculation(self):
        code_linear = "def add(a, b):\n    return a + b\n"
        tree_lin = ast.parse(code_linear)
        vis_lin = _ComplexityVisitor()
        vis_lin.visit(tree_lin)
        self.assertEqual(vis_lin.complexity, 1)

        code_branched = (
            "def complex_eval(x, y):\n"
            "    if x > 0:\n"
            "        for i in range(x):\n"
            "            if i % 2 == 0:\n"
            "                pass\n"
            "    return y\n"
        )
        tree_br = ast.parse(code_branched)
        vis_br = _ComplexityVisitor()
        vis_br.visit(tree_br)
        # 1 base + 1 if + 1 for + 1 if = 4
        self.assertEqual(vis_br.complexity, 4)

    def test_03_code_smell_detection_dead_code(self):
        engine = AutonomousRefactorEngine(
            project_root=self.temp_path,
            data_dir=self.temp_path / "refactor",
        )
        test_py = self.temp_path / "dead_code_sample.py"
        test_py.write_text(
            "def calculate_tax(amount):\n"
            "    return amount * 0.1\n"
            "    print('This line is dead code')\n"
            "    unused_val = 42\n",
            encoding="utf-8",
        )
        report = engine.analyze_file(test_py)
        smell_rules = [s.rule_id for s in report.smells]
        self.assertIn("DEAD_CODE", smell_rules)

    def test_04_code_smell_detection_deep_nesting(self):
        engine = AutonomousRefactorEngine(
            project_root=self.temp_path,
            data_dir=self.temp_path / "refactor",
        )
        test_py = self.temp_path / "nested_sample.py"
        test_py.write_text(
            "def deep_nest(a, b, c, d, e):\n"
            "    if a:\n"
            "        for x in range(b):\n"
            "            while c:\n"
            "                if d:\n"
            "                    if e:\n"
            "                        return True\n"
            "    return False\n",
            encoding="utf-8",
        )
        report = engine.analyze_file(test_py)
        smell_rules = [s.rule_id for s in report.smells]
        self.assertIn("DEEP_NESTING", smell_rules)

    def test_05_code_smell_detection_long_function(self):
        engine = AutonomousRefactorEngine(
            project_root=self.temp_path,
            data_dir=self.temp_path / "refactor",
        )
        test_py = self.temp_path / "long_fn_sample.py"
        lines = ["def very_long_function():"] + [f"    x_{i} = {i}" for i in range(90)] + ["    return x_0"]
        test_py.write_text("\n".join(lines), encoding="utf-8")

        report = engine.analyze_file(test_py)
        smell_rules = [s.rule_id for s in report.smells]
        self.assertIn("LONG_FUNCTION", smell_rules)

    def test_06_technical_debt_scoring_and_grading(self):
        engine = AutonomousRefactorEngine(
            project_root=self.temp_path,
            data_dir=self.temp_path / "refactor",
        )
        clean_py = self.temp_path / "pristine.py"
        clean_py.write_text("def pristine():\n    return 42\n", encoding="utf-8")
        clean_rep = engine.analyze_file(clean_py)
        self.assertEqual(clean_rep.tech_debt_score, 0.0)
        self.assertEqual(clean_rep.health_grade, "A")

    def test_07_suggest_refactorings(self):
        engine = AutonomousRefactorEngine(
            project_root=self.temp_path,
            data_dir=self.temp_path / "refactor",
        )
        smelly_py = self.temp_path / "smelly.py"
        smelly_py.write_text(
            "def broken_logic():\n"
            "    return 1\n"
            "    print('dead')\n",
            encoding="utf-8",
        )
        props = engine.suggest_refactorings(smelly_py)
        self.assertGreater(len(props), 0)
        p = props[0]
        self.assertIsInstance(p, RefactorProposal)
        self.assertTrue(p.proposal_id.startswith("ref_"))
        self.assertEqual(p.rule_id, "DEAD_CODE")
        self.assertEqual(p.status, "PROPOSED")

    def test_08_apply_refactor_patch_success(self):
        engine = AutonomousRefactorEngine(
            project_root=self.temp_path,
            data_dir=self.temp_path / "refactor",
        )
        target_py = self.temp_path / "patchable.py"
        target_py.write_text("def test_worker():\n    return 'OK'\n", encoding="utf-8")

        props = engine.suggest_refactorings(target_py)
        # Create synthetic proposal
        synth_prop = RefactorProposal(
            proposal_id="ref_synth_01",
            file_path="patchable.py",
            target_symbol="test_worker",
            rule_id="EXTRACT_HELPER",
            description="Add validated helper",
            suggested_patch="",
        )
        engine._proposals["ref_synth_01"] = synth_prop

        res = engine.apply_refactor_patch("ref_synth_01")
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "APPLIED")
        # Ensure file still valid syntax
        ast.parse(target_py.read_text(encoding="utf-8"))

    def test_09_apply_refactor_patch_syntax_error_rollback(self):
        engine = AutonomousRefactorEngine(
            project_root=self.temp_path,
            data_dir=self.temp_path / "refactor",
        )
        target_py = self.temp_path / "protected.py"
        orig_content = "def protected_worker():\n    return 'SAFE'\n"
        target_py.write_text(orig_content, encoding="utf-8")

        synth_prop = RefactorProposal(
            proposal_id="ref_broken_02",
            file_path="protected.py",
            target_symbol="protected_worker",
            rule_id="CORRUPT_TEST",
            description="Corrupt syntax injection test",
            suggested_patch="",
        )
        engine._proposals["ref_broken_02"] = synth_prop

        # Inject broken Python code
        res = engine.apply_refactor_patch(
            "ref_broken_02",
            replacement_code="def broken_syntax(:::\n",
            target_span=(1, 2),
        )
        self.assertFalse(res["success"])
        self.assertIn("Pre-flight syntax validation failed", res["error"])
        self.assertEqual(res["action"], "AUTOMATIC_ROLLBACK_PRESERVED")
        # Ensure file content remains 100% original
        self.assertEqual(target_py.read_text(encoding="utf-8"), orig_content)

    def test_10_receipt_ledger_integration(self):
        ledger = MockReceiptLedger()
        engine = AutonomousRefactorEngine(
            project_root=self.temp_path,
            receipt_ledger=ledger,
            data_dir=self.temp_path / "refactor",
        )
        test_py = self.temp_path / "receipt_target.py"
        test_py.write_text("def fn():\n    return 1\n    x = 2\n", encoding="utf-8")

        engine.suggest_refactorings(test_py)
        props = list(engine._proposals.keys())
        if props:
            engine.apply_refactor_patch(props[0])

        categories = [r["category"] for r in ledger.receipts]
        self.assertIn("REFACTOR_PROPOSAL", categories)
        self.assertIn("REFACTOR_APPLY", categories)

    def test_11_cp1252_tech_debt_table(self):
        engine = AutonomousRefactorEngine(
            project_root=self.project_root,
            data_dir=self.temp_path / "refactor",
        )
        table = engine.format_tech_debt_table(top_n=5)
        self.assertIn("LUCY OS - TECHNICAL DEBT & QUALITY AUDIT", table)
        self.assertIn("STAGE 104: AST CYCLOMATIC DEBT SCANNER", table)
        table.encode("cp1252")

        st = engine.status()
        self.assertEqual(st["stage"], 104)
        self.assertEqual(st["creator"], "Senin")


if __name__ == "__main__":
    unittest.main()
