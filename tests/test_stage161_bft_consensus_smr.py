r"""
tests/test_stage161_bft_consensus_smr.py
Stage 161 Test Suite: Byzantine Fault Tolerant (BFT) State Machine Replication
Era 17: Distributed Consensus, Mesh Virtualization & High-Availability Primitives
"""

import unittest

from backend.lucy_core.bft_consensus_smr import (
    CREATOR,
    ERA,
    HMAC_SECRET,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    BFTConsensusCluster,
    BFTMessage,
    BFTNode,
    BFTPhase,
    BFTTransaction,
    get_bft_cluster,
)


class TestStage161BFTConsensusSMR(unittest.TestCase):
    def setUp(self) -> None:
        self.cluster = BFTConsensusCluster(node_count=4, fault_tolerance=1)

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 161)
        self.assertEqual(ERA, 17)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Byzantine Fault Tolerant (BFT) State Machine Replication",
        )

    def test_02_bft_transaction_digest(self) -> None:
        tx = BFTTransaction(
            tx_id="tx_test_1",
            op="SET",
            key="sovereign_core",
            value={"status": "online"},
            client_id="client_senin",
        )
        d = tx.digest()
        self.assertEqual(len(d), 64)
        # Deterministic digest
        self.assertEqual(d, tx.digest())

    def test_03_message_signature_and_verification(self) -> None:
        msg = BFTMessage(
            phase=BFTPhase.PREPARE,
            view=0,
            seq_num=1,
            tx_digest="abc123digest",
            node_id="replica_0",
        )
        self.assertFalse(msg.verify())
        msg.sign()
        self.assertTrue(msg.verify())

        # Tampering with payload fails verification
        msg.tx_digest = "tampered_digest"
        self.assertFalse(msg.verify())

    def test_04_cluster_initialization(self) -> None:
        self.assertEqual(self.cluster.node_count, 4)
        self.assertEqual(self.cluster.f, 1)
        self.assertEqual(self.cluster.quorum_size, 3)
        self.assertEqual(self.cluster.primary_id, "replica_0")
        self.assertEqual(self.cluster.current_view, 0)
        self.assertEqual(len(self.cluster.nodes), 4)

    def test_05_honest_consensus_proposal(self) -> None:
        ok, reason, tx = self.cluster.propose_transaction(
            op="SET",
            key="config/node_id",
            value="lucy_omega",
        )
        self.assertTrue(ok)
        self.assertIn("SUCCESS", reason)
        self.assertIsNotNone(tx)
        self.assertEqual(len(self.cluster.global_committed_txs), 1)

        val = self.cluster.read_state("config/node_id")
        self.assertEqual(val, "lucy_omega")

    def test_06_state_machine_operations(self) -> None:
        # SET
        self.cluster.propose_transaction(op="SET", key="balance/alice", value=100)
        self.assertEqual(self.cluster.read_state("balance/alice"), 100)

        # CAS (Compare-And-Swap)
        ok, _, _ = self.cluster.propose_transaction(
            op="CAS",
            key="balance/alice",
            value=[100, 150],
        )
        self.assertTrue(ok)
        self.assertEqual(self.cluster.read_state("balance/alice"), 150)

        # DEL
        ok, _, _ = self.cluster.propose_transaction(op="DEL", key="balance/alice", value=None)
        self.assertTrue(ok)
        self.assertIsNone(self.cluster.read_state("balance/alice"))

    def test_07_byzantine_fault_tolerance(self) -> None:
        # 1 node becomes Byzantine in a 4-node cluster (f=1)
        self.cluster.set_byzantine_fault("replica_3", is_byzantine=True)
        self.assertTrue(self.cluster.nodes["replica_3"].is_byzantine)

        # 3 honest nodes remain, which equals quorum_size (2f + 1 = 3)
        ok, reason, tx = self.cluster.propose_transaction(
            op="SET",
            key="security/key",
            value="sovereign_secret",
        )
        self.assertTrue(ok)
        self.assertIn("Quorum 3/4", reason)
        self.assertEqual(self.cluster.read_state("security/key"), "sovereign_secret")

    def test_08_quorum_failure_exceeding_f(self) -> None:
        # 2 nodes become Byzantine in a 4-node cluster (exceeds f=1)
        self.cluster.set_byzantine_fault("replica_2", is_byzantine=True)
        self.cluster.set_byzantine_fault("replica_3", is_byzantine=True)

        ok, reason, tx = self.cluster.propose_transaction(
            op="SET",
            key="security/key",
            value="should_fail",
        )
        self.assertFalse(ok)
        self.assertIn("Prepare quorum failed", reason)

    def test_09_view_change_failover(self) -> None:
        # Mark primary replica_0 as Byzantine
        self.cluster.set_byzantine_fault("replica_0", is_byzantine=True)

        # Trigger view change
        ok, new_view, new_primary = self.cluster.trigger_view_change()
        self.assertTrue(ok)
        self.assertEqual(new_view, 1)
        self.assertEqual(new_primary, "replica_1")

        # Now replica_1 is primary, proposal should succeed through replica_1
        ok_prop, _, tx = self.cluster.propose_transaction(
            op="SET",
            key="post_view_change",
            value="alive",
        )
        self.assertTrue(ok_prop)
        self.assertEqual(self.cluster.read_state("post_view_change"), "alive")

    def test_10_ascii_status_and_singleton(self) -> None:
        ascii_out = self.cluster.format_ascii_status()
        self.assertIn("LUCY STAGE 161: BFT CONSENSUS & STATE MACHINE REPLICATION", ascii_out)
        self.assertIn("Senin", ascii_out)
        self.assertIn("Senin Ali K P", ascii_out)
        self.assertIn("Cluster Size", ascii_out)
        self.assertIn("Quorum Size", ascii_out)

        c1 = get_bft_cluster()
        c2 = get_bft_cluster()
        self.assertIs(c1, c2)


if __name__ == "__main__":
    unittest.main()
