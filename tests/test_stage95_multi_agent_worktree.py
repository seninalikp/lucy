"""
tests/test_stage95_multi_agent_worktree.py
Stage 95 = Multi-Agent Autonomous Worktree & Branching Fabric

Verifies:
1. STAGE constant is 95.
2. spawn_branch creates isolated worktree directory and initializes branch metadata.
3. write_file and read_file operate strictly within the isolated worktree.
4. Main workspace files remain completely untouched during worktree modifications.
5. diff_branch produces accurate unified diffs against the base project.
6. Pre-merge AST syntax check rejects syntactically broken code.
7. Conflict detection catches concurrent changes in main workspace.
8. Safe merge applies verified modifications into the main workspace.
9. abandon_branch safely cleans up worktree files and transitions status.
10. list_branches filters branches by status.
11. Execution receipt ledger records receipts for spawn, merge, and abandon.
12. tree_status produces CP1252-safe ASCII table output.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.lucy_core.multi_agent_worktree import (
    STAGE,
    BranchStatus,
    MergeConflict,
    MergeResult,
    MultiAgentWorktreeFabric,
    WorktreeBranch,
)


class MockReceiptLedger:
    def __init__(self) -> None:
        self.receipts: List[Dict[str, Any]] = []

    def issue_receipt(
        self,
        action_category: str,
        operation: str,
        target: str,
        verified_outcome: str,
    ) -> Dict[str, Any]:
        rcpt = {
            "receipt_id": f"rcpt_{len(self.receipts)+1}",
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self.receipts.append(rcpt)
        return rcpt


class TestStage95MultiAgentWorktree(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Build basic workspace skeleton
        (self.root / "backend" / "lucy_core").mkdir(parents=True, exist_ok=True)
        (self.root / "tests").mkdir(parents=True, exist_ok=True)
        (self.root / "config").mkdir(parents=True, exist_ok=True)

        # Sample source file in main
        self.sample_code = 'def greet(name: str) -> str:\n    return f"Hello, {name}!"\n'
        (self.root / "backend" / "sample.py").write_text(self.sample_code, encoding="utf-8")

        self.mock_ledger = MockReceiptLedger()
        self.fabric = MultiAgentWorktreeFabric(
            project_root=self.root,
            receipt_ledger=self.mock_ledger,
            worktree_base_dir=self.root / "data" / "lucy" / "worktrees",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_stage_constant(self) -> None:
        self.assertEqual(STAGE, 95)

    def test_02_spawn_branch(self) -> None:
        branch = self.fabric.spawn_branch(
            branch_name="agent-coder-patch",
            task="Refactor sample function",
            agent_role="refactorer",
        )
        self.assertEqual(branch.branch_name, "agent-coder-patch")
        self.assertEqual(branch.agent_role, "refactorer")
        self.assertEqual(branch.status, BranchStatus.ACTIVE.value)
        self.assertTrue(Path(branch.worktree_dir).exists())
        self.assertTrue((Path(branch.worktree_dir) / "backend" / "sample.py").exists())

        # Check receipt
        self.assertEqual(len(self.mock_ledger.receipts), 1)
        self.assertEqual(self.mock_ledger.receipts[0]["action_category"], "WORKTREE_SPAWN")

    def test_03_write_and_read_isolation(self) -> None:
        self.fabric.spawn_branch("branch1", task="test isolation")
        new_code = 'def greet(name: str) -> str:\n    return f"Hey, {name}!"\n'
        ok = self.fabric.write_file("branch1", "backend/sample.py", new_code)
        self.assertTrue(ok)

        # Worktree file is updated
        worktree_content = self.fabric.read_file("branch1", "backend/sample.py")
        self.assertEqual(worktree_content, new_code)

        # Main project file remains completely untouched
        main_content = (self.root / "backend" / "sample.py").read_text(encoding="utf-8")
        self.assertEqual(main_content, self.sample_code)

    def test_04_diff_computation(self) -> None:
        self.fabric.spawn_branch("diff_branch", task="diff test")
        new_code = 'def greet(name: str) -> str:\n    return f"Greetings, {name}!"\n'
        self.fabric.write_file("diff_branch", "backend/sample.py", new_code)

        diffs = self.fabric.diff_branch("diff_branch")
        self.assertIn("backend/sample.py", diffs)
        self.assertIn("-    return f\"Hello, {name}!\"", diffs["backend/sample.py"])
        self.assertIn("+    return f\"Greetings, {name}!\"", diffs["backend/sample.py"])

    def test_05_pre_merge_syntax_rejection(self) -> None:
        self.fabric.spawn_branch("broken_syntax", task="break syntax")
        broken_code = "def syntax_error(:\n    pass\n"
        self.fabric.write_file("broken_syntax", "backend/sample.py", broken_code)

        result = self.fabric.merge_worktree("broken_syntax")
        self.assertFalse(result.success)
        self.assertIn("syntax", result.message.lower())

        # Main file remains safe
        main_content = (self.root / "backend" / "sample.py").read_text(encoding="utf-8")
        self.assertEqual(main_content, self.sample_code)

    def test_06_conflict_detection(self) -> None:
        self.fabric.spawn_branch("conflict_branch", task="conflict test")

        # Main file is edited independently after branch was spawned
        main_concurrent = 'def greet(name: str) -> str:\n    return "MAIN CONCURRENT"\n'
        (self.root / "backend" / "sample.py").write_text(main_concurrent, encoding="utf-8")

        # Branch also edits file with different content
        branch_edit = 'def greet(name: str) -> str:\n    return "BRANCH EDIT"\n'
        self.fabric.write_file("conflict_branch", "backend/sample.py", branch_edit)

        # Merge must reject due to conflict
        result = self.fabric.merge_worktree("conflict_branch")
        self.assertFalse(result.success)
        self.assertGreater(len(result.conflicts), 0)
        self.assertEqual(result.conflicts[0].rel_path, "backend/sample.py")

        branch = self.fabric.get_branch("conflict_branch")
        self.assertEqual(branch.status, BranchStatus.CONFLICT.value)

    def test_07_safe_merge(self) -> None:
        self.fabric.spawn_branch("clean_branch", task="clean update")
        new_code = 'def greet(name: str) -> str:\n    return f"Salutations, {name}!"\n'
        self.fabric.write_file("clean_branch", "backend/sample.py", new_code)

        result = self.fabric.merge_worktree("clean_branch")
        self.assertTrue(result.success)
        self.assertIn("backend/sample.py", result.merged_files)

        # Main file is now updated
        main_content = (self.root / "backend" / "sample.py").read_text(encoding="utf-8")
        self.assertEqual(main_content, new_code)

        branch = self.fabric.get_branch("clean_branch")
        self.assertEqual(branch.status, BranchStatus.MERGED.value)

        # Merge receipt issued
        merge_rcpts = [r for r in self.mock_ledger.receipts if r["action_category"] == "WORKTREE_MERGE"]
        self.assertEqual(len(merge_rcpts), 1)

    def test_08_abandon_branch(self) -> None:
        branch = self.fabric.spawn_branch("abandon_me", task="will be abandoned")
        worktree_path = Path(branch.worktree_dir)
        self.assertTrue(worktree_path.exists())

        ok = self.fabric.abandon_branch("abandon_me", remove_files=True)
        self.assertTrue(ok)
        self.assertFalse(worktree_path.exists())
        self.assertEqual(self.fabric.get_branch("abandon_me").status, BranchStatus.ABANDONED.value)

    def test_09_list_branches_filtering(self) -> None:
        self.fabric.spawn_branch("b_active", task="active")
        self.fabric.spawn_branch("b_merged", task="merged")
        self.fabric.spawn_branch("b_abandoned", task="abandoned")

        self.fabric.merge_worktree("b_merged")
        self.fabric.abandon_branch("b_abandoned")

        active_list = self.fabric.list_branches(status_filter="ACTIVE")
        merged_list = self.fabric.list_branches(status_filter="MERGED")
        abandoned_list = self.fabric.list_branches(status_filter="ABANDONED")

        self.assertEqual(len(active_list), 1)
        self.assertEqual(len(merged_list), 1)
        self.assertEqual(len(abandoned_list), 1)

    def test_10_terminal_summary_cp1252(self) -> None:
        self.fabric.spawn_branch("visual_branch", task="visualize", agent_role="fuzzer")
        summary = self.fabric.tree_status()

        # CP1252 encode safety
        encoded = summary.encode("cp1252")
        self.assertTrue(len(encoded) > 0)

        # No Unicode box drawing
        for ch in summary:
            self.assertFalse(0x2500 <= ord(ch) <= 0x257F)

        self.assertIn("+----------------------------------------------------------------------+", summary)
        self.assertIn("visual_branch", summary)

    def test_11_status_dictionary(self) -> None:
        st = self.fabric.status()
        self.assertEqual(st["stage"], 95)
        self.assertIn("total_branches", st)
        self.assertIn("active_branches", st)


if __name__ == "__main__":
    unittest.main()
