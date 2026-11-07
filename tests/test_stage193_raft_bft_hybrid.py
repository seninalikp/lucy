r"""
tests/test_stage193_raft_bft_hybrid.py
Stage 193: Sovereign Distributed Consensus Raft-BFT Hybrid
Era 20: The Sovereign Bicentennial AGI Singularity & Autonomous Kernel Transcendence
"""

import unittest
from backend.lucy_core.raft_bft_hybrid import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    DEFAULT_CLUSTER_SIZE,
    MessageType,
    LogEntry,
    ConsensusMessage,
    BFTNode,
    RaftBFTHybridFabric,
)


class TestStage193RaftBFTHybrid(unittest.TestCase):
    """10 Unit Tests for Stage 193 Sovereign Raft-BFT Hybrid Consensus Fabric."""

    def setUp(self):
        self.fabric = RaftBFTHybridFabric(cluster_size=4, byzantine_nodes=1)

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric.cluster_size, 4)
        self.assertEqual(self.fabric.f, 1)
        self.assertEqual(self.fabric.quorum_size, 3)
        self.assertEqual(self.fabric.leader_id, "node_0")
        self.assertEqual(self.fabric.current_term, 1)
        self.assertEqual(len(self.fabric.nodes), 4)
        byz_count = sum(1 for n in self.fabric.nodes.values() if n.is_byzantine)
        self.assertEqual(byz_count, 1)

    def test_02_digest_computation(self):
        node = self.fabric.nodes["node_0"]
        cmd1 = {"action": "write", "key": "senin", "val": 200}
        cmd2 = {"val": 200, "action": "write", "key": "senin"}
        d1 = node.compute_digest(cmd1)
        d2 = node.compute_digest(cmd2)
        self.assertEqual(d1, d2, "JSON key ordering should not affect digest")
        self.assertEqual(len(d1), 64)

    def test_03_pre_prepare_signature_verification(self):
        node_1 = self.fabric.nodes["node_1"]
        node_0 = self.fabric.nodes["node_0"]
        cmd = {"state": "active"}
        digest = node_0.compute_digest(cmd)
        sig = node_0._sign(f"1:1:{digest}")
        valid_entry = LogEntry(term=1, index=1, command=cmd, digest=digest, leader_sig=sig)

        res = node_1.receive_pre_prepare(valid_entry, leader_id="node_0")
        self.assertIsNotNone(res)
        self.assertEqual(res.msg_type, MessageType.PREPARE)
        self.assertEqual(res.node_id, "node_1")

        # Invalid leader sig
        tampered_entry = LogEntry(term=1, index=2, command=cmd, digest=digest, leader_sig="bogus_sig")
        tampered_res = node_1.receive_pre_prepare(tampered_entry, leader_id="node_0")
        self.assertIsNone(tampered_res)

    def test_04_equivocation_detection(self):
        node_1 = self.fabric.nodes["node_1"]
        node_0 = self.fabric.nodes["node_0"]
        cmd1 = {"val": "alpha"}
        d1 = node_0.compute_digest(cmd1)
        sig1 = node_0._sign(f"1:10:{d1}")
        entry1 = LogEntry(term=1, index=10, command=cmd1, digest=d1, leader_sig=sig1)
        res1 = node_1.receive_pre_prepare(entry1, leader_id="node_0")
        self.assertIsNotNone(res1)

        # Conflicting entry for the same index 10
        cmd2 = {"val": "beta_byzantine"}
        d2 = node_0.compute_digest(cmd2)
        sig2 = node_0._sign(f"1:10:{d2}")
        entry2 = LogEntry(term=1, index=10, command=cmd2, digest=d2, leader_sig=sig2)
        res2 = node_1.receive_pre_prepare(entry2, leader_id="node_0")
        self.assertIsNone(res2)
        self.assertGreaterEqual(node_1.equivocations_detected, 1)

    def test_05_prepare_phase_and_certificate(self):
        node_1 = self.fabric.nodes["node_1"]
        term = 1
        index = 5
        digest = "a" * 64

        # Send prepare votes from node_0, node_1, node_2
        sig0 = self.fabric.nodes["node_0"]._sign(f"{term}:{index}:{digest}")
        sig1 = self.fabric.nodes["node_1"]._sign(f"{term}:{index}:{digest}")
        sig2 = self.fabric.nodes["node_2"]._sign(f"{term}:{index}:{digest}")

        m0 = ConsensusMessage(MessageType.PREPARE, "node_0", term, index, digest, sig0)
        m1 = ConsensusMessage(MessageType.PREPARE, "node_1", term, index, digest, sig1)
        m2 = ConsensusMessage(MessageType.PREPARE, "node_2", term, index, digest, sig2)

        r0 = node_1.receive_prepare(m0, quorum_needed=3)
        self.assertIsNone(r0)  # Count = 1 < 3
        r1 = node_1.receive_prepare(m1, quorum_needed=3)
        self.assertIsNone(r1)  # Count = 2 < 3
        r2 = node_1.receive_prepare(m2, quorum_needed=3)
        self.assertIsNotNone(r2)  # Count = 3 >= 3 -> Prepared Certificate achieved
        self.assertEqual(r2.msg_type, MessageType.COMMIT)

    def test_06_commit_phase_and_state_machine_application(self):
        node_1 = self.fabric.nodes["node_1"]
        cmd = {"bicentennial_target": 200}
        digest = node_1.compute_digest(cmd)
        sig = self.fabric.nodes["node_0"]._sign(f"1:2:{digest}")
        entry = LogEntry(term=1, index=2, command=cmd, digest=digest, leader_sig=sig)
        node_1.receive_pre_prepare(entry, "node_0")

        # Deliver commits
        for nid in ["node_0", "node_1", "node_2"]:
            s = self.fabric.nodes[nid]._sign(f"1:2:{digest}")
            c_msg = ConsensusMessage(MessageType.COMMIT, nid, 1, 2, digest, s)
            node_1.receive_commit(c_msg, quorum_needed=3)

        self.assertEqual(node_1.state_machine.get("bicentennial_target"), 200)

    def test_07_end_to_end_propose_command_success(self):
        cmd = {"sovereign_operator": "Senin", "status": "ASCENDANT"}
        success, entry = self.fabric.propose_command(cmd)
        self.assertTrue(success)
        self.assertIsNotNone(entry)
        self.assertTrue(entry.is_committed)
        self.assertEqual(self.fabric._proposals_committed, 1)

        # Check honest nodes applied the command
        for nid, node in self.fabric.nodes.items():
            if not node.is_byzantine:
                self.assertEqual(node.state_machine.get("sovereign_operator"), "Senin")

    def test_08_byzantine_node_vote_rejection(self):
        # Byzantine node is node_3
        byz_node = self.fabric.nodes["node_3"]
        self.assertTrue(byz_node.is_byzantine)

        # Pre-prepare to byzantine node returns corrupted digest
        cmd = {"payload": "test"}
        digest = "b" * 64
        sig = self.fabric.nodes["node_0"]._sign(f"1:3:{digest}")
        entry = LogEntry(term=1, index=3, command=cmd, digest=digest, leader_sig=sig)
        byz_msg = byz_node.receive_pre_prepare(entry, "node_0")

        self.assertIsNotNone(byz_msg)
        self.assertNotEqual(byz_msg.digest, digest)  # Corrupted!

        # Honest node receiving this byzantine prepare vote will not advance target digest
        honest_node = self.fabric.nodes["node_1"]
        honest_node.receive_prepare(byz_msg, quorum_needed=3)
        k = (1, 3, digest)
        self.assertNotIn("node_3", honest_node.prepare_votes[k])

    def test_09_view_change_progression(self):
        self.assertEqual(self.fabric.current_term, 1)
        self.assertEqual(self.fabric.leader_id, "node_0")

        ok = self.fabric.trigger_view_change(2)
        self.assertTrue(ok)
        self.assertEqual(self.fabric.current_term, 2)
        self.assertEqual(self.fabric.leader_id, "node_1")

        for node in self.fabric.nodes.values():
            self.assertEqual(node.current_term, 2)
            self.assertEqual(node.leader_id, "node_1")

    def test_10_ascii_status_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 193)
        self.assertEqual(s["era"], 20)
        self.assertEqual(s["byzantine_tolerance_f"], 1)

        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 193: SOVEREIGN DISTRIBUTED CONSENSUS RAFT-BFT HYBRID", ascii_out)
        self.assertIn("Fault Tolerance (f)   : 1 Byzantine Nodes", ascii_out)
        self.assertIn("BFT Quorum (2f + 1)   : 3 Replicas Needed", ascii_out)


if __name__ == "__main__":
    unittest.main()
