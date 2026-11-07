"""
tests/test_stage109_ambient_hud_overlay.py
Stage 109: Ambient HUD & Desktop Overlay Unit Tests
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.ambient_hud_overlay import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    DEFAULT_HOTKEY,
    STAGE,
    AmbientHUDOverlay,
    HUDState,
    NotificationLevel,
    TelemetrySnapshot,
    TrayNotification,
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


class TestStage109AmbientHUDOverlay(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lucy_stage109_test_")
        self.temp_path = Path(self.temp_dir)
        self.project_root = Path(__file__).resolve().parent.parent

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_constants_and_metadata(self):
        self.assertEqual(STAGE, 109)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        self.assertEqual(DEFAULT_HOTKEY, "Win+Alt+L")

    def test_02_hud_states(self):
        self.assertEqual(HUDState.HIDDEN.value, "HIDDEN")
        self.assertEqual(HUDState.VISIBLE.value, "VISIBLE")
        self.assertEqual(HUDState.MINIMIZED_TRAY.value, "MINIMIZED_TRAY")
        self.assertEqual(HUDState.ACTIVE_COMMAND.value, "ACTIVE_COMMAND")

    def test_03_telemetry_sampling(self):
        hud = AmbientHUDOverlay(
            project_root=self.project_root,
            data_dir=self.temp_path / "hud",
        )
        telem = hud.sample_telemetry()
        self.assertIsInstance(telem, TelemetrySnapshot)
        self.assertGreater(telem.ram_used_mb, 0.0)
        self.assertEqual(telem.current_stage, 109)
        self.assertGreaterEqual(telem.uptime_seconds, 0.0)

    def test_04_launch_and_toggle_hud(self):
        hud = AmbientHUDOverlay(
            project_root=self.project_root,
            data_dir=self.temp_path / "hud",
        )
        self.assertEqual(hud.current_state, HUDState.HIDDEN)

        bar = hud.launch_hud("floating")
        self.assertEqual(hud.current_state, HUDState.VISIBLE)
        self.assertIn("LUCY OS", bar)
        self.assertIn("VISIBLE", bar)

        toggle_res = hud.toggle_hud()
        self.assertEqual(hud.current_state, HUDState.HIDDEN)
        self.assertIn("HIDDEN", toggle_res)

        toggle_res2 = hud.toggle_hud()
        self.assertEqual(hud.current_state, HUDState.VISIBLE)
        self.assertIn("VISIBLE", toggle_res2)

    def test_05_tray_notifications(self):
        hud = AmbientHUDOverlay(
            project_root=self.project_root,
            data_dir=self.temp_path / "hud",
        )
        notif = hud.tray_notify(
            title="Kernel Alert",
            message="Zero-leak sandbox verified.",
            level=NotificationLevel.SUCCESS,
        )
        self.assertTrue(notif.notification_id.startswith("NOTIF-"))
        self.assertEqual(notif.title, "Kernel Alert")
        self.assertEqual(notif.level, NotificationLevel.SUCCESS)
        self.assertFalse(notif.read)

        st = hud.status()
        self.assertEqual(st["total_notifications"], 1)
        self.assertEqual(st["unread_notifications"], 1)

    def test_06_mark_notifications_read(self):
        hud = AmbientHUDOverlay(
            project_root=self.project_root,
            data_dir=self.temp_path / "hud",
        )
        hud.tray_notify("Test 1", "Msg 1")
        hud.tray_notify("Test 2", "Msg 2")
        self.assertEqual(hud.status()["unread_notifications"], 2)

        marked = hud.mark_notifications_read()
        self.assertEqual(marked, 2)
        self.assertEqual(hud.status()["unread_notifications"], 0)

    def test_07_hotkey_trigger(self):
        hud = AmbientHUDOverlay(
            project_root=self.project_root,
            data_dir=self.temp_path / "hud",
            hotkey="Win+Alt+L",
        )
        self.assertEqual(hud.current_state, HUDState.HIDDEN)
        res = hud.trigger_hotkey()
        self.assertEqual(hud.current_state, HUDState.VISIBLE)
        self.assertIn("LUCY OS", res)

        res2 = hud.trigger_hotkey()
        self.assertEqual(hud.current_state, HUDState.HIDDEN)
        self.assertIn("HIDDEN", res2)

    def test_08_receipt_ledger_emission(self):
        ledger = MockReceiptLedger()
        hud = AmbientHUDOverlay(
            project_root=self.project_root,
            data_dir=self.temp_path / "hud",
            receipt_ledger=ledger,
        )
        hud.launch_hud()
        self.assertGreaterEqual(len(ledger.receipts), 1)
        self.assertEqual(ledger.receipts[0]["category"], "HUD_INTERACTION_RECEIPT")

    def test_09_ascii_formatting(self):
        hud = AmbientHUDOverlay(
            project_root=self.project_root,
            data_dir=self.temp_path / "hud",
        )
        hud.launch_hud()
        bar = hud.format_hud_floating_bar()
        self.assertIn("+================================================================================+", bar)
        self.assertIn("LUCY OS [v2.0]", bar)
        self.assertIn("OPERATOR: Senin", bar)

        tbl = hud.format_hud_status_table()
        self.assertIn("+--------------------------------------------------------------------------------+", tbl)
        self.assertIn("AMBIENT HUD & DESKTOP OVERLAY STATUS", tbl)
        self.assertIn("Senin Ali K P", tbl)

    def test_10_status_dictionary(self):
        hud = AmbientHUDOverlay(
            project_root=self.project_root,
            data_dir=self.temp_path / "hud",
        )
        st = hud.status()
        self.assertEqual(st["stage"], 109)
        self.assertEqual(st["creator"], "Senin")
        self.assertEqual(st["creator_full_name"], "Senin Ali K P")
        self.assertEqual(st["hud_state"], "HIDDEN")
        self.assertIn("telemetry", st)


if __name__ == "__main__":
    unittest.main()
