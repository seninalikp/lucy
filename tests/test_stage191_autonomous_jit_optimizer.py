r"""
tests/test_stage191_autonomous_jit_optimizer.py
Unit tests for Stage 191: Autonomous JIT Micro-Optimizer & Bytecode Vectorizer
Era 20: The Sovereign Bicentennial AGI Singularity & Autonomous Kernel Transcendence
"""

from __future__ import annotations

import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import unittest
from backend.lucy_core.autonomous_jit_optimizer import (
    AutonomousJITOptimizerFabric,
    OptimizationTier,
    TraceInstruction,
)


class TestAutonomousJITOptimizer(unittest.TestCase):
    def setUp(self) -> None:
        self.jit = AutonomousJITOptimizerFabric(tier1_threshold=5, tier2_threshold=15)

    def test_profiler_call_recording_and_averages(self) -> None:
        self.jit.record_call("compute_hash", 2.0)
        self.jit.record_call("compute_hash", 4.0)

        m = self.jit.metrics["compute_hash"]
        self.assertEqual(m.call_count, 2)
        self.assertEqual(m.total_time_ms, 6.0)
        self.assertEqual(m.avg_time_ms, 3.0)

    def test_tier_promotion_thresholds(self) -> None:
        # Tier 0 (calls < 5)
        for _ in range(4):
            t = self.jit.record_call("render_frame", 1.0)
        self.assertEqual(t, OptimizationTier.INTERPRETED)

        # Tier 1 (calls >= 5)
        t = self.jit.record_call("render_frame", 1.0)
        self.assertEqual(t, OptimizationTier.BASELINE_JIT)

        # Tier 2 (calls >= 15)
        for _ in range(10):
            t = self.jit.record_call("render_frame", 1.0)
        self.assertEqual(t, OptimizationTier.VECTORIZED_HOT_JIT)

    def test_constant_folding_pass(self) -> None:
        # 10 + 25 -> 35
        raw = [
            TraceInstruction("CONST", [10], "x"),
            TraceInstruction("CONST", [25], "y"),
            TraceInstruction("ADD", ["x", "y"], "z"),
        ]
        folded = self.jit.pass_constant_folding(raw)
        # Result should fold into CONST 35
        dest_ops = {ins.dest: (ins.op, ins.args[0]) for ins in folded}
        self.assertIn("z", dest_ops)
        self.assertEqual(dest_ops["z"], ("CONST", 35))

    def test_dead_code_elimination_pass(self) -> None:
        # 'unused_temp' is never read; 'final_res' is live output
        raw = [
            TraceInstruction("CONST", [100], "unused_temp"),
            TraceInstruction("CONST", [50], "live_input"),
            TraceInstruction("ADD", ["live_input", 10], "final_res"),
        ]
        pruned = self.jit.pass_dead_code_elimination(raw, live_outputs={"final_res"})
        dests = [ins.dest for ins in pruned]
        self.assertNotIn("unused_temp", dests)
        self.assertIn("live_input", dests)
        self.assertIn("final_res", dests)

    def test_loop_unrolling_pass(self) -> None:
        raw = [
            TraceInstruction("ADD", ["acc", "val"], "acc"),
        ]
        unrolled = self.jit.pass_loop_unrolling(raw, unroll_factor=3)
        self.assertEqual(len(unrolled), 3)
        self.assertEqual(unrolled[0].dest, "acc__u0")
        self.assertEqual(unrolled[1].dest, "acc__u1")
        self.assertEqual(unrolled[2].dest, "acc__u2")

    def test_bytecode_vectorization_pass(self) -> None:
        raw = [
            TraceInstruction("ADD", ["vec_a", "vec_b"], "vec_res"),
            TraceInstruction("MUL", ["vec_res", 2], "vec_scaled"),
        ]
        vectorized, applied = self.jit.pass_vectorization(raw)
        self.assertTrue(applied)
        ops = [ins.op for ins in vectorized]
        self.assertIn("VEC_ADD", ops)
        self.assertIn("VEC_MUL", ops)

    def test_full_trace_optimization_pipeline(self) -> None:
        raw = [
            TraceInstruction("CONST", [5], "c1"),
            TraceInstruction("CONST", [10], "c2"),
            TraceInstruction("ADD", ["c1", "c2"], "base_sum"),
            TraceInstruction("MUL", ["base_sum", "dyn_var"], "out"),
        ]
        opt_trace = self.jit.optimize_trace("calc", raw, target_tier=OptimizationTier.BASELINE_JIT, live_outputs={"out"})
        self.assertEqual(opt_trace.tier, OptimizationTier.BASELINE_JIT)
        self.assertIn("calc", self.jit.compiled_traces)
        # Constant folded base_sum = 15
        dest_map = {ins.dest: ins for ins in opt_trace.instructions}
        self.assertIn("base_sum", dest_map)
        self.assertEqual(dest_map["base_sum"].args[0], 15)

    def test_execute_trace_scalar(self) -> None:
        raw = [
            TraceInstruction("CONST", [10], "a"),
            TraceInstruction("LOAD", ["input_x"], "x"),
            TraceInstruction("ADD", ["a", "x"], "result"),
        ]
        opt_trace = self.jit.optimize_trace("add_ten", raw, target_tier=OptimizationTier.BASELINE_JIT)
        env = self.jit.execute_trace(opt_trace, {"input_x": 42})
        self.assertEqual(env["result"], 52)

    def test_execute_trace_vector(self) -> None:
        raw = [
            TraceInstruction("VEC_ADD", ["arr1", "arr2"], "out_arr"),
        ]
        opt_trace = self.jit.optimize_trace("vec_op", raw, target_tier=OptimizationTier.VECTORIZED_HOT_JIT)
        env = self.jit.execute_trace(opt_trace, {"arr1": [1, 2, 3], "arr2": [10, 20, 30]})
        self.assertEqual(env["out_arr"], [11, 22, 33])

    def test_fabric_status_and_ascii_table(self) -> None:
        self.jit.record_call("compute_loss", 5.0)
        stat = self.jit.status()
        self.assertEqual(stat["total_functions_profiled"], 1)

        tbl = self.jit.format_ascii_status()
        self.assertIn("STAGE 191: AUTONOMOUS JIT MICRO-OPTIMIZER & BYTECODE VECTORIZER", tbl)
        self.assertIn("compute_loss", tbl)


if __name__ == "__main__":
    unittest.main()
