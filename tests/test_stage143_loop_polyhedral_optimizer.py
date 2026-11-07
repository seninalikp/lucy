r"""
tests/test_stage143_loop_polyhedral_optimizer.py
Unit tests for Stage 143: Loop Invariant & Polyhedral Transformation Engine.
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
from backend.lucy_core.loop_polyhedral_optimizer import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    LoopDescriptor,
    LoopPolyhedralOptimizer,
    LoopTransformReport,
)


class TestStage143LoopPolyhedralOptimizer(unittest.TestCase):
    def setUp(self):
        self.compiler = IRCompilerCore()
        self.optimizer = LoopPolyhedralOptimizer()

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 143)
        self.assertEqual(ERA, 15)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")

        st = self.optimizer.status()
        self.assertEqual(st["stage"], 143)
        self.assertEqual(st["status"], "LOOP_OPTIMIZER_ACTIVE")
        self.assertEqual(st["total_optimizations"], 0)

    def test_02_dominator_computation(self):
        # Create a simple CFG: entry -> b1 -> b2
        b_entry = BasicBlock(label="entry", successors=["b1"])
        b1 = BasicBlock(label="b1", predecessors=["entry"], successors=["b2"])
        b2 = BasicBlock(label="b2", predecessors=["b1"])
        fn = IRFunction(
            name="test_dom",
            args=[],
            blocks={"entry": b_entry, "b1": b1, "b2": b2},
            entry_block="entry",
        )
        doms = self.optimizer._compute_dominators(fn)
        self.assertIn("entry", doms["b1"])
        self.assertIn("entry", doms["b2"])
        self.assertIn("b1", doms["b2"])

    def test_03_natural_loop_detection(self):
        # Build loop: entry -> header -> body -> latch -> header
        #                                     \-> exit
        b_entry = BasicBlock(label="entry", successors=["header"])
        b_header = BasicBlock(label="header", predecessors=["entry", "latch"], successors=["body"])
        b_body = BasicBlock(label="body", predecessors=["header"], successors=["latch", "exit"])
        b_latch = BasicBlock(label="latch", predecessors=["body"], successors=["header"])
        b_exit = BasicBlock(label="exit", predecessors=["body"])

        fn = IRFunction(
            name="loop_func",
            args=[],
            blocks={"entry": b_entry, "header": b_header, "body": b_body, "latch": b_latch, "exit": b_exit},
            entry_block="entry",
        )
        loops = self.optimizer.find_natural_loops(fn)
        self.assertEqual(len(loops), 1)
        self.assertEqual(loops[0].header, "header")
        self.assertEqual(loops[0].latch, "latch")
        self.assertIn("header", loops[0].blocks)
        self.assertIn("body", loops[0].blocks)
        self.assertIn("latch", loops[0].blocks)

    def test_04_preheader_synthesis(self):
        # Build loop: entry -> header <-> latch
        b_entry = BasicBlock(label="entry", successors=["header"], instructions=[IRInstruction("JUMP", args=["header"])])
        b_header = BasicBlock(label="header", predecessors=["entry", "latch"], successors=["latch"])
        b_latch = BasicBlock(label="latch", predecessors=["header"], successors=["header"], instructions=[IRInstruction("JUMP", args=["header"])])

        fn = IRFunction(
            name="preheader_test",
            args=[],
            blocks={"entry": b_entry, "header": b_header, "latch": b_latch},
            entry_block="entry",
        )
        opt_fn, metrics = self.optimizer.optimize_function_loops(fn)
        self.assertGreaterEqual(metrics["preheaders_created"], 1)
        self.assertIn("preheader_header", opt_fn.blocks)

    def test_05_licm_invariant_hoisting(self):
        # Loop with an invariant instruction inside body: %v_inv = CONST 42
        b_entry = BasicBlock(label="entry", successors=["header"], instructions=[IRInstruction("JUMP", args=["header"])])
        b_header = BasicBlock(label="header", predecessors=["entry", "latch"], successors=["body"])
        b_body = BasicBlock(
            label="body",
            predecessors=["header"],
            successors=["latch"],
            instructions=[
                IRInstruction("CONST", dest="%v_inv", args=[42]),
                IRInstruction("JUMP", args=["latch"]),
            ],
        )
        b_latch = BasicBlock(label="latch", predecessors=["body"], successors=["header"], instructions=[IRInstruction("JUMP", args=["header"])])

        fn = IRFunction(
            name="licm_func",
            args=[],
            blocks={"entry": b_entry, "header": b_header, "body": b_body, "latch": b_latch},
            entry_block="entry",
        )
        opt_fn, metrics = self.optimizer.optimize_function_loops(fn)
        self.assertGreaterEqual(metrics["invariants_hoisted"], 1)

        # Invariant should now reside in preheader
        preheader = opt_fn.blocks.get("preheader_header")
        self.assertIsNotNone(preheader)
        hoisted_ops = [i.dest for i in preheader.instructions]
        self.assertIn("%v_inv", hoisted_ops)

        # And body should no longer contain %v_inv
        body_ops = [i.dest for i in opt_fn.blocks["body"].instructions]
        self.assertNotIn("%v_inv", body_ops)

    def test_06_loop_exits_extraction(self):
        b_entry = BasicBlock(label="entry", successors=["header"])
        b_header = BasicBlock(label="header", predecessors=["entry", "latch"], successors=["latch", "exit"])
        b_latch = BasicBlock(label="latch", predecessors=["header"], successors=["header"])
        b_exit = BasicBlock(label="exit", predecessors=["header"])

        fn = IRFunction(
            name="exit_test",
            args=[],
            blocks={"entry": b_entry, "header": b_header, "latch": b_latch, "exit": b_exit},
            entry_block="entry",
        )
        loops = self.optimizer.find_natural_loops(fn)
        self.assertEqual(len(loops), 1)
        self.assertIn("exit", loops[0].exits)

    def test_07_optimize_module_with_loops(self):
        b_entry = BasicBlock(label="entry", successors=["header"], instructions=[IRInstruction("JUMP", args=["header"])])
        b_header = BasicBlock(label="header", predecessors=["entry", "latch"], successors=["latch"])
        b_latch = BasicBlock(
            label="latch",
            predecessors=["header"],
            successors=["header"],
            instructions=[
                IRInstruction("CONST", dest="%v_loop_inv", args=[100]),
                IRInstruction("JUMP", args=["header"]),
            ],
        )
        fn = IRFunction("mod_loop", [], {"entry": b_entry, "header": b_header, "latch": b_latch}, "entry")
        mod = IRModule("test_loop_mod", {"mod_loop": fn}, {})

        opt_mod, rep = self.optimizer.optimize_module(mod)
        self.assertEqual(rep.total_loops_detected, 1)
        self.assertGreaterEqual(rep.invariants_hoisted, 1)
        self.assertGreaterEqual(rep.preheaders_created, 1)

    def test_08_hmac_provenance_signature(self):
        fn = IRFunction("empty_fn", [], {"entry": BasicBlock("entry")}, "entry")
        mod = IRModule("sig_mod", {"empty_fn": fn}, {})
        opt_mod, rep = self.optimizer.optimize_module(mod)
        self.assertTrue(rep.hmac_signature)
        self.assertEqual(len(rep.hmac_signature), 64)

    def test_09_ascii_status_and_transform_tables(self):
        fn = IRFunction("fn1", [], {"entry": BasicBlock("entry")}, "entry")
        mod = IRModule("fmt_mod", {"fn1": fn}, {})
        opt_mod, rep = self.optimizer.optimize_module(mod)

        stat_table = self.optimizer.format_loop_status_table()
        self.assertIn("+=============================================================================+", stat_table)
        self.assertIn("LUCY LOOP INVARIANT & POLYHEDRAL OPTIMIZER [STAGE 143 | ERA 15]", stat_table)
        self.assertIn("Senin Ali K P", stat_table)

        rep_table = self.optimizer.format_transform_report(rep)
        self.assertIn("LOOP OPTIMIZATION REPORT:", rep_table)
        self.assertIn("fmt_mod_loop_opt", rep_table)

    def test_10_optimize_source_convenience(self):
        code = (
            "def worker():\n"
            "    x = 10\n"
            "    return x\n"
        )
        mod, rep = self.optimizer.optimize_source(code, module_name="worker_mod")
        self.assertIn("worker", mod.functions)
        self.assertEqual(rep.module_name, "worker_mod_loop_opt")


if __name__ == "__main__":
    unittest.main()
