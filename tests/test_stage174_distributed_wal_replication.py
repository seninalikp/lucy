r"""
tests/test_stage174_distributed_wal_replication.py
Stage 174 Test Suite: Distributed Write-Ahead Log (WAL) Segment Replication
Era 18: Autonomous Distributed Storage, Geo-Replication & Sharding Primitives
"""

import time
import unittest

from backend.lucy_core.distributed_wal_replication import (
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    DistributedWALManager,
    LogRecordType,
    WALRecord,
    WALReplica,
    WALSegment,
    get_distributed_wal_manager,
)


class TestStage174DistributedWALReplication(unittest.TestCase):
    def setUp(self) -> None:
        self.wal_mgr = DistributedWALManager(node_id="wal_leader_0", max_segment_records=8, quorum_size=2)

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 174)
        self.assertEqual(ERA, 18)
        self.assertEqual(
            STAGE_NAME,
            "Distributed Write-Ahead Log (WAL) Segment Replication",
        )
        self.assertEqual(
            ERA_NAME,
            "Autonomous Distributed Storage, Geo-Replication & Sharding Primitives",
        )
        self.assertEqual(self.wal_mgr.max_segment_records, 8)
        self.assertEqual(self.wal_mgr.quorum_size, 2)

    def test_02_crc32_integrity_validation(self) -> None:
        rec = WALRecord(
            lsn=1,
            tx_id="tx_100",
            record_type=LogRecordType.PUT,
            key="config/active",
            value={"val": 42},
            timestamp=1000.0,
        )
        rec.crc32 = rec.compute_crc()
        self.assertTrue(rec.verify_crc())

        # Tampering with payload fails CRC validation
        rec.key = "config/corrupted"
        self.assertFalse(rec.verify_crc())

    def test_03_segment_append_and_rotation(self) -> None:
        self.assertEqual(len(self.wal_mgr._segments), 1)

        # Write 8 records (max_segment_records = 8)
        for i in range(8):
            ok, rec = self.wal_mgr.append_log(f"tx_{i}", LogRecordType.PUT, f"k_{i}", f"v_{i}")
            self.assertTrue(ok)

        # First segment should be sealed
        self.assertTrue(self.wal_mgr._segments[0].is_sealed)
        self.assertEqual(len(self.wal_mgr._segments[0].records), 8)

        # 9th record should trigger rotation to segment 1
        ok, rec9 = self.wal_mgr.append_log("tx_8", LogRecordType.PUT, "k_8", "v_8")
        self.assertTrue(ok)
        self.assertEqual(len(self.wal_mgr._segments), 2)
        self.assertEqual(self.wal_mgr._segments[1].start_lsn, 9)

    def test_04_quorum_replication_and_hwm(self) -> None:
        ok, rec = self.wal_mgr.append_log("tx_init", LogRecordType.PUT, "sys_mode", "sovereign")
        self.assertTrue(ok)
        self.assertEqual(self.wal_mgr._high_water_mark, 1)

        # Confirm both followers received and advanced HWM
        for rep in self.wal_mgr._replicas.values():
            self.assertEqual(rep.last_appended_lsn, 1)
            self.assertEqual(rep.high_water_mark, 1)

    def test_05_replica_continuity_and_gap_rejection(self) -> None:
        replica = WALReplica("test_replica", max_segment_records=8)
        # Attempting to append LSN=2 when expected is LSN=1
        bad_rec = WALRecord(lsn=2, tx_id="tx_err", record_type=LogRecordType.PUT, key="k", value="v", timestamp=100.0)
        bad_rec.crc32 = bad_rec.compute_crc()

        self.assertFalse(replica.append_entry(bad_rec))
        self.assertEqual(replica.last_appended_lsn, 0)

        # Valid LSN=1 succeeds
        good_rec = WALRecord(lsn=1, tx_id="tx_ok", record_type=LogRecordType.PUT, key="k", value="v", timestamp=100.0)
        good_rec.crc32 = good_rec.compute_crc()
        self.assertTrue(replica.append_entry(good_rec))
        self.assertEqual(replica.last_appended_lsn, 1)

    def test_06_checkpoint_boundary_writing(self) -> None:
        self.wal_mgr.append_log("tx_01", LogRecordType.PUT, "key_a", "val_a")
        chk = self.wal_mgr.write_checkpoint()
        self.assertEqual(chk.record_type, LogRecordType.CHECKPOINT)
        self.assertEqual(self.wal_mgr._last_checkpoint_lsn, chk.lsn)
        self.assertGreaterEqual(chk.lsn, 2)

    def test_07_crash_recovery_replay(self) -> None:
        self.wal_mgr.append_log("tx_1", LogRecordType.PUT, "key_alpha", "100")
        self.wal_mgr.append_log("tx_2", LogRecordType.PUT, "key_beta", "200")
        self.wal_mgr.append_log("tx_3", LogRecordType.DELETE, "key_alpha", None)

        # Clear in-memory applied state to simulate crash
        self.wal_mgr._applied_state.clear()
        self.assertEqual(len(self.wal_mgr._applied_state), 0)

        # Replay log
        count, recovered = self.wal_mgr.replay_log_from_checkpoint()
        self.assertEqual(count, 3)
        self.assertEqual(recovered.get("key_beta"), "200")
        self.assertNotIn("key_alpha", recovered)

    def test_08_uncommitted_suffix_truncation(self) -> None:
        replica = WALReplica("test_rep", max_segment_records=8)
        for i in range(1, 6):
            r = WALRecord(lsn=i, tx_id=f"tx_{i}", record_type=LogRecordType.PUT, key=f"k_{i}", value="v", timestamp=100.0)
            r.crc32 = r.compute_crc()
            replica.append_entry(r)

        self.assertEqual(replica.last_appended_lsn, 5)

        # Truncate back to LSN=3 (divergent entries 4 and 5 pruned)
        removed = replica.truncate_uncommitted(3)
        self.assertEqual(removed, 2)
        self.assertEqual(replica.last_appended_lsn, 3)

    def test_09_ascii_formatting_and_status(self) -> None:
        self.wal_mgr.append_log("tx_status", LogRecordType.PUT, "status_k", "status_v")
        st = self.wal_mgr.status()
        self.assertEqual(st["stage"], 174)
        self.assertEqual(st["node_id"], "wal_leader_0")

        tbl = self.wal_mgr.format_ascii_status()
        self.assertIn("LUCY STAGE 174: DISTRIBUTED WRITE-AHEAD LOG (WAL) SEGMENT REPLICATION", tbl)
        self.assertIn("wal_leader_0", tbl)
        self.assertIn("wal_follower_1", tbl)

    def test_10_singleton_accessor(self) -> None:
        wal1 = get_distributed_wal_manager()
        wal2 = get_distributed_wal_manager()
        self.assertIs(wal1, wal2)


if __name__ == "__main__":
    unittest.main()
