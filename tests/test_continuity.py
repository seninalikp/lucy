import tempfile
import unittest
import zipfile
from pathlib import Path

from backend.lucy_core.continuity import ContinuityBackup


class ContinuityBackupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.lucy_data = Path(self.temp_dir.name)
        (self.lucy_data / "memory").mkdir()
        (self.lucy_data / "secure").mkdir()
        (self.lucy_data / "knowledge").mkdir()
        (self.lucy_data / "memory" / "memory.json").write_text('{"memories":[]}', encoding="utf-8")
        (self.lucy_data / "projects.json").write_text('{"projects":{}}', encoding="utf-8")
        (self.lucy_data / "secure" / "API_KEY.json").write_text("secret", encoding="utf-8")
        (self.lucy_data / "knowledge" / "ai_collections_index.json").write_text("large index", encoding="utf-8")
        self.continuity = ContinuityBackup(self.lucy_data, retention=3)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_snapshot_includes_memory_and_excludes_secrets(self) -> None:
        result = self.continuity.snapshot("unit test")

        self.assertTrue(result["created"])
        with zipfile.ZipFile(result["path"]) as archive:
            names = set(archive.namelist())
        self.assertIn("memory/memory.json", names)
        self.assertIn("projects.json", names)
        self.assertIn("manifest.json", names)
        self.assertNotIn("secure/API_KEY.json", names)
        self.assertNotIn("knowledge/ai_collections_index.json", names)

    def test_auto_backup_threshold(self) -> None:
        self.continuity.snapshot("baseline")
        state = self.continuity._read_state()
        state["next_auto_backup_after"] = 2
        state["change_counter"] = 0
        self.continuity._write_state(state)

        first = self.continuity.maybe_auto_backup("memory saved")
        second = self.continuity.maybe_auto_backup("project changed")

        self.assertFalse(first["created"])
        self.assertTrue(second["created"])

    def test_retention_prunes_old_backups(self) -> None:
        for index in range(5):
            self.continuity.snapshot(f"backup {index}")

        status = self.continuity.status()
        self.assertLessEqual(status["backup_count"], 3)


if __name__ == "__main__":
    unittest.main()
