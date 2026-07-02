import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.cognition import CognitionCore
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class CognitionTests(unittest.TestCase):
    def test_reflection_persists_without_claiming_consciousness(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            cognition = CognitionCore(Path(temp))
            thought = cognition.reflect(
                "test",
                "please make her conscious",
                {
                    "project": {"name": "Lucy", "next_action": "", "open_tasks": []},
                    "memory": {"active": 2},
                    "knowledge": {"available": False},
                    "pending_approvals": 0,
                },
            )

            self.assertIn("not fake consciousness", thought["boundary"])
            status = cognition.status()
            self.assertEqual(status["reflection_count"], 1)
            self.assertIn("not_consciousness", status["mode"])

    def test_router_cognition_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = LucyRuntime(project_root=Path(temp))
            router = CommandRouter(runtime)

            vision = router.handle("vision")
            self.assertIn("Lucy vision", vision.message)
            self.assertIn("Foundation first", vision.message)

            thought = router.handle("think about becoming Jarvis safely")
            self.assertIn("Lucy reflected", thought.message)

            thoughts = router.handle("thoughts")
            self.assertIn("Lucy working thoughts", thoughts.message)

    def test_consciousness_question_is_honest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = LucyRuntime(project_root=Path(temp))
            router = CommandRouter(runtime)

            response = router.handle("are you conscious?")

            self.assertIn("not literally conscious", response.message.lower())


if __name__ == "__main__":
    unittest.main()
