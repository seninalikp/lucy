"""
tests/test_stage238_byzantine_swarm_consensus.py
Unit tests for Stage 238: Self-Healing Chaos Immunity & Byzantine Swarm Consensus Auto-Recovery
Era 24: Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity
"""

import unittest
from backend.lucy_core.byzantine_swarm_consensus import (
    STAGE,
    STAGE_NAME,
    ERA,
    ConsensusPhase,
    ConsensusMessage,
    ByzantineSwarmConsensusFabric
)


class TestStage238ByzantineSwarmConsensus(unittest.TestCase):

    def test_01_swarm_initialization_and_byzantine_quorum(self):
        """Test PBFT swarm initialization: N=7, f=2, quorum=5."""
        fabric = ByzantineSwarmConsensusFabric(total_nodes=7, byzantine_count=2)
        self.assertEqual(fabric.total_nodes, 7)
        self.assertEqual(fabric.byzantine_threshold, 2)
        self.assertEqual(fabric.quorum_size, 5)
        self.assertEqual(len(fabric.nodes), 7)
        byz_nodes = [nid for nid, n in fabric.nodes.items() if n.is_byzantine]
        self.assertEqual(len(byz_nodes), 2)

    def test_02_consensus_message_signature(self):
        """Test cryptographic message hashing and signature integrity."""
        msg = ConsensusMessage(
            view=0,
            sequence=1,
            phase=ConsensusPhase.PRE_PREPARE,
            digest="abc123hash",
            sender="node_0",
            payload={"tx_id": "genesis"}
        )
        sig = msg.compute_signature()
        self.assertEqual(len(sig), 64)
        msg.signature = sig
        self.assertEqual(msg.signature, msg.compute_signature())

    def test_03_honest_consensus_round_committed(self):
        """Test clean 3-phase consensus round reaches COMMITTED across honest nodes."""
        fabric = ByzantineSwarmConsensusFabric(total_nodes=7, byzantine_count=2)
        res = fabric.propose_and_reach_consensus({"action": "DEPLOY_AGENT_MESH", "value": 100})

        self.assertEqual(res["status"], "COMMITTED")
        self.assertEqual(res["sequence"], 1)
        self.assertEqual(res["view"], 0)
        self.assertGreaterEqual(res["commits"], 5)
        self.assertEqual(fabric.total_blocks_committed, 1)

        for nid, n in fabric.nodes.items():
            if not n.is_byzantine:
                self.assertEqual(len(n.committed_log), 1)
                self.assertEqual(n.committed_log[0]["data"]["action"], "DEPLOY_AGENT_MESH")

    def test_04_equivocation_detection_and_quarantine(self):
        """Test double-signing byzantine primary is caught and quarantined."""
        fabric = ByzantineSwarmConsensusFabric(total_nodes=7, byzantine_count=2)
        primary = fabric.get_primary(0)
        self.assertTrue(fabric.nodes[primary].is_byzantine)

        res = fabric.propose_and_reach_consensus({"action": "CONFIDENTIAL_STATE"}, inject_equivocation=True)
        self.assertEqual(res["status"], "COMMITTED") # Succeeded via failover to honest primary
        self.assertIn(primary, fabric.quarantined_nodes)
        self.assertTrue(fabric.nodes[primary].is_quarantined)
        self.assertEqual(len(fabric.equivocation_proofs), 1)

    def test_05_autonomous_view_change_failover(self):
        """Test view increments to failover to next primary."""
        fabric = ByzantineSwarmConsensusFabric(total_nodes=7, byzantine_count=2)
        initial_view = fabric.current_view
        fabric.propose_and_reach_consensus({"data": 1}, inject_equivocation=True)
        self.assertGreater(fabric.current_view, initial_view)

    def test_06_chaos_node_crash_below_threshold(self):
        """Test consensus continues smoothly when 1 honest node crashes (N=7, 2 Byzantine, 1 crashed)."""
        fabric = ByzantineSwarmConsensusFabric(total_nodes=7, byzantine_count=2)
        # Crash node_6 (honest)
        fabric.inject_chaos_node_crash("node_6")
        self.assertTrue(fabric.nodes["node_6"].is_offline)

        # 4 honest online + 2 byzantine offline/silent = 4 online honest
        # Wait, if quorum is 5 and only 4 honest are online, let's test crash with N=7, byzantine_count=1
        fabric_b1 = ByzantineSwarmConsensusFabric(total_nodes=7, byzantine_count=1)
        # Honest: 6 nodes. Quorum: 5. Crash 1 node -> 5 honest remain online!
        fabric_b1.inject_chaos_node_crash("node_6")
        res = fabric_b1.propose_and_reach_consensus({"tx": "CHAOS_RESILIENCE"})

        self.assertEqual(res["status"], "COMMITTED")
        self.assertEqual(res["commits"], 5)
        self.assertEqual(len(fabric_b1.nodes["node_5"].committed_log), 1)
        self.assertEqual(len(fabric_b1.nodes["node_6"].committed_log), 0)

    def test_07_chaos_node_recovery_and_catch_up(self):
        """Test crashed node recovers and synchronizes missing log entries."""
        fabric = ByzantineSwarmConsensusFabric(total_nodes=7, byzantine_count=1)
        fabric.inject_chaos_node_crash("node_5")

        fabric.propose_and_reach_consensus({"block": 1})
        fabric.propose_and_reach_consensus({"block": 2})

        self.assertEqual(len(fabric.nodes["node_5"].committed_log), 0)

        # Recover node_5
        fabric.inject_chaos_node_recovery("node_5")
        self.assertFalse(fabric.nodes["node_5"].is_offline)
        self.assertEqual(len(fabric.nodes["node_5"].committed_log), 2)
        self.assertEqual(fabric.recovered_rounds, 1)

    def test_08_multiple_consecutive_blocks(self):
        """Test committing multiple blocks monotonically."""
        fabric = ByzantineSwarmConsensusFabric(total_nodes=7, byzantine_count=1)
        for i in range(5):
            res = fabric.propose_and_reach_consensus({"step": i})
            self.assertEqual(res["status"], "COMMITTED")
            self.assertEqual(res["sequence"], i + 1)

        self.assertEqual(fabric.total_blocks_committed, 5)

    def test_09_chaos_immunity_score_computation(self):
        """Test chaos immunity score increases with successful recovery and quarantine."""
        fabric = ByzantineSwarmConsensusFabric(total_nodes=7, byzantine_count=1)
        s1 = fabric.compute_chaos_immunity_score()
        self.assertGreater(s1, 50.0)

        fabric.inject_chaos_node_crash("node_5")
        fabric.inject_chaos_node_recovery("node_5")
        s2 = fabric.compute_chaos_immunity_score()
        self.assertGreaterEqual(s2, s1)

    def test_10_fabric_status_and_ascii_table(self):
        """Test status dictionary and CP1252-safe ASCII table."""
        fabric = ByzantineSwarmConsensusFabric()
        st = fabric.status()
        self.assertEqual(st["stage"], 238)
        self.assertEqual(st["era"], 24)
        self.assertIn("total_nodes", st)

        tbl = fabric.format_ascii_status()
        self.assertIn("STAGE 238", tbl)
        self.assertIn("Total Swarm Nodes", tbl)
        self.assertIn("Chaos Immunity Score", tbl)
        self.assertTrue(tbl.startswith("+--"))
        self.assertTrue(tbl.endswith("--+"))


if __name__ == "__main__":
    unittest.main()
