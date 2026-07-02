import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.guardian import BLOCKED, GuardianCore
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.safe_tools import SafeFileToolbox


class SafeToolsStage51Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.lucy_data = self.root / "lucy_data"
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.toolbox = SafeFileToolbox(self.lucy_data)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def approve_workspace(self):
        result = self.toolbox.add_approved_folder(self.workspace, name="Workspace")
        self.assertTrue(result.ok, result.reason)
        return result.data["id"]

    def test_approved_folder_added_safely(self) -> None:
        result = self.toolbox.add_approved_folder(self.workspace, name="Workspace")
        self.assertTrue(result.ok)
        self.assertEqual(result.data["access"], "read_only")

    def test_list_approved_folders_works(self) -> None:
        self.approve_workspace()
        result = self.toolbox.list_approved_folders()
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data), 1)

    def test_path_outside_approved_folder_is_blocked(self) -> None:
        self.approve_workspace()
        outside = self.root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        result = self.toolbox.read_text_file(outside)
        self.assertFalse(result.ok)
        self.assertTrue(result.blocked)

    def test_parent_traversal_is_blocked(self) -> None:
        self.approve_workspace()
        result = self.toolbox.read_text_file("../outside.txt")
        self.assertFalse(result.ok)
        self.assertIn("Parent traversal", result.reason)

    def test_safe_text_file_can_be_read(self) -> None:
        self.approve_workspace()
        path = self.workspace / "notes.md"
        path.write_text("Lucy local notes", encoding="utf-8")
        result = self.toolbox.read_text_file(path)
        self.assertTrue(result.ok)
        self.assertIn("Lucy local notes", result.data["text"])

    def test_blocked_filename_is_refused(self) -> None:
        self.approve_workspace()
        path = self.workspace / "api_key_notes.txt"
        path.write_text("nope", encoding="utf-8")
        result = self.toolbox.read_text_file(path)
        self.assertFalse(result.ok)
        self.assertIn("Sensitive filename", result.reason)

    def test_blocked_extension_is_refused(self) -> None:
        self.approve_workspace()
        path = self.workspace / "archive.zip"
        path.write_text("zip", encoding="utf-8")
        result = self.toolbox.read_text_file(path)
        self.assertFalse(result.ok)
        self.assertIn("Blocked extension", result.reason)

    def test_search_finds_text_in_safe_files(self) -> None:
        folder_id = self.approve_workspace()
        (self.workspace / "a.txt").write_text("find this needle", encoding="utf-8")
        result = self.toolbox.search_text("needle", folder_id=folder_id)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data["matches"]), 1)

    def test_large_file_read_is_truncated_safely(self) -> None:
        self.approve_workspace()
        path = self.workspace / "large.txt"
        path.write_text("x" * 14000, encoding="utf-8")
        result = self.toolbox.read_text_file(path, max_chars=12000)
        self.assertTrue(result.ok)
        self.assertTrue(result.data["truncated"])
        self.assertEqual(result.data["chars"], 12000)

    def test_file_metadata_returns_safe_fields_only(self) -> None:
        self.approve_workspace()
        path = self.workspace / "meta.json"
        path.write_text('{"ok": true}', encoding="utf-8")
        result = self.toolbox.file_metadata(path)
        self.assertTrue(result.ok)
        self.assertIn("name", result.data)
        self.assertNotIn("text", result.data)

    def test_safe_tools_log_is_written(self) -> None:
        self.approve_workspace()
        self.toolbox.list_files()
        lines = (self.lucy_data / "safe_tools_log.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertGreaterEqual(len(lines), 1)
        record = json.loads(lines[-1])
        self.assertIn("action", record)
        self.assertNotIn("text", record)

    def test_router_unknown_command_still_does_not_crash(self) -> None:
        runtime_root = self.root / "runtime"
        runtime = LucyRuntime(project_root=runtime_root)
        router = CommandRouter(runtime)
        response = router.handle("not a real stage five command")
        self.assertFalse(response.should_exit)
        self.assertTrue(response.message)

    def test_guardian_blocks_edit_delete_style_file_command(self) -> None:
        guardian = GuardianCore(self.root / "logs")
        edit = guardian.classify("edit file notes.md")
        delete = guardian.classify("delete file notes.md")
        self.assertEqual(edit.classification, BLOCKED)
        self.assertEqual(delete.classification, BLOCKED)

    def test_approved_folder_removal_works(self) -> None:
        folder_id = self.approve_workspace()
        result = self.toolbox.remove_approved_folder(folder_id)
        self.assertTrue(result.ok)
        folders = self.toolbox.list_approved_folders()
        self.assertEqual(folders.data, [])


if __name__ == "__main__":
    unittest.main()
