"""
test_stage21_smart_organizer.py
Stage 21 = smart organizer.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.smart_organizer import SmartOrganizer


class TestStage21SmartOrganizer(unittest.TestCase):
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

    def test_01_smart_organizer_status_returns_stage21_status(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("smart organizer status")
        self.assertIn("Smart organizer status:", response.message)
        self.assertIn("Stage: 21 smart organizer", response.message)
        self.assertIn("Smart organizer: active", response.message)

    def test_02_organizer_status_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("organizer status")
        self.assertIn("Smart organizer status:", response.message)

    def test_03_create_organizer_item_creates_structured_item(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("create organizer item")
        self.assertIn("Organizer item:", response.message)
        items = runtime.smart_organizer.list_items()
        self.assertEqual(len(items), 1)
        item = items[0]
        expected = {
            "organizer_item_id",
            "created_at",
            "stage",
            "title",
            "group",
            "status",
            "priority",
            "summary",
            "next_visible_step",
            "blocked_until",
            "safety_notes",
            "approval_required",
            "action_allowed",
            "proactive_allowed",
            "not_implemented",
        }
        self.assertEqual(set(item.keys()), expected)

    def test_04_create_organizer_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("create organizer")
        self.assertIn("Organizer item:", response.message)

    def test_05_show_organizer_items_displays_existing_item(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create organizer item")
        response = router.handle("show organizer items")
        self.assertIn("Organizer items:", response.message)
        self.assertIn("Stage 21 smart organizer checks before backup", response.message)

    def test_06_show_organizer_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create organizer item")
        response = router.handle("show organizer")
        self.assertIn("Organizer items:", response.message)

    def test_07_organizer_reuses_existing_item(self) -> None:
        runtime, router = self._runtime_and_router()
        first = router.handle("create organizer item")
        second = router.handle("create organizer item")
        self.assertIn("Organizer item:", first.message)
        self.assertIn("Existing organizer item reused.", second.message)
        self.assertEqual(len(runtime.smart_organizer.list_items()), 1)

    def test_08_organizer_safety_booleans_are_fixed(self) -> None:
        runtime, _ = self._runtime_and_router()
        item = runtime.smart_organizer.create_organizer_item()["item"]
        self.assertTrue(item["approval_required"])
        self.assertFalse(item["action_allowed"])
        self.assertFalse(item["proactive_allowed"])

    def test_09_organizer_values_are_valid(self) -> None:
        runtime, _ = self._runtime_and_router()
        item = runtime.smart_organizer.create_organizer_item()["item"]
        self.assertIn(item["group"], {"current_stage", "blocked_until_approval", "backup_required", "manual_checks", "future_parking_lot", "safety_boundary"})
        self.assertIn(item["status"], {"open", "blocked", "ready", "done"})
        self.assertIn(item["priority"], {"low", "medium", "high"})

    def test_10_does_not_create_stage22_or_later_systems(self) -> None:
        runtime, _ = self._runtime_and_router()
        for method in [
            "safe_local_actions_status",
            "external_app_bridge_status",
            "proactive_awareness_status",
            "deep_recall_status",
            "judgment_status",
            "adaptive_communication_status",
            "human_state_awareness_status",
            "call_external_api",
            "start_server",
            "take_action",
            "monitor_user",
        ]:
            self.assertFalse(hasattr(runtime.smart_organizer, method))

    def test_11_stage20_long_term_strategy_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Long-term strategy status:", router.handle("long-term strategy status").message)

    def test_12_stage19_identity_stability_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Identity stability status:", router.handle("identity stability status").message)

    def test_13_stage18_experience_storage_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Experience storage status:", router.handle("experience storage status").message)

    def test_14_stage17_patch_pipeline_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Patch pipeline status:", router.handle("patch pipeline status").message)

    def test_15_stage16_shadow_testing_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Shadow testing status:", router.handle("shadow testing status").message)

    def test_16_stage15_evaluation_lab_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Evaluation lab status:", router.handle("evaluation lab status").message)

    def test_17_stage14_growth_proposals_still_work(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Growth proposals status:", router.handle("growth proposals status").message)

    def test_18_stage13_self_model_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Self-model status:", router.handle("self model status").message)

    def test_19_stage12_first_thought_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("First thought status:", router.handle("first thought status").message)

    def test_20_stage11_access_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Safe access status:", router.handle("access status").message)

    def test_21_stage10_runtime_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Runtime status:", router.handle("runtime status").message)

    def test_22_stage09_agent_report_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Internal agent report:", router.handle("agent report").message)

    def test_23_stage08_agent_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Internal agents:", router.handle("agent status").message)

    def test_24_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        aliases = {
            "organizer": "Organizer item:",
            "organiser": "Organizer item:",
            "organizer status": "Smart organizer status:",
            "show organizer": "Organizer items:",
            "organizer items": "Organizer items:",
            "strategy status": "Long-term strategy status:",
        }
        router.handle("create organizer item")
        for command, expected in aliases.items():
            self.assertIn(expected, router.handle(command).message)

    def test_25_tell_me_reflects_stage21_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("tell me")
        self.assertIn("Active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Guardian: active", response.message)
        self.assertIn("Smart organizer: active", response.message)
        self.assertIn("Stage 35 gate:", response.message)

    def test_26_what_next_reflects_stage21_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("what next")
        self.assertIn("Current active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("describe what a provider health check would do, dry-run only, no network", response.message)
        self.assertIn("Stage 35:", response.message)

    def test_27_no_ui_voice_network_or_external_api_added(self) -> None:
        runtime, router = self._runtime_and_router()
        output = router.handle("smart organizer status").message.lower()
        for method in ["start_server", "listen", "bind", "start_voice", "call_external_api"]:
            self.assertFalse(hasattr(runtime.smart_organizer, method))
        self.assertNotIn("provider router", output)

    def test_28_no_actions_or_proactive_monitoring_added(self) -> None:
        runtime, router = self._runtime_and_router()
        output = router.handle("create organizer item").message
        self.assertFalse(hasattr(runtime.smart_organizer, "run_actions"))
        self.assertFalse(hasattr(runtime.smart_organizer, "monitor_proactively"))
        self.assertIn("Action allowed: false", output)
        self.assertIn("Proactive allowed: false", output)

    def test_29_no_fake_consciousness_language_in_normal_output(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("smart organizer status").message,
                router.handle("create organizer item").message,
                router.handle("show organizer items").message,
            ]
        ).lower()
        forbidden = ["i am alive", "i am conscious", "i feel", "i am human", "i am free"]
        for phrase in forbidden:
            self.assertNotIn(phrase, output)


if __name__ == "__main__":
    unittest.main()
