r"""
backend/lucy_core/perf_regression_sentinel.py
Stage 137: Real-Time Performance Regression Sentinel
Era 14: Autonomous Code Evolution, Semantic Mutation & Static Synthesis

100% offline, real-time performance regression sentinel and micro-benchmark telemetry
engine for Lucy OS:
1. High-Resolution Micro-Benchmarking:
   - Measures CPU execution time with nanosecond accuracy (perf_counter_ns).
   - Monitors memory allocation deltas and peak heap overhead (tracemalloc).
   - Computes deterministic latency distributions (min, max, mean, p95) and throughput (ops/sec).
2. Sovereign Baseline Tracking:
   - Calibrates and maintains baseline performance profiles for core Lucy subsystems.
   - Cryptographically secures baseline states using HMAC-SHA256 locked to operator: Senin (Senin Ali K P).
3. Automated Regression Detection:
   - Compares observed execution profiles against calibrated baselines.
   - Flags regressions exceeding user-configured thresholds (latency degradation % or memory bloat %).
4. Subsystem Health Diagnostics:
   - Pre-calibrated micro-benchmarks for AST mutation, constraint solving, bytecode disassembler,
     wheel index, and router throughput.
5. Strict CP1252-Safe ASCII Presentation:
   - /perf-status / /perf-sentinel-status
   - /perf-benchmark [target_name] [iterations]
   - /perf-check [target_name]
   - /perf-baselines
"""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import hmac
import json
import os
import sys
import threading
import time
import tracemalloc
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

STAGE: int = 137
STAGE_NAME: str = "Real-Time Performance Regression Sentinel"
ERA: int = 14
CREATOR: str = "Senin"
OPERATOR: str = "Senin Ali K P"
HMAC_SECRET: bytes = b"senin-lucy-sovereign-perf-sentinel-key-2026"


@dataclasses.dataclass
class BenchmarkMetric:
    name: str
    iterations: int
    total_duration_sec: float
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p95_latency_ms: float
    ops_per_sec: float
    memory_delta_kb: float
    peak_memory_kb: float
    timestamp: float
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BenchmarkMetric:
        return cls(**data)


@dataclasses.dataclass
class RegressionAlert:
    alert_id: str
    target: str
    metric: str
    baseline_val: float
    observed_val: float
    degradation_pct: float
    severity: str
    timestamp: float
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


