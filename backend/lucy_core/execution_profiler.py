r"""
backend/lucy_core/execution_profiler.py
Stage 102: Dynamic Execution Profiler & Flamegraph Tracer
Era 11: The Sovereign Super-Autonomous Core & Hyper-Resilient Operating Fabric

High-precision microsecond execution tracing for Lucy OS:
1. Microsecond Function Profiling:
   - Uses standard library cProfile and high-resolution time.perf_counter_ns().
   - Instruments arbitrary code scopes, command routing, and internal reasoning steps.
2. Hot-Path Analysis:
   - Aggregates call counts, cumulative time (ms), per-call latency (us), and percentage overhead.
3. CP1252-Safe ASCII Flamegraph:
   - Renders intuitive hierarchical flamegraph bars depicting execution proportion.
4. Latency Percentiles & Regression Detection:
   - Computes rolling p50, p95, and p99 latencies.
   - Detects execution regressions exceeding moving baseline thresholds.
5. Receipt Ledger Integration:
   - Logs PROFILER_RUN and PROFILER_REGRESSION_ALERT receipts.
6. Commands:
   - /profile-run
   - /flamegraph
   - /latency-audit
   - /hot-paths
"""

from __future__ import annotations

import cProfile
import io
import json
import os
import pstats
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

STAGE: int = 102

CREATOR_NAME: str = "Senin"
CREATOR_FULL_NAME: str = "Senin Ali K P"


@dataclass
class FunctionProfileEntry:
    name: str
    filename: str
    lineno: int
    call_count: int
    total_time_ms: float
    cumulative_time_ms: float
    time_per_call_us: float
    pct_of_total: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProfileRunResult:
    run_id: str
    target: str
    timestamp: str
    total_wall_time_ms: float
    total_function_calls: int
    top_hot_paths: List[FunctionProfileEntry]
    flamegraph_ascii: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "target": self.target,
            "timestamp": self.timestamp,
            "total_wall_time_ms": round(self.total_wall_time_ms, 3),
            "total_function_calls": self.total_function_calls,
            "top_hot_paths": [p.to_dict() for p in self.top_hot_paths],
            "flamegraph_ascii": self.flamegraph_ascii,
        }

    def format_terminal_summary(self) -> str:
        lines: List[str] = [
            "+======================================================================+",
            "|               LUCY OS - EXECUTION PROFILER AUDIT                     |",
            "|             STAGE 102: DYNAMIC HIGH-PRECISION TRACER                 |",
            "+======================================================================+",
            f"| Run ID:        {self.run_id:<17} | Target:    {self.target[:20]:<20} |",
            f"| Wall Time:     {self.total_wall_time_ms:>8.3f} ms        | Calls:     {self.total_function_calls:<20} |",
            "+----------------------------------------------------------------------+",
            "| TOP EXECUTION BOTTLENECKS (HOT PATHS):                               |",
            "| Method / Function           | Calls    | Cumul (ms) | Per-Call | % Tot|",
            "+-----------------------------+----------+------------+----------+------+",
        ]
        for p in self.top_hot_paths[:6]:
            m_name = p.name[:27]
            calls = str(p.call_count)[:8]
            cum = f"{p.cumulative_time_ms:.2f}"[:10]
            per = f"{p.time_per_call_us:.1f}us"[:8]
            pct = f"{p.pct_of_total:.1f}%"[:5]
            lines.append(f"| {m_name:<27} | {calls:<8} | {cum:<10} | {per:<8} |{pct:>5} |")

        lines.append("+----------------------------------------------------------------------+")
        lines.append("| EXECUTION FLAMEGRAPH:                                                |")
        for fline in self.flamegraph_ascii.splitlines()[:8]:
            lines.append(f"| {fline:<68} |")
        lines.append("+======================================================================+")
        return "\n".join(lines)


