r"""
tests/test_stage165_multipaxos_commit.py
Stage 165 Test Suite: Multi-Paxos Distributed Transaction Commit Protocol
Era 17: Distributed Consensus, Mesh Virtualization & High-Availability Primitives
"""

import unittest

from backend.lucy_core.multipaxos_commit import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    MultiPaxosCluster,
    PaxosAcceptor,
    ProposalNum,
    SlotState,
    get_paxos_cluster,
)


class TestStage165MultiPaxosCommit(unittest.TestCase):
    def setUp(self) -> None:
        self.cluster = MultiPaxosCluster(node_count=5)

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 165)
        self.assertEqual(ERA, 17)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Multi-Paxos Distributed Transaction Commit Protocol",
        )

    def test_02_proposal_num_ordering(self) -> None:
        p1 = ProposalNum(round_num=1, proposer_id="acceptor_0")
        p2 = ProposalNum(round_num=2, proposer_id="acceptor_0")
        p3 = ProposalNum(round_num=1, proposer_id="acceptor_1")

        self.assertTrue(p1 < p2)
        self.assertTrue(p1 < p3)  # Lexical comparison on proposer_id for equal round
        self.assertFalse(p2 < p1)

    def test_03_cluster_init_acceptors(self) -> None:
        self.assertEqual(self.cluster.node_count, 5)
        self.assertEqual(self.cluster.quorum_size, 3)
        self.assertFalse(self.cluster.phase1_established)
        self.assertEqual(len(self.cluster.acceptors), 5)

    def test_04_phase1_leadership_establishment(self) -> None:
        ok = self.cluster.establish_leadership()
        self.assertTrue(ok)
        self.assertTrue(self.cluster.phase1_established)
        self.assertEqual(self.cluster.leader_round, 2)

    def test_05_steady_state_phase2_propose(self) -> None:
        # Initial proposal triggers Phase 1 then Phase 2
        ok1, slot1 = self.cluster.propose_slot_value({"action": "MUTATE_CONFIG", "key": "port"})
        self.assertTrue(ok1)
        self.assertEqual(slot1, 1)
        self.assertIn(1, self.cluster.committed_slots)

        # Subsequent proposal skips Phase 1 and directly commits via steady-state Phase 2
        ok2, slot2 = self.cluster.propose_slot_value({"action": "DEPLOY_AGENT", "id": "agent_alpha"})
        self.assertTrue(ok2)
        self.assertEqual(slot2, 2)
        self.assertIn(2, self.cluster.committed_slots)

    def test_06_slot_state_progression(self) -> None:
        acceptor = PaxosAcceptor("test_acc")
        prop = ProposalNum(round_num=10, proposer_id="leader_a")

        # Prepare
        ok_prep, prev_n, prev_v = acceptor.handle_prepare(prop, slot_id=5)
        self.assertTrue(ok_prep)
        self.assertIsNone(prev_n)

        # Accept
        ok_acc = acceptor.handle_accept(prop, slot_id=5, value="PAYLOAD_5")
        self.assertTrue(ok_acc)

        # Commit
        acceptor.handle_commit(slot_id=5, value="PAYLOAD_5")
        slot = acceptor.slots[5]
        self.assertTrue(slot.is_committed)
        self.assertEqual(slot.accepted_v, "PAYLOAD_5")

    def test_07_higher_proposal_preemption(self) -> None:
        acceptor = PaxosAcceptor("test_acc_preempt")
        p_high = ProposalNum(round_num=20, proposer_id="leader_high")
        p_low = ProposalNum(round_num=5, proposer_id="leader_low")

        acceptor.handle_prepare(p_high, slot_id=1)
        # Attempting prepare with lower proposal number fails
        ok_low, _, _ = acceptor.handle_prepare(p_low, slot_id=1)
        self.assertFalse(ok_low)

        # Attempting accept with lower proposal number fails
        ok_acc_low = acceptor.handle_accept(p_low, slot_id=1, value="STALE_VAL")
        self.assertFalse(ok_acc_low)

    def test_08_distributed_2pc_global_commit(self) -> None:
        ops = [
            {"account": "A", "amount": 50},
            {"account": "B", "amount": 100},
        ]
        ok, msg = self.cluster.execute_2pc_transaction("tx_commit_1", ops)
        self.assertTrue(ok)
        self.assertIn("GLOBAL_COMMIT", msg)
        self.assertEqual(self.cluster.total_transactions_2pc, 1)

    def test_09_distributed_2pc_global_abort(self) -> None:
        # Negative amount triggers abort
        ops = [
            {"account": "A", "amount": 50},
            {"account": "B", "amount": -10},
        ]
        ok, msg = self.cluster.execute_2pc_transaction("tx_abort_1", ops)
        self.assertFalse(ok)
        self.assertIn("GLOBAL_ABORT", msg)

    def test_10_ascii_status_and_singleton(self) -> None:
        ascii_out = self.cluster.format_ascii_status()
        self.assertIn("LUCY STAGE 165: MULTI-PAXOS CONSENSUS", ascii_out)
        self.assertIn("Senin", ascii_out)
        self.assertIn("Senin Ali K P", ascii_out)
        self.assertIn("Cluster Size", ascii_out)

        c1 = get_paxos_cluster()
        c2 = get_paxos_cluster()
        self.assertIs(c1, c2)


if __name__ == "__main__":
    unittest.main()
