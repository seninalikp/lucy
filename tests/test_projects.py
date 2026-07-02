import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.projects import ProjectTracker


class ProjectTrackerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.projects = ProjectTracker(Path(self.temp_dir.name))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_default_active_project_is_lucy(self) -> None:
        summary = self.projects.summary()
        self.assertEqual(summary["name"], "Lucy")

    def test_add_and_complete_task(self) -> None:
        added = self.projects.add_task("Write focused router tests.")
        self.assertTrue(added["added"])

        tasks = self.projects.show_tasks()["tasks"]
        self.assertGreaterEqual(len(tasks), 1)

        completed = self.projects.complete_task(str(len(tasks)))
        self.assertTrue(completed["completed"])

    def test_set_active_project_creates_project(self) -> None:
        result = self.projects.set_active_project("Portfolio website")
        self.assertTrue(result["changed"])
        self.assertEqual(self.projects.summary()["name"], "Portfolio website")


if __name__ == "__main__":
    unittest.main()
