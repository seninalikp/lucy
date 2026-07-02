import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.guardian import BLOCKED, REQUIRES_MANUAL_CONFIRMATION, SAFE, GuardianCore
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.tool_confirmations import ToolConfirmationManager
from backend.lucy_core.tool_policy import ToolActionPolicy, ToolActionRequest


class Stage5FullToolSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.runtime = LucyRuntime(project_root=self.root / "runtime")
        approved = self.runtime.safe_file_tools.add_approved_folder(self.workspace, name="Workspace")
        self.assertTrue(approved.ok, approved.reason)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_safe_read_only_action_allowed(self) -> None:
        policy = ToolActionPolicy()
        decision = policy.classify(ToolActionRequest("read_file", "notes.txt", {"file_size": 20, "extension": ".txt"}))
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_confirmation)
        self.assertFalse(decision.blocked)

    def test_delete_action_blocked(self) -> None:
        policy = ToolActionPolicy()
        decision = policy.classify(ToolActionRequest("delete file", "notes.txt"))
        self.assertTrue(decision.blocked)

    def test_edit_action_blocked_or_proposal_only(self) -> None:
        policy = ToolActionPolicy()
        edit = policy.classify(ToolActionRequest("edit file", "notes.txt"))
        proposal = policy.classify(ToolActionRequest("propose_edit", "notes.txt"))
        self.assertTrue(edit.blocked)
        self.assertTrue(proposal.allowed)
        self.assertEqual(proposal.category, "WRITE_PROPOSED_ONLY")

    def test_outside_approved_path_blocked(self) -> None:
        outside = self.root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        result = self.runtime.read_file(str(outside))
        self.assertFalse(result["ok"])
        self.assertTrue(result["blocked"])
        self.assertIn("outside approved", result["reason"])

    def test_secret_filename_blocked(self) -> None:
        path = self.workspace / "api_key_notes.txt"
        path.write_text("should not read", encoding="utf-8")
        result = self.runtime.read_file(str(path))
        self.assertFalse(result["ok"])
        self.assertTrue(result["blocked"])

    def test_large_read_requires_confirmation(self) -> None:
        path = self.workspace / "large.txt"
        path.write_text("x" * (ToolActionPolicy.MAX_SAFE_READ_BYTES + 10), encoding="utf-8")
        result = self.runtime.read_file(str(path))
        self.assertFalse(result["ok"])
        self.assertFalse(result["blocked"])
        self.assertTrue(result["data"]["requires_confirmation"])
        self.assertTrue(result["data"]["confirmation_id"].startswith("tool_"))

    def test_confirmation_created(self) -> None:
        manager = ToolConfirmationManager(self.root / "confirmations")
        result = manager.create_confirmation("read_file", "Large read", "medium")
        self.assertTrue(result["ok"])
        self.assertEqual(result["confirmation"]["status"], "pending")

    def test_confirmation_approved(self) -> None:
        manager = ToolConfirmationManager(self.root / "confirmations")
        created = manager.create_confirmation("read_file", "Large read", "medium")
        approved = manager.approve_confirmation(created["confirmation"]["id"])
        self.assertTrue(approved["ok"])
        self.assertEqual(approved["confirmation"]["status"], "approved")

    def test_rejected_confirmation_blocks_consume(self) -> None:
        manager = ToolConfirmationManager(self.root / "confirmations")
        created = manager.create_confirmation("read_file", "Large read", "medium")
        manager.reject_confirmation(created["confirmation"]["id"])
        consumed = manager.consume_confirmation(created["confirmation"]["id"])
        self.assertFalse(consumed["ok"])
        self.assertFalse(consumed["consumed"])

    def test_audit_log_writes_without_contents(self) -> None:
        path = self.workspace / "audit.txt"
        path.write_text("AUDIT_CONTENT_SHOULD_NOT_APPEAR", encoding="utf-8")
        result = self.runtime.read_file(str(path))
        self.assertTrue(result["ok"])
        audit_file = self.runtime.project_root / "data" / "lucy" / "tool_audit_log.jsonl"
        text = audit_file.read_text(encoding="utf-8")
        self.assertIn("read_file", text)
        self.assertNotIn("AUDIT_CONTENT_SHOULD_NOT_APPEAR", text)
        json.loads(text.splitlines()[-1])

    def test_guardian_tool_action_structured(self) -> None:
        guardian = GuardianCore(self.root / "logs")
        safe = guardian.classify_tool_action("read_file", "notes.txt", {"file_size": 5, "extension": ".txt"})
        blocked = guardian.classify_tool_action("delete file", "notes.txt")
        large = guardian.classify_tool_action(
            "read_file",
            "large.txt",
            {"file_size": ToolActionPolicy.MAX_SAFE_READ_BYTES + 1, "extension": ".txt"},
        )
        self.assertEqual(safe["classification"], SAFE)
        self.assertEqual(blocked["classification"], BLOCKED)
        self.assertEqual(large["classification"], REQUIRES_MANUAL_CONFIRMATION)
        self.assertIn("policy_decision", safe)

    def test_safe_tools_status_keeps_power_tools_disabled(self) -> None:
        status = self.runtime.safe_tools_status()
        data = status["data"]
        self.assertFalse(data["write_enabled"])
        self.assertFalse(data["network_enabled"])
        self.assertFalse(data["execution_enabled"])
        self.assertTrue(data["confirmation_required_for_large_reads"])

    def test_router_tool_policy_command_no_crash(self) -> None:
        router = CommandRouter(self.runtime)
        response = router.handle("tool policy")
        self.assertFalse(response.should_exit)
        self.assertIn("Tool policy", response.message)

    def test_router_pending_confirmations_no_crash(self) -> None:
        router = CommandRouter(self.runtime)
        response = router.handle("pending confirmations")
        self.assertFalse(response.should_exit)
        self.assertIn("Pending tool confirmations", response.message)


if __name__ == "__main__":
    unittest.main()
