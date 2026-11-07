r"""
tests/test_stage146_jit_hotpath_tracer.py
Unit tests for Stage 146: Just-In-Time (JIT) Hotpath Tracer & Tiered Execution Engine.
Era 15: Autonomous Self-Hosting Compiler & Multi-Tier Optimization Pipeline
"""

import unittest

from backend.lucy_core.ir_compiler_core import IRCompilerCore
from backend.lucy_core.jit_hotpath_tracer import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    JITExecutionResult,
    JITHotpathTracer,
    JITTrace,
)


class TestStage146JITHotpathTracer(unittest.TestCase):
    def setUp(self):
        self.compiler = IRCompilerCore()
        self.tracer = JITHotpathTracer(hot_threshold=5)

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 146)
        self.assertEqual(ERA, 15)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")

        st = self.tracer.status()
        self.assertEqual(st["stage"], 146)
        self.assertEqual(st["status"], "JIT_ENGINE_ACTIVE")
        self.assertEqual(st["hot_threshold"], 5)
        self.assertEqual(st["cached_traces"], 0)

    def test_02_tier0_interpreter_execution(self):
        code = (
            "def add(a, b):\n"
            "    return a + b\n"
        )
        res = self.tracer.execute_source(code, "add", [15, 25])
        self.assertEqual(res.return_value, 40)
        self.assertEqual(res.execution_tier, 0)  # Under threshold -> Tier 0
        self.assertFalse(res.deoptimized)

    def test_03_invocation_counter_tracking(self):
        code = "def count_fn(): return 1\n"
        for _ in range(3):
            self.tracer.execute_source(code, "count_fn")
        cnt = self.tracer.invocation_counters.get(("count_fn", "entry"), 0)
        self.assertEqual(cnt, 3)

    def test_04_hotpath_promotion_to_tier1(self):
        code = "def hot_fn(x): return x * 2\n"
        # Call 5 times to hit hot_threshold = 5
        for _ in range(5):
            self.tracer.execute_source(code, "hot_fn", [10])

        # 6th execution should run in Tier 1 JIT
        res = self.tracer.execute_source(code, "hot_fn", [10])
        self.assertEqual(res.return_value, 20)
        self.assertEqual(res.execution_tier, 1)
        self.assertIsNotNone(res.trace_id)

    def test_05_jit_trace_cache_storage(self):
        code = "def traced(a, b): return (a * b) + 5\n"
        for _ in range(6):
            self.tracer.execute_source(code, "traced", [2, 3])

        self.assertIn("traced", self.tracer.jit_cache)
        trace = self.tracer.jit_cache["traced"]
        self.assertEqual(trace.func_name, "traced")
        self.assertGreater(trace.instructions_count, 0)
        self.assertGreater(trace.invocations, 0)

    def test_06_deoptimization_bailout(self):
        code = (
            "def guarded(x):\n"
            "    if x:\n"
            "        return 100\n"
            "    return 200\n"
        )
        # Promote to Tier 1
        for _ in range(5):
            self.tracer.execute_source(code, "guarded", [1])

        # Pass a non-boolean / non-int value object to trigger guard deoptimization
        class NonStandardValue:
            pass

        res = self.tracer.execute_source(code, "guarded", [NonStandardValue()])
        self.assertTrue(res.deoptimized)
        self.assertEqual(res.execution_tier, 0)

    def test_07_flush_jit_cache(self):
        code = "def sample(): return 10\n"
        for _ in range(6):
            self.tracer.execute_source(code, "sample")
        self.assertGreater(len(self.tracer.jit_cache), 0)

        flushed = self.tracer.flush_jit_cache()
        self.assertGreater(flushed, 0)
        self.assertEqual(len(self.tracer.jit_cache), 0)

    def test_08_branching_function_execution(self):
        code = (
            "def branch_eval(x):\n"
            "    if x:\n"
            "        return 42\n"
            "    else:\n"
            "        return 99\n"
        )
        res_true = self.tracer.execute_source(code, "branch_eval", [1])
        self.assertEqual(res_true.return_value, 42)

        res_false = self.tracer.execute_source(code, "branch_eval", [0])
        self.assertEqual(res_false.return_value, 99)

    def test_09_ascii_status_and_trace_tables(self):
        code = "def tbl_fn(): return 1\n"
        for _ in range(6):
            self.tracer.execute_source(code, "tbl_fn")

        stat_table = self.tracer.format_jit_status_table()
        self.assertIn("+=============================================================================+", stat_table)
        self.assertIn("LUCY JIT HOTPATH TRACER & TIERED EXECUTION ENGINE [STAGE 146 | ERA 15]", stat_table)
        self.assertIn("Senin Ali K P", stat_table)

        trace = self.tracer.jit_cache["tbl_fn"]
        tr_table = self.tracer.format_trace_table(trace)
        self.assertIn("JIT TRACE:", tr_table)
        self.assertIn("tbl_fn", tr_table)

    def test_10_execute_source_convenience(self):
        code = "def mult(x, y): return x * y\n"
        res = self.tracer.execute_source(code, "mult", [6, 7])
        self.assertEqual(res.return_value, 42)
        self.assertGreater(res.elapsed_ns, 0)


if __name__ == "__main__":
    unittest.main()
