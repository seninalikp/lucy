r"""
tests/test_stage209_hyperscale_mesh_synchronizer.py
Stage 209: Autonomous Hyper-Scale Cluster Mesh Synchronizer
Era 21: Autonomous Hyper-Scale Multi-Kernel Federation, Quantum-Resistant Keys & Post-Singularity Architecture
"""

import unittest
from backend.lucy_core.hyperscale_mesh_synchronizer import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    ClusterRecord,
    HyperscaleMeshSynchronizerFabric,
)


class TestStage209HyperscaleMeshSynchronizer(unittest.TestCase):
    """10 Unit Tests for Stage 209 Hyper-Scale Mesh Synchronizer Fabric."""

    def setUp(self):
        self.fabric = HyperscaleMeshSynchronizerFabric(local_cluster_id="test_cluster_alpha")

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric.local_cluster_id, "test_cluster_alpha")
        self.assertEqual(len(self.fabric.cluster_stores), 0)
        self.assertEqual(self.fabric.status()["stage"], 209)
        self.assertEqual(self.fabric.status()["era"], 21)

    def test_02_put_record_and_versioning(self):
        r1 = self.fabric.put_record("c1", "key_a", "val_1", timestamp_ms=100)
        self.assertEqual(r1.version, 1)
        self.assertEqual(r1.value, "val_1")

        r2 = self.fabric.put_record("c1", "key_a", "val_2", timestamp_ms=200)
        self.assertEqual(r2.version, 2)
        self.assertEqual(r2.value, "val_2")

    def test_03_build_merkle_root_empty(self):
        root = self.fabric.build_merkle_root("c_empty")
        self.assertEqual(len(root), 64)
        self.assertIn("c_empty", self.fabric.partition_roots)

    def test_04_build_merkle_root_determinism(self):
        # Cluster A: insert key1 then key2
        self.fabric.put_record("cA", "k1", 100, 1000)
        self.fabric.put_record("cA", "k2", 200, 1000)
        rootA = self.fabric.build_merkle_root("cA")

        # Cluster B: insert key2 then key1
        self.fabric.put_record("cB", "k2", 200, 1000)
        self.fabric.put_record("cB", "k1", 100, 1000)
        rootB = self.fabric.build_merkle_root("cB")

        self.assertEqual(rootA, rootB)

    def test_05_anti_entropy_already_synced(self):
        self.fabric.put_record("c1", "k", "v", 500)
        self.fabric.put_record("c2", "k", "v", 500)

        count, keys = self.fabric.anti_entropy_sync("c1", "c2")
        self.assertEqual(count, 0)
        self.assertEqual(len(keys), 0)

    def test_06_anti_entropy_missing_keys_replicated(self):
        self.fabric.put_record("c_source", "shared_k", "val_shared", 1000)
        self.fabric.put_record("c_source", "unique_k", "val_unique", 1000)
        self.fabric.put_record("c_target", "shared_k", "val_shared", 1000)

        count, keys = self.fabric.anti_entropy_sync("c_source", "c_target")
        self.assertEqual(count, 1)
        self.assertIn("unique_k", keys)
        self.assertEqual(self.fabric.cluster_stores["c_target"]["unique_k"].value, "val_unique")

    def test_07_anti_entropy_last_write_wins_conflict(self):
        # Target has older write, Source has newer write
        self.fabric.put_record("c_src", "config_k", "new_val", timestamp_ms=5000)
        self.fabric.put_record("c_tgt", "config_k", "old_val", timestamp_ms=1000)

        count, keys = self.fabric.anti_entropy_sync("c_src", "c_tgt")
        self.assertEqual(count, 1)
        self.assertEqual(self.fabric.cluster_stores["c_tgt"]["config_k"].value, "new_val")

    def test_08_anti_entropy_bidirectional_sync(self):
        self.fabric.put_record("c_east", "east_data", 111, 1000)
        self.fabric.put_record("c_west", "west_data", 222, 1000)

        count, keys = self.fabric.anti_entropy_sync("c_east", "c_west")
        self.assertEqual(count, 2)
        self.assertIn("east_data", keys)
        self.assertIn("west_data", keys)

        # Both now have both keys
        self.assertIn("west_data", self.fabric.cluster_stores["c_east"])
        self.assertIn("east_data", self.fabric.cluster_stores["c_west"])

    def test_09_sync_session_counters(self):
        self.fabric.put_record("c1", "k", 1, 100)
        self.fabric.anti_entropy_sync("c1", "c2")
        s = self.fabric.status()
        self.assertEqual(s["sync_sessions"], 1)
        self.assertEqual(s["records_reconciled"], 1)

    def test_10_ascii_status_and_metadata(self):
        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 209: HYPER-SCALE CLUSTER MESH SYNCHRONIZER", ascii_out)
        self.assertIn("Era 21 (Post-Singularity Cluster Mesh)", ascii_out)


if __name__ == "__main__":
    unittest.main()
