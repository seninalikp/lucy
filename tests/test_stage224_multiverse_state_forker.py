r"""
tests/test_stage224_multiverse_state_forker.py
Stage 224 Unit Tests: Universal Multi-Verse Counterfactual State Forker & Timeline Brancher
"""

import threading
import unittest

from backend.lucy_core.multiverse_state_forker import (
    MergeConflictStrategy,
    MultiverseStateForkerFabric,
    TimelineBranch,
    TimelineCommit,
    compute_state_hash,
    STAGE,
    STAGE_NAME,
)


class TestStage224MultiverseStateForker(unittest.TestCase):
    def setUp(self):
        self.fabric = MultiverseStateForkerFabric(initial_state={"energy": 100, "defense": "nominal"})

    def test_01_initialization_and_genesis(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 224)
        self.assertEqual(s["stage_name"], STAGE_NAME)
        self.assertEqual(s["active_branch"], "canonical")
        self.assertEqual(s["total_branches"], 1)
        self.assertIn("canonical", s["branch_ids"])
        canonical = self.fabric.branches["canonical"]
        self.assertEqual(len(canonical.commits), 1)
        self.assertEqual(canonical.current_state["energy"], 100)

    def test_02_fork_branch_lineage(self):
        branch_beta = self.fabric.fork_branch("timeline_beta", from_branch_id="canonical")
        self.assertEqual(branch_beta.branch_id, "timeline_beta")
        self.assertEqual(branch_beta.parent_branch_id, "canonical")
        self.assertEqual(branch_beta.current_state["energy"], 100)
        self.assertIn("timeline_beta", self.fabric.branches)

    def test_03_counterfactual_state_isolation(self):
        # Fork and mutate beta: canonical must remain untouched
        self.fabric.fork_branch("what_if_warp", from_branch_id="canonical")
        self.fabric.mutate_state("what_if_warp", {"energy": 9999, "warp_speed": 9.9})
        self.assertEqual(self.fabric.branches["what_if_warp"].current_state["energy"], 9999)
        self.assertEqual(self.fabric.branches["what_if_warp"].current_state["warp_speed"], 9.9)
        # Canonical unchanged:
        self.assertEqual(self.fabric.branches["canonical"].current_state["energy"], 100)
        self.assertNotIn("warp_speed", self.fabric.branches["canonical"].current_state)

    def test_04_commits_and_hash_integrity(self):
        commit1 = self.fabric.mutate_state("canonical", {"sensor": "active"}, "Enable sensors")
        self.assertEqual(commit1.branch_id, "canonical")
        self.assertTrue(len(commit1.state_hash) == 64)
        h1 = self.fabric.branches["canonical"].latest_state_hash
        self.assertEqual(h1, commit1.state_hash)

    def test_05_switch_active_branch(self):
        self.fabric.fork_branch("timeline_gamma")
        self.fabric.switch_active_branch("timeline_gamma")
        self.assertEqual(self.fabric.active_branch_id, "timeline_gamma")
        with self.assertRaises(ValueError):
            self.fabric.switch_active_branch("non_existent_branch")

    def test_06_compute_divergence(self):
        self.fabric.fork_branch("sim_branch")
        self.fabric.mutate_state("sim_branch", {"energy": 50, "shields": "offline"})
        div = self.fabric.compute_divergence("canonical", "sim_branch")
        self.assertIn("shields", div["added_in_b"])
        self.assertEqual(len(div["modified"]), 1)
        self.assertEqual(div["modified"][0]["key"], "energy")
        self.assertEqual(div["modified"][0]["val_a"], 100)
        self.assertEqual(div["modified"][0]["val_b"], 50)
        self.assertGreater(div["divergence_ratio"], 0.0)

    def test_07_three_way_merge_branch_prefer(self):
        self.fabric.fork_branch("recon_branch")
        self.fabric.mutate_state("recon_branch", {"energy": 250, "scan_depth": 10})
        res = self.fabric.merge_branches("recon_branch", "canonical", strategy=MergeConflictStrategy.BRANCH_PREFER)
        self.assertEqual(res["conflicts_count"], 1)
        self.assertEqual(self.fabric.branches["canonical"].current_state["energy"], 250)
        self.assertEqual(self.fabric.branches["canonical"].current_state["scan_depth"], 10)

    def test_08_three_way_merge_fail_on_conflict(self):
        self.fabric.fork_branch("conflict_branch")
        self.fabric.mutate_state("conflict_branch", {"energy": 42})
        with self.assertRaises(RuntimeError):
            self.fabric.merge_branches("conflict_branch", "canonical", strategy=MergeConflictStrategy.FAIL_ON_CONFLICT)

    def test_09_ascii_formatting_cp1252(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 224", tbl)
        self.assertIn("UNIVERSAL MULTI-VERSE", tbl)
        tbl.encode("cp1252")
        self.assertTrue(tbl.startswith("+--"))

    def test_10_multithreaded_concurrency(self):
        def worker(wid: int):
            b_name = f"worker_branch_{wid}"
            self.fabric.fork_branch(b_name)
            for i in range(5):
                self.fabric.mutate_state(b_name, {f"k_{wid}": i})
            _ = self.fabric.status()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertGreaterEqual(len(self.fabric.branches), 5)


if __name__ == "__main__":
    unittest.main()
