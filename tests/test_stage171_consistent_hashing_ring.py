r"""
tests/test_stage171_consistent_hashing_ring.py
Stage 171 Test Suite: Consistent Hashing Ring & Virtual Node Partitioning
Era 18: Autonomous Distributed Storage, Geo-Replication & Sharding Primitives
"""

import unittest

from backend.lucy_core.consistent_hashing_ring import (
    ERA,
    ERA_NAME,
    RING_MODULUS,
    STAGE,
    STAGE_NAME,
    ConsistentHashRing,
    RangeTransfer,
    RingLoadStats,
    VNode,
    get_consistent_hash_ring,
    hash_token_64,
)


class TestStage171ConsistentHashingRing(unittest.TestCase):
    def setUp(self) -> None:
        self.ring = ConsistentHashRing(default_vnodes=128, replication_factor=3)

    def test_01_metadata_and_initialization(self) -> None:
        self.assertEqual(STAGE, 171)
        self.assertEqual(ERA, 18)
        self.assertEqual(STAGE_NAME, "Consistent Hashing Ring & Virtual Node Partitioning")
        self.assertEqual(
            ERA_NAME,
            "Autonomous Distributed Storage, Geo-Replication & Sharding Primitives",
        )
        self.assertEqual(self.ring.default_vnodes, 128)
        self.assertEqual(self.ring.replication_factor, 3)
        self.assertEqual(RING_MODULUS, 2**64)

    def test_02_deterministic_64bit_hashing(self) -> None:
        t1 = hash_token_64("storage_node_0#vnode_1")
        t2 = hash_token_64("storage_node_0#vnode_1")
        t3 = hash_token_64("storage_node_0#vnode_2")
        self.assertEqual(t1, t2)
        self.assertNotEqual(t1, t3)
        self.assertGreaterEqual(t1, 0)
        self.assertLess(t1, RING_MODULUS)

    def test_03_add_nodes_and_vnode_expansion(self) -> None:
        added_0 = self.ring.add_node("storage_0", vnodes=64)
        added_1 = self.ring.add_node("storage_1", vnodes=64)
        self.assertEqual(added_0, 64)
        self.assertEqual(added_1, 64)
        self.assertEqual(len(self.ring._ring), 128)
        # Ring must be monotonically sorted
        self.assertEqual(self.ring._ring, sorted(self.ring._ring))
        # Adding duplicate node returns 0
        self.assertEqual(self.ring.add_node("storage_0"), 0)

    def test_04_remove_nodes_cleanup(self) -> None:
        self.ring.add_node("storage_0", vnodes=32)
        self.ring.add_node("storage_1", vnodes=32)
        self.ring.add_node("storage_2", vnodes=32)
        self.assertEqual(len(self.ring._ring), 96)

        removed = self.ring.remove_node("storage_1")
        self.assertEqual(removed, 32)
        self.assertEqual(len(self.ring._ring), 64)
        # Check no vnodes belong to storage_1
        for tok in self.ring._ring:
            self.assertNotEqual(self.ring._token_to_vnode[tok].physical_node_id, "storage_1")

        # Removing non-existent node returns 0
        self.assertEqual(self.ring.remove_node("non_existent"), 0)

    def test_05_primary_node_lookup_and_wraparound(self) -> None:
        # Empty ring returns None
        self.assertIsNone(self.ring.get_primary_node("user_1001"))

        self.ring.add_node("node_alpha", vnodes=64)
        self.ring.add_node("node_beta", vnodes=64)
        self.ring.add_node("node_gamma", vnodes=64)

        keys = [f"lucy_doc_{i}" for i in range(50)]
        for k in keys:
            primary = self.ring.get_primary_node(k)
            self.assertIn(primary, {"node_alpha", "node_beta", "node_gamma"})

    def test_06_preference_list_replication(self) -> None:
        self.ring.add_node("node_0", vnodes=64)
        self.ring.add_node("node_1", vnodes=64)
        self.ring.add_node("node_2", vnodes=64)
        self.ring.add_node("node_3", vnodes=64)

        prefs = self.ring.get_preference_list("test_key", n=3)
        self.assertEqual(len(prefs), 3)
        # All physical nodes must be unique
        self.assertEqual(len(set(prefs)), 3)

        # Asking for more replicas than available nodes caps at cluster size
        all_prefs = self.ring.get_preference_list("test_key", n=10)
        self.assertEqual(len(all_prefs), 4)
        self.assertEqual(set(all_prefs), {"node_0", "node_1", "node_2", "node_3"})

    def test_07_ring_load_distribution_and_balance(self) -> None:
        # Add 4 nodes with default 128 vnodes each
        for i in range(4):
            self.ring.add_node(f"rack_node_{i}", vnodes=128)

        stats = self.ring.get_load_stats()
        self.assertEqual(stats.total_physical_nodes, 4)
        self.assertEqual(stats.total_vnodes, 512)
        self.assertTrue(stats.is_balanced)
        self.assertLess(stats.standard_deviation, 0.08)

        # Each node should have roughly ~25% coverage
        for nid, frac in stats.node_coverage_fractions.items():
            self.assertGreater(frac, 0.15)
            self.assertLess(frac, 0.35)

    def test_08_rebalance_delta_planning(self) -> None:
        for i in range(3):
            self.ring.add_node(f"node_{i}", vnodes=64)

        plan = self.ring.calculate_rebalance_plan("node_new", new_vnodes=32)
        self.assertEqual(len(plan), 32)
        for transfer in plan:
            self.assertEqual(transfer.to_node, "node_new")
            self.assertIn(transfer.from_node, {"node_0", "node_1", "node_2"})
            self.assertIsInstance(transfer.start_token, int)
            self.assertIsInstance(transfer.end_token, int)

    def test_09_ascii_formatting_and_status(self) -> None:
        self.ring.add_node("storage_east_1", vnodes=64)
        self.ring.add_node("storage_west_1", vnodes=64)

        st = self.ring.status()
        self.assertEqual(st["stage"], 171)
        self.assertEqual(st["total_vnodes"], 128)

        tbl = self.ring.format_ascii_status()
        self.assertIn("LUCY STAGE 171: CONSISTENT HASHING RING & VIRTUAL NODE PARTITIONING", tbl)
        self.assertIn("storage_east_1", tbl)
        self.assertIn("storage_west_1", tbl)
        self.assertIn("BALANCED", tbl)

    def test_10_singleton_accessor(self) -> None:
        ring1 = get_consistent_hash_ring()
        ring2 = get_consistent_hash_ring()
        self.assertIs(ring1, ring2)


if __name__ == "__main__":
    unittest.main()
