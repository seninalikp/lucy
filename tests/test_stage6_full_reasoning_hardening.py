import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.brain import BrainRouter
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.reasoning_policy import (
    BLOCKED_BY_GUARDIAN,
    CLARIFICATION_REQUIRED,
    DAILY_CONTEXT,
    EXTERNAL_BRAIN_RECOMMENDED_BUT_DISABLED,
    MEMORY_LOOKUP,
    PROJECT_CONTEXT,
    REASONING_MODE_RECOMMENDED,
    SAFE_FILE_READ_CONTEXT,
    SIMPLE_LOCAL,
)
from backend.lucy_core.router import CommandRouter


class Stage6FullReasoningHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runtime = LucyRuntime(project_root=Path(self.temp_dir.name))
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_unclear_input_routes_clarification_required(self) -> None:
        decision = BrainRouter().route_request("...")
        self.assertEqual(decision["decision"], CLARIFICATION_REQUIRED)

    def test_simple_greeting_routes_simple_local(self) -> None:
        decision = BrainRouter().route_request("hello lucy")
        self.assertEqual(decision["decision"], SIMPLE_LOCAL)

    def test_memory_question_routes_memory_lookup(self) -> None:
        decision = BrainRouter().route_request("do you remember what I said about Lucy")
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

    def test_dangerous_command_routes_blocked_by_guardian(self) -> None:
        result = self.runtime.route_preview("delete file notes.txt")
        self.assertEqual(result["route_decision"]["decision"], BLOCKED_BY_GUARDIAN)

    def test_complex_architecture_routes_reasoning_recommended(self) -> None:
        decision = BrainRouter().route_request("design architecture for Lucy routing and explain tradeoffs")
        self.assertEqual(decision["decision"], REASONING_MODE_RECOMMENDED)

    def test_external_brain_disabled_by_default(self) -> None:
        status = self.runtime.reasoning_status()
        decision = BrainRouter().route_request("use groq external brain for this")
        self.assertFalse(status["external_brain_enabled"])
        self.assertEqual(decision["decision"], EXTERNAL_BRAIN_RECOMMENDED_BUT_DISABLED)
        self.assertFalse(decision["external_api_allowed"])

    def test_context_packet_excludes_secrets(self) -> None:
        result = self.runtime.context_packet_preview("api key = sk-1234567890abcdef should not show")
        packet_text = repr(result["context_packet"]).lower()
        self.assertNotIn("sk-1234567890abcdef", packet_text)
        self.assertNotIn("api key", packet_text)
        self.assertIn("redacted", packet_text)

    def test_response_frame_does_not_expose_hidden_reasoning(self) -> None:
        result = self.runtime.response_frame_preview("design architecture for Lucy")
        frame = result["response_frame"]
        frame_text = repr(frame).lower()
        self.assertFalse(frame["hidden_reasoning_output"])
        self.assertNotIn("chain-of-thought", frame_text)
        self.assertNotIn("step-by-step reasoning", frame_text)

    def test_explain_route_command_works(self) -> None:
        response = self.router.handle("explain route hello lucy")
        self.assertFalse(response.should_exit)
        self.assertIn("Route explanation", response.message)

    def test_context_packet_command_works(self) -> None:
        response = self.router.handle("context packet do you remember Lucy")
        self.assertFalse(response.should_exit)
        self.assertIn("Context packet preview", response.message)

    def test_response_frame_command_works(self) -> None:
        response = self.router.handle("response frame design architecture for Lucy")
        self.assertFalse(response.should_exit)
        self.assertIn("Response frame preview", response.message)


if __name__ == "__main__":
    unittest.main()
