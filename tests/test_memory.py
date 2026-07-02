import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.memory import MemorySystem


class MemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.memory = MemorySystem(Path(self.temp_dir.name))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_remember_and_recall(self) -> None:
        saved = self.memory.remember("Lucy should stay local first.")
        self.assertTrue(saved["saved"])

        matches = self.memory.recall("local")
        self.assertEqual(len(matches), 1)
        self.assertIn("local first", matches[0]["fact"])
        self.assertEqual(matches[0]["content"], matches[0]["fact"])
        self.assertEqual(matches[0]["status"], "active")
        self.assertIn(matches[0]["type"], {"general", "project_fact", "correction_anti_drift_rule"})
        self.assertIsInstance(matches[0]["tags"], list)

    def test_duplicate_memory_is_not_added(self) -> None:
        first = self.memory.remember("Lucy keeps clean logs.")
        second = self.memory.remember("Lucy keeps clean logs.")

        self.assertTrue(first["saved"])
        self.assertFalse(second["saved"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(self.memory.audit()["active"], 1)

    def test_sensitive_memory_is_refused(self) -> None:
        result = self.memory.remember("My password is test.")
        self.assertFalse(result["saved"])
        self.assertEqual(self.memory.audit()["active"], 0)

    def test_forget_specific_memory(self) -> None:
        self.memory.remember("Lucy tracks active projects.")
        result = self.memory.forget("active projects")

        self.assertEqual(result["forgotten"], 1)
        self.assertEqual(self.memory.audit()["active"], 0)


if __name__ == "__main__":
    unittest.main()
