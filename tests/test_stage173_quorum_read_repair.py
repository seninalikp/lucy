r"""
tests/test_stage173_quorum_read_repair.py
Stage 173 Test Suite: Quorum Read-Repair & Active Anti-Entropy Merkle Fabric
Era 18: Autonomous Distributed Storage, Geo-Replication & Sharding Primitives
"""

import time
import unittest

from backend.lucy_core.quorum_read_repair import (
    ERA,
    ERA_NAME,
    STAGE,
    STAGE_NAME,
    AntiEntropySyncResult,
    KeyRangeMerkleTree,
    QuorumAntiEntropyCoordinator,
    QuorumReadResult,
    StorageReplicaNode,
    VersionedValue,
    get_quorum_anti_entropy_coordinator,
)


class TestStage173QuorumReadRepair(unittest.TestCase):
    def setUp(self) -> None:
        self.coordinator = QuorumAntiEntropyCoordinator(default_n=3, default_w=2, default_r=2)

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 173)
        self.assertEqual(ERA, 18)
        self.assertEqual(STAGE_NAME, "Quorum Read-Repair & Active Anti-Entropy Merkle Fabric")
        self.assertEqual(
            ERA_NAME,
            "Autonomous Distributed Storage, Geo-Replication & Sharding Primitives",
        )
        self.assertEqual(self.coordinator.n, 3)
        self.assertEqual(self.coordinator.w, 2)
        self.assertEqual(self.coordinator.r, 2)

    def test_02_merkle_tree_construction_and_root(self) -> None:
        tree1 = KeyRangeMerkleTree(bucket_count=8)
        tree2 = KeyRangeMerkleTree(bucket_count=8)

        v1 = VersionedValue("k1", "val1", 1000.0, 1)
        v2 = VersionedValue("k2", "val2", 1000.0, 1)

        tree1.insert(v1)
        tree1.insert(v2)

        tree2.insert(v1)
        tree2.insert(v2)

        r1 = tree1.build_tree()
        r2 = tree2.build_tree()
        self.assertEqual(r1, r2)
        self.assertEqual(len(r1), 64)

    def test_03_merkle_differing_buckets_isolation(self) -> None:
        tree1 = KeyRangeMerkleTree(bucket_count=8)
        tree2 = KeyRangeMerkleTree(bucket_count=8)

        tree1.insert(VersionedValue("shared", "val", 1000.0, 1))
        tree2.insert(VersionedValue("shared", "val", 1000.0, 1))

        # tree2 gets an extra record
        tree2.insert(VersionedValue("divergent_key", "divergent_val", 2000.0, 2))

        tree1.build_tree()
        tree2.build_tree()

        self.assertNotEqual(tree1.root_hash, tree2.root_hash)
        diff_buckets = tree1.find_differing_buckets(tree2)
        self.assertGreaterEqual(len(diff_buckets), 1)

    def test_04_quorum_write_success(self) -> None:
        ok, acks, ts = self.coordinator.quorum_write("account:100", {"balance": 5000})
        self.assertTrue(ok)
        self.assertEqual(acks, 3)  # All 3 acknowledged
        self.assertGreater(ts, 0.0)

        # Verify each node has the stored value
        for nid, node in self.coordinator.nodes.items():
            rec = node.get("account:100")
            self.assertIsNotNone(rec)
            self.assertEqual(rec.value, {"balance": 5000})

    def test_05_quorum_read_consensus(self) -> None:
        self.coordinator.quorum_write("user:alpha", "active_session")
        res = self.coordinator.quorum_read("user:alpha")
        self.assertTrue(res.quorum_achieved)
        self.assertEqual(res.resolved_value, "active_session")
        self.assertEqual(res.stale_replicas_found, 0)
        self.assertEqual(len(res.nodes_repaired), 0)

    def test_06_opportunistic_read_repair(self) -> None:
        # Step 1: Write initial value to all nodes
        self.coordinator.quorum_write("config:theme", "light")

        # Step 2: Manually simulate partial write or network partition:
        # Update replica_node_0 and replica_node_1 with newer value, leaving replica_node_2 stale
        newer_ts = time.time() + 50.0
        self.coordinator.nodes["replica_node_0"].put("config:theme", "dark_matrix", timestamp=newer_ts, version=2)
        self.coordinator.nodes["replica_node_1"].put("config:theme", "dark_matrix", timestamp=newer_ts, version=2)

        # Confirm replica_node_2 is stale
        self.assertEqual(self.coordinator.nodes["replica_node_2"].get("config:theme").value, "light")

        # Step 3: Quorum read with R=3 across all replicas
        res = self.coordinator.quorum_read("config:theme", r=3)
        self.assertTrue(res.quorum_achieved)
        self.assertEqual(res.resolved_value, "dark_matrix")
        self.assertEqual(res.stale_replicas_found, 1)
        self.assertIn("replica_node_2", res.nodes_repaired)

        # Confirm replica_node_2 was repaired!
        repaired_rec = self.coordinator.nodes["replica_node_2"].get("config:theme")
        self.assertEqual(repaired_rec.value, "dark_matrix")
        self.assertEqual(repaired_rec.version, 2)

    def test_07_strong_consistency_dynamo_model(self) -> None:
        st = self.coordinator.status()
        q = st["quorum_config"]
        # R + W > N ensures strict overlap (Pigeonhole principle)
        self.assertTrue(q["strong_consistency"])
        self.assertGreater(q["R"] + q["W"], q["N"])

    def test_08_active_anti_entropy_merkle_sync(self) -> None:
        node_a = self.coordinator.nodes["replica_node_0"]
        node_b = self.coordinator.nodes["replica_node_1"]

        # Insert asymmetric keys
        node_a.put("key_only_on_a", "val_a", timestamp=100.0, version=1)
        node_b.put("key_only_on_b", "val_b", timestamp=100.0, version=1)

        # Run Anti-Entropy Sync
        sync_res = self.coordinator.run_anti_entropy_sync("replica_node_0", "replica_node_1")
        self.assertFalse(sync_res.root_match)
        self.assertGreaterEqual(sync_res.keys_synced, 2)
        self.assertIn("key_only_on_a", sync_res.differing_keys)
        self.assertIn("key_only_on_b", sync_res.differing_keys)

        # Now both nodes must have identical root hashes
        self.assertEqual(node_a.merkle_tree.root_hash, node_b.merkle_tree.root_hash)
        self.assertEqual(node_a.get("key_only_on_b").value, "val_b")
        self.assertEqual(node_b.get("key_only_on_a").value, "val_a")

    def test_09_ascii_formatting_and_status(self) -> None:
        st = self.coordinator.status()
        self.assertEqual(st["stage"], 173)
        self.assertEqual(st["total_replicas"], 3)

        tbl = self.coordinator.format_ascii_status()
        self.assertIn("LUCY STAGE 173: QUORUM READ-REPAIR & ACTIVE ANTI-ENTROPY MERKLE FABRIC", tbl)
        self.assertIn("replica_node_0", tbl)
        self.assertIn("N=3, W=2, R=2", tbl)

    def test_10_singleton_accessor(self) -> None:
        coord1 = get_quorum_anti_entropy_coordinator()
        coord2 = get_quorum_anti_entropy_coordinator()
        self.assertIs(coord1, coord2)


if __name__ == "__main__":
    unittest.main()
