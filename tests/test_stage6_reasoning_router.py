import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.brain import BrainRouter
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.reasoning_policy import (
    BLOCKED_BY_GUARDIAN,
    DAILY_CONTEXT,
    EXTERNAL_BRAIN_DISABLED,
    MEMORY_LOOKUP,
    PROJECT_CONTEXT,
    REASONING_MODE_RECOMMENDED,
    SAFE_FILE_READ_CONTEXT,
    SIMPLE_LOCAL,
)
from backend.lucy_core.router import CommandRouter


class Stage6ReasoningRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runtime = LucyRuntime(project_root=Path(self.temp_dir.name))
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_simple_greeting_routes_simple_local(self) -> None:
        decision = BrainRouter().route_request("hello lucy")
        self.assertEqual(decision["decision"], SIMPLE_LOCAL)

    def test_memory_question_routes_memory_lookup(self) -> None:
        decision = BrainRouter().route_request("do you remember my project preference")
        self.assertEqual(decision["decision"], MEMORY_LOOKUP)

    def test_project_question_routes_project_context(self) -> None:
        decision = BrainRouter().route_request("what is the active project next action")
        self.assertEqual(decision["decision"], PROJECT_CONTEXT)

    def test_daily_question_routes_daily_context(self) -> None:
        decision = BrainRouter().route_request("what is my daily routine today")
        self.assertEqual(decision["decision"], DAILY_CONTEXT)

    def test_file_question_routes_safe_file_context(self) -> None:
        decision = BrainRouter().route_request("read file notes.txt")
        self.assertEqual(decision["decision"], SAFE_FILE_READ_CONTEXT)
        self.assertTrue(decision["tool_required"])

    def test_dangerous_command_routes_blocked_or_guardian_required(self) -> None:
        preview = self.runtime.route_preview("delete file notes.txt")
        decision = preview["route_decision"]
        self.assertIn(decision["decision"], {BLOCKED_BY_GUARDIAN})
        self.assertTrue(decision["guardian_required"])

    def test_complex_architecture_routes_reasoning_recommended(self) -> None:
        decision = BrainRouter().route_request("design architecture for the Lucy reasoning router and explain tradeoffs")
        self.assertEqual(decision["decision"], REASONING_MODE_RECOMMENDED)

    def test_external_brain_disabled_by_default(self) -> None:
        status = self.runtime.reasoning_status()
        self.assertFalse(status["external_brain_enabled"])
        decision = BrainRouter().route_request("use groq external brain for this")
        self.assertEqual(decision["decision"], EXTERNAL_BRAIN_DISABLED)
        self.assertFalse(decision["external_api_allowed"])

    def test_explain_route_command_does_not_crash(self) -> None:
        response = self.router.handle("explain route hello lucy")
        self.assertFalse(response.should_exit)
        self.assertIn("Route explanation", response.message)

    def test_reasoning_status_command_does_not_crash(self) -> None:
        response = self.router.handle("reasoning status")
        self.assertFalse(response.should_exit)
        self.assertIn("Lucy reasoning router", response.message)

    def test_route_decision_includes_confidence(self) -> None:
        decision = BrainRouter().route_request("hello lucy")
        self.assertIn("confidence", decision)
        self.assertIsInstance(decision["confidence"], float)

    def test_no_hidden_reasoning_output_is_exposed(self) -> None:
        response = self.router.handle("explain route design architecture for Lucy")
        lowered = response.message.lower()
        self.assertNotIn("chain-of-thought", lowered)
        self.assertNotIn("step-by-step reasoning", lowered)
        self.assertIn("hidden reasoning output: disabled", lowered)

    def test_brain_router_status_command_does_not_crash(self) -> None:
        response = self.router.handle("brain router status")
        self.assertFalse(response.should_exit)
        self.assertIn("Lucy brain router detailed status", response.message)

    def test_reasoning_policy_command_does_not_crash(self) -> None:
        response = self.router.handle("reasoning policy")
        self.assertFalse(response.should_exit)
        self.assertIn("Categories", response.message)


if __name__ == "__main__":
    unittest.main()
