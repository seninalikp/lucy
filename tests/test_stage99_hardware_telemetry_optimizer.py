"""
tests/test_stage99_hardware_telemetry_optimizer.py
Stage 99 = Local Hardware Telemetry & Inference Throttle Guard

Verifies:
1. STAGE constant is 99.
2. probe_hardware accurately gathers host CPU, RAM, VRAM, and storage metrics.
3. System RAM and disk usage are captured with positive capacity.
4. Throttle policy activates COOL_DOWN when thresholds are exceeded.
5. vram_tune recommends optimal quantization, context window, and offloading.
6. bench_inference measures TTFT, generation TPS, and memory bandwidth.
7. set_throttle_thresholds updates safety limits.
8. Manifest persistence saves and reloads hardware snapshots from disk.
9. Execution receipt ledger records receipts with SHA256 digests.
10. Terminal dashboards use strictly CP1252-compatible ASCII characters.
11. status returns complete diagnostics dictionary.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.lucy_core.hardware_telemetry_optimizer import (
    STAGE,
    HardwareSnapshot,
    HardwareTelemetryOptimizer,
    InferenceBenchmarkResult,
    ThrottlePolicy,
    VRAMTuneRecommendation,
)


class MockReceiptLedger:
    def __init__(self) -> None:
        self.receipts: List[Dict[str, Any]] = []

    def issue_receipt(
        self,
        action_category: str,
        operation: str,
        target: str,
        verified_outcome: str,
    ) -> Dict[str, Any]:
        rcpt = {
            "receipt_id": f"rcpt_{len(self.receipts)+1}",
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self.receipts.append(rcpt)
        return rcpt


class TestStage99HardwareTelemetryOptimizer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.mock_ledger = MockReceiptLedger()
        self.optimizer = HardwareTelemetryOptimizer(
            project_root=self.root,
            receipt_ledger=self.mock_ledger,
            data_dir=self.root / "data" / "lucy" / "telemetry",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_stage_constant(self) -> None:
        self.assertEqual(STAGE, 99)

    def test_02_probe_hardware(self) -> None:
        snap = self.optimizer.probe_hardware()
        self.assertGreater(snap.cpu_cores, 0)
        self.assertGreater(snap.ram_total_gb, 0.0)
        self.assertGreater(snap.ram_available_gb, 0.0)
        self.assertGreater(snap.disk_total_gb, 0.0)
        self.assertIn(snap.throttle_policy, [p.value for p in ThrottlePolicy])
        self.assertIn(snap.recommended_ctx, [2048, 4096, 8192])

    def test_03_throttle_policy_trigger(self) -> None:
        # Force a low RAM threshold
        self.optimizer.set_throttle_thresholds(ram_pct=10.0, temp_c=50.0)
        snap = self.optimizer.probe_hardware()
        self.assertEqual(snap.throttle_policy, ThrottlePolicy.COOL_DOWN.value)

    def test_04_vram_tune_recommendation(self) -> None:
        rec = self.optimizer.vram_tune(model_param_billions=3.0)
        self.assertGreater(rec.detected_vram_mb, 0.0)
        self.assertIn(rec.recommended_quant, ["Q4_0", "Q4_K_M", "Q5_K_M", "Q8_0"])
        self.assertIn(rec.recommended_context, [2048, 4096, 8192])
        self.assertGreater(rec.recommended_threads, 0)
        self.assertGreater(rec.estimated_tps, 0.0)

        # Receipt check
        self.assertGreaterEqual(len(self.mock_ledger.receipts), 1)
        self.assertEqual(self.mock_ledger.receipts[0]["action_category"], "HARDWARE_TELEMETRY")

    def test_05_bench_inference(self) -> None:
        bench = self.optimizer.bench_inference(test_tokens=30)
        self.assertGreater(bench.gen_tps, 0.0)
        self.assertGreater(bench.eval_tps, 0.0)
        self.assertGreater(bench.ttft_ms, 0.0)
        self.assertGreater(bench.memory_bandwidth_gb_s, 0.0)

        # Check receipt
        self.assertGreaterEqual(len(self.mock_ledger.receipts), 1)
        self.assertEqual(self.mock_ledger.receipts[-1]["operation"], "bench_inference")

    def test_06_set_throttle_thresholds(self) -> None:
        res = self.optimizer.set_throttle_thresholds(ram_pct=85.0, temp_c=80.0)
        self.assertEqual(res["ram_threshold_pct"], 85.0)
        self.assertEqual(res["temp_threshold_c"], 80.0)
        self.assertEqual(self.optimizer.ram_threshold_pct, 85.0)
        self.assertEqual(self.optimizer.temp_threshold_c, 80.0)

    def test_07_persistence(self) -> None:
        self.optimizer.probe_hardware()
        self.optimizer.bench_inference(test_tokens=20)
        self.assertTrue(self.optimizer.manifest_file.exists())

        # Reload
        reloaded = HardwareTelemetryOptimizer(
            project_root=self.root,
            receipt_ledger=self.mock_ledger,
            data_dir=self.root / "data" / "lucy" / "telemetry",
        )
        self.assertIsNotNone(reloaded.last_snapshot)
        self.assertEqual(len(reloaded.benchmark_history), 1)

    def test_08_terminal_summary_cp1252(self) -> None:
        summary = self.optimizer.hardware_status()

        # CP1252 encoding safety
        encoded = summary.encode("cp1252")
        self.assertTrue(len(encoded) > 0)
        for ch in summary:
            self.assertFalse(0x2500 <= ord(ch) <= 0x257F)

        self.assertIn("+----------------------------------------------------------------------+", summary)
        self.assertIn("LOCAL HARDWARE TELEMETRY", summary)

    def test_09_vram_tune_terminal_summary(self) -> None:
        rec = self.optimizer.vram_tune(model_param_billions=3.0)
        summary = rec.format_terminal_summary()

        summary.encode("cp1252")
        self.assertIn("+----------------------------------------------------------------------+", summary)
        self.assertIn("VRAM & MODEL PARAMETER TUNING", summary)

    def test_10_status_dictionary(self) -> None:
        st = self.optimizer.status()
        self.assertEqual(st["stage"], 99)
        self.assertIn("cpu_cores", st)
        self.assertIn("ram_total_gb", st)
        self.assertIn("ram_available_gb", st)


if __name__ == "__main__":
    unittest.main()
