r"""
tests/test_stage118_thermal_governor.py
Comprehensive test suite for Stage 118: Thermal & Compute Governor
Era 12: The Autonomous Cognitive Matrix & Distributed IPC Fabric
"""

import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.thermal_governor import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    STAGE,
    GovernorMetrics,
    GovernorMode,
    ThermalComputeGovernor,
    TripwireConfig,
)


class MockReceiptLedger:
    def __init__(self) -> None:
        self.receipts = []

    def record_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        rcpt = {
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self.receipts.append(rcpt)
        return rcpt


class TestStage118ThermalGovernor(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.data_dir = self.root / "data" / "governor"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.receipt_ledger = MockReceiptLedger()

        self.governor = ThermalComputeGovernor(
            project_root=self.root,
            data_dir=self.data_dir,
            receipt_ledger=self.receipt_ledger,
            initial_mode=GovernorMode.BALANCED,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_initialization(self) -> None:
        st = self.governor.status()
        self.assertEqual(st["stage"], 118)
        self.assertEqual(st["era"], 12)
        self.assertEqual(st["creator"], CREATOR_NAME)
        self.assertEqual(st["creator_full_name"], CREATOR_FULL_NAME)
        self.assertEqual(st["mode"], "BALANCED")
        self.assertGreaterEqual(st["cpu_cores"], 1)

    def test_02_metrics_sampling(self) -> None:
        m = self.governor.get_metrics()
        self.assertIsInstance(m, GovernorMetrics)
        self.assertGreater(m.ram_total_gb, 0.0)
        self.assertGreater(m.ram_avail_gb, 0.0)
        self.assertTrue(0.0 <= m.ram_used_pct <= 100.0)
        self.assertTrue(0.0 <= m.cpu_load_pct <= 100.0)
        self.assertGreater(m.thermal_estimated_c, 20.0)

    def test_03_operating_mode_transitions(self) -> None:
        # ECO mode
        ok = self.governor.set_mode("eco")
        self.assertTrue(ok)
        self.assertEqual(self.governor.mode, GovernorMode.ECO)

        # TURBO mode
        ok = self.governor.set_mode("turbo")
        self.assertTrue(ok)
        self.assertEqual(self.governor.mode, GovernorMode.TURBO)

        # BALANCED mode
        ok = self.governor.set_mode("balanced")
        self.assertTrue(ok)
        self.assertEqual(self.governor.mode, GovernorMode.BALANCED)

    def test_04_worker_allocation_by_mode(self) -> None:
        self.governor.set_mode("eco")
        w_eco = self.governor.allocate_workers("general")

        self.governor.set_mode("turbo")
        w_turbo = self.governor.allocate_workers("general")

        self.assertLessEqual(w_eco, w_turbo)
        self.assertGreaterEqual(w_eco, 1)

    def test_05_manual_cooldown_trigger(self) -> None:
        self.governor.trigger_cooldown(duration_sec=10.0)
        self.assertEqual(self.governor.mode, GovernorMode.THROTTLED)
        self.assertEqual(self.governor.allocate_workers(), 1)

        m = self.governor.get_metrics()
        self.assertTrue(m.is_throttled)

    def test_06_cooldown_expiration(self) -> None:
        self.governor.set_mode("balanced")
        self.governor.trigger_cooldown(duration_sec=0.1)
        self.assertEqual(self.governor.mode, GovernorMode.THROTTLED)

        time.sleep(0.15)
        m = self.governor.get_metrics()
        self.assertFalse(m.is_throttled)
        self.assertEqual(m.operating_mode, GovernorMode.BALANCED)

    def test_07_automatic_thermal_tripwire(self) -> None:
        # Lower critical tripwire below ambient
        self.governor.tripwires.temp_critical_c = 25.0
        m = self.governor.get_metrics()
        self.assertTrue(m.is_throttled)
        self.assertEqual(m.operating_mode, GovernorMode.THROTTLED)

    def test_08_invalid_mode_handling(self) -> None:
        ok = self.governor.set_mode("SUPER_QUANTUM_OVERDRIVE")
        self.assertFalse(ok)
        self.assertEqual(self.governor.mode, GovernorMode.BALANCED)

    def test_09_receipt_ledger_integration(self) -> None:
        self.governor.set_mode("turbo")
        self.governor.trigger_cooldown(0.1)

        cats = [r["action_category"] for r in self.receipt_ledger.receipts]
        self.assertIn("THERMAL_MODE_CHANGED", cats)
        self.assertIn("THERMAL_THROTTLE_TRIGGERED", cats)

    def test_10_ascii_status_table_formatting(self) -> None:
        tbl = self.governor.format_governor_status_table()

        self.assertIn("LUCY OS - THERMAL & COMPUTE GOVERNOR", tbl)
        self.assertIn("Active Operating Mode", tbl)
        self.assertIn(CREATOR_NAME, tbl)
        self.assertIn(CREATOR_FULL_NAME, tbl)
        self.assertTrue(tbl.startswith("+--"))


if __name__ == "__main__":
    unittest.main()
