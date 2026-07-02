import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime


class CheckpointBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runtime = LucyRuntime(project_root=Path(self.temp_dir.name))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_ensure_minimum_creates_checkpoints_and_learning_traces(self) -> None:
        result = self.runtime.overnight_checkpoint_run(5)

        self.assertEqual(result["target"], 5)
        self.assertEqual(result["created_count"], 5)
        self.assertEqual(result["final_count"], 5)
        self.assertEqual(result["learning_traces"], 5)
        self.assertEqual(self.runtime.learning.status()["checkpoint_lessons"], 5)

    def test_ensure_minimum_does_not_create_extra_when_target_met(self) -> None:
        self.runtime.overnight_checkpoint_run(3)
        result = self.runtime.overnight_checkpoint_run(2)

        self.assertEqual(result["created_count"], 0)
        self.assertEqual(result["final_count"], 3)


if __name__ == "__main__":
    unittest.main()
