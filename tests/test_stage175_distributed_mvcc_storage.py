r"""
tests/test_stage175_distributed_mvcc_storage.py
Stage 175 Test Suite: Distributed Snapshot Isolation & MVCC Storage
Era 18: Autonomous Distributed Storage, Geo-Replication & Sharding Primitives
"""

import unittest

from backend.lucy_core.distributed_mvcc_storage import (
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    DistributedMVCCStorage,
    MVCCTransaction,
    MVCCVersion,
    TransactionState,
    WriteConflictError,
    get_distributed_mvcc_storage,
)


class TestStage175DistributedMVCCStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.mvcc = DistributedMVCCStorage(node_id="test_mvcc_0")

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 175)
        self.assertEqual(ERA, 18)
        self.assertEqual(
            STAGE_NAME,
            "Distributed Snapshot Isolation & MVCC Storage",
        )
        self.assertEqual(
            ERA_NAME,
            "Autonomous Distributed Storage, Geo-Replication & Sharding Primitives",
        )

    def test_02_transaction_lifecycle(self) -> None:
        tx = self.mvcc.begin_transaction("tx_init")
        self.assertEqual(tx.state, TransactionState.ACTIVE)
        self.mvcc.tx_put("tx_init", "balance/user1", 1000)

        # Before commit, value is visible within transaction
        self.assertEqual(self.mvcc.tx_get("tx_init", "balance/user1"), 1000)

        # Commit transaction
        commit_ts = self.mvcc.commit_transaction("tx_init")
        self.assertGreater(commit_ts, tx.read_ts)

        # New transaction can see committed value
        tx2 = self.mvcc.begin_transaction("tx_read")
        self.assertEqual(self.mvcc.tx_get("tx_read", "balance/user1"), 1000)

    def test_03_read_your_own_writes(self) -> None:
        tx = self.mvcc.begin_transaction("tx_work")
        self.mvcc.tx_put("tx_work", "doc_title", "Draft Alpha")
        self.assertEqual(self.mvcc.tx_get("tx_work", "doc_title"), "Draft Alpha")

        self.mvcc.tx_put("tx_work", "doc_title", "Draft Beta")
        self.assertEqual(self.mvcc.tx_get("tx_work", "doc_title"), "Draft Beta")

        self.mvcc.commit_transaction("tx_work")

    def test_04_snapshot_isolation_consistent_reads(self) -> None:
        # Initial state
        tx0 = self.mvcc.begin_transaction("tx0")
        self.mvcc.tx_put("tx0", "stock_count", 50)
        self.mvcc.commit_transaction("tx0")

        # T1 begins (snapshot at ts_1)
        t1 = self.mvcc.begin_transaction("t1")
        self.assertEqual(self.mvcc.tx_get("t1", "stock_count"), 50)

        # T2 begins, updates stock_count, and commits
        t2 = self.mvcc.begin_transaction("t2")
        self.mvcc.tx_put("t2", "stock_count", 100)
        self.mvcc.commit_transaction("t2")

        # T1 must STILL see 50 (repeatable read / snapshot isolation guarantee)
        self.assertEqual(self.mvcc.tx_get("t1", "stock_count"), 50)
        self.mvcc.commit_transaction("t1")

        # T3 begins after T2's commit -> sees 100
        t3 = self.mvcc.begin_transaction("t3")
        self.assertEqual(self.mvcc.tx_get("t3", "stock_count"), 100)
        self.mvcc.commit_transaction("t3")

    def test_05_non_blocking_concurrent_reads(self) -> None:
        tx_setup = self.mvcc.begin_transaction("tx_setup")
        self.mvcc.tx_put("tx_setup", "mesh/status", "HEALTHY")
        self.mvcc.commit_transaction("tx_setup")

        # Multiple concurrent transactions reading simultaneously
        tx_a = self.mvcc.begin_transaction("tx_a")
        tx_b = self.mvcc.begin_transaction("tx_b")

        self.assertEqual(self.mvcc.tx_get("tx_a", "mesh/status"), "HEALTHY")
        self.assertEqual(self.mvcc.tx_get("tx_b", "mesh/status"), "HEALTHY")

        self.mvcc.commit_transaction("tx_a")
        self.mvcc.commit_transaction("tx_b")

    def test_06_first_committer_wins_write_conflict(self) -> None:
        # Setup initial key
        tx_init = self.mvcc.begin_transaction("tx_init")
        self.mvcc.tx_put("tx_init", "shared_counter", 0)
        self.mvcc.commit_transaction("tx_init")

        # T1 and T2 both start at snapshot ts
        t1 = self.mvcc.begin_transaction("t1")
        t2 = self.mvcc.begin_transaction("t2")

        # Both modify shared_counter
        self.mvcc.tx_put("t1", "shared_counter", 1)
        self.mvcc.tx_put("t2", "shared_counter", 2)

        # T1 commits first -> succeeds
        self.mvcc.commit_transaction("t1")

        # T2 attempts to commit -> WriteConflictError raised!
        with self.assertRaises(WriteConflictError):
            self.mvcc.commit_transaction("t2")

    def test_07_tombstone_deletion_visibility(self) -> None:
        # Setup key
        tx_init = self.mvcc.begin_transaction("tx_init")
        self.mvcc.tx_put("tx_init", "temp_token", "SECRET_XYZ")
        self.mvcc.commit_transaction("tx_init")

        # T1 starts before delete
        t1 = self.mvcc.begin_transaction("t1")

        # T2 deletes key
        t2 = self.mvcc.begin_transaction("t2")
        self.mvcc.tx_delete("t2", "temp_token")
        self.mvcc.commit_transaction("t2")

        # T1 can still read the token as of its snapshot
        self.assertEqual(self.mvcc.tx_get("t1", "temp_token"), "SECRET_XYZ")
        self.mvcc.commit_transaction("t1")

        # T3 starts after delete -> returns None
        t3 = self.mvcc.begin_transaction("t3")
        self.assertIsNone(self.mvcc.tx_get("t3", "temp_token"))
        self.mvcc.commit_transaction("t3")

    def test_08_multi_version_vacuum_gc(self) -> None:
        # Write multiple versions of a key
        for v in range(5):
            tx = self.mvcc.begin_transaction(f"tx_ver_{v}")
            self.mvcc.tx_put(f"tx_ver_{v}", "gc_key", f"version_{v}")
            self.mvcc.commit_transaction(f"tx_ver_{v}")

        # Currently 5 versions in chain
        self.assertEqual(len(self.mvcc._versions["gc_key"]), 5)

        # With no active transactions, vacuum purges all obsolete superseded versions
        purged = self.mvcc.vacuum()
        self.assertEqual(purged, 4)
        self.assertEqual(len(self.mvcc._versions["gc_key"]), 1)
        self.assertEqual(self.mvcc._versions["gc_key"][0].value, "version_4")

    def test_09_ascii_formatting_and_status(self) -> None:
        tx = self.mvcc.begin_transaction("tx_st")
        self.mvcc.tx_put("tx_st", "telemetry/status", "OK")
        self.mvcc.commit_transaction("tx_st")

        st = self.mvcc.status()
        self.assertEqual(st["stage"], 175)
        self.assertGreater(st["total_tx_committed"], 0)

        tbl = self.mvcc.format_ascii_status()
        self.assertIn("LUCY STAGE 175: DISTRIBUTED SNAPSHOT ISOLATION & MVCC STORAGE ENGINE", tbl)
        self.assertIn("telemetry/statu", tbl)
        self.assertIn("OK", tbl)

    def test_10_singleton_accessor(self) -> None:
        m1 = get_distributed_mvcc_storage()
        m2 = get_distributed_mvcc_storage()
        self.assertIs(m1, m2)


if __name__ == "__main__":
    unittest.main()