class RealTimePerfRegressionSentinel:
    """
    Stage 137: Real-Time Performance Regression Sentinel.
    Provides sub-microsecond microbenchmarking, regression analysis against
    sovereign baselines, and telemetry reports.
    """

    def __init__(
        self,
        project_root: Optional[str | Path] = None,
        runtime: Any = None,
        latency_threshold_pct: float = 25.0,
        memory_threshold_pct: float = 20.0,
    ) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.runtime = runtime
        self.latency_threshold_pct = float(latency_threshold_pct)
        self.memory_threshold_pct = float(memory_threshold_pct)

        self.storage_dir = self.project_root / "data" / "lucy" / "perf_sentinel"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.baselines_file = self.storage_dir / "perf_baselines.json"

        self._lock = threading.RLock()
        self.baselines: Dict[str, BenchmarkMetric] = {}
        self.recent_metrics: List[BenchmarkMetric] = []
        self.alerts: List[RegressionAlert] = []
        self.total_benchmarks_run: int = 0

        self._load_baselines()
        if not self.baselines:
            self._seed_default_baselines()

    def _seed_default_baselines(self) -> None:
        """Seed initial sovereign baselines for standard subsystems."""
        defaults = [
            ("ast_mutation", 100, 0.05, 0.50, 0.35, 1.20, 0.85, 2000.0, 12.5, 45.0),
            ("constraint_solver", 50, 0.04, 0.80, 0.60, 1.80, 1.20, 1250.0, 8.0, 30.0),
            ("bytecode_inspector", 100, 0.03, 0.30, 0.20, 0.90, 0.60, 3333.3, 5.0, 20.0),
            ("wheel_builder", 20, 0.10, 5.00, 4.00, 8.00, 6.50, 200.0, 64.0, 128.0),
            ("router_dispatch", 500, 0.02, 0.04, 0.02, 0.15, 0.08, 25000.0, 2.0, 10.0),
        ]
        now = time.time()
        for name, iters, dur, avg_l, min_l, max_l, p95, ops, mem_d, peak_m in defaults:
            metric = BenchmarkMetric(
                name=name,
                iterations=iters,
                total_duration_sec=dur,
                avg_latency_ms=avg_l,
                min_latency_ms=min_l,
                max_latency_ms=max_l,
                p95_latency_ms=p95,
                ops_per_sec=ops,
                memory_delta_kb=mem_d,
                peak_memory_kb=peak_m,
                timestamp=now,
                metadata={"seeded": True, "operator": OPERATOR},
            )
            self.baselines[name] = metric
        self._save_baselines()

    def _compute_baseline_signature(self, serialized_data: str) -> str:
        return hmac.new(HMAC_SECRET, serialized_data.encode("utf-8"), hashlib.sha256).hexdigest()

    def _save_baselines(self) -> None:
        with self._lock:
            payload = {
                "version": "1.0",
                "creator": CREATOR,
                "operator": OPERATOR,
                "baselines": {k: v.to_dict() for k, v in self.baselines.items()},
            }
            raw = json.dumps(payload, indent=2, sort_keys=True)
            sig = self._compute_baseline_signature(raw)
            bundle = {"payload": payload, "hmac_signature": sig}
            self.baselines_file.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    def _load_baselines(self) -> None:
        with self._lock:
            if not self.baselines_file.exists():
                return
            try:
                data = json.loads(self.baselines_file.read_text(encoding="utf-8"))
                payload = data.get("payload", {})
                expected_sig = data.get("hmac_signature", "")
                raw = json.dumps(payload, indent=2, sort_keys=True)
                computed_sig = self._compute_baseline_signature(raw)
                if not hmac.compare_digest(expected_sig, computed_sig):
                    # Signature mismatch / tampered, reject loading
                    return
                for k, v in payload.get("baselines", {}).items():
                    self.baselines[k] = BenchmarkMetric.from_dict(v)
            except Exception:
                pass

    def run_microbenchmark(
        self,
        name: str,
        target_callable: Callable[[], Any],
        iterations: int = 100,
        record_as_baseline: bool = False,
        warmup_iterations: int = 5,
    ) -> BenchmarkMetric:
        """
        Executes a callable across specified iterations measuring CPU execution time
        and memory overhead.
        """
        if iterations <= 0:
            iterations = 1

        # Warmup phase
        for _ in range(warmup_iterations):
            try:
                target_callable()
            except Exception:
                pass

        latencies_ms: List[float] = []
        was_tracing = tracemalloc.is_tracing()
        if not was_tracing:
            tracemalloc.start()
        tracemalloc.reset_peak()

        mem_start, _ = tracemalloc.get_traced_memory()
        t_start_total = time.perf_counter_ns()

        for _ in range(iterations):
            t0 = time.perf_counter_ns()
            target_callable()
            t1 = time.perf_counter_ns()
            latencies_ms.append((t1 - t0) / 1_000_000.0)

        t_end_total = time.perf_counter_ns()
        mem_end, mem_peak = tracemalloc.get_traced_memory()
        if not was_tracing:
            tracemalloc.stop()

        total_sec = (t_end_total - t_start_total) / 1_000_000_000.0
        latencies_ms.sort()
        avg_lat = sum(latencies_ms) / len(latencies_ms)
        min_lat = latencies_ms[0]
        max_lat = latencies_ms[-1]
        p95_idx = int(len(latencies_ms) * 0.95)
        p95_lat = latencies_ms[min(p95_idx, len(latencies_ms) - 1)]
        ops_sec = (iterations / total_sec) if total_sec > 0 else 0.0

        mem_delta_kb = max(0.0, (mem_end - mem_start) / 1024.0)
        peak_mem_kb = max(0.0, mem_peak / 1024.0)

        metric = BenchmarkMetric(
            name=name,
            iterations=iterations,
            total_duration_sec=round(total_sec, 6),
            avg_latency_ms=round(avg_lat, 4),
            min_latency_ms=round(min_lat, 4),
            max_latency_ms=round(max_lat, 4),
            p95_latency_ms=round(p95_lat, 4),
            ops_per_sec=round(ops_sec, 2),
            memory_delta_kb=round(mem_delta_kb, 2),
            peak_memory_kb=round(peak_mem_kb, 2),
            timestamp=time.time(),
            metadata={"operator": OPERATOR},
        )

        with self._lock:
            self.total_benchmarks_run += 1
            self.recent_metrics.append(metric)
            if len(self.recent_metrics) > 100:
                self.recent_metrics.pop(0)

            if record_as_baseline:
                self.baselines[name] = metric
                self._save_baselines()

        return metric

    def check_regression(self, metric: BenchmarkMetric) -> List[RegressionAlert]:
        """
        Compares an observed benchmark metric against established baselines.
        Generates alerts if latency or memory degradation exceeds thresholds.
        """
        alerts: List[RegressionAlert] = []
        baseline = self.baselines.get(metric.name)
        if not baseline:
            return alerts

        # Check Latency Degradation
        if baseline.avg_latency_ms > 0:
            deg_pct = ((metric.avg_latency_ms - baseline.avg_latency_ms) / baseline.avg_latency_ms) * 100.0
            if deg_pct >= self.latency_threshold_pct:
                sev = "CRITICAL" if deg_pct >= (self.latency_threshold_pct * 2) else "WARNING"
                aid = f"ALERT-LAT-{int(time.time()*1000)%1000000}"
                msg = f"Latency regression on '{metric.name}': {metric.avg_latency_ms:.3f}ms vs baseline {baseline.avg_latency_ms:.3f}ms (+{deg_pct:.1f}%)"
                alerts.append(
                    RegressionAlert(
                        alert_id=aid,
                        target=metric.name,
                        metric="avg_latency_ms",
                        baseline_val=baseline.avg_latency_ms,
                        observed_val=metric.avg_latency_ms,
                        degradation_pct=round(deg_pct, 2),
                        severity=sev,
                        timestamp=time.time(),
                        message=msg,
                    )
                )

        # Check Memory Degradation
        if baseline.peak_memory_kb > 0:
            mem_deg_pct = ((metric.peak_memory_kb - baseline.peak_memory_kb) / baseline.peak_memory_kb) * 100.0
            if mem_deg_pct >= self.memory_threshold_pct:
                aid = f"ALERT-MEM-{int(time.time()*1000)%1000000}"
                msg = f"Memory overhead regression on '{metric.name}': {metric.peak_memory_kb:.1f}KB vs baseline {baseline.peak_memory_kb:.1f}KB (+{mem_deg_pct:.1f}%)"
                alerts.append(
                    RegressionAlert(
                        alert_id=aid,
                        target=metric.name,
                        metric="peak_memory_kb",
                        baseline_val=baseline.peak_memory_kb,
                        observed_val=metric.peak_memory_kb,
                        degradation_pct=round(mem_deg_pct, 2),
                        severity="WARNING",
                        timestamp=time.time(),
                        message=msg,
                    )
                )

        with self._lock:
            self.alerts.extend(alerts)
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]

        return alerts

    def benchmark_subsystem(self, target_name: str, iterations: int = 100) -> Tuple[BenchmarkMetric, List[RegressionAlert]]:
        """
        Runs a standardized sovereign benchmark for a known subsystem.
        """
        tname = target_name.lower().strip()
        if tname == "ast_mutation":
            from backend.lucy_core.ast_mutation_operator import ASTSemanticMutationOperator
            op = ASTSemanticMutationOperator()
            code = "def calc(a, b):\n    return (a * b) + 10\n"
            metric = self.run_microbenchmark("ast_mutation", lambda: op.mutate_ast(code, mutation_types=["operator_flip"]), iterations=iterations)
        elif tname == "constraint_solver":
            from backend.lucy_core.static_constraint_solver import StaticConstraintSolver
            solver = StaticConstraintSolver()
            code = "def compute(x: int, y: int) -> int:\n    return x + y\n"
            metric = self.run_microbenchmark("constraint_solver", lambda: solver.solve_file_constraints(code), iterations=iterations)
        elif tname == "bytecode_inspector":
            from backend.lucy_core.bytecode_disassembler import BytecodeDisassemblyInspector
            insp = BytecodeDisassemblyInspector()
            code = "def foo(n):\n    return sum(i * 2 for i in range(n))\n"
            metric = self.run_microbenchmark("bytecode_inspector", lambda: insp.inspect_source(code), iterations=iterations)
        elif tname == "wheel_builder":
            from backend.lucy_core.sovereign_wheel_fabric import SovereignWheelFabricIndex
            wf = SovereignWheelFabricIndex(project_root=self.project_root)
            metric = self.run_microbenchmark("wheel_builder", lambda: wf.build_wheel("test_benchmark_pkg", version="0.1.0"), iterations=max(5, iterations // 10))
        elif tname == "router_dispatch" and self.runtime and hasattr(self.runtime, "route_command"):
            metric = self.run_microbenchmark("router_dispatch", lambda: self.runtime.route_command("/ping"), iterations=iterations)
        else:
            # Synthetic standard CPU matrix computation benchmark
            def synthetic_workload():
                x = [i * i for i in range(500)]
                _ = sum(x)
            metric = self.run_microbenchmark(tname, synthetic_workload, iterations=iterations)

        alerts = self.check_regression(metric)
        return metric, alerts

    def record_manual_baseline(
        self,
        name: str,
        avg_latency_ms: float,
        ops_per_sec: float,
        peak_memory_kb: float,
        iterations: int = 100,
    ) -> BenchmarkMetric:
        """Explicitly records or updates a baseline benchmark metric."""
        metric = BenchmarkMetric(
            name=name,
            iterations=iterations,
            total_duration_sec=(avg_latency_ms * iterations) / 1000.0,
            avg_latency_ms=avg_latency_ms,
            min_latency_ms=avg_latency_ms * 0.8,
            max_latency_ms=avg_latency_ms * 1.5,
            p95_latency_ms=avg_latency_ms * 1.2,
            ops_per_sec=ops_per_sec,
            memory_delta_kb=peak_memory_kb * 0.2,
            peak_memory_kb=peak_memory_kb,
            timestamp=time.time(),
            metadata={"manual": True, "operator": OPERATOR},
        )
        with self._lock:
            self.baselines[name] = metric
            self._save_baselines()
        return metric

    def get_alerts(self, severity: Optional[str] = None) -> List[RegressionAlert]:
        with self._lock:
            if severity:
                return [a for a in self.alerts if a.severity.upper() == severity.upper()]
            return list(self.alerts)

    def clear_alerts(self) -> None:
        with self._lock:
            self.alerts.clear()

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "creator": CREATOR,
                "operator": OPERATOR,
                "total_baselines": len(self.baselines),
                "total_benchmarks_run": self.total_benchmarks_run,
                "active_alerts": len(self.alerts),
                "latency_threshold_pct": self.latency_threshold_pct,
                "memory_threshold_pct": self.memory_threshold_pct,
                "status": "ACTIVE_SENTINEL",
            }

    def format_perf_status_table(self) -> str:
        """Formats an ASCII overview of sentinel status and recent benchmarks."""
        s = self.status()
        lines = [
            "+=============================================================================+",
            f"| LUCY REAL-TIME PERFORMANCE REGRESSION SENTINEL [STAGE {STAGE:03d} | ERA {ERA:02d}]        |",
            "+=============================================================================+",
            f"| Status: {s['status']:<16} Total Baselines: {s['total_baselines']:<5} Total Benchmarks: {s['total_benchmarks_run']:<6} |",
            f"| Latency Threshold: +{self.latency_threshold_pct:<5.1f}%   Memory Threshold: +{self.memory_threshold_pct:<5.1f}%  Alerts: {len(self.alerts):<7} |",
            f"| Sovereign Operator: {OPERATOR:<55} |",
            "+-----------------------------------------------------------------------------+",
            "| RECENT BENCHMARKS & TELEMETRY                                               |",
            "+----------------------+------------+------------+------------+---------------+",
            "| Target Subsystem     | Iters      | Latency    | Peak Mem   | Throughput    |",
            "+----------------------+------------+------------+------------+---------------+",
        ]
        with self._lock:
            sample = self.recent_metrics[-5:] if self.recent_metrics else list(self.baselines.values())[:5]
            for m in sample:
                lines.append(
                    f"| {m.name[:20]:<20} | {m.iterations:<10} | {m.avg_latency_ms:<7.3f}ms  | {m.peak_memory_kb:<7.1f}KB | {m.ops_per_sec:<9.1f}/s |"
                )
        lines.append("+----------------------+------------+------------+------------+---------------+")

        if self.alerts:
            lines.extend([
                "| ACTIVE PERFORMANCE REGRESSION ALERTS                                        |",
                "+---------------+----------------------+-----------+-------------+------------+",
                "| Alert ID      | Target               | Metric    | Degraded    | Severity   |",
                "+---------------+----------------------+-----------+-------------+------------+",
            ])
            with self._lock:
                for a in self.alerts[-3:]:
                    lines.append(
                        f"| {a.alert_id:<13} | {a.target[:20]:<20} | {a.metric[:9]:<9} | +{a.degradation_pct:<8.1f}% | {a.severity:<10} |"
                    )
            lines.append("+---------------+----------------------+-----------+-------------+------------+")

        return "\n".join(lines)

    def format_baselines_table(self) -> str:
        """Formats the registered sovereign baseline metrics table."""
        lines = [
            "+=============================================================================+",
            "| CALIBRATED PERFORMANCE BASELINES (SOVEREIGN REFERENCE METRICS)              |",
            "+=============================================================================+",
            "| Target Name          | Base Latency | P95 Latency | Peak Memory | Base Ops/sec|",
            "+----------------------+--------------+-------------+-------------+-------------+",
        ]
        with self._lock:
            for name, m in sorted(self.baselines.items()):
                lines.append(
                    f"| {name[:20]:<20} | {m.avg_latency_ms:<9.3f} ms | {m.p95_latency_ms:<8.3f} ms | {m.peak_memory_kb:<8.1f} KB | {m.ops_per_sec:<11.1f} |"
                )
        lines.append("+----------------------+--------------+-------------+-------------+-------------+")
        return "\n".join(lines)


__all__ = [
    "STAGE",
    "STAGE_NAME",
    "ERA",
    "CREATOR",
    "OPERATOR",
    "BenchmarkMetric",
    "RegressionAlert",
    "RealTimePerfRegressionSentinel",
]
