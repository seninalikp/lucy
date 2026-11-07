r"""
tests/test_stage197_global_chrono_log.py
Stage 197: Autonomous Global Chrono-Log & Event Sourcing Fabric
Era 20: The Sovereign Bicentennial AGI Singularity & Autonomous Kernel Transcendence
"""

import unittest
from backend.lucy_core.global_chrono_log import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    HybridTimestamp,
    ChronoEvent,
    StreamSnapshot,
    GlobalChronoLogFabric,
)


class TestStage197GlobalChronoLog(unittest.TestCase):
    """10 Unit Tests for Stage 197 Global Chrono-Log & Event Sourcing Fabric."""

    def setUp(self):
        self.fabric = GlobalChronoLogFabric(node_id="test_chrono_node")

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric.node_id, "test_chrono_node")
        self.assertEqual(len(self.fabric.events), 0)
        self.assertEqual(len(self.fabric.streams), 0)
        self.assertTrue(self.fabric._last_checksum.startswith("GENESIS_CHRONO"))

    def test_02_hlc_monotonicity(self):
        t1 = self.fabric._get_hlc()
        t2 = self.fabric._get_hlc()
        t3 = self.fabric._get_hlc()
        self.assertLess(t1, t2)
        self.assertLess(t2, t3)

    def test_03_append_event_and_hash_chain(self):
        ev1 = self.fabric.append_event("stream_1", "SET", {"sovereign": "Senin"})
        self.assertEqual(ev1.global_seq, 1)
        self.assertTrue(ev1.prev_checksum.startswith("GENESIS_CHRONO"))

        ev2 = self.fabric.append_event("stream_1", "INCREMENT", {"key": "counter", "amount": 5})
        self.assertEqual(ev2.global_seq, 2)
        self.assertEqual(ev2.prev_checksum, ev1.checksum)

    def test_04_verify_ledger_integrity_pass(self):
        for i in range(10):
            self.fabric.append_event("stream_alpha", "SET", {"index": i})
        ok, count = self.fabric.verify_ledger_integrity()
        self.assertTrue(ok)
        self.assertEqual(count, 10)

    def test_05_verify_ledger_integrity_detects_tampering(self):
        for i in range(5):
            self.fabric.append_event("stream_sec", "SET", {"val": i})

        # Artificially tamper with event 3 payload
        self.fabric.events[2].payload["val"] = 99999
        ok, failed_seq = self.fabric.verify_ledger_integrity()
        self.assertFalse(ok)
        self.assertEqual(failed_seq, 3)

    def test_06_time_travel_replay_state_mutations(self):
        s_id = "user_account_0"
        self.fabric.append_event(s_id, "SET", {"name": "Senin Ali K P", "role": "Creator"})
        self.fabric.append_event(s_id, "INCREMENT", {"key": "balance", "amount": 100})
        self.fabric.append_event(s_id, "INCREMENT", {"key": "balance", "amount": 50})
        self.fabric.append_event(s_id, "DELETE", {"keys": ["role"]})

        state = self.fabric.time_travel_replay(s_id)
        self.assertEqual(state.get("name"), "Senin Ali K P")
        self.assertEqual(state.get("balance"), 150)
        self.assertNotIn("role", state)

    def test_07_time_travel_point_in_time_query(self):
        s_id = "stock_stream"
        e1 = self.fabric.append_event(s_id, "SET", {"price": 10.0})
        e2 = self.fabric.append_event(s_id, "SET", {"price": 20.0})
        e3 = self.fabric.append_event(s_id, "SET", {"price": 30.0})

        # Query up to e2 (seq 2)
        past_state = self.fabric.time_travel_replay(s_id, target_seq=2)
        self.assertEqual(past_state.get("price"), 20.0)

        # Query up to e1 timestamp
        t1_state = self.fabric.time_travel_replay(s_id, target_hlc=e1.hlc)
        self.assertEqual(t1_state.get("price"), 10.0)

    def test_08_snapshot_creation_and_fast_replay(self):
        s_id = "snap_stream"
        for i in range(5):
            self.fabric.append_event(s_id, "INCREMENT", {"key": "total", "amount": 10})

        snap = self.fabric.create_snapshot(s_id)
        self.assertEqual(snap.state.get("total"), 50)
        self.assertEqual(snap.up_to_seq, 5)

        # Append more events after snapshot
        self.fabric.append_event(s_id, "INCREMENT", {"key": "total", "amount": 25})
        replayed_state = self.fabric.time_travel_replay(s_id)
        self.assertEqual(replayed_state.get("total"), 75)

    def test_09_multiple_independent_streams(self):
        self.fabric.append_event("stream_A", "SET", {"owner": "Senin"})
        self.fabric.append_event("stream_B", "SET", {"target": "Stage 200"})

        state_A = self.fabric.time_travel_replay("stream_A")
        state_B = self.fabric.time_travel_replay("stream_B")

        self.assertEqual(state_A, {"owner": "Senin"})
        self.assertEqual(state_B, {"target": "Stage 200"})

    def test_10_ascii_status_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 197)
        self.assertEqual(s["era"], 20)
        self.assertEqual(s["node_id"], "test_chrono_node")

        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 197: AUTONOMOUS GLOBAL CHRONO-LOG & EVENT SOURCING", ascii_out)
        self.assertIn("Chrono Node ID        : test_chrono_node", ascii_out)


if __name__ == "__main__":
    unittest.main()
