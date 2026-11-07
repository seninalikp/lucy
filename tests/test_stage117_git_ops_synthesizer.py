r"""
tests/test_stage117_git_ops_synthesizer.py
Comprehensive test suite for Stage 117: Autonomous GitOps Engine
Era 12: The Autonomous Cognitive Matrix & Distributed IPC Fabric
"""

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.git_ops_synthesizer import (
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    STAGE,
    AutonomousGitOpsSynthesizer,
    ChangelogReport,
    ConventionalCommitProposal,
    GitOpsStatus,
)


class MockReceiptLedger:
    def __init__(self) -> None:
        self.receipts = []

    def record_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        rcpt = {
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self.receipts.append(rcpt)
        return rcpt


class TestStage117GitOpsSynthesizer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.data_dir = self.root / "data" / "gitops"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.receipt_ledger = MockReceiptLedger()

        # Create dummy initial repo structure
        (self.root / "backend" / "lucy_core").mkdir(parents=True, exist_ok=True)
        (self.root / "backend" / "lucy_core" / "init.py").write_text("# Initial file\n", encoding="utf-8")

        self.gitops = AutonomousGitOpsSynthesizer(
            project_root=self.root,
            data_dir=self.data_dir,
            receipt_ledger=self.receipt_ledger,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_initialization(self) -> None:
        st = self.gitops.status()
        self.assertEqual(st["stage"], 117)
        self.assertEqual(st["era"], 12)
        self.assertEqual(st["creator"], CREATOR_NAME)
        self.assertEqual(st["creator_full_name"], CREATOR_FULL_NAME)
        self.assertIsInstance(st["is_git_repo"], bool)

    def test_02_snapshot_status_untracked_and_modified(self) -> None:
        # Create new untracked file
        (self.root / "new_module.py").write_text("print('new')\n", encoding="utf-8")

        # Modify existing file
        (self.root / "backend" / "lucy_core" / "init.py").write_text("# Modified file content\n", encoding="utf-8")

        status = self.gitops.get_status()
        self.assertFalse(status.is_clean)
        self.assertIn("new_module.py", status.untracked_files)
        self.assertIn("backend/lucy_core/init.py", status.modified_files)

    def test_03_synthesize_commit_feat(self) -> None:
        files = ["backend/lucy_core/git_ops_synthesizer.py", "backend/lucy_core/stage117.py"]
        prop = self.gitops.synthesize_commit_proposal(files)

        self.assertIsInstance(prop, ConventionalCommitProposal)
        self.assertEqual(prop.type, "feat")
        self.assertEqual(prop.scope, "stage117")
        self.assertIn("feat(stage117):", prop.raw_message)
        self.assertIn("Touched files:", prop.body)

    def test_04_synthesize_commit_test(self) -> None:
        files = ["tests/test_stage117_gitops.py"]
        prop = self.gitops.synthesize_commit_proposal(files)

        self.assertEqual(prop.type, "test")
        self.assertEqual(prop.scope, "stage117")
        self.assertIn("test(stage117):", prop.raw_message)

    def test_05_synthesize_commit_clean(self) -> None:
        prop = self.gitops.synthesize_commit_proposal([])
        self.assertEqual(prop.type, "chore")
        self.assertEqual(prop.scope, "core")
        self.assertIn("zero working tree drift", prop.subject)

    def test_06_generate_changelog(self) -> None:
        report = self.gitops.generate_changelog(era=12)

        self.assertIsInstance(report, ChangelogReport)
        self.assertEqual(report.era, 12)
        self.assertIn("Release Changelog: Lucy OS", report.markdown)
        self.assertIn("Stage 111: Proactive Workspace & Process Sensor Daemon", report.markdown)
        self.assertIn("Stage 117: Autonomous GitOps Engine", report.markdown)
        self.assertIn(CREATOR_NAME, report.markdown)
        self.assertTrue(self.gitops.changelog_file.exists())

    def test_07_preflight_conflict_clean(self) -> None:
        base = "def compute():\n    return 42\n"
        incoming = "def compute():\n    return 42 * 2\n"

        check = self.gitops.check_preflight_conflicts(base, incoming)
        self.assertTrue(check["has_changes"])
        self.assertFalse(check["has_raw_conflict_markers"])
        self.assertTrue(check["safe_to_apply"])

    def test_08_preflight_conflict_markers_detected(self) -> None:
        base = "line 1\n"
        incoming = "<<<<<<< HEAD\nline A\n=======\nline B\n>>>>>>> branch\n"

        check = self.gitops.check_preflight_conflicts(base, incoming)
        self.assertTrue(check["has_raw_conflict_markers"])
        self.assertFalse(check["safe_to_apply"])

    def test_09_receipt_ledger_integration(self) -> None:
        self.gitops.synthesize_commit_proposal(["file.py"])
        self.gitops.generate_changelog(era=12)

        cats = [r["action_category"] for r in self.receipt_ledger.receipts]
        self.assertIn("GITOPS_COMMIT_SYNTHESIZED", cats)
        self.assertIn("GITOPS_CHANGELOG_GENERATED", cats)

    def test_10_ascii_status_table_formatting(self) -> None:
        tbl = self.gitops.format_gitops_status_table()

        self.assertIn("LUCY OS - AUTONOMOUS GITOPS ENGINE", tbl)
        self.assertIn("Repository Mode", tbl)
        self.assertIn(CREATOR_NAME, tbl)
        self.assertIn(CREATOR_FULL_NAME, tbl)
        self.assertTrue(tbl.startswith("+--"))


if __name__ == "__main__":
    unittest.main()
