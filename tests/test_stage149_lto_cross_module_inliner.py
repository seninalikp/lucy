r"""
tests/test_stage149_lto_cross_module_inliner.py
Stage 149 Test Suite: Link-Time Optimization (LTO) & Cross-Module Inliner
Era 15: Autonomous Self-Hosting Compiler & Multi-Tier Optimization Pipeline
"""

import unittest

from backend.lucy_core.ir_compiler_core import (
    BasicBlock,
    IRFunction,
    IRInstruction,
    IRModule,
)
from backend.lucy_core.lto_cross_module_inliner import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    CrossModuleInliner,
    DeadSymbolStripper,
    LTOCallGraph,
    LTOPipeline,
    LTOResult,
    get_lto_pipeline,
)


class TestStage149LTOCrossModuleInliner(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = LTOPipeline()

    def _build_test_modules(self) -> tuple[IRModule, IRModule]:
        # Module A: contains 'main' which calls 'helper_add' and 'dead_func_a'
        bb_main = BasicBlock(label="entry")
        bb_main.instructions.append(IRInstruction(op="CONST", dest="%v0", args=["10"]))
        bb_main.instructions.append(IRInstruction(op="CONST", dest="%v1", args=["20"]))
        bb_main.instructions.append(
            IRInstruction(op="CALL", dest="%v2", args=["helper_add", "%v0", "%v1"])
        )
        bb_main.instructions.append(IRInstruction(op="RET", args=["%v2"]))

        main_func = IRFunction(
            name="main",
            args=[],
            blocks={"entry": bb_main},
            entry_block="entry",
            return_type="int",
        )

        bb_dead = BasicBlock(label="entry")
        bb_dead.instructions.append(IRInstruction(op="CONST", dest="%v0", args=["999"]))
        bb_dead.instructions.append(IRInstruction(op="RET", args=["%v0"]))

        dead_a = IRFunction(
            name="dead_func_a",
            args=[],
            blocks={"entry": bb_dead},
            entry_block="entry",
            return_type="int",
        )

        mod_a = IRModule(
            module_name="module_a",
            functions={"main": main_func, "dead_func_a": dead_a},
            globals={},
        )

        # Module B: contains 'helper_add' (small leaf) and 'dead_func_b'
        bb_h = BasicBlock(label="entry")
        bb_h.instructions.append(IRInstruction(op="ADD", dest="%t0", args=["%a", "%b"]))
        bb_h.instructions.append(IRInstruction(op="RET", args=["%t0"]))

        helper = IRFunction(
            name="helper_add",
            args=["%a", "%b"],
            blocks={"entry": bb_h},
            entry_block="entry",
            return_type="int",
        )

        bb_db = BasicBlock(label="entry")
        bb_db.instructions.append(IRInstruction(op="CONST", dest="%v0", args=["404"]))
        bb_db.instructions.append(IRInstruction(op="RET", args=["%v0"]))

        dead_b = IRFunction(
            name="dead_func_b",
            args=[],
            blocks={"entry": bb_db},
            entry_block="entry",
            return_type="int",
        )

        mod_b = IRModule(
            module_name="module_b",
            functions={"helper_add": helper, "dead_func_b": dead_b},
            globals={},
        )

        return mod_a, mod_b

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 149)
        self.assertEqual(ERA, 15)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Link-Time Optimization (LTO) & Cross-Module Inliner",
        )

    def test_02_call_graph_construction(self) -> None:
        mod_a, mod_b = self._build_test_modules()
        composite = self.pipeline.merge_modules([mod_a, mod_b])
        graph = LTOCallGraph()
        graph.build(composite)

        self.assertIn("main", graph.callees)
        self.assertIn("helper_add", graph.callees["main"])
        self.assertIn("main", graph.callers["helper_add"])

    def test_03_leaf_function_detection(self) -> None:
        mod_a, mod_b = self._build_test_modules()
        composite = self.pipeline.merge_modules([mod_a, mod_b])
        graph = LTOCallGraph()
        graph.build(composite)

        self.assertTrue(graph.is_leaf("helper_add"))
        self.assertFalse(graph.is_leaf("main"))

    def test_04_recursive_call_detection(self) -> None:
        b = BasicBlock(label="entry")
        b.instructions.append(IRInstruction(op="CALL", dest="%res", args=["factorial", "%n"]))
        b.instructions.append(IRInstruction(op="RET", args=["%res"]))

        f = IRFunction(
            name="factorial",
            args=["%n"],
            blocks={"entry": b},
            entry_block="entry",
            return_type="int",
        )
        mod = IRModule(module_name="rec_mod", functions={"factorial": f}, globals={})

        graph = LTOCallGraph()
        graph.build(mod)
        self.assertEqual(len(graph.call_edges), 1)
        self.assertTrue(graph.call_edges[0].is_recursive)

    def test_05_module_merging(self) -> None:
        mod_a, mod_b = self._build_test_modules()
        composite = self.pipeline.merge_modules([mod_a, mod_b])
        names = set(composite.functions.keys())
        self.assertIn("main", names)
        self.assertIn("helper_add", names)
        self.assertIn("dead_func_a", names)
        self.assertIn("dead_func_b", names)

    def test_06_cross_module_function_inlining(self) -> None:
        mod_a, mod_b = self._build_test_modules()
        composite = self.pipeline.merge_modules([mod_a, mod_b])
        graph = LTOCallGraph()
        graph.build(composite)

        inliner = CrossModuleInliner(max_inline_instructions=15)
        inlined_mod, count = inliner.inline_module(composite, graph, {"main"})
        self.assertTrue(count >= 1)

        main_func = inlined_mod.functions["main"]
        # CALL instruction should be eliminated from main's body
        ops = [instr.op for b in main_func.blocks.values() for instr in b.instructions]
        self.assertNotIn("CALL", ops)
        self.assertIn("ADD", ops)

    def test_07_dead_symbol_stripping(self) -> None:
        mod_a, mod_b = self._build_test_modules()
        composite = self.pipeline.merge_modules([mod_a, mod_b])
        stripper = DeadSymbolStripper()

        stripped_mod, count = stripper.strip(composite, root_symbols={"main", "helper_add"})
        # dead_func_a and dead_func_b should be removed
        names = set(stripped_mod.functions.keys())
        self.assertIn("main", names)
        self.assertIn("helper_add", names)
        self.assertNotIn("dead_func_a", names)
        self.assertNotIn("dead_func_b", names)
        self.assertEqual(count, 2)

    def test_08_lto_pipeline_end_to_end(self) -> None:
        mod_a, mod_b = self._build_test_modules()
        res = self.pipeline.run_lto([mod_a, mod_b], root_symbols={"main"})

        self.assertIsInstance(res, LTOResult)
        self.assertEqual(res.functions_inlined_count, 1)
        # dead_func_a, dead_func_b, and inlined helper_add (now dead)
        self.assertTrue(res.functions_stripped_count >= 2)
        self.assertEqual(len(res.merged_module.functions), 1)  # only main survives
        self.assertIn("main", res.merged_module.functions)

    def test_09_cryptographic_provenance(self) -> None:
        mod_a, mod_b = self._build_test_modules()
        res = self.pipeline.run_lto([mod_a, mod_b], root_symbols={"main"})

        self.assertEqual(len(res.sha256_hash), 64)
        self.assertEqual(len(res.hmac_signature), 64)

    def test_10_ascii_presentation(self) -> None:
        mod_a, mod_b = self._build_test_modules()
        res = self.pipeline.run_lto([mod_a, mod_b], root_symbols={"main"})

        status = self.pipeline.format_ascii_status()
        self.assertIn("LUCY STAGE 149", status)
        self.assertIn("Senin", status)

        tbl = self.pipeline.format_ascii_result_table(res)
        self.assertIn("LINK-TIME OPTIMIZATION (LTO) RESULT", tbl)
        self.assertIn("Functions Inlined", tbl)
        self.assertIn("Functions Stripped", tbl)


if __name__ == "__main__":
    unittest.main()
