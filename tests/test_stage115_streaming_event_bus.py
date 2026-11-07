r"""
tests/test_stage115_streaming_event_bus.py
Comprehensive test suite for Stage 115: Sovereign IPC Event Bus
Era 12: The Autonomous Cognitive Matrix & Distributed IPC Fabric
"""

import json
import socket
import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.streaming_event_bus import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    STAGE,
    IPCEvent,
    MmapRingBuffer,
    SovereignIPCEventBus,
    _compile_topic_pattern,
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


class TestStage115StreamingEventBus(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.data_dir = self.root / "data" / "ipc"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.receipt_ledger = MockReceiptLedger()

        self.bus = SovereignIPCEventBus(
            project_root=self.root,
            data_dir=self.data_dir,
            receipt_ledger=self.receipt_ledger,
            shm_size=16384,
        )

    def tearDown(self) -> None:
        self.bus.close()
        self.temp_dir.cleanup()

    def test_01_initialization(self) -> None:
        st = self.bus.status()
        self.assertEqual(st["stage"], 115)
        self.assertEqual(st["era"], 12)
        self.assertEqual(st["creator"], CREATOR_NAME)
        self.assertEqual(st["creator_full_name"], CREATOR_FULL_NAME)
        self.assertTrue(st["shm_active"])
        self.assertGreater(st["loopback_port"], 0)

    def test_02_publish_and_exact_subscriber(self) -> None:
        received = []
        sub_id = self.bus.subscribe("workspace.file_created", lambda evt: received.append(evt))
        self.assertIsNotNone(sub_id)

        evt = self.bus.publish("workspace.file_created", {"file": "core.py"}, source="sensor")
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].topic, "workspace.file_created")
        self.assertEqual(received[0].payload["file"], "core.py")

    def test_03_single_level_wildcard(self) -> None:
        events = []
        self.bus.subscribe("telemetry.*", lambda e: events.append(e.topic))

        self.bus.publish("telemetry.cpu", {"usage": 40})
        self.bus.publish("telemetry.gpu", {"usage": 15})
        self.bus.publish("telemetry.cpu.temp", {"val": 55})  # Should NOT match single level

        self.assertIn("telemetry.cpu", events)
        self.assertIn("telemetry.gpu", events)
        self.assertNotIn("telemetry.cpu.temp", events)

    def test_04_multi_level_wildcard(self) -> None:
        events = []
        self.bus.subscribe("pipeline.#", lambda e: events.append(e.topic))

        self.bus.publish("pipeline.start", {})
        self.bus.publish("pipeline.step.complete.synthesizer", {"ok": True})
        self.bus.publish("workspace.delta", {})

        self.assertIn("pipeline.start", events)
        self.assertIn("pipeline.step.complete.synthesizer", events)
        self.assertNotIn("workspace.delta", events)

    def test_05_unsubscribe(self) -> None:
        events = []
        sub_id = self.bus.subscribe("chat.message", lambda e: events.append(e))

        self.bus.publish("chat.message", {"msg": "hello"})
        self.assertEqual(len(events), 1)

        ok = self.bus.unsubscribe(sub_id)
        self.assertTrue(ok)

        self.bus.publish("chat.message", {"msg": "world"})
        self.assertEqual(len(events), 1)  # No new event received

    def test_06_tail_events(self) -> None:
        for i in range(5):
            self.bus.publish(f"log.item.{i}", {"idx": i})

        tailed = self.bus.tail("log.#", limit=3)
        self.assertEqual(len(tailed), 3)
        self.assertEqual(tailed[-1].payload["idx"], 4)

    def test_07_mmap_ring_buffer_write(self) -> None:
        shm_file = self.data_dir / "shm_test.bin"
        ring = MmapRingBuffer(shm_file, size=8192)
        written = ring.write_event(b"Test binary event chunk")
        self.assertGreater(written, 0)
        self.assertIsNotNone(ring.read_latest())
        ring.close()

    def test_08_loopback_socket_client(self) -> None:
        port = self.bus._server_port
        self.assertGreater(port, 0)

        # Connect loopback socket client
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", port))
        req = json.dumps({"command": "publish", "topic": "external.cli", "payload": {"status": "ok"}})
        s.sendall(req.encode("utf-8"))

        raw = s.recv(1024).decode("utf-8")
        s.close()

        resp = json.loads(raw)
        self.assertTrue(resp.get("ok"))
        self.assertIn("event_id", resp)

        tailed = self.bus.tail("external.cli", limit=1)
        self.assertEqual(len(tailed), 1)
        self.assertEqual(tailed[0].payload.get("status"), "ok")

    def test_09_journal_persistence(self) -> None:
        self.bus.publish("journal.test", {"data": "persisted"})
        self.assertTrue(self.bus.journal_file.exists())
        lines = self.bus.journal_file.read_text(encoding="utf-8").splitlines()
        self.assertGreaterEqual(len(lines), 1)
        last_rec = json.loads(lines[-1])
        self.assertEqual(last_rec["topic"], "journal.test")

    def test_10_receipt_ledger_integration(self) -> None:
        self.bus.subscribe("receipt.topic", lambda e: None)
        self.bus.publish("receipt.topic", {"val": 1})

        cats = [r["action_category"] for r in self.receipt_ledger.receipts]
        self.assertIn("IPC_SUBSCRIPTION_REGISTERED", cats)
        self.assertIn("IPC_EVENT_PUBLISHED", cats)

    def test_11_ascii_status_table_formatting(self) -> None:
        self.bus.publish("status.test", {})
        tbl = self.bus.format_ipc_status_table()

        self.assertIn("LUCY OS - SOVEREIGN IPC EVENT BUS", tbl)
        self.assertIn("Memory-Mapped Ring Buffer", tbl)
        self.assertIn(CREATOR_NAME, tbl)
        self.assertIn(CREATOR_FULL_NAME, tbl)
        self.assertTrue(tbl.startswith("+--"))


if __name__ == "__main__":
    unittest.main()
