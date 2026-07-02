import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.learning import LearningSystem


class LearningSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.learning = LearningSystem(Path(self.temp_dir.name))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_record_interaction(self) -> None:
        self.learning.record_interaction("status", "Lucy is online")
        status = self.learning.status()
        self.assertEqual(status["interactions"], 1)

    def test_add_lesson(self) -> None:
        result = self.learning.add_lesson("Lucy should use APIs as tools only.")
        self.assertTrue(result["saved"])
        self.assertEqual(self.learning.status()["local_lessons"], 1)

    def test_record_checkpoint_learning(self) -> None:
        checkpoint = {
            "checkpoint_id": "checkpoint_0007",
            "stage": "test",
            "reason": "Test checkpoint",
        }
        self.learning.record_checkpoint_learning(checkpoint, "Lucy should learn from checkpoints.")
        status = self.learning.status()
        self.assertEqual(status["checkpoint_lessons"], 1)

    def test_add_style_preference(self) -> None:
        result = self.learning.add_style_preference("Be concise and casual.")
        self.assertTrue(result["saved"])
        self.assertEqual(self.learning.status()["style_preferences"], 2)

    def test_apply_talking_style(self) -> None:
        self.learning.add_style_preference("Be warm and casual.")
        styled = self.learning.apply_talking_style("I am here. I do not need the API for this.")
        self.assertIn("Got you.", styled)
        self.assertIn("I'm here", styled)
        self.assertIn("I don't need", styled)

    def test_sensitive_lesson_refused(self) -> None:
        result = self.learning.add_lesson("My password is test.")
        self.assertFalse(result["saved"])


if __name__ == "__main__":
    unittest.main()
