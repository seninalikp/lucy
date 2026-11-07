r"""
tests/test_stage198_daemon_mesh_sentinel.py
Stage 198: Sovereign Autonomous Daemon Mesh & Heartbeat Sentinel
Era 20: The Sovereign Bicentennial AGI Singularity & Autonomous Kernel Transcendence
"""

import unittest
from backend.lucy_core.daemon_mesh_sentinel import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    NodeHealthState,
    PeerNode,
    GossipPacket,
    DaemonMeshSentinelFabric,
)


class TestStage198DaemonMeshSentinel(unittest.TestCase):
    """10 Unit Tests for Stage 198 Daemon Mesh & Heartbeat Sentinel Fabric."""

    def setUp(self):
        self.fabric = DaemonMeshSentinelFabric(local_node_id="test_node_0")

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric.local_node_id, "test_node_0")
        self.assertEqual(self.fabric.primary_node_id, "test_node_0")
        self.assertEqual(self.fabric.epoch, 1)
        self.assertIn("test_node_0", self.fabric.peers)
        self.assertTrue(self.fabric.peers["test_node_0"].is_primary)

    def test_02_peer_registration(self):
        peer1 = self.fabric.register_peer("peer_node_1", "127.0.0.1", 9001)
        self.assertEqual(peer1.node_id, "peer_node_1")
        self.assertEqual(peer1.state, NodeHealthState.ALIVE)
        self.assertFalse(peer1.is_primary)
        self.assertEqual(len(self.fabric.peers), 2)

    def test_03_record_heartbeat(self):
        self.fabric.register_peer("peer_node_2")
        self.fabric.peers["peer_node_2"].state = NodeHealthState.SUSPECT
        self.fabric.peers["peer_node_2"].suspicion_score = 5.2

        ok = self.fabric.record_heartbeat("peer_node_2", timestamp_ms=10000)
        self.assertTrue(ok)
        peer = self.fabric.peers["peer_node_2"]
        self.assertEqual(peer.last_heartbeat_ms, 10000)
        self.assertEqual(peer.suspicion_score, 0.0)
        self.assertEqual(peer.state, NodeHealthState.ALIVE)

        # Non-existent node
        self.assertFalse(self.fabric.record_heartbeat("ghost_node"))

    def test_04_generate_gossip_packet(self):
        self.fabric.register_peer("peer_3")
        pkt = self.fabric.generate_gossip_packet()
        self.assertEqual(pkt.sender_id, "test_node_0")
        self.assertEqual(pkt.epoch, 1)
        self.assertIn("test_node_0", pkt.peer_states)
        self.assertIn("peer_3", pkt.peer_states)
        self.assertEqual(self.fabric._gossip_packets_sent, 1)

    def test_05_receive_gossip_updates_peer_states(self):
        self.fabric.register_peer("peer_4")
        g_pkt = GossipPacket(
            packet_id="GOSSIP-TEST-1",
            sender_id="peer_5",
            epoch=1,
            peer_states={
                "peer_4": "DEAD",
                "test_node_0": "DEAD",  # Incoming gossip says local node is dead; must be ignored!
            },
            timestamp_ms=5000,
        )
        updates = self.fabric.receive_gossip(g_pkt)
        self.assertEqual(updates, 1)
        self.assertEqual(self.fabric.peers["peer_4"].state, NodeHealthState.DEAD)
        self.assertEqual(self.fabric.peers["test_node_0"].state, NodeHealthState.ALIVE)

    def test_06_evaluate_health_suspect_transition(self):
        p = self.fabric.register_peer("peer_suspect")
        base_time = 100000
        p.last_heartbeat_ms = base_time

        # Advance time by 2000ms (>= suspect 1500, < dead 3000)
        eval_res = self.fabric.evaluate_health_and_failover(
            current_time_ms=base_time + 2000,
            suspect_threshold_ms=1500,
            dead_threshold_ms=3000,
        )
        self.assertEqual(eval_res["state_changes"].get("peer_suspect"), "SUSPECT")
        self.assertEqual(p.state, NodeHealthState.SUSPECT)
        self.assertGreater(p.suspicion_score, 1.0)

    def test_07_evaluate_health_dead_transition(self):
        p = self.fabric.register_peer("peer_dead")
        base_time = 100000
        p.last_heartbeat_ms = base_time

        # Advance time by 3500ms (>= dead 3000)
        eval_res = self.fabric.evaluate_health_and_failover(
            current_time_ms=base_time + 3500,
            suspect_threshold_ms=1500,
            dead_threshold_ms=3000,
        )
        self.assertEqual(eval_res["state_changes"].get("peer_dead"), "DEAD")
        self.assertEqual(p.state, NodeHealthState.DEAD)

    def test_08_automated_failover_when_primary_dies(self):
        # Configure peer_1 as primary
        peer1 = self.fabric.register_peer("node_1")
        peer2 = self.fabric.register_peer("node_2")

        for p in self.fabric.peers.values():
            p.is_primary = False
        peer1.is_primary = True
        self.fabric.primary_node_id = "node_1"

        base_time = 100000
        peer1.last_heartbeat_ms = base_time
        peer2.last_heartbeat_ms = base_time + 4000

        # Advance time to base_time + 4000: node_1 delta = 4000 >= 3000 -> DEAD!
        eval_res = self.fabric.evaluate_health_and_failover(
            current_time_ms=base_time + 4000,
            suspect_threshold_ms=1500,
            dead_threshold_ms=3000,
        )

        self.assertTrue(eval_res["failover_executed"])
        self.assertEqual(peer1.state, NodeHealthState.DEAD)
        self.assertFalse(peer1.is_primary)
        # Lowest alive node among ['node_2', 'test_node_0'] -> 'node_2'
        self.assertEqual(self.fabric.primary_node_id, "node_2")
        self.assertTrue(peer2.is_primary)
        self.assertEqual(self.fabric.epoch, 2)
        self.assertEqual(self.fabric._failovers_triggered, 1)

    def test_09_self_healing_recovery_on_heartbeat(self):
        p = self.fabric.register_peer("recovering_node")
        p.state = NodeHealthState.DEAD
        self.assertEqual(p.state, NodeHealthState.DEAD)

        self.fabric.record_heartbeat("recovering_node")
        self.assertEqual(p.state, NodeHealthState.ALIVE)

    def test_10_ascii_status_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 198)
        self.assertEqual(s["era"], 20)
        self.assertEqual(s["local_node_id"], "test_node_0")

        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 198: SOVEREIGN AUTONOMOUS DAEMON MESH & SENTINEL", ascii_out)
        self.assertIn("Local Node ID         : test_node_0", ascii_out)


if __name__ == "__main__":
    unittest.main()
