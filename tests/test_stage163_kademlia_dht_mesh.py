r"""
tests/test_stage163_kademlia_dht_mesh.py
Stage 163 Test Suite: Sovereign Distributed Hash Table & Kademlia Node Routing
Era 17: Distributed Consensus, Mesh Virtualization & High-Availability Primitives
"""

import unittest

from backend.lucy_core.kademlia_dht_mesh import (
    CREATOR,
    ERA,
    ID_BITS,
    K_BUCKET_SIZE,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    Contact,
    KBucket,
    KademliaNode,
    SovereignDHTMesh,
    get_dht_mesh,
    hash_key_160,
    xor_distance,
)


class TestStage163KademliaDHTMesh(unittest.TestCase):
    def setUp(self) -> None:
        self.mesh = SovereignDHTMesh()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 163)
        self.assertEqual(ERA, 17)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Sovereign Distributed Hash Table (DHT) & Kademlia Node Routing",
        )
        self.assertEqual(ID_BITS, 160)
        self.assertEqual(K_BUCKET_SIZE, 20)

    def test_02_160bit_hash_key(self) -> None:
        k_id = hash_key_160("lucy://peer_key")
        self.assertIsInstance(k_id, int)
        self.assertGreater(k_id, 0)
        self.assertLessEqual(k_id.bit_length(), 160)
        # Deterministic
        self.assertEqual(k_id, hash_key_160("lucy://peer_key"))

    def test_03_xor_distance_metric(self) -> None:
        a = 0x1234567890ABCDEF1234567890ABCDEF12345678
        b = 0x8765432109FEDCBA8765432109FEDCBA87654321
        c = 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA

        # Self-distance is 0
        self.assertEqual(xor_distance(a, a), 0)
        # Symmetry
        self.assertEqual(xor_distance(a, b), xor_distance(b, a))
        # Triangle inequality in XOR metric: d(a, c) <= d(a, b) ^ d(b, c) -> in fact d(a, c) == d(a, b) ^ d(b, c)
        self.assertEqual(xor_distance(a, c), xor_distance(a, b) ^ xor_distance(b, c))

    def test_04_k_bucket_contacts(self) -> None:
        bucket = KBucket(k=3)
        c1 = Contact(node_id=1, uri="node1")
        c2 = Contact(node_id=2, uri="node2")
        c3 = Contact(node_id=3, uri="node3")
        c4 = Contact(node_id=4, uri="node4")

        self.assertTrue(bucket.add_or_update(c1))
        self.assertTrue(bucket.add_or_update(c2))
        self.assertTrue(bucket.add_or_update(c3))
        # Bucket full, rejects 4th
        self.assertFalse(bucket.add_or_update(c4))

        # Updating existing contact moves it to end
        self.assertTrue(bucket.add_or_update(c1))
        contacts = bucket.get_contacts()
        self.assertEqual(contacts[-1].node_id, 1)

    def test_05_node_rpc_ping(self) -> None:
        node = KademliaNode(node_id=100, uri="local://test")
        self.assertEqual(node.total_pings, 0)
        self.assertTrue(node.rpc_ping())
        self.assertEqual(node.total_pings, 1)

    def test_06_node_rpc_store_and_find_value(self) -> None:
        node = KademliaNode(node_id=200, uri="local://storage_node")
        key_id = hash_key_160("sovereign_doc")
        node.rpc_store(key_id, "SECRET_DOCUMENT_CONTENT")

        # Find existing value
        val, closer_nodes = node.rpc_find_value(key_id)
        self.assertEqual(val, "SECRET_DOCUMENT_CONTENT")
        self.assertEqual(len(closer_nodes), 0)

        # Find non-existent value returns closer nodes
        missing_id = hash_key_160("missing_key")
        val2, closer_nodes2 = node.rpc_find_value(missing_id)
        self.assertIsNone(val2)

    def test_07_rpc_find_node_sorting(self) -> None:
        node = KademliaNode(node_id=0, uri="local://pivot")
        # Add contacts at distances 100, 10, 50 from target 0
        node.update_contact(Contact(node_id=100, uri="node_100"))
        node.update_contact(Contact(node_id=10, uri="node_10"))
        node.update_contact(Contact(node_id=50, uri="node_50"))

        closest = node.rpc_find_node(target_id=0, count=3)
        self.assertEqual(len(closest), 3)
        # Should be sorted: 10, 50, 100
        self.assertEqual(closest[0].node_id, 10)
        self.assertEqual(closest[1].node_id, 50)
        self.assertEqual(closest[2].node_id, 100)

    def test_08_mesh_store_and_lookup(self) -> None:
        key_id, target_nodes = self.mesh.store_value(
            key="mesh_manifest_v1",
            value={"version": "1.0.0", "author": "Senin"},
        )
        self.assertGreater(len(target_nodes), 0)

        # Query across mesh
        retrieved = self.mesh.get_value("mesh_manifest_v1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["author"], "Senin")

    def test_09_mesh_nonexistent_key(self) -> None:
        val = self.mesh.get_value("ghost_key_never_stored")
        self.assertIsNone(val)

    def test_10_ascii_status_and_singleton(self) -> None:
        ascii_out = self.mesh.format_ascii_status()
        self.assertIn("LUCY STAGE 163: DISTRIBUTED HASH TABLE", ascii_out)
        self.assertIn("Senin", ascii_out)
        self.assertIn("Senin Ali K P", ascii_out)
        self.assertIn("Active Peers", ascii_out)

        d1 = get_dht_mesh()
        d2 = get_dht_mesh()
        self.assertIs(d1, d2)


if __name__ == "__main__":
    unittest.main()
