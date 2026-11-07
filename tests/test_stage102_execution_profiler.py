"""
tests/test_stage102_execution_profiler.py
Stage 102: Dynamic Execution Profiler & Flamegraph Tracer Unit Tests
"""

import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.execution_profiler import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    STAGE,
    ExecutionProfiler,
    FunctionProfileEntry,
    ProfileRunResult,
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


class TestStage102ExecutionProfiler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lucy_stage102_test_")
        self.temp_path = Path(self.temp_dir)
        self.project_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_constants_and_metadata(self):
        self.assertEqual(STAGE, 102)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")

    def test_02_profile_scope_context_manager(self):
        profiler = ExecutionProfiler(
            project_root=self.project_root,
            data_dir=self.temp_path / "profiler",
        )
        with profiler.profile_scope("test_workload") as meta:
            # Simple dummy workload
            total = sum(i * i for i in range(5000))

        self.assertTrue(meta["completed"])
        self.assertGreater(meta["wall_time_ms"], 0.0)
        self.assertIsInstance(meta["result"], ProfileRunResult)
        self.assertEqual(meta["result"].target, "test_workload")
        self.assertGreater(meta["result"].total_function_calls, 0)

    def test_03_profile_callable(self):
        def sample_computation(x: int) -> int:
            return sum(i for i in range(x))

        profiler = ExecutionProfiler(
            project_root=self.project_root,
            data_dir=self.temp_path / "profiler",
        )
        val, run_res = profiler.profile_callable(sample_computation, 10000)
        self.assertEqual(val, sum(i for i in range(10000)))
        self.assertIsInstance(run_res, ProfileRunResult)
        self.assertIn("sample_computation", run_res.target)

    def test_04_hot_paths_analysis(self):
        profiler = ExecutionProfiler(
            project_root=self.project_root,
            data_dir=self.temp_path / "profiler",
        )

        def nested_calls():
            for _ in range(100):
                _ = len(str(list(range(20))))

        _, res = profiler.profile_callable(nested_calls)
        self.assertGreater(len(res.top_hot_paths), 0)
        top = res.top_hot_paths[0]
        self.assertIsInstance(top, FunctionProfileEntry)
        self.assertGreater(top.call_count, 0)
        self.assertGreaterEqual(top.pct_of_total, 0.0)

    def test_05_flamegraph_ascii_rendering(self):
        profiler = ExecutionProfiler(
            project_root=self.project_root,
            data_dir=self.temp_path / "profiler",
        )
        with profiler.profile_scope("flamegraph_test"):
            _ = [str(x) for x in range(3000)]

        fg = profiler.get_latest_flamegraph()
        self.assertIn("100.0% Root: flamegraph_test", fg)
        self.assertIn("[", fg)
        self.assertIn("]", fg)
        # Verify CP1252 validity
        fg.encode("cp1252")

    def test_06_record_latency_and_percentiles(self):
        profiler = ExecutionProfiler(
            project_root=self.project_root,
            data_dir=self.temp_path / "profiler",
        )
        # Record samples: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100 ms
        for val in range(10, 110, 10):
            profiler.record_latency("test_query", float(val))

        p = profiler.get_latency_percentiles("test_query")
        self.assertEqual(p["count"], 10)
        self.assertEqual(p["min_ms"], 10.0)
        self.assertEqual(p["max_ms"], 100.0)
        self.assertAlmostEqual(p["mean_ms"], 55.0, delta=1.0)
        self.assertAlmostEqual(p["p50_ms"], 50.0, delta=5.0)
        self.assertAlmostEqual(p["p95_ms"], 100.0, delta=5.0)

    def test_07_latency_regression_detection(self):
        profiler = ExecutionProfiler(
            project_root=self.project_root,
            data_dir=self.temp_path / "profiler",
        )
        # Establish stable 10ms baseline
        for _ in range(10):
            profiler.record_latency("fast_api", 10.0)

        # Normal run
        reg_none = profiler.detect_latency_regression("fast_api", 12.0)
        self.assertIsNone(reg_none)

        # Severe spike (100ms > 2.5 * 10ms)
        reg_spike = profiler.detect_latency_regression("fast_api", 100.0, multiplier=2.5)
        self.assertIsNotNone(reg_spike)
        self.assertEqual(reg_spike["operation"], "fast_api")
        self.assertGreaterEqual(reg_spike["ratio"], 2.5)

    def test_08_receipt_ledger_integration(self):
        ledger = MockReceiptLedger()
        profiler = ExecutionProfiler(
            project_root=self.project_root,
            receipt_ledger=ledger,
            data_dir=self.temp_path / "profiler",
        )
        with profiler.profile_scope("receipt_test"):
            _ = 42 * 42

        # Check PROFILER_RUN receipt
        categories = [r["category"] for r in ledger.receipts]
        self.assertIn("PROFILER_RUN", categories)

        # Trigger regression spike
        for _ in range(10):
            profiler.record_latency("spiky_task", 5.0)
        profiler.record_latency("spiky_task", 150.0)

        categories = [r["category"] for r in ledger.receipts]
        self.assertIn("PROFILER_REGRESSION_ALERT", categories)

    def test_09_terminal_summary_and_hot_paths_table(self):
        profiler = ExecutionProfiler(
            project_root=self.project_root,
            data_dir=self.temp_path / "profiler",
        )
        with profiler.profile_scope("table_test"):
            _ = [i ** 2 for i in range(1000)]

        run_res = profiler._profile_runs[-1]
        summary = run_res.format_terminal_summary()
        self.assertIn("LUCY OS - EXECUTION PROFILER AUDIT", summary)
        self.assertIn("STAGE 102: DYNAMIC HIGH-PRECISION TRACER", summary)
        summary.encode("cp1252")

        table = profiler.get_hot_paths_table(top_n=5)
        self.assertIn("LATEST PROFILE HOT PATHS", table)
        table.encode("cp1252")

    def test_10_latency_audit_report(self):
        profiler = ExecutionProfiler(
            project_root=self.project_root,
            data_dir=self.temp_path / "profiler",
        )
        for d in (12.5, 14.2, 11.8, 16.0, 13.1):
            profiler.record_latency("dispatch", d)

        report = profiler.get_latency_audit_report()
        self.assertIn("LUCY OS - LATENCY PERCENTILES AUDIT", report)
        self.assertIn("Median (p50)", report)
        self.assertIn("p95", report)
        report.encode("cp1252")

    def test_11_status_and_persistence(self):
        profiler = ExecutionProfiler(
            project_root=self.project_root,
            data_dir=self.temp_path / "profiler",
        )
        with profiler.profile_scope("status_test"):
            _ = 1 + 1

        st = profiler.status()
        self.assertEqual(st["stage"], 102)
        self.assertEqual(st["creator"], "Senin")
        self.assertGreaterEqual(st["total_profile_runs"], 1)
        self.assertGreaterEqual(st["total_latency_samples"], 1)


if __name__ == "__main__":
    unittest.main()
