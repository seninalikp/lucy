r"""
tests/test_stage176_dynamic_shard_migrator.py
Stage 176 Test Suite: Dynamic Shard Migration & Range Splitter Sentinel
Era 18: Autonomous Distributed Storage, Geo-Replication & Sharding Primitives
"""

import unittest

from backend.lucy_core.dynamic_shard_migrator import (
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    DynamicShardSentinel,
    MigrationResult,
    ShardRange,
    ShardState,
    get_dynamic_shard_sentinel,
)


class TestStage176DynamicShardMigrator(unittest.TestCase):
    def setUp(self) -> None:
        self.sentinel = DynamicShardSentinel(split_threshold_records=8)

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 176)
        self.assertEqual(ERA, 18)
        self.assertEqual(
            STAGE_NAME,
            "Dynamic Shard Migration & Range Splitter Sentinel",
        )
        self.assertEqual(
            ERA_NAME,
            "Autonomous Distributed Storage, Geo-Replication & Sharding Primitives",
        )
        self.assertEqual(self.sentinel.split_threshold_records, 8)

    def test_02_root_shard_initialization(self) -> None:
        self.assertEqual(len(self.sentinel.shards), 1)
        root = list(self.sentinel.shards.values())[0]
        self.assertEqual(root.start_key, "")
        self.assertEqual(root.end_key, "")
        self.assertEqual(root.primary_node, "node_alpha")
        self.assertEqual(root.state, ShardState.ACTIVE)

    def test_03_key_routing_and_storage(self) -> None:
        sid, pnode = self.sentinel.put_key("user_01", {"name": "Alice"})
        self.assertEqual(pnode, "node_alpha")

        val = self.sentinel.get_key("user_01")
        self.assertEqual(val, {"name": "Alice"})
        self.assertIsNone(self.sentinel.get_key("absent_user"))

    def test_04_autonomous_median_range_split(self) -> None:
        # Initial 1 shard
        self.assertEqual(len(self.sentinel.shards), 1)

        # Insert 8 keys (split_threshold = 8)
        for i in range(8):
            self.sentinel.put_key(f"doc_{i:02d}", f"content_{i}")

        # Shard should have autonomously split into 2 shards
        self.assertEqual(len(self.sentinel.shards), 2)
        self.assertEqual(self.sentinel._total_splits, 1)

        # All 8 keys must remain retrievable
        for i in range(8):
            self.assertEqual(self.sentinel.get_key(f"doc_{i:02d}"), f"content_{i}")

    def test_05_half_open_range_invariants(self) -> None:
        for i in range(8):
            self.sentinel.put_key(f"key_{i:02d}", f"val_{i}")

        shards = sorted(self.sentinel.shards.values(), key=lambda s: s.start_key)
        self.assertEqual(len(shards), 2)
        left, right = shards[0], shards[1]

        # Invariant 1: Left start is root start ("")
        self.assertEqual(left.start_key, "")
        # Invariant 2: Left end == Right start
        self.assertEqual(left.end_key, right.start_key)
        # Invariant 3: Right end is root end ("")
        self.assertEqual(right.end_key, "")

    def test_06_live_online_shard_migration(self) -> None:
        self.sentinel.put_key("record_1", "data_1")
        self.sentinel.put_key("record_2", "data_2")

        target_shard = list(self.sentinel.shards.values())[0]
        self.assertEqual(target_shard.primary_node, "node_alpha")

        # Migrate to node_beta
        res = self.sentinel.migrate_shard(target_shard.shard_id, "node_beta")
        self.assertTrue(res.success)
        self.assertEqual(res.destination_node, "node_beta")
        self.assertEqual(res.source_node, "node_alpha")
        self.assertEqual(res.phase_reached, "CUTOVER_COMPLETE")
        self.assertEqual(target_shard.primary_node, "node_beta")

    def test_07_post_migration_routing(self) -> None:
        self.sentinel.put_key("item_alpha", 123)
        target_shard = list(self.sentinel.shards.values())[0]

        self.sentinel.migrate_shard(target_shard.shard_id, "node_delta")
        # Reading still succeeds
        self.assertEqual(self.sentinel.get_key("item_alpha"), 123)

        # New put routes to node_delta
        _, pnode = self.sentinel.put_key("item_beta", 456)
        self.assertEqual(pnode, "node_delta")
        self.assertEqual(self.sentinel.get_key("item_beta"), 456)

    def test_08_adjacent_range_merging(self) -> None:
        # Trigger split
        for i in range(8):
            self.sentinel.put_key(f"item_{i:02d}", f"val_{i}")
        self.assertEqual(len(self.sentinel.shards), 2)

        shards = sorted(self.sentinel.shards.values(), key=lambda s: s.start_key)
        left_id, right_id = shards[0].shard_id, shards[1].shard_id

        # Merge them back
        merged = self.sentinel.merge_shards(left_id, right_id)
        self.assertEqual(len(self.sentinel.shards), 1)
        self.assertEqual(merged.start_key, "")
        self.assertEqual(merged.end_key, "")
        self.assertEqual(len(merged.data), 8)
        self.assertEqual(self.sentinel._total_merges, 1)

    def test_09_ascii_formatting_and_status(self) -> None:
        self.sentinel.put_key("test_telemetry", "active")
        st = self.sentinel.status()
        self.assertEqual(st["stage"], 176)
        self.assertGreater(st["total_records_indexed"], 0)

        tbl = self.sentinel.format_ascii_status()
        self.assertIn("LUCY STAGE 176: DYNAMIC SHARD MIGRATION & RANGE SPLITTER SENTINEL", tbl)
        self.assertIn("node_alpha", tbl)
        self.assertIn("-INF", tbl)
        self.assertIn("+INF", tbl)

    def test_10_singleton_accessor(self) -> None:
        s1 = get_dynamic_shard_sentinel()
        s2 = get_dynamic_shard_sentinel()
        self.assertIs(s1, s2)


if __name__ == "__main__":
    unittest.main()
