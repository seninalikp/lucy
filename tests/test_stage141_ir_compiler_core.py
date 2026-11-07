r"""
tests/test_stage141_ir_compiler_core.py
Unit tests for Stage 141: Intermediate Representation (IR) Compiler Core.
Era 15: Autonomous Self-Hosting Compiler & Multi-Tier Optimization Pipeline
"""

import shutil
import tempfile
import unittest

from backend.lucy_core.ir_compiler_core import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    BasicBlock,
    IRCompilerCore,
    IRFunction,
    IRInstruction,
    IRModule,
)


class TestStage141IRCompilerCore(unittest.TestCase):
    def setUp(self):
        self.compiler = IRCompilerCore()

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 141)
        self.assertEqual(ERA, 15)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")

        st = self.compiler.status()
        self.assertEqual(st["stage"], 141)
        self.assertEqual(st["era"], 15)
        self.assertEqual(st["status"], "COMPILER_ACTIVE")
        self.assertEqual(st["total_compilations"], 0)

    def test_02_lower_simple_arithmetic_function(self):
        code = (
            "def add(a, b):\n"
            "    c = a + b\n"
            "    return c\n"
        )
        mod = self.compiler.compile_source(code, module_name="math_mod")
        self.assertIn("add", mod.functions)

        fn = mod.functions["add"]
        self.assertEqual(fn.name, "add")
        self.assertEqual(fn.args, ["a", "b"])
        self.assertIn("entry", fn.blocks)

        entry_bb = fn.blocks["entry"]
        ops = [i.op for i in entry_bb.instructions]
        self.assertIn("ALLOC", ops)
        self.assertIn("BINOP", ops)
        self.assertIn("STORE", ops)
        self.assertIn("RET", ops)

    def test_03_lower_conditional_branches(self):
        code = (
            "def check_num(x):\n"
            "    if x:\n"
            "        y = 1\n"
            "    else:\n"
            "        y = 2\n"
            "    return y\n"
        )
        mod = self.compiler.compile_source(code, module_name="branch_mod")
        fn = mod.functions["check_num"]

        # Should have entry, then_0, else_1, and merge_2 blocks
        self.assertGreaterEqual(len(fn.blocks), 3)
        entry_bb = fn.blocks["entry"]
        self.assertTrue(any(i.op == "BRANCH" for i in entry_bb.instructions))
        self.assertGreater(len(entry_bb.successors), 0)

    def test_04_lower_function_call(self):
        code = (
            "def run():\n"
            "    return greet('Senin')\n"
        )
        mod = self.compiler.compile_source(code, module_name="call_mod")
        fn = mod.functions["run"]
        calls = [i for i in fn.blocks["entry"].instructions if i.op == "CALL"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].args[0], "greet")

    def test_05_module_text_disassembly(self):
        code = (
            "def foo(x):\n"
            "    return x * 2\n"
        )
        mod = self.compiler.compile_source(code, module_name="disasm_mod")
        txt = mod.to_text()
        self.assertIn("; ModuleID = 'disasm_mod'", txt)
        self.assertIn("define @foo(x)", txt)
        self.assertIn("BINOP MULT", txt)
        self.assertIn("RET", txt)

    def test_06_verify_module_valid(self):
        code = (
            "def compute(a, b):\n"
            "    return (a * b) + 10\n"
        )
        mod = self.compiler.compile_source(code, module_name="valid_mod")
        valid, errors = self.compiler.verify_module(mod)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_07_verify_module_invalid_target_detected(self):
        code = "def sample(): return 1\n"
        mod = self.compiler.compile_source(code, module_name="invalid_mod")

        # Invalidate by inserting jump to non-existent block
        mod.functions["sample"].blocks["entry"].instructions.insert(
            0, IRInstruction("JUMP", args=["non_existent_bb"])
        )
        valid, errors = self.compiler.verify_module(mod)
        self.assertFalse(valid)
        self.assertTrue(any("non_existent_bb" in err for err in errors))

    def test_08_top_level_module_wrap(self):
        code = "x = 42\ny = x + 10\n"
        mod = self.compiler.compile_source(code, module_name="script_mod")
        self.assertIn("__module_init__", mod.functions)
        self.assertIn("x", mod.globals)

    def test_09_serialization_and_deserialization(self):
        code = "def mul(a, b): return a * b\n"
        mod = self.compiler.compile_source(code, module_name="serde_mod")
        mod_dict = mod.to_dict()
        reconstructed = IRModule.from_dict(mod_dict)
        self.assertEqual(reconstructed.module_name, "serde_mod")
        self.assertIn("mul", reconstructed.functions)
        self.assertEqual(reconstructed.functions["mul"].args, ["a", "b"])

    def test_10_ascii_status_table_formatting(self):
        self.compiler.compile_source("def t1(): return 1\n", module_name="m1")
        self.compiler.compile_source("def t2(): return 2\n", module_name="m2")

        table = self.compiler.format_ir_status_table()
        self.assertIn("+=============================================================================+", table)
        self.assertIn("LUCY INTERMEDIATE REPRESENTATION (IR) COMPILER [STAGE 141 | ERA 15]", table)
        self.assertIn("m1", table)
        self.assertIn("m2", table)
        self.assertIn("Senin Ali K P", table)


if __name__ == "__main__":
    unittest.main()
