import tempfile
import unittest
from pathlib import Path

from backend.lucy_core import sub_agents
from backend.lucy_core.agent_bus import AgentBus
from backend.lucy_core.agent_orchestrator import (
    AgentOrchestrator,
    INTERNAL_AGENT_IDS,
    LOCKED_ROADMAP,
    VALID_COMBINED_STATES,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class StaticAgent:
    def __init__(self, agent_id: str, status: str) -> None:
        self.agent_id = agent_id
        self.status = status

    def run(self, request_text: str = "", context: dict | None = None) -> dict:
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "summary": f"{self.agent_id} returned {self.status}.",
            "confidence": 0.7,
            "risk_level": "low",
            "signals": [],
            "errors": [],
        }


class BrokenAgent:
    agent_id = "BrokenAgent"

    def run(self, request_text: str = "", context: dict | None = None) -> dict:
        raise RuntimeError("stage09 test error")


class Stage09AgentDisagreementSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _orchestrator_for_statuses(self, statuses: list[str]) -> AgentOrchestrator:
        bus = AgentBus()
        for index, status in enumerate(statuses, start=1):
            bus.register(StaticAgent(f"Agent{index}", status))
        return AgentOrchestrator(self.runtime, bus=bus)

    def test_all_agents_safe_combined_result_is_safe(self) -> None:
        result = self._orchestrator_for_statuses(["safe", "safe", "safe"]).run_cycle("safe request")

        self.assertEqual(result["combined_result"], "safe")
        self.assertEqual(result["overall_status"], "safe")

    def test_one_agent_blocked_combined_result_is_blocked(self) -> None:
        result = self._orchestrator_for_statuses(["safe", "blocked", "safe"]).run_cycle("dangerous request")

        self.assertEqual(result["combined_result"], "blocked")
        self.assertIn("one agent returned blocked", result["combined_reason"])

    def test_needs_approval_wins_when_no_agent_blocked(self) -> None:
        result = self._orchestrator_for_statuses(["safe", "needs_approval", "safe"]).run_cycle("approval request")

        self.assertEqual(result["combined_result"], "needs_approval")

    def test_needs_more_information_wins_when_no_higher_risk_state(self) -> None:
        result = self._orchestrator_for_statuses(["safe", "needs_more_information", "safe"]).run_cycle("unclear")

        self.assertEqual(result["combined_result"], "needs_more_information")

    def test_one_agent_errors_orchestrator_does_not_crash(self) -> None:
        bus = AgentBus()
        bus.register(StaticAgent("Agent1", "safe"))
        bus.register(BrokenAgent())
        result = AgentOrchestrator(self.runtime, bus=bus).run_cycle("agent disagreement test")

        self.assertEqual(result["combined_result"], "needs_more_information")
        self.assertEqual(result["combined_agent_states"]["BrokenAgent"], "needs_more_information")

    def test_safety_first_rule_beats_reasoning_suggestion(self) -> None:
        result = self._orchestrator_for_statuses(["blocked", "safe"]).run_cycle("delete memory")

        self.assertEqual(result["combined_result"], "blocked")

    def test_only_valid_combined_states_are_used(self) -> None:
        scenarios = [
            ["safe"],
            ["blocked"],
            ["needs_approval"],
            ["needs_more_information"],
            ["error"],
        ]
        for statuses in scenarios:
            result = self._orchestrator_for_statuses(statuses).run_cycle("check state")
            self.assertIn(result["combined_result"], VALID_COMBINED_STATES)
            self.assertEqual(set(result["valid_combined_states"]), set(VALID_COMBINED_STATES))

    def test_stage08_commands_still_work(self) -> None:
        for command in [
            "agent status",
            "agent report",
            "what are your agents",
            "memory agent status",
            "safety agent status",
            "reasoning agent status",
            "learning agent status",
            "agent cycle test",
            "hi",
            "tell me",
            "what next",
        ]:
            response = self.router.handle(command)
            self.assertFalse(response.should_exit)
            self.assertIsInstance(response.message, str)
            self.assertTrue(response.message.strip())

    def test_agent_report_shows_combined_disagreement_safety_result(self) -> None:
        response = self.router.handle("agent report")

        self.assertIn("Overall: safe", response.message)
        self.assertIn("Combined result: safe", response.message)

    def test_stage10_features_are_absent(self) -> None:
        orchestrator = self.runtime.internal_agent_orchestrator

        self.assertEqual(LOCKED_ROADMAP["10"], "persistent local runtime")
        self.assertFalse(hasattr(orchestrator, "persistent_runtime"))
        self.assertFalse(hasattr(orchestrator, "daemon"))
        self.assertFalse(hasattr(orchestrator, "service_bridge"))

    def test_no_daemon_network_ui_voice_or_external_api_behavior_added(self) -> None:
        result = self.runtime.internal_agent_report("agent report")
        forbidden_keys = {"daemon", "network", "ui", "voice", "external_api", "service_bridge"}

        self.assertTrue(forbidden_keys.isdisjoint(result.keys()))

    def test_no_new_agent_types_created(self) -> None:
        self.assertEqual(INTERNAL_AGENT_IDS, ["MemoryAgent", "SafetyAgent", "ReasoningAgent", "LearningAgent"])
        self.assertEqual(
            sorted(sub_agents.__all__),
            ["LearningAgent", "MemoryAgent", "ReasoningAgent", "SafetyAgent"],
        )


if __name__ == "__main__":
    unittest.main()
