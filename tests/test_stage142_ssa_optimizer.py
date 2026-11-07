r"""
tests/test_stage142_ssa_optimizer.py
Unit tests for Stage 142: Static Single Assignment (SSA) Optimizer.
Era 15: Autonomous Self-Hosting Compiler & Multi-Tier Optimization Pipeline
"""

import unittest

from backend.lucy_core.ir_compiler_core import IRCompilerCore
from backend.lucy_core.ssa_optimizer import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    SSAOptimizationReport,
    SSAOptimizer,
)


class TestStage142SSAOptimizer(unittest.TestCase):
    def setUp(self):
        self.compiler = IRCompilerCore()
        self.optimizer = SSAOptimizer()

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 142)
        self.assertEqual(ERA, 15)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")

        st = self.optimizer.status()
        self.assertEqual(st["stage"], 142)
        self.assertEqual(st["status"], "OPTIMIZER_ACTIVE")
        self.assertEqual(st["total_modules_optimized"], 0)

    def test_02_constant_folding_addition(self):
        code = (
            "def calc():\n"
            "    x = 10 + 20\n"
            "    return x\n"
        )
        mod, report = self.optimizer.optimize_source(code, module_name="fold_add")
        self.assertGreaterEqual(report.constants_folded, 1)

        # Verify that 30 is present as a CONST in instructions
        fn = mod.functions["calc"]
        consts = [i.args[0] for b in fn.blocks.values() for i in b.instructions if i.op == "CONST"]
        self.assertIn(30, consts)

    def test_03_constant_folding_multiplication(self):
        code = (
            "def mul():\n"
            "    return 6 * 7\n"
        )
        mod, report = self.optimizer.optimize_source(code, module_name="fold_mul")
        self.assertGreaterEqual(report.constants_folded, 1)
        fn = mod.functions["mul"]
        consts = [i.args[0] for b in fn.blocks.values() for i in b.instructions if i.op == "CONST"]
        self.assertIn(42, consts)

    def test_04_dead_code_elimination(self):
        code = (
            "def dead_task():\n"
            "    unused = 999\n"
            "    return 42\n"
        )
        mod, report = self.optimizer.optimize_source(code, module_name="dce_test")
        fn = mod.functions["dead_task"]
        # Verify 999 CONST is eliminated because it is never loaded/returned
        consts = [i.args[0] for b in fn.blocks.values() for i in b.instructions if i.op == "CONST"]
        self.assertNotIn(999, consts)
        self.assertIn(42, consts)

    def test_05_common_subexpression_elimination(self):
        code = (
            "def cse_task(a, b):\n"
            "    x = a + b\n"
            "    y = a + b\n"
            "    return x + y\n"
        )
        mod, report = self.optimizer.optimize_source(code, module_name="cse_test")
        self.assertGreaterEqual(report.cse_eliminated, 1)

    def test_06_branch_simplification_constant_condition(self):
        code = (
            "def branch_test():\n"
            "    if True:\n"
            "        return 1\n"
            "    else:\n"
            "        return 2\n"
        )
        mod, report = self.optimizer.optimize_source(code, module_name="branch_opt")
        fn = mod.functions["branch_test"]
        # The dead else-branch should be pruned
        self.assertGreaterEqual(report.blocks_pruned, 1)

    def test_07_optimize_module_overall_reduction(self):
        code = (
            "def heavy():\n"
            "    a = 1 + 2\n"
            "    b = 3 + 4\n"
            "    dead = 100\n"
            "    return a + b\n"
        )
        mod, report = self.optimizer.optimize_source(code, module_name="heavy_test")
        self.assertLess(report.optimized_instructions, report.original_instructions)
        self.assertGreater(report.instructions_eliminated, 0)

    def test_08_hmac_provenance_signature(self):
        code = "def sample(): return 10 * 10\n"
        mod, report = self.optimizer.optimize_source(code, module_name="sig_test")
        self.assertTrue(report.hmac_signature)
        self.assertEqual(len(report.hmac_signature), 64)

    def test_09_ascii_status_and_report_tables(self):
        code = "def foo(): return 1 + 1\n"
        mod, report = self.optimizer.optimize_source(code, module_name="fmt_test")

        stat_table = self.optimizer.format_ssa_status_table()
        self.assertIn("+=============================================================================+", stat_table)
        self.assertIn("LUCY STATIC SINGLE ASSIGNMENT (SSA) OPTIMIZER [STAGE 142 | ERA 15]", stat_table)
        self.assertIn("Senin Ali K P", stat_table)

        rep_table = self.optimizer.format_optimization_report(report)
        self.assertIn("SSA OPTIMIZATION REPORT:", rep_table)
        self.assertIn("fmt_test_opt", rep_table)

    def test_10_optimize_source_convenience(self):
        raw_mod = self.compiler.compile_source("def add(x): return x + 0\n", module_name="raw")
        opt_mod, rep = self.optimizer.optimize_module(raw_mod)
        self.assertEqual(opt_mod.module_name, "raw_opt")
        self.assertIn("add", opt_mod.functions)


if __name__ == "__main__":
    unittest.main()
