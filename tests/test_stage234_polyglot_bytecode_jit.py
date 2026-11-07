r"""
tests/test_stage234_polyglot_bytecode_jit.py
Stage 234 Unit Tests: Self-Synthesizing AST Bytecode JIT Compiler & Polyglot IR
"""

import threading
import unittest

from backend.lucy_core.polyglot_bytecode_jit import (
    BasicBlock,
    CompiledFunction,
    IRInstruction,
    IROpcode,
    PolyglotBytecodeJITFabric,
    STAGE,
    STAGE_NAME,
)


class TestStage234PolyglotBytecodeJIT(unittest.TestCase):
    def setUp(self):
        self.fabric = PolyglotBytecodeJITFabric(jit_threshold=5)

    def test_01_initialization_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 234)
        self.assertEqual(s["stage_name"], STAGE_NAME)
        self.assertIn("fib_step", s["registered_functions"])
        self.assertIn("poly_eval", s["registered_functions"])
        self.assertEqual(s["jit_threshold"], 5)
        self.assertEqual(s["total_invocations"], 0)

    def test_02_interpret_polynomial_evaluation(self):
        # poly_eval(a=2, b=3, c=5, x=4) -> ((2 * 4 + 3) * 4) + 5 = (11 * 4) + 5 = 49
        res = self.fabric.execute_function("poly_eval", 2, 3, 5, 4)
        self.assertEqual(res, 49)

    def test_03_conditional_branching_ir(self):
        # fib_step(1) -> base case: returns 1
        res_base = self.fabric.execute_function("fib_step", 1)
        self.assertEqual(res_base, 1)

        # fib_step(5) -> rec case: (5-1) + (5-2) = 4 + 3 = 7
        res_rec = self.fabric.execute_function("fib_step", 5)
        self.assertEqual(res_rec, 7)

    def test_04_constant_folding_optimization(self):
        bb = BasicBlock(
            label="entry",
            instructions=[
                IRInstruction("t1", IROpcode.ADD, 10, 20),
                IRInstruction("t2", IROpcode.MUL, "t1", 2),
                IRInstruction("", IROpcode.RET, "t2"),
            ],
        )
        fn = CompiledFunction(
            func_name="fold_test",
            arg_names=[],
            entry_block="entry",
            blocks={"entry": bb},
        )
        self.fabric.functions["fold_test"] = fn
        opt_count = self.fabric.optimize_function("fold_test")
        self.assertGreaterEqual(opt_count, 1)
        # Verify result remains correct: (10 + 20) * 2 = 60
        res = self.fabric.execute_function("fold_test")
        self.assertEqual(res, 60)

    def test_05_explicit_jit_compilation(self):
        self.assertFalse(self.fabric.functions["poly_eval"].is_jit_compiled)
        self.fabric.compile_jit("poly_eval")
        self.assertTrue(self.fabric.functions["poly_eval"].is_jit_compiled)
        self.assertIsNotNone(self.fabric.functions["poly_eval"].jit_native_callable)
        # Native execution gives identical output
        res = self.fabric.execute_function("poly_eval", 1, 2, 3, 10)
        self.assertEqual(res, 123)

    def test_06_jit_auto_promotion_threshold(self):
        fn = self.fabric.functions["poly_eval"]
        self.assertFalse(fn.is_jit_compiled)
        # Execute 5 times (threshold is 5)
        for _ in range(5):
            _ = self.fabric.execute_function("poly_eval", 1, 1, 1, 2)
        # After 5th call, must be auto-promoted to JIT!
        self.assertTrue(fn.is_jit_compiled)
        self.assertGreaterEqual(self.fabric.total_jit_compilations, 1)

    def test_07_safe_division_by_zero(self):
        bb = BasicBlock(
            label="entry",
            instructions=[
                IRInstruction("res", IROpcode.DIV, 100, 0),
                IRInstruction("", IROpcode.RET, "res"),
            ],
        )
        self.fabric.functions["div_zero_test"] = CompiledFunction(
            func_name="div_zero_test",
            arg_names=[],
            entry_block="entry",
            blocks={"entry": bb},
        )
        res = self.fabric.execute_function("div_zero_test")
        # Division by zero is clamped to 1e-9 without throwing ZeroDivisionError
        self.assertGreater(res, 1e8)

    def test_08_unknown_function_error(self):
        with self.assertRaises(ValueError):
            self.fabric.execute_function("non_existent_func")
        with self.assertRaises(ValueError):
            self.fabric.optimize_function("non_existent_func")

    def test_09_cp1252_safe_ascii_table(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 234", tbl)
        self.assertIn("SELF-SYNTHESIZING AST BYTECODE JIT", tbl)
        tbl.encode("cp1252")
        self.assertTrue(tbl.startswith("+--"))

    def test_10_multithreaded_concurrency(self):
        def worker():
            for i in range(10):
                _ = self.fabric.execute_function("poly_eval", 1, 2, 3, i)
            _ = self.fabric.status()

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertGreaterEqual(self.fabric.total_invocations, 40)


if __name__ == "__main__":
    unittest.main()
