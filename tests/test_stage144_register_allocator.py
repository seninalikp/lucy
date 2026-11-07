r"""
tests/test_stage144_register_allocator.py
Unit tests for Stage 144: Register Allocation & Spill Cost Graph Colorer.
Era 15: Autonomous Self-Hosting Compiler & Multi-Tier Optimization Pipeline
"""

import unittest

from backend.lucy_core.ir_compiler_core import (
    BasicBlock,
    IRCompilerCore,
    IRFunction,
    IRInstruction,
    IRModule,
)
from backend.lucy_core.register_allocator import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    AllocationResult,
    LiveRange,
    RegisterAllocator,
)


class TestStage144RegisterAllocator(unittest.TestCase):
    def setUp(self):
        self.compiler = IRCompilerCore()
        self.allocator = RegisterAllocator(default_k=8)

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 144)
        self.assertEqual(ERA, 15)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")

        st = self.allocator.status()
        self.assertEqual(st["stage"], 144)
        self.assertEqual(st["status"], "ALLOCATOR_ACTIVE")
        self.assertEqual(st["total_allocations"], 0)

    def test_02_liveness_analysis_computation(self):
        # %v0 = CONST 10
        # %v1 = CONST 20
        # %v2 = BINOP ADD, %v0, %v1
        # RET %v2
        bb = BasicBlock(
            label="entry",
            instructions=[
                IRInstruction("CONST", dest="%v0", args=[10]),
                IRInstruction("CONST", dest="%v1", args=[20]),
                IRInstruction("BINOP", dest="%v2", args=["ADD", "%v0", "%v1"]),
                IRInstruction("RET", args=["%v2"]),
            ],
        )
        fn = IRFunction(name="test_live", args=[], blocks={"entry": bb}, entry_block="entry")
        ranges = self.allocator.compute_liveness(fn)

        self.assertIn("%v0", ranges)
        self.assertIn("%v1", ranges)
        self.assertIn("%v2", ranges)
        # %v0 is defined at 0, used at 2
        self.assertEqual(ranges["v0" if "v0" in ranges else "%v0"].start_idx, 0)
        self.assertEqual(ranges["v0" if "v0" in ranges else "%v0"].end_idx, 2)

    def test_03_interference_graph_construction(self):
        bb = BasicBlock(
            label="entry",
            instructions=[
                IRInstruction("CONST", dest="%v0", args=[10]),
                IRInstruction("CONST", dest="%v1", args=[20]),
                IRInstruction("BINOP", dest="%v2", args=["ADD", "%v0", "%v1"]),
                IRInstruction("RET", args=["%v2"]),
            ],
        )
        fn = IRFunction(name="test_interfere", args=[], blocks={"entry": bb}, entry_block="entry")
        adj, weights, ranges = self.allocator.build_interference_graph(fn)

        # %v0 and %v1 are live simultaneously across instruction 1 -> edge between them
        self.assertIn("%v1", adj["%v0"])
        self.assertIn("%v0", adj["%v1"])

    def test_04_chaitin_briggs_coloring_sufficient_registers(self):
        code = (
            "def calc(a, b):\n"
            "    return a + b\n"
        )
        mod = self.compiler.compile_source(code, module_name="test_color")
        fn = mod.functions["calc"]
        res = self.allocator.allocate_registers(fn, k=8)

        self.assertEqual(len(res.spilled_vregs), 0)
        self.assertGreater(res.vregs_allocated, 0)
        self.assertLessEqual(res.physical_regs_used, 8)
        # All assigned colors start with %r
        for vreg, col in res.reg_assignment.items():
            self.assertTrue(col.startswith("%r"))

    def test_05_register_reuse_disjoint_ranges(self):
        # Two disjoint live ranges can share the same physical register
        bb = BasicBlock(
            label="entry",
            instructions=[
                IRInstruction("CONST", dest="%v0", args=[1]),
                IRInstruction("RET", args=["%v0"]),
                IRInstruction("CONST", dest="%v1", args=[2]),
                IRInstruction("RET", args=["%v1"]),
            ],
        )
        fn = IRFunction(name="disjoint_fn", args=[], blocks={"entry": bb}, entry_block="entry")
        res = self.allocator.allocate_registers(fn, k=1)
        # With K = 1, disjoint variables can both get %r0
        self.assertEqual(len(res.spilled_vregs), 0)
        self.assertEqual(res.reg_assignment["%v0"], "%r0")
        self.assertEqual(res.reg_assignment["%v1"], "%r0")

    def test_06_spill_candidate_selection_under_pressure(self):
        # %v0 and %v1 interfere, but K = 1 -> exactly 1 must spill
        bb = BasicBlock(
            label="entry",
            instructions=[
                IRInstruction("CONST", dest="%v0", args=[10]),
                IRInstruction("CONST", dest="%v1", args=[20]),
                IRInstruction("BINOP", dest="%v2", args=["ADD", "%v0", "%v1"]),
                IRInstruction("RET", args=["%v2"]),
            ],
        )
        fn = IRFunction(name="spill_test", args=[], blocks={"entry": bb}, entry_block="entry")
        res = self.allocator.allocate_registers(fn, k=1)

        self.assertGreaterEqual(len(res.spilled_vregs), 1)
        self.assertIn(res.spilled_vregs[0], res.spill_slots)

    def test_07_spill_slots_assignment(self):
        bb = BasicBlock(
            label="entry",
            instructions=[
                IRInstruction("CONST", dest="%v0", args=[10]),
                IRInstruction("CONST", dest="%v1", args=[20]),
                IRInstruction("BINOP", dest="%v2", args=["ADD", "%v0", "%v1"]),
                IRInstruction("RET", args=["%v2"]),
            ],
        )
        fn = IRFunction(name="slot_test", args=[], blocks={"entry": bb}, entry_block="entry")
        res = self.allocator.allocate_registers(fn, k=1)
        for v in res.spilled_vregs:
            self.assertGreaterEqual(res.spill_slots[v], 0)

    def test_08_hmac_provenance_signature(self):
        fn = IRFunction(name="sig_fn", args=[], blocks={"entry": BasicBlock("entry")}, entry_block="entry")
        res = self.allocator.allocate_registers(fn, k=4)
        self.assertTrue(res.hmac_signature)
        self.assertEqual(len(res.hmac_signature), 64)

    def test_09_ascii_status_and_allocation_tables(self):
        code = "def foo(): return 42\n"
        results = self.allocator.allocate_source(code, module_name="fmt_test")
        res = results["foo"]

        stat_table = self.allocator.format_reg_status_table()
        self.assertIn("+=============================================================================+", stat_table)
        self.assertIn("LUCY REGISTER ALLOCATOR & GRAPH COLORER [STAGE 144 | ERA 15]", stat_table)
        self.assertIn("Senin Ali K P", stat_table)

        alloc_table = self.allocator.format_allocation_table(res)
        self.assertIn("REGISTER ALLOCATION: @foo", alloc_table)
        self.assertIn("Target Registers (K): 8", alloc_table)

    def test_10_allocate_source_convenience(self):
        code = (
            "def f1(x): return x + 1\n"
            "def f2(y): return y * 2\n"
        )
        res = self.allocator.allocate_source(code, module_name="two_funcs", k=4)
        self.assertIn("f1", res)
        self.assertIn("f2", res)
        self.assertEqual(res["f1"].k_registers, 4)


if __name__ == "__main__":
    unittest.main()
