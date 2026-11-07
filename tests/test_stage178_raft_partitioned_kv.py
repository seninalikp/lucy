r"""
tests/test_stage178_raft_partitioned_kv.py
Stage 178 Test Suite: Raft-Partitioned Distributed KV Engine
Era 18: Autonomous Distributed Storage, Geo-Replication & Sharding Primitives
"""

import unittest

from backend.lucy_core.raft_partitioned_kv import (
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    MultiRaftKVEngine,
    RaftGroupLogEntry,
    RaftKVCommand,
    RaftKVGroup,
    get_multi_raft_kv_engine,
)


class TestStage178RaftPartitionedKV(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = MultiRaftKVEngine(group_count=4, peers_per_group=3)

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 178)
        self.assertEqual(ERA, 18)
        self.assertEqual(STAGE_NAME, "Raft-Partitioned Distributed KV Engine")
        self.assertEqual(
            ERA_NAME,
            "Autonomous Distributed Storage, Geo-Replication & Sharding Primitives",
        )
        self.assertEqual(self.engine.group_count, 4)

    def test_02_group_partitioning_mapping(self) -> None:
        g1 = self.engine.get_group_for_key("user:101")
        g2 = self.engine.get_group_for_key("user:101")
        # Must be deterministic
        self.assertEqual(g1.group_id, g2.group_id)
        self.assertIn(g1.group_id, {"raft_group_0", "raft_group_1", "raft_group_2", "raft_group_3"})

    def test_03_single_group_put_and_quorum_commit(self) -> None:
        ok, gid, idx = self.engine.put("order:4001", {"total": 99.5})
        self.assertTrue(ok)
        self.assertGreaterEqual(idx, 1)

        val = self.engine.get("order:4001")
        self.assertEqual(val, {"total": 99.5})

    def test_04_linearizable_read_with_leader_lease(self) -> None:
        self.engine.put("mesh_token", "ALPHA_99")
        group = self.engine.get_group_for_key("mesh_token")
        self.assertTrue(group.is_leader_lease_valid)

        val = self.engine.get("mesh_token")
        self.assertEqual(val, "ALPHA_99")

    def test_05_group_independence(self) -> None:
        # Find keys mapping to different groups
        k_g0, k_g1 = None, None
        for i in range(100):
            k = f"key_sample_{i}"
            gid = self.engine._get_group_id_for_key(k)
            if gid == "raft_group_0" and not k_g0:
                k_g0 = k
            elif gid == "raft_group_1" and not k_g1:
                k_g1 = k
            if k_g0 and k_g1:
                break

        self.assertIsNotNone(k_g0)
        self.assertIsNotNone(k_g1)

        # Write to group 0
        self.engine.put(k_g0, "val_0")
        self.assertEqual(self.engine.groups["raft_group_0"].commit_index, 1)
        # Group 1 must remain untouched
        self.assertEqual(self.engine.groups["raft_group_1"].commit_index, 0)

    def test_06_deletion_operation(self) -> None:
        self.engine.put("key_to_delete", "temporary")
        self.assertEqual(self.engine.get("key_to_delete"), "temporary")

        ok, gid, idx = self.engine.delete("key_to_delete")
        self.assertTrue(ok)
        self.assertIsNone(self.engine.get("key_to_delete"))

    def test_07_cross_partition_2pc_success(self) -> None:
        mutations = {
            "account:alice": {"balance": 400},
            "account:bob": {"balance": 600},
        }
        ok = self.engine.execute_cross_partition_tx(mutations)
        self.assertTrue(ok)

        # Both keys committed
        self.assertEqual(self.engine.get("account:alice"), {"balance": 400})
        self.assertEqual(self.engine.get("account:bob"), {"balance": 600})

    def test_08_log_continuity_and_indices(self) -> None:
        k = "log_test_key"
        grp = self.engine.get_group_for_key(k)
        start_idx = grp.commit_index

        for step in range(3):
            self.engine.put(k, f"step_{step}")

        self.assertEqual(grp.commit_index, start_idx + 3)
        self.assertEqual(len(grp.log), start_idx + 3)

    def test_09_ascii_formatting_and_status(self) -> None:
        self.engine.put("status_key", "status_val")
        st = self.engine.status()
        self.assertEqual(st["stage"], 178)
        self.assertEqual(st["group_count"], 4)

        tbl = self.engine.format_ascii_status()
        self.assertIn("LUCY STAGE 178: RAFT-PARTITIONED DISTRIBUTED KV ENGINE (MULTI-RAFT)", tbl)
        self.assertIn("raft_group_0", tbl)
        self.assertIn("ACTIVE", tbl)

    def test_10_singleton_accessor(self) -> None:
        e1 = get_multi_raft_kv_engine()
        e2 = get_multi_raft_kv_engine()
        self.assertIs(e1, e2)


if __name__ == "__main__":
    unittest.main()
