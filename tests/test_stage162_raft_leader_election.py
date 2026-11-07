r"""
tests/test_stage162_raft_leader_election.py
Stage 162 Test Suite: Raft Leader Election & Distributed Heartbeat Sentinel
Era 17: Distributed Consensus, Mesh Virtualization & High-Availability Primitives
"""

import unittest

from backend.lucy_core.raft_leader_election import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    AppendEntriesArgs,
    NodeRole,
    RaftLogEntry,
    RaftNode,
    RequestVoteArgs,
    SovereignRaftCluster,
    get_raft_cluster,
)


class TestStage162RaftLeaderElection(unittest.TestCase):
    def setUp(self) -> None:
        self.cluster = SovereignRaftCluster(node_count=5)

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 162)
        self.assertEqual(ERA, 17)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Raft Leader Election & Distributed Heartbeat Sentinel",
        )

    def test_02_raft_log_entry(self) -> None:
        entry = RaftLogEntry(index=1, term=1, command={"set": "x", "val": 42})
        self.assertEqual(entry.index, 1)
        self.assertEqual(entry.term, 1)
        d = entry.to_dict()
        self.assertEqual(d["index"], 1)
        self.assertEqual(d["command"]["set"], "x")

    def test_03_cluster_init_roles(self) -> None:
        self.assertEqual(self.cluster.node_count, 5)
        self.assertEqual(self.cluster.majority_size, 3)
        self.assertIsNone(self.cluster.active_leader_id)
        for n in self.cluster.nodes.values():
            self.assertEqual(n.role, NodeRole.FOLLOWER)
            self.assertEqual(n.current_term, 0)
            self.assertEqual(len(n.log), 1)  # Root entry

    def test_04_successful_leader_election(self) -> None:
        ok = self.cluster.start_election("raft_node_0")
        self.assertTrue(ok)
        self.assertEqual(self.cluster.active_leader_id, "raft_node_0")
        leader = self.cluster.nodes["raft_node_0"]
        self.assertEqual(leader.role, NodeRole.LEADER)
        self.assertEqual(leader.current_term, 1)
        self.assertEqual(leader.election_wins, 1)

    def test_05_heartbeat_broadcast(self) -> None:
        self.cluster.start_election("raft_node_1")
        acks = self.cluster.broadcast_heartbeat()
        self.assertEqual(acks, 4)  # 4 peers acknowledged
        leader = self.cluster.nodes["raft_node_1"]
        self.assertEqual(leader.heartbeats_sent, 1)

        # Peer receives heartbeat
        peer = self.cluster.nodes["raft_node_0"]
        self.assertGreaterEqual(peer.heartbeats_received, 1)

    def test_06_log_replication_success(self) -> None:
        self.cluster.start_election("raft_node_2")
        ok, log_idx = self.cluster.replicate_command({"cmd": "UPDATE_STATE", "val": "OK"})
        self.assertTrue(ok)
        self.assertEqual(log_idx, 1)

        # Leader committed index
        leader = self.cluster.nodes["raft_node_2"]
        self.assertEqual(leader.commit_index, 1)

        # Followers received entry
        peer = self.cluster.nodes["raft_node_3"]
        self.assertEqual(peer.last_log_index(), 1)
        self.assertEqual(peer.log[1].command["val"], "OK")

    def test_07_higher_term_step_down(self) -> None:
        self.cluster.start_election("raft_node_0")
        leader = self.cluster.nodes["raft_node_0"]
        self.assertEqual(leader.role, NodeRole.LEADER)

        # Higher term RPC received by leader
        higher_term_args = AppendEntriesArgs(
            term=10,
            leader_id="raft_node_4",
            prev_log_index=0,
            prev_log_term=0,
            entries=[],
            leader_commit=0,
        )
        reply = leader.handle_append_entries(higher_term_args)
        self.assertEqual(leader.role, NodeRole.FOLLOWER)
        self.assertEqual(leader.current_term, 10)

    def test_08_split_vote_rejection(self) -> None:
        # If peers are on higher term, candidate vote is rejected
        for pid in ["raft_node_1", "raft_node_2", "raft_node_3", "raft_node_4"]:
            self.cluster.nodes[pid].current_term = 5

        # Candidate on term 0 attempts election -> will increment to 1, still < 5
        ok = self.cluster.start_election("raft_node_0")
        self.assertFalse(ok)
        cand = self.cluster.nodes["raft_node_0"]
        self.assertEqual(cand.role, NodeRole.FOLLOWER)

    def test_09_manual_step_down(self) -> None:
        self.cluster.start_election("raft_node_3")
        self.assertEqual(self.cluster.active_leader_id, "raft_node_3")

        stepped = self.cluster.step_down_leader()
        self.assertTrue(stepped)
        self.assertIsNone(self.cluster.active_leader_id)
        self.assertEqual(self.cluster.nodes["raft_node_3"].role, NodeRole.FOLLOWER)

    def test_10_ascii_status_and_singleton(self) -> None:
        ascii_out = self.cluster.format_ascii_status()
        self.assertIn("LUCY STAGE 162: RAFT LEADER ELECTION", ascii_out)
        self.assertIn("Senin", ascii_out)
        self.assertIn("Senin Ali K P", ascii_out)
        self.assertIn("Cluster Size", ascii_out)
        self.assertIn("Current Leader", ascii_out)

        c1 = get_raft_cluster()
        c2 = get_raft_cluster()
        self.assertIs(c1, c2)


if __name__ == "__main__":
    unittest.main()
