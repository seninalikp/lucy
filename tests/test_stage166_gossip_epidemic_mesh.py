r"""
tests/test_stage166_gossip_epidemic_mesh.py
Stage 166 Test Suite: Gossip Protocol & Epidemic State Propagation Engine
Era 17: Distributed Consensus, Mesh Virtualization & High-Availability Primitives
"""

import unittest

from backend.lucy_core.gossip_epidemic_mesh import (
    CREATOR,
    DEFAULT_FANOUT,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    GossipPeer,
    NodeHealth,
    Rumor,
    SovereignGossipMesh,
    get_gossip_mesh,
)


class TestStage166GossipEpidemicMesh(unittest.TestCase):
    def setUp(self) -> None:
        self.mesh = SovereignGossipMesh(node_count=8, fanout=3)

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 166)
        self.assertEqual(ERA, 17)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Gossip Protocol & Epidemic State Propagation Engine",
        )
        self.assertEqual(DEFAULT_FANOUT, 3)

    def test_02_rumor_dataclass(self) -> None:
        r = Rumor(
            rumor_id="r1",
            key="config/rate",
            value=1000,
            version=1,
            origin_node="peer_0",
        )
        self.assertEqual(r.key, "config/rate")
        self.assertEqual(r.version, 1)
        self.assertEqual(r.max_rounds, 15)
        d = r.to_dict()
        self.assertEqual(d["value"], 1000)

    def test_03_peer_infect_state(self) -> None:
        peer = GossipPeer("test_p0")
        rumor = peer.infect("network/ip", "10.0.0.1")
        self.assertEqual(rumor.origin_node, "test_p0")
        self.assertEqual(rumor.version, 1)
        self.assertEqual(peer.state_store["network/ip"], ("10.0.0.1", 1))
        self.assertIn(rumor.rumor_id, peer.active_rumors)

    def test_04_peer_receive_newer_rumor(self) -> None:
        p1 = GossipPeer("p1")
        p2 = GossipPeer("p2")

        rumor = p1.infect("shared_key", "VALUE_NEW")
        pull = p2.receive_rumors([rumor])
        self.assertEqual(len(pull), 0)
        self.assertEqual(p2.state_store["shared_key"], ("VALUE_NEW", 1))

    def test_05_peer_pull_reply_older_rumor(self) -> None:
        p1 = GossipPeer("p1")
        p2 = GossipPeer("p2")

        # p2 has version 2
        p2.infect("key_x", "OLD_VAL")
        p2.infect("key_x", "LATEST_VAL")  # Version 2

        # p1 sends older version 1
        stale_rumor = Rumor("r_stale", "key_x", "OLD_VAL", version=1, origin_node="p1")
        pull_reply = p2.receive_rumors([stale_rumor])
        self.assertEqual(len(pull_reply), 1)
        self.assertEqual(pull_reply[0].version, 2)
        self.assertEqual(pull_reply[0].value, "LATEST_VAL")

    def test_06_single_gossip_round_propagation(self) -> None:
        self.mesh.seed_update("peer_0", "cluster_epoch", 42)
        transfers = self.mesh.execute_gossip_round()
        self.assertGreater(transfers, 0)
        self.assertEqual(self.mesh.total_rounds_executed, 1)

    def test_07_full_mesh_convergence(self) -> None:
        self.mesh.seed_update("peer_0", "mesh_manifest_v2", {"sha": "abc"})
        converged, rounds, ms = self.mesh.run_until_convergence("mesh_manifest_v2", max_rounds=15)
        self.assertTrue(converged)
        self.assertLessEqual(rounds, 10)  # Logarithmic convergence

        # Verify all alive peers have the exact value
        for p in self.mesh.nodes.values():
            val, ver = p.state_store.get("mesh_manifest_v2", (None, 0))
            self.assertEqual(val, {"sha": "abc"})
            self.assertEqual(ver, 1)

    def test_08_dead_node_skipped(self) -> None:
        self.mesh.nodes["peer_7"].health = NodeHealth.DEAD
        self.mesh.seed_update("peer_0", "dead_test", 999)
        converged, _, _ = self.mesh.run_until_convergence("dead_test", max_rounds=15)
        self.assertTrue(converged)
        # Dead node did not receive update
        self.assertNotIn("dead_test", self.mesh.nodes["peer_7"].state_store)

    def test_09_rumor_aging_and_expiry(self) -> None:
        peer = GossipPeer("p_aging")
        r = peer.infect("temp", 1)
        r.max_rounds = 2
        # After 2 rounds sent, rumor is aged out
        self.mesh.nodes["p_aging"] = peer
        self.mesh.execute_gossip_round()
        self.mesh.execute_gossip_round()
        self.assertNotIn(r.rumor_id, peer.active_rumors)

    def test_10_ascii_status_and_singleton(self) -> None:
        ascii_out = self.mesh.format_ascii_status()
        self.assertIn("LUCY STAGE 166: GOSSIP PROTOCOL & EPIDEMIC STATE", ascii_out)
        self.assertIn("Senin", ascii_out)
        self.assertIn("Senin Ali K P", ascii_out)
        self.assertIn("Cluster Size", ascii_out)

        g1 = get_gossip_mesh()
        g2 = get_gossip_mesh()
        self.assertIs(g1, g2)


if __name__ == "__main__":
    unittest.main()
