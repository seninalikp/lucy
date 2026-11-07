r"""
tests/test_stage137_perf_regression_sentinel.py
Unit tests for Stage 137: Real-Time Performance Regression Sentinel.
Era 14: Autonomous Code Evolution, Semantic Mutation & Static Synthesis
"""

import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.perf_regression_sentinel import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    BenchmarkMetric,
    RealTimePerfRegressionSentinel,
    RegressionAlert,
)


class TestStage137PerfRegressionSentinel(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sentinel = RealTimePerfRegressionSentinel(
            project_root=self.test_dir,
            latency_threshold_pct=25.0,
            memory_threshold_pct=20.0,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_initialization_and_default_baselines(self):
        self.assertEqual(STAGE, 137)
        self.assertEqual(ERA, 14)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")

        st = self.sentinel.status()
        self.assertEqual(st["stage"], 137)
        self.assertEqual(st["status"], "ACTIVE_SENTINEL")
        self.assertGreaterEqual(st["total_baselines"], 5)
        self.assertIn("ast_mutation", self.sentinel.baselines)
        self.assertIn("constraint_solver", self.sentinel.baselines)
        self.assertIn("bytecode_inspector", self.sentinel.baselines)

    def test_02_microbenchmark_callable_execution(self):
        def sample_work():
            return sum(x * 2 for x in range(200))

        metric = self.sentinel.run_microbenchmark("sample_task", sample_work, iterations=50)
        self.assertEqual(metric.name, "sample_task")
        self.assertEqual(metric.iterations, 50)
        self.assertGreater(metric.total_duration_sec, 0.0)
        self.assertGreater(metric.avg_latency_ms, 0.0)
        self.assertLessEqual(metric.min_latency_ms, metric.avg_latency_ms)
        self.assertGreaterEqual(metric.max_latency_ms, metric.avg_latency_ms)
        self.assertLessEqual(metric.p95_latency_ms, metric.max_latency_ms)
        self.assertGreater(metric.ops_per_sec, 0.0)

    def test_03_memory_tracing_overhead(self):
        def mem_work():
            arr = [str(i) * 100 for i in range(1000)]
            return len(arr)

        metric = self.sentinel.run_microbenchmark("mem_task", mem_work, iterations=20)
        self.assertGreaterEqual(metric.peak_memory_kb, 0.0)
        self.assertGreaterEqual(metric.memory_delta_kb, 0.0)

    def test_04_record_and_persist_baseline(self):
        def fast_work():
            return 42

        metric = self.sentinel.run_microbenchmark("fast_target", fast_work, iterations=30, record_as_baseline=True)
        self.assertIn("fast_target", self.sentinel.baselines)

        # Create new sentinel on same directory to test loading from persisted storage
        sentinel2 = RealTimePerfRegressionSentinel(project_root=self.test_dir)
        self.assertIn("fast_target", sentinel2.baselines)
        self.assertEqual(sentinel2.baselines["fast_target"].name, "fast_target")

    def test_05_tamper_detection_on_load(self):
        # Corrupt baselines file payload
        bfile = Path(self.test_dir) / "data" / "lucy" / "perf_sentinel" / "perf_baselines.json"
        raw_json = json.loads(bfile.read_text(encoding="utf-8"))
        raw_json["payload"]["baselines"]["tampered_key"] = {"name": "tampered"}
        bfile.write_text(json.dumps(raw_json), encoding="utf-8")

        # Reloading should detect signature mismatch and reject tampered baselines
        fresh_dir = tempfile.mkdtemp()
        try:
            sentinel_tampered = RealTimePerfRegressionSentinel(project_root=self.test_dir)
            self.assertNotIn("tampered_key", sentinel_tampered.baselines)
        finally:
            shutil.rmtree(fresh_dir, ignore_errors=True)

    def test_06_latency_regression_detection(self):
        # Record a low latency baseline (0.01 ms)
        self.sentinel.record_manual_baseline("slow_prone_target", avg_latency_ms=0.01, ops_per_sec=100000.0, peak_memory_kb=10.0)

        # Create a slow metric that exceeds baseline by 100%
        slow_metric = BenchmarkMetric(
            name="slow_prone_target",
            iterations=10,
            total_duration_sec=0.1,
            avg_latency_ms=0.025,  # +150% degradation
            min_latency_ms=0.02,
            max_latency_ms=0.03,
            p95_latency_ms=0.028,
            ops_per_sec=40000.0,
            memory_delta_kb=5.0,
            peak_memory_kb=10.0,
            timestamp=time.time(),
        )

        alerts = self.sentinel.check_regression(slow_metric)
        self.assertGreaterEqual(len(alerts), 1)
        lat_alert = alerts[0]
        self.assertEqual(lat_alert.target, "slow_prone_target")
        self.assertEqual(lat_alert.metric, "avg_latency_ms")
        self.assertEqual(lat_alert.severity, "CRITICAL")
        self.assertIn("+150.0%", lat_alert.message)

    def test_07_memory_regression_detection(self):
        self.sentinel.record_manual_baseline("mem_prone_target", avg_latency_ms=1.0, ops_per_sec=1000.0, peak_memory_kb=50.0)

        bloated_metric = BenchmarkMetric(
            name="mem_prone_target",
            iterations=10,
            total_duration_sec=0.01,
            avg_latency_ms=1.0,
            min_latency_ms=0.8,
            max_latency_ms=1.2,
            p95_latency_ms=1.1,
            ops_per_sec=1000.0,
            memory_delta_kb=40.0,
            peak_memory_kb=100.0,  # +100% memory degradation
            timestamp=time.time(),
        )

        alerts = self.sentinel.check_regression(bloated_metric)
        self.assertTrue(any(a.metric == "peak_memory_kb" for a in alerts))

    def test_08_subsystem_synthetic_benchmarks(self):
        metric, alerts = self.sentinel.benchmark_subsystem("synthetic_test", iterations=15)
        self.assertEqual(metric.name, "synthetic_test")
        self.assertEqual(metric.iterations, 15)
        self.assertGreater(metric.ops_per_sec, 0.0)

    def test_09_ascii_status_and_baseline_tables(self):
        status_table = self.sentinel.format_perf_status_table()
        self.assertIn("+=============================================================================+", status_table)
        self.assertIn("LUCY REAL-TIME PERFORMANCE REGRESSION SENTINEL [STAGE 137 | ERA 14]", status_table)
        self.assertIn("Senin Ali K P", status_table)

        base_table = self.sentinel.format_baselines_table()
        self.assertIn("CALIBRATED PERFORMANCE BASELINES", base_table)
        self.assertIn("ast_mutation", base_table)

    def test_10_clear_alerts_and_metric_rotation(self):
        self.sentinel.record_manual_baseline("rot_target", avg_latency_ms=0.001, ops_per_sec=100000.0, peak_memory_kb=1.0)
        slow_metric = BenchmarkMetric(
            name="rot_target",
            iterations=1,
            total_duration_sec=0.1,
            avg_latency_ms=1.0,
            min_latency_ms=1.0,
            max_latency_ms=1.0,
            p95_latency_ms=1.0,
            ops_per_sec=10.0,
            memory_delta_kb=0.0,
            peak_memory_kb=1.0,
            timestamp=time.time(),
        )
        self.sentinel.check_regression(slow_metric)
        self.assertGreater(len(self.sentinel.get_alerts()), 0)

        self.sentinel.clear_alerts()
        self.assertEqual(len(self.sentinel.get_alerts()), 0)


if __name__ == "__main__":
    unittest.main()
