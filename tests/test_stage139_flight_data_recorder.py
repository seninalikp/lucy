r"""
tests/test_stage139_flight_data_recorder.py
Unit tests for Stage 139: Deterministic Replay & Flight-Data Recorder.
Era 14: Autonomous Code Evolution, Semantic Mutation & Static Synthesis
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.flight_data_recorder import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    FlightDataRecorder,
    FlightEvent,
    FlightRecording,
    ReplayDiff,
)


class TestStage139FlightDataRecorder(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.recorder = FlightDataRecorder(project_root=self.test_dir, max_buffer_events=10)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_metadata_and_initialization(self):
        self.assertEqual(STAGE, 139)
        self.assertEqual(ERA, 14)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")

        st = self.recorder.status()
        self.assertEqual(st["stage"], 139)
        self.assertEqual(st["status"], "RECORDING_ACTIVE")
        self.assertGreaterEqual(st["total_recorded_events"], 1)  # Boot event
        self.assertEqual(self.recorder.event_buffer[0].event_type, "BOOT_CHECKPOINT")

    def test_02_record_flight_event(self):
        ev = self.recorder.record_event("COMMAND_EXEC", "router", {"cmd": "/ping", "user": "Senin"})
        self.assertEqual(ev.event_type, "COMMAND_EXEC")
        self.assertEqual(ev.subsystem, "router")
        self.assertGreater(ev.timestamp_ns, 0)
        self.assertEqual(len(ev.state_hash), 64)

    def test_03_take_snapshot(self):
        snap = self.recorder.take_snapshot(label="test_checkpoint_alpha")
        self.assertEqual(snap.event_type, "STATE_SNAPSHOT")
        self.assertEqual(snap.payload["label"], "test_checkpoint_alpha")
        self.assertEqual(snap.payload["operator"], "Senin Ali K P")

    def test_04_flush_and_persist_recording(self):
        for i in range(3):
            self.recorder.record_event("MUTATION_TRACE", "ast_operator", {"iter": i})

        rec = self.recorder.flush_flight_recording()
        self.assertGreaterEqual(rec.events_count, 3)
        self.assertEqual(len(rec.merkle_root), 64)
        self.assertEqual(len(rec.hmac_signature), 64)

        fpath = Path(self.test_dir) / "data" / "lucy" / "blackbox" / f"{rec.flight_id}.json"
        self.assertTrue(fpath.exists())

    def test_05_load_recording(self):
        self.recorder.record_event("TEST_EVENT", "kernel", {"val": 123})
        rec = self.recorder.flush_flight_recording()

        loaded = self.recorder.load_recording(rec.flight_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.flight_id, rec.flight_id)
        self.assertEqual(loaded.events_count, rec.events_count)

    def test_06_deterministic_replay_pass(self):
        for i in range(4):
            self.recorder.record_event("REPLAY_TEST", "executor", {"step": i})

        rec = self.recorder.flush_flight_recording()
        diff = self.recorder.replay_flight(rec)
        self.assertTrue(diff.is_deterministic)
        self.assertEqual(len(diff.divergent_events), 0)
        self.assertGreater(diff.total_events_checked, 0)

    def test_07_tamper_detection_in_replay(self):
        self.recorder.record_event("SENSITIVE_OP", "vault", {"key": "secret"})
        rec = self.recorder.flush_flight_recording()

        # Tamper with recorded JSON on disk
        fpath = Path(self.test_dir) / "data" / "lucy" / "blackbox" / f"{rec.flight_id}.json"
        data = json.loads(fpath.read_text(encoding="utf-8"))
        data["events"][-1]["payload"]["key"] = "tampered_value"
        fpath.write_text(json.dumps(data), encoding="utf-8")

        diff = self.recorder.replay_flight(rec.flight_id)
        self.assertFalse(diff.is_deterministic)
        self.assertGreaterEqual(len(diff.divergent_events), 1)

    def test_08_buffer_auto_flush_threshold(self):
        # Buffer limit set to 10 in setUp
        current_id = self.recorder.current_flight_id
        for i in range(15):
            self.recorder.record_event("OVERFLOW_TEST", "buffer", {"index": i})

        # Buffer should have auto-flushed at least once
        persisted = list((Path(self.test_dir) / "data" / "lucy" / "blackbox").glob("FLIGHT-*.json"))
        self.assertGreaterEqual(len(persisted), 1)

    def test_09_list_persisted_recordings(self):
        self.recorder.record_event("REC_1", "sys", {})
        self.recorder.flush_flight_recording()

        self.recorder.record_event("REC_2", "sys", {})
        self.recorder.flush_flight_recording()

        recs = self.recorder.list_recordings()
        self.assertGreaterEqual(len(recs), 2)
        self.assertIn("flight_id", recs[0])
        self.assertIn("merkle_root", recs[0])

    def test_10_ascii_status_and_replay_tables(self):
        stat_table = self.recorder.format_flight_status_table()
        self.assertIn("+=============================================================================+", stat_table)
        self.assertIn("LUCY FLIGHT DATA RECORDER & DETERMINISTIC REPLAY [STAGE 139 | ERA 14]", stat_table)
        self.assertIn("Senin Ali K P", stat_table)

        self.recorder.record_event("EVT", "mod", {})
        rec = self.recorder.flush_flight_recording()
        diff = self.recorder.replay_flight(rec)
        diff_table = self.recorder.format_replay_diff_table(diff)
        self.assertIn("FLIGHT REPLAY VERIFICATION:", diff_table)
        self.assertIn("DETERMINISTIC_PASS", diff_table)


if __name__ == "__main__":
    unittest.main()
