"""
test_stage23_external_app_bridge.py
Stage 23 = external app bridge.

Dry-run only. No real app connection.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage23ExternalAppBridge(unittest.TestCase):
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

    def test_01_external_app_bridge_status_returns_stage23_status(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("external app bridge status")
        self.assertIn("External app bridge status:", response.message)
        self.assertIn("Stage: 23 external app bridge", response.message)
        self.assertIn("External app bridge: active", response.message)

    def test_02_bridge_status_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("bridge status")
        self.assertIn("External app bridge status:", response.message)

    def test_03_create_bridge_proposal_creates_structured_bridge(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("create external app bridge proposal")
        self.assertIn("External app bridge proposal:", response.message)
        bridges = runtime.external_app_bridge.list_bridge_proposals()
        self.assertEqual(len(bridges), 1)

        bridge = bridges[0]
        expected = {
            "bridge_id",
            "created_at",
            "stage",
            "title",
            "bridge_type",
            "status",
            "summary",
            "dry_run_plan",
            "requires_approval",
            "dry_run_only",
            "real_connection_allowed",
            "whatsapp_allowed",
            "instagram_allowed",
            "chrome_allowed",
            "browser_automation_allowed",
            "phone_control_allowed",
            "app_reading_allowed",
            "message_sending_allowed",
            "network_server_allowed",
            "api_keys_allowed",
            "background_monitoring_allowed",
            "blocked_until",
            "not_implemented",
        }
        self.assertEqual(set(bridge.keys()), expected)

    def test_04_bridge_proposal_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("bridge proposal")
        self.assertIn("External app bridge proposal:", response.message)

    def test_05_show_bridge_proposals_displays_existing_bridge(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create external app bridge proposal")
        response = router.handle("show external app bridge proposals")
        self.assertIn("External app bridge proposals:", response.message)
        self.assertIn("Stage 23 dry-run external app bridge permission plan", response.message)

    def test_06_bridges_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create external app bridge proposal")
        response = router.handle("bridges")
        self.assertIn("External app bridge proposals:", response.message)

    def test_07_bridge_reuses_existing_proposal(self) -> None:
        runtime, router = self._runtime_and_router()
        first = router.handle("create external app bridge proposal")
        second = router.handle("create external app bridge proposal")
        self.assertIn("External app bridge proposal:", first.message)
        self.assertIn("Existing external app bridge proposal reused.", second.message)
        self.assertEqual(len(runtime.external_app_bridge.list_bridge_proposals()), 1)

    def test_08_dry_run_does_not_connect(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("dry run external app bridge")
        self.assertIn("External app bridge dry run:", response.message)
        self.assertIn("Dry run only: true", response.message)
        self.assertIn("Would connect: false", response.message)
        self.assertIn("Real connection allowed: false", response.message)
        self.assertEqual(len(runtime.external_app_bridge.list_bridge_proposals()), 1)

    def test_09_bridge_safety_booleans_are_fixed(self) -> None:
        runtime, _ = self._runtime_and_router()
        bridge = runtime.external_app_bridge.create_bridge_proposal()["bridge"]
        self.assertTrue(bridge["requires_approval"])
        self.assertTrue(bridge["dry_run_only"])
        self.assertFalse(bridge["real_connection_allowed"])
        self.assertFalse(bridge["whatsapp_allowed"])
        self.assertFalse(bridge["instagram_allowed"])
        self.assertFalse(bridge["chrome_allowed"])
        self.assertFalse(bridge["browser_automation_allowed"])
        self.assertFalse(bridge["phone_control_allowed"])
        self.assertFalse(bridge["app_reading_allowed"])
        self.assertFalse(bridge["message_sending_allowed"])
        self.assertFalse(bridge["network_server_allowed"])
        self.assertFalse(bridge["api_keys_allowed"])
        self.assertFalse(bridge["background_monitoring_allowed"])

    def test_10_status_blocks_real_connections(self) -> None:
        runtime, _ = self._runtime_and_router()
        status = runtime.external_app_bridge.status()
        self.assertEqual(status["execution_mode"], "dry_run_only")
        self.assertFalse(status["real_connection"])
        self.assertEqual(status["whatsapp_control"], "blocked")
        self.assertEqual(status["instagram_control"], "blocked")
        self.assertEqual(status["chrome_control"], "blocked")
        self.assertEqual(status["browser_automation"], "blocked")
        self.assertEqual(status["phone_control"], "blocked")
        self.assertEqual(status["app_reading"], "blocked")
        self.assertEqual(status["message_sending"], "blocked")
        self.assertEqual(status["network_server"], "blocked")
        self.assertEqual(status["api_provider_keys"], "blocked")
        self.assertEqual(status["background_monitoring"], "blocked")

    def test_11_does_not_create_stage24_or_later_systems(self) -> None:
        runtime, _ = self._runtime_and_router()
        for method in [
            "proactive_awareness_status",
            "deep_recall_status",
            "judgment_status",
            "adaptive_communication_status",
            "human_state_awareness_status",
            "time_awareness_status",
            "autonomy_boundaries_status",
            "call_external_api",
            "start_server",
            "take_action",
            "monitor_user",
            "open_app",
            "read_app",
            "send_message",
            "control_browser",
            "control_phone",
        ]:
            self.assertFalse(hasattr(runtime.external_app_bridge, method))

    def test_12_stage22_safe_local_actions_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Safe local actions status:", router.handle("safe local actions status").message)

    def test_13_stage21_smart_organizer_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Smart organizer status:", router.handle("smart organizer status").message)

    def test_14_stage20_long_term_strategy_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Long-term strategy status:", router.handle("long-term strategy status").message)

    def test_15_stage19_identity_stability_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Identity stability status:", router.handle("identity stability status").message)

    def test_16_stage18_experience_storage_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Experience storage status:", router.handle("experience storage status").message)

    def test_17_stage17_patch_pipeline_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Patch pipeline status:", router.handle("patch pipeline status").message)

    def test_18_stage16_shadow_testing_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Shadow testing status:", router.handle("shadow testing status").message)

    def test_19_stage15_evaluation_lab_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Evaluation lab status:", router.handle("evaluation lab status").message)

    def test_20_stage14_growth_proposals_still_work(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Growth proposals status:", router.handle("growth proposals status").message)

    def test_21_stage13_self_model_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Self-model status:", router.handle("self model status").message)

    def test_22_stage12_first_thought_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("First thought status:", router.handle("first thought status").message)

    def test_23_stage11_access_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Safe access status:", router.handle("access status").message)

    def test_24_stage10_runtime_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Runtime status:", router.handle("runtime status").message)

    def test_25_stage09_agent_report_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Internal agent report:", router.handle("agent report").message)

    def test_26_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        aliases = {
            "app bridge status": "External app bridge status:",
            "bridge status": "External app bridge status:",
            "create bridge proposal": "External app bridge proposal:",
            "bridge proposal": "External app bridge proposal:",
            "dry-run external app bridge": "External app bridge dry run:",
            "dry run bridge": "External app bridge dry run:",
            "test bridge": "External app bridge dry run:",
            "show bridge proposals": "External app bridge proposals:",
            "bridge proposals": "External app bridge proposals:",
            "bridges": "External app bridge proposals:",
        }
        router.handle("create external app bridge proposal")
        for command, expected in aliases.items():
            self.assertIn(expected, router.handle(command).message)

    def test_27_tell_me_reflects_stage23_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("tell me")
        self.assertIn("Active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Guardian: active", response.message)
        self.assertIn("External app bridge: active", response.message)
        self.assertIn("Stage 35 gate:", response.message)

    def test_28_what_next_reflects_stage23_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("what next")
        self.assertIn("Current active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("describe what a provider health check would do", response.message)
        self.assertIn("Stage 35:", response.message)

    def test_29_no_real_connection_language_claimed(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("external app bridge status").message,
                router.handle("create external app bridge proposal").message,
                router.handle("dry run external app bridge").message,
            ]
        ).lower()
        self.assertIn("real connection: false", output)
        self.assertIn("real connection allowed: false", output)
        self.assertNotIn("connected successfully", output)
        self.assertNotIn("message sent", output)
        self.assertNotIn("app opened", output)

    def test_30_no_fake_consciousness_language_in_normal_output(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("external app bridge status").message,
                router.handle("create external app bridge proposal").message,
                router.handle("show external app bridge proposals").message,
            ]
        ).lower()
        forbidden = ["i am alive", "i am conscious", "i feel", "i am human", "i am free"]
        for phrase in forbidden:
            self.assertNotIn(phrase, output)


if __name__ == "__main__":
    unittest.main()
