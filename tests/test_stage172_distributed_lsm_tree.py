r"""
tests/test_stage172_distributed_lsm_tree.py
Stage 172 Test Suite: Distributed LSM-Tree & Memtable SSTable Engine
Era 18: Autonomous Distributed Storage, Geo-Replication & Sharding Primitives
"""

import time
import unittest

from backend.lucy_core.distributed_lsm_tree import (
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    TOMBSTONE,
    BloomFilter,
    DistributedLSMTree,
    SSTable,
    SSTableRecord,
    get_distributed_lsm_tree,
)


class TestStage172DistributedLSMTree(unittest.TestCase):
    def setUp(self) -> None:
        self.lsm = DistributedLSMTree(node_id="test_node_0", memtable_max_entries=8, compaction_threshold=3)

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 172)
        self.assertEqual(ERA, 18)
        self.assertEqual(STAGE_NAME, "Distributed LSM-Tree & Memtable SSTable Engine")
        self.assertEqual(
            ERA_NAME,
            "Autonomous Distributed Storage, Geo-Replication & Sharding Primitives",
        )
        self.assertEqual(TOMBSTONE, "__LUCY_TOMBSTONE_DELETED__")

    def test_02_bloom_filter_precision(self) -> None:
        bf = BloomFilter(size_bits=1024, num_hashes=4)
        keys = ["user:101", "user:102", "order:999"]
        for k in keys:
            bf.add(k)

        for k in keys:
            self.assertTrue(bf.might_contain(k))

        # Check negative rejection on distinct keys
        negatives = ["absent_key_alpha", "absent_key_beta", "nonexistent:404"]
        rejections = sum(not bf.might_contain(nk) for nk in negatives)
        self.assertGreaterEqual(rejections, 2)

    def test_03_sstable_creation_and_sparse_index(self) -> None:
        records = [
            SSTableRecord("k_03", "v3", time.time()),
            SSTableRecord("k_01", "v1", time.time()),
            SSTableRecord("k_05", "v5", time.time()),
            SSTableRecord("k_02", "v2", time.time()),
            SSTableRecord("k_04", "v4", time.time()),
        ]
        sst = SSTable("sst_test_01", level=0, records=records, sparse_interval=2)
        self.assertEqual(sst.min_key, "k_01")
        self.assertEqual(sst.max_key, "k_05")
        self.assertEqual(len(sst.sparse_index), 3)

        rec = sst.get("k_03")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.value, "v3")
        self.assertIsNone(sst.get("k_99"))

    def test_04_memtable_put_and_point_lookup(self) -> None:
        self.lsm.put("doc_1", {"title": "Manifest"})
        self.lsm.put("doc_2", {"title": "Consensus"})

        val1 = self.lsm.get("doc_1")
        self.assertEqual(val1, {"title": "Manifest"})
        val2 = self.lsm.get("doc_2")
        self.assertEqual(val2, {"title": "Consensus"})
        self.assertIsNone(self.lsm.get("nonexistent"))

    def test_05_automatic_memtable_flush(self) -> None:
        self.assertEqual(len(self.lsm._levels[0]), 0)
        # Put 8 entries (memtable_max_entries = 8)
        for i in range(8):
            self.lsm.put(f"key_{i:02d}", f"val_{i:02d}")

        # Active Memtable should have flushed to L0 SSTable
        self.assertEqual(len(self.lsm._levels[0]), 1)
        self.assertEqual(len(self.lsm._active_memtable), 0)

        # Values must remain accessible via SSTable
        for i in range(8):
            self.assertEqual(self.lsm.get(f"key_{i:02d}"), f"val_{i:02d}")

    def test_06_tombstone_deletion_and_masking(self) -> None:
        self.lsm.put("item_to_delete", "active_data")
        self.assertEqual(self.lsm.get("item_to_delete"), "active_data")

        # Flush to SSTable so old data resides on disk/SSTable
        self.lsm.force_flush()
        self.assertEqual(self.lsm.get("item_to_delete"), "active_data")

        # Delete writes tombstone in active Memtable
        self.lsm.delete("item_to_delete")
        self.assertIsNone(self.lsm.get("item_to_delete"))

    def test_07_leveled_compaction(self) -> None:
        # Trigger 3 flushes (compaction_threshold = 3)
        for batch in range(3):
            for i in range(8):
                self.lsm.put(f"k_{batch}_{i:02d}", f"v_{batch}_{i:02d}")

        # Compaction should trigger automatically from L0 to L1
        self.assertGreaterEqual(len(self.lsm._levels[1]), 1)
        self.assertGreaterEqual(self.lsm._total_compactions, 1)

        # All values should remain accessible
        for batch in range(3):
            for i in range(8):
                self.assertEqual(self.lsm.get(f"k_{batch}_{i:02d}"), f"v_{batch}_{i:02d}")

    def test_08_multi_version_range_scan(self) -> None:
        # Insert a set of keys
        for i in range(10):
            self.lsm.put(f"user_{i:02d}", f"name_{i:02d}")

        self.lsm.force_flush()

        # Update user_03, delete user_05
        self.lsm.put("user_03", "updated_name_03")
        self.lsm.delete("user_05")

        scanned = self.lsm.scan(start_key="user_02", end_key="user_07")
        keys = [k for k, _ in scanned]

        self.assertIn("user_02", keys)
        self.assertIn("user_03", keys)
        self.assertIn("user_04", keys)
        self.assertNotIn("user_05", keys)  # Tombstone must be excluded
        self.assertIn("user_06", keys)
        self.assertIn("user_07", keys)

        # Check updated value for user_03
        val_map = dict(scanned)
        self.assertEqual(val_map["user_03"], "updated_name_03")

    def test_09_ascii_formatting_and_status(self) -> None:
        self.lsm.put("status_key", "status_val")
        st = self.lsm.status()
        self.assertEqual(st["stage"], 172)
        self.assertEqual(st["node_id"], "test_node_0")
        self.assertGreater(st["total_writes"], 0)

        tbl = self.lsm.format_ascii_status()
        self.assertIn("LUCY STAGE 172: DISTRIBUTED LSM-TREE & MEMTABLE SSTABLE ENGINE", tbl)
        self.assertIn("test_node_0", tbl)
        self.assertIn("L0", tbl)

    def test_10_singleton_accessor(self) -> None:
        lsm1 = get_distributed_lsm_tree()
        lsm2 = get_distributed_lsm_tree()
        self.assertIs(lsm1, lsm2)


if __name__ == "__main__":
    unittest.main()