class ExecutionProfiler:
    """
    Stage 102 Dynamic Execution Profiler & Flamegraph Tracer.
    Instruments sub-millisecond execution times, traces hot paths,
    builds CP1252-safe ASCII flamegraphs, and tracks p50/p95/p99 latency regressions.
    """

    def __init__(
        self,
        project_root: Optional[Union[str, Path]] = None,
        runtime: Optional[Any] = None,
        receipt_ledger: Optional[Any] = None,
        data_dir: Optional[Union[str, Path]] = None,
        history_limit: int = 100,
    ) -> None:
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parent.parent.parent
        self.runtime = runtime
        self.receipt_ledger = receipt_ledger
        self.data_dir = Path(data_dir) if data_dir else (self.project_root / "data" / "lucy" / "profiler")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_limit = history_limit

        self._profile_runs: List[ProfileRunResult] = []
        self._latency_samples: List[Dict[str, Any]] = []
        self._runs_file = self.data_dir / "profiler_runs.json"
        self._latency_file = self.data_dir / "latency_samples.json"

        self._load_history()

    @contextmanager
    def profile_scope(self, scope_name: str) -> Generator[Dict[str, Any], None, None]:
        """
        Context manager to profile a specific code block using cProfile.
        Yields a dict that will be populated with summary metrics upon exit.
        """
        profiler = cProfile.Profile()
        meta: Dict[str, Any] = {"scope": scope_name, "completed": False}
        t0 = time.perf_counter_ns()
        profiler.enable()
        try:
            yield meta
        finally:
            profiler.disable()
            elapsed_ns = time.perf_counter_ns() - t0
            elapsed_ms = elapsed_ns / 1_000_000.0

            result = self._process_cprofile_data(profiler, scope_name, elapsed_ms)
            self._record_run(result)
            self.record_latency(scope_name, elapsed_ms)

            meta["completed"] = True
            meta["wall_time_ms"] = elapsed_ms
            meta["result"] = result

    def profile_callable(self, func: Callable, *args: Any, **kwargs: Any) -> Tuple[Any, ProfileRunResult]:
        """Runs a callable under the profiler and returns (return_value, ProfileRunResult)."""
        target_name = getattr(func, "__qualname__", getattr(func, "__name__", "callable"))
        with self.profile_scope(target_name) as meta:
            retval = func(*args, **kwargs)
        return retval, meta["result"]

    def record_latency(self, operation: str, duration_ms: float) -> Dict[str, Any]:
        """Records a single operation latency sample and detects sudden latency spikes."""
        now_iso = datetime.now(timezone.utc).isoformat()
        sample = {
            "operation": operation,
            "duration_ms": round(duration_ms, 3),
            "timestamp": now_iso,
        }

        # Check for latency spike against prior baseline (> 2.5x of rolling p95 or > 250ms)
        regression = self.detect_latency_regression(operation, duration_ms)
        if regression:
            self._record_receipt(
                "PROFILER_REGRESSION_ALERT",
                "latency_spike_detected",
                operation,
                f"duration={duration_ms:.2f}ms, p95={regression['p95']:.2f}ms, ratio={regression['ratio']:.2f}x",
            )

        self._latency_samples.append(sample)
        if len(self._latency_samples) > self.history_limit:
            self._latency_samples = self._latency_samples[-self.history_limit:]

        self._save_latency_samples()

        return sample

    def get_latency_percentiles(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Calculates min, mean, p50, p95, p99, and max latencies from recorded samples."""
        samples = self._latency_samples
        if operation:
            samples = [s for s in samples if s["operation"] == operation]

        if not samples:
            return {
                "operation": operation or "all",
                "count": 0,
                "min_ms": 0.0,
                "mean_ms": 0.0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
                "max_ms": 0.0,
            }

        durations = sorted([s["duration_ms"] for s in samples])
        cnt = len(durations)

        def _p(pct: float) -> float:
            idx = int(round((pct / 100.0) * (cnt - 1)))
            return durations[min(idx, cnt - 1)]

        return {
            "operation": operation or "all",
            "count": cnt,
            "min_ms": round(durations[0], 3),
            "mean_ms": round(sum(durations) / cnt, 3),
            "p50_ms": round(_p(50), 3),
            "p95_ms": round(_p(95), 3),
            "p99_ms": round(_p(99), 3),
            "max_ms": round(durations[-1], 3),
        }

    def detect_latency_regression(
        self,
        operation: str,
        duration_ms: float,
        multiplier: float = 2.5,
    ) -> Optional[Dict[str, Any]]:
        """Flags whether current duration is a regression compared to p95 historical baseline."""
        matching = [s["duration_ms"] for s in self._latency_samples if s["operation"] == operation]
        if len(matching) < 5:
            return None

        sorted_d = sorted(matching)
        p95_idx = int(round(0.95 * (len(sorted_d) - 1)))
        p95_val = max(1.0, sorted_d[p95_idx])

        if duration_ms > (p95_val * multiplier) and duration_ms > 20.0:
            return {
                "operation": operation,
                "current_ms": round(duration_ms, 3),
                "p95": round(p95_val, 3),
                "ratio": round(duration_ms / p95_val, 2),
                "threshold_multiplier": multiplier,
            }
        return None

    def get_latest_flamegraph(self) -> str:
        """Returns the flamegraph ASCII visualization from the most recent profile run."""
        if self._profile_runs:
            return self._profile_runs[-1].flamegraph_ascii
        return "[No profiler runs recorded yet. Execute /profile-run to generate trace.]"

    def get_hot_paths_table(self, top_n: int = 8) -> str:
        """Renders CP1252-safe ASCII table of the top hot execution paths."""
        if not self._profile_runs:
            return "[No profile runs recorded. Run a command under /profile-run first.]"

        run = self._profile_runs[-1]
        lines: List[str] = [
            "+======================================================================+",
            f"| LATEST PROFILE HOT PATHS: {run.target[:40]:<42} |",
            "+======================================================================+",
            "| Method / Function           | Calls    | Cumul (ms) | Per-Call | % Tot|",
            "+-----------------------------+----------+------------+----------+------+",
        ]
        for p in run.top_hot_paths[:top_n]:
            m_name = p.name[:27]
            calls = str(p.call_count)[:8]
            cum = f"{p.cumulative_time_ms:.2f}"[:10]
            per = f"{p.time_per_call_us:.1f}us"[:8]
            pct = f"{p.pct_of_total:.1f}%"[:5]
            lines.append(f"| {m_name:<27} | {calls:<8} | {cum:<10} | {per:<8} |{pct:>5} |")
        lines.append("+======================================================================+")
        return "\n".join(lines)

    def get_latency_audit_report(self) -> str:
        """Renders CP1252-safe ASCII table summarizing latency distributions."""
        p_all = self.get_latency_percentiles()
        lines: List[str] = [
            "+======================================================================+",
            "|                 LUCY OS - LATENCY PERCENTILES AUDIT                  |",
            "|              STAGE 102: ROLLING EXECUTION TIME METRICS               |",
            "+======================================================================+",
            f"| Total Samples: {p_all['count']:<8} | Mean:   {p_all['mean_ms']:>6.2f} ms | Min:     {p_all['min_ms']:>6.2f} ms |",
            f"| Median (p50):  {p_all['p50_ms']:>6.2f} ms | p95:    {p_all['p95_ms']:>6.2f} ms | p99:     {p_all['p99_ms']:>6.2f} ms |",
            f"| Peak Latency:  {p_all['max_ms']:>6.2f} ms | Policy: ZERO_CLOUD   | SLA:     <50.0 ms (p95)|",
            "+======================================================================+",
        ]
        return "\n".join(lines)

    def status(self) -> Dict[str, Any]:
        """Returns structured diagnostic status dictionary."""
        p_all = self.get_latency_percentiles()
        return {
            "stage": STAGE,
            "creator": CREATOR_NAME,
            "creator_full_name": CREATOR_FULL_NAME,
            "total_profile_runs": len(self._profile_runs),
            "total_latency_samples": len(self._latency_samples),
            "latest_run": self._profile_runs[-1].to_dict() if self._profile_runs else None,
            "latency_percentiles": p_all,
        }

    # --- Internal Helpers ---

    def _process_cprofile_data(
        self,
        profiler: cProfile.Profile,
        target: str,
        total_wall_ms: float,
    ) -> ProfileRunResult:
        """Parses pstats from cProfile, extracts hot paths, and renders ASCII flamegraph."""
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats("cumulative")

        entries: List[FunctionProfileEntry] = []
        flame_items: List[Tuple[str, float, float]] = []

        total_cum_ms = max(0.001, total_wall_ms)
        func_calls = 0

        # Parse stats dict: (filename, lineno, func_name) -> (cc, nc, tt, ct, callers)
        for (fpath, lno, func_name), (cc, nc, tt, ct, callers) in stats.stats.items():
            func_calls += cc
            ct_ms = ct * 1000.0
            tt_ms = tt * 1000.0
            per_call_us = (ct_ms / max(1, cc)) * 1000.0
            pct = min(100.0, (ct_ms / total_cum_ms) * 100.0)

            # Clean function name representation
            base_file = Path(fpath).name if fpath else "~"
            clean_name = f"{func_name} ({base_file}:{lno})" if lno > 0 else func_name

            entries.append(
                FunctionProfileEntry(
                    name=clean_name,
                    filename=base_file,
                    lineno=lno,
                    call_count=cc,
                    total_time_ms=round(tt_ms, 3),
                    cumulative_time_ms=round(ct_ms, 3),
                    time_per_call_us=round(per_call_us, 2),
                    pct_of_total=round(pct, 2),
                )
            )

            # Keep top candidates for flamegraph
            if pct >= 2.0:
                flame_items.append((func_name[:24], ct_ms, pct))

        entries.sort(key=lambda x: x.cumulative_time_ms, reverse=True)

        # Generate CP1252-safe ASCII flamegraph
        flamegraph_ascii = self._build_flamegraph_ascii(target, flame_items[:8], total_wall_ms)

        run_id = f"prf_{int(time.time() * 1000) % 10000000:07d}"
        now_iso = datetime.now(timezone.utc).isoformat()

        return ProfileRunResult(
            run_id=run_id,
            target=target,
            timestamp=now_iso,
            total_wall_time_ms=total_wall_ms,
            total_function_calls=func_calls,
            top_hot_paths=entries[:12],
            flamegraph_ascii=flamegraph_ascii,
        )

    def _build_flamegraph_ascii(
        self,
        root_name: str,
        items: List[Tuple[str, float, float]],
        total_ms: float,
    ) -> str:
        """Constructs an ASCII flamegraph visual hierarchy using CP1252-safe block meters."""
        lines: List[str] = []
        bar_len = 32

        # Root entry
        lines.append(f"[{'=' * bar_len}] 100.0% Root: {root_name[:28]} ({total_ms:.2f}ms)")

        for name, ct_ms, pct in items:
            filled = int(round((pct / 100.0) * bar_len))
            filled = max(1, min(bar_len, filled))
            empty = bar_len - filled
            bar_str = "=" * filled + " " * empty
            lines.append(f"  [{bar_str}] {pct:>5.1f}% -> {name:<24} ({ct_ms:.2f}ms)")

        if not items:
            lines.append(f"  [{'=' * bar_len}] 100.0% -> Executed inline (<0.1ms)")

        return "\n".join(lines)

    def _record_run(self, result: ProfileRunResult) -> None:
        self._profile_runs.append(result)
        if len(self._profile_runs) > self.history_limit:
            self._profile_runs = self._profile_runs[-self.history_limit:]

        self._record_receipt(
            "PROFILER_RUN",
            "profile_scope",
            result.target,
            f"wall_time={result.total_wall_time_ms:.2f}ms, calls={result.total_function_calls}, run_id={result.run_id}",
        )
        self._save_runs()

    def _record_receipt(
        self,
        action_category: str,
        operation: str,
        target: str,
        verified_outcome: str,
    ) -> Optional[Dict[str, Any]]:
        ledger = self.receipt_ledger or (getattr(self.runtime, "receipt_ledger", None) if self.runtime else None)
        if ledger:
            try:
                if hasattr(ledger, "issue_receipt"):
                    return ledger.issue_receipt(action_category, operation, target, verified_outcome)
                elif hasattr(ledger, "record_receipt"):
                    return ledger.record_receipt(action_category, operation, target, verified_outcome)
            except Exception:
                pass
        return None

    def _save_runs(self) -> None:
        try:
            data = [r.to_dict() for r in self._profile_runs[-20:]]
            self._runs_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _save_latency_samples(self) -> None:
        try:
            self._latency_file.write_text(json.dumps(self._latency_samples[-50:], indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_history(self) -> None:
        if self._latency_file.exists():
            try:
                self._latency_samples = json.loads(self._latency_file.read_text(encoding="utf-8"))
            except Exception:
                self._latency_samples = []
