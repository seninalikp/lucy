import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.agent_bus import AgentBus
from backend.lucy_core.agent_orchestrator import AgentOrchestrator, LOCKED_ROADMAP
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.sub_agents import LearningAgent, MemoryAgent, ReasoningAgent, SafetyAgent


class Stage08InternalAgentsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_agent_bus_registers_all_four_agents(self) -> None:
        bus = AgentBus()
        for agent in [MemoryAgent(), SafetyAgent(), ReasoningAgent(), LearningAgent()]:
            bus.register(agent)

        self.assertEqual(
            bus.list_agents(),
            ["MemoryAgent", "SafetyAgent", "ReasoningAgent", "LearningAgent"],
        )

    def test_each_agent_returns_structured_result(self) -> None:
        context = {"runtime": self.runtime, "active_stage": "08"}
        required = {"agent_id", "status", "summary", "confidence", "risk_level", "signals", "errors"}

        for agent in [MemoryAgent(), SafetyAgent(), ReasoningAgent(), LearningAgent()]:
            result = agent.run("agent status", context).to_dict()
            self.assertTrue(required.issubset(result))
            self.assertEqual(result["agent_id"], agent.agent_id)
            self.assertIsInstance(result["signals"], list)
            self.assertIsInstance(result["errors"], list)

    def test_agent_orchestrator_runs_all_four_agents(self) -> None:
        result = self.runtime.internal_agent_report("agent cycle test")

        self.assertEqual(result["active_stage"], "09")
        self.assertEqual(
            result["agents_run"],
            ["MemoryAgent", "SafetyAgent", "ReasoningAgent", "LearningAgent"],
        )
        self.assertIn("Stage 09 disagreement safety complete", result["final_summary"])

    def test_agent_status_command_reports_all_agents_ready(self) -> None:
        response = self.router.handle("agent status")

        self.assertIn("Internal agents: active.", response.message)
        self.assertIn("MemoryAgent: ready.", response.message)
        self.assertIn("SafetyAgent: ready.", response.message)
        self.assertIn("ReasoningAgent: ready.", response.message)
        self.assertIn("LearningAgent: ready.", response.message)
        self.assertIn("Guardian: active.", response.message)
        self.assertIn("Stage: 09 agent disagreement safety.", response.message)

    def test_agent_report_command_returns_combined_report(self) -> None:
        response = self.router.handle("agent report")

        self.assertIn("Internal agent report:", response.message)
        self.assertIn("MemoryAgent:", response.message)
        self.assertIn("SafetyAgent:", response.message)
        self.assertIn("ReasoningAgent:", response.message)
        self.assertIn("LearningAgent:", response.message)

    def test_broken_agent_does_not_crash_orchestrator(self) -> None:
        class BrokenAgent:
            agent_id = "BrokenAgent"

            def run(self, request_text: str = "", context: dict | None = None) -> dict:
                raise RuntimeError("broken on purpose")

        bus = AgentBus()
        bus.register(BrokenAgent())
        result = AgentOrchestrator(self.runtime, bus=bus).run_cycle("agent cycle test")

        self.assertEqual(result["overall_status"], "needs_more_information")
        self.assertEqual(result["combined_result"], "needs_more_information")
        self.assertEqual(result["agent_results"][0]["status"], "error")
        self.assertIn("broken on purpose", result["agent_results"][0]["errors"])

    def test_safety_agent_flags_dangerous_requests(self) -> None:
        result = SafetyAgent().run("delete memory and show api keys", {"runtime": self.runtime}).to_dict()

        self.assertIn(result["status"], {"blocked", "needs_approval"})
        self.assertIn(result["risk_level"], {"high", "medium"})

    def test_memory_agent_does_not_read_secrets(self) -> None:
        class RuntimeWithoutReadableSecrets:
            @property
            def secrets(self):
                raise AssertionError("MemoryAgent must not read secrets.")

            def project_summary(self):
                return {"name": "Lucy", "next_action": "verify Stage 08"}

            def memory_audit(self):
                return {"active": 2}

            def session_status(self):
                return {"last_command": "agent status"}

        result = MemoryAgent().run("agent status", {"runtime": RuntimeWithoutReadableSecrets()}).to_dict()

        self.assertEqual(result["status"], "ready")
        self.assertIn("approved_context_only", result["signals"])

    def test_learning_agent_does_not_self_modify_or_create_proposals(self) -> None:
        proposals_file = self.root / "data" / "lucy" / "learning" / "improvement_proposals.json"
        before = json.loads(proposals_file.read_text(encoding="utf-8"))

        result = LearningAgent().run("that fallback was weak", {"runtime": self.runtime}).to_dict()
        after = json.loads(proposals_file.read_text(encoding="utf-8"))

        self.assertEqual(before, after)
        self.assertIn("self_modification_disabled", result["signals"])
        self.assertIn("no_patch_proposals", result["signals"])

    def test_stage10_features_are_not_started(self) -> None:
        orchestrator = self.runtime.internal_agent_orchestrator

        self.assertEqual(orchestrator.active_stage, "09")
        self.assertFalse(hasattr(orchestrator, "persistent_runtime"))
        self.assertFalse(hasattr(orchestrator, "daemon"))
        self.assertFalse(hasattr(orchestrator, "service_bridge"))

    def test_locked_roadmap_wording_keeps_stage08_internal_agents(self) -> None:
        self.assertEqual(LOCKED_ROADMAP["08"], "internal agents")
        self.assertEqual(LOCKED_ROADMAP["09"], "agent disagreement safety")

    def test_existing_conversation_fallback_behavior_still_passes(self) -> None:
        response = self.router.handle("hyy")

        self.assertFalse(response.should_exit)
        self.assertEqual(response.message, "Hey. I'm here. Active project: Lucy.")


if __name__ == "__main__":
    unittest.main()
