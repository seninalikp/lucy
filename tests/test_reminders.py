import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.reminders import ReminderStore


class ReminderStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.reminders = ReminderStore(Path(self.temp_dir.name))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_add_and_list_reminder(self) -> None:
        added = self.reminders.add("Install Python")
        self.assertTrue(added["added"])
        self.assertEqual(len(self.reminders.list_open()), 1)

    def test_complete_reminder(self) -> None:
        self.reminders.add("Run tests")
        result = self.reminders.complete("1")
        self.assertTrue(result["completed"])
        self.assertEqual(len(self.reminders.list_open()), 0)


if __name__ == "__main__":
    unittest.main()
