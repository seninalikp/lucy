"""
test_stage20_long_term_strategy.py
Stage 20 = long-term strategy.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.long_term_strategy import LongTermStrategy
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage20LongTermStrategy(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _runtime_and_router(self):
        runtime = LucyRuntime(project_root=self.root)
        router = CommandRouter(runtime)
        return runtime, router

    def test_01_long_term_strategy_status_returns_stage20_status(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("long-term strategy status")
        self.assertIn("Long-term strategy status:", response.message)
        self.assertIn("Stage: 20 long-term strategy", response.message)
        self.assertIn("Long-term strategy: active", response.message)

    def test_02_strategy_status_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("strategy status")
        self.assertIn("Long-term strategy status:", response.message)

    def test_03_create_long_term_strategy_creates_structured_strategy(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("create long-term strategy")
        self.assertIn("Long-term strategy:", response.message)
        strategies = runtime.long_term_strategy.list_strategies()
        self.assertEqual(len(strategies), 1)
        strategy = strategies[0]
        expected = {
            "strategy_id",
            "created_at",
            "stage",
            "title",
            "horizon",
            "status",
            "summary",
            "strategic_rules",
            "near_term_focus",
            "future_direction",
            "risk_level",
            "blocked_reasons",
            "approval_required",
            "autonomy_allowed",
            "implementation_allowed",
            "not_implemented",
        }
        self.assertEqual(set(strategy.keys()), expected)

    def test_04_create_strategy_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("create strategy")
        self.assertIn("Long-term strategy:", response.message)

    def test_05_show_long_term_strategies_displays_existing_strategy(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create long-term strategy")
        response = router.handle("show long-term strategies")
        self.assertIn("Long-term strategies:", response.message)
        self.assertIn("Protect Lucy roadmap", response.message)

    def test_06_show_strategies_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create long-term strategy")
        response = router.handle("show strategies")
        self.assertIn("Long-term strategies:", response.message)

    def test_07_strategy_reuses_existing_record(self) -> None:
        runtime, router = self._runtime_and_router()
        first = router.handle("create long-term strategy")
        second = router.handle("create long-term strategy")
        self.assertIn("Long-term strategy:", first.message)
        self.assertIn("Existing long-term strategy reused.", second.message)
        self.assertEqual(len(runtime.long_term_strategy.list_strategies()), 1)

    def test_08_strategy_safety_booleans_are_fixed(self) -> None:
        runtime, _ = self._runtime_and_router()
        result = runtime.long_term_strategy.create_strategy()
        strategy = result["strategy"]
        self.assertTrue(strategy["approval_required"])
        self.assertFalse(strategy["autonomy_allowed"])
        self.assertFalse(strategy["implementation_allowed"])

    def test_09_strategy_values_are_valid(self) -> None:
        runtime, _ = self._runtime_and_router()
        strategy = runtime.long_term_strategy.create_strategy()["strategy"]
        self.assertIn(strategy["horizon"], {"short", "medium", "long"})
        self.assertIn(strategy["status"], {"draft", "needs_review", "active"})
        self.assertIn(strategy["risk_level"], {"low", "medium", "high", "blocked"})

    def test_10_does_not_create_stage21_or_later_systems(self) -> None:
        runtime, _ = self._runtime_and_router()
        for method in [
            "smart_organizer_status",
            "safe_local_actions_status",
            "external_app_bridge_status",
            "proactive_awareness_status",
            "deep_recall_status",
            "judgment_status",
            "adaptive_communication_status",
            "call_external_api",
            "start_server",
            "take_action",
        ]:
            self.assertFalse(hasattr(runtime.long_term_strategy, method))

    def test_11_stage19_identity_stability_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Identity stability status:", router.handle("identity stability status").message)

    def test_12_stage18_experience_storage_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Experience storage status:", router.handle("experience storage status").message)

    def test_13_stage17_patch_pipeline_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Patch pipeline status:", router.handle("patch pipeline status").message)

    def test_14_stage16_shadow_testing_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Shadow testing status:", router.handle("shadow testing status").message)

    def test_15_stage15_evaluation_lab_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Evaluation lab status:", router.handle("evaluation lab status").message)

    def test_16_stage14_growth_proposals_still_work(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Growth proposals status:", router.handle("growth proposals status").message)

    def test_17_stage13_self_model_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Self-model status:", router.handle("self model status").message)

    def test_18_stage12_first_thought_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("First thought status:", router.handle("first thought status").message)

    def test_19_stage11_access_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Safe access status:", router.handle("access status").message)

    def test_20_stage10_runtime_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Runtime status:", router.handle("runtime status").message)

    def test_21_stage09_agent_report_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Internal agent report:", router.handle("agent report").message)

    def test_22_stage08_agent_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Internal agents:", router.handle("agent status").message)

    def test_23_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        aliases = {
            "strategy": "Long-term strategy:",
            "strategies": "Long-term strategies:",
            "strategy status": "Long-term strategy status:",
            "show strategies": "Long-term strategies:",
            "identity": "Identity stability status:",
        }
        router.handle("create long-term strategy")
        for command, expected in aliases.items():
            self.assertIn(expected, router.handle(command).message)

    def test_24_tell_me_reflects_stage20_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("tell me")
        self.assertIn("Active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Guardian: active", response.message)
        self.assertIn("Long-term strategy: active", response.message)
        self.assertIn("Stage 35 gate:", response.message)

    def test_25_what_next_reflects_stage20_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("what next")
        self.assertIn("Current active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("describe what a provider health check would do, dry-run only, no network", response.message)
        self.assertIn("Stage 35:", response.message)

    def test_26_no_ui_voice_network_or_external_api_added(self) -> None:
        runtime, router = self._runtime_and_router()
        output = router.handle("long-term strategy status").message.lower()
        for method in ["start_server", "listen", "bind", "start_voice", "call_external_api"]:
            self.assertFalse(hasattr(runtime.long_term_strategy, method))
        self.assertNotIn("provider router", output)

    def test_27_no_autonomy_features_added(self) -> None:
        runtime, router = self._runtime_and_router()
        output = router.handle("create long-term strategy").message.lower()
        self.assertFalse(hasattr(runtime.long_term_strategy, "run_autonomously"))
        self.assertIn("Autonomy allowed: false", router.handle("create long-term strategy").message)

    def test_28_no_fake_consciousness_language_in_normal_output(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("long-term strategy status").message,
                router.handle("create long-term strategy").message,
                router.handle("show long-term strategies").message,
            ]
        ).lower()
        forbidden = ["i am alive", "i am conscious", "i feel", "i am human", "i am free"]
        for phrase in forbidden:
            self.assertNotIn(phrase, output)


if __name__ == "__main__":
    unittest.main()
