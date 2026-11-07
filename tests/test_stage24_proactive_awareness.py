"""
test_stage24_proactive_awareness.py
Stage 24 = proactive awareness.

Manual dry-run only. No background monitoring, notifications, or autonomous actions.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.proactive_awareness import ProactiveAwareness


class TestStage24ProactiveAwareness(unittest.TestCase):
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

    def test_01_proactive_awareness_status_returns_stage24_status(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("proactive awareness status")
        self.assertIn("Proactive awareness status:", response.message)
        self.assertIn("Stage: 24 proactive awareness", response.message)
        self.assertIn("Proactive awareness: active", response.message)

    def test_02_awareness_status_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("awareness status")
        self.assertIn("Proactive awareness status:", response.message)

    def test_03_create_awareness_scan_creates_structured_scan(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("create proactive awareness scan")
        self.assertIn("Proactive awareness scan:", response.message)
        scans = runtime.proactive_awareness.list_awareness_scans()
        self.assertEqual(len(scans), 1)

        scan = scans[0]
        expected = {
            "awareness_scan_id",
            "created_at",
            "stage",
            "title",
            "awareness_type",
            "status",
            "summary",
            "observations",
            "dry_run_plan",
            "requires_approval",
            "dry_run_only",
            "background_monitoring_allowed",
            "automatic_notifications_allowed",
            "automatic_reminder_firing_allowed",
            "scheduled_autonomous_checks_allowed",
            "real_action_allowed",
            "external_bridge_execution_allowed",
            "network_allowed",
            "api_keys_allowed",
            "blocked_until",
            "not_implemented",
        }
        self.assertEqual(set(scan.keys()), expected)

    def test_04_awareness_scan_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("awareness scan")
        self.assertIn("Proactive awareness scan:", response.message)

    def test_05_show_awareness_scans_displays_existing_scan(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create proactive awareness scan")
        response = router.handle("show proactive awareness scans")
        self.assertIn("Proactive awareness scans:", response.message)
        self.assertIn("Stage 24 manual proactive awareness dry-run scan", response.message)

    def test_06_awareness_scans_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create proactive awareness scan")
        response = router.handle("awareness scans")
        self.assertIn("Proactive awareness scans:", response.message)

    def test_07_awareness_scan_reuses_existing_scan(self) -> None:
        runtime, router = self._runtime_and_router()
        first = router.handle("create proactive awareness scan")
        second = router.handle("create proactive awareness scan")
        self.assertIn("Proactive awareness scan:", first.message)
        self.assertIn("Existing proactive awareness scan reused.", second.message)
        self.assertEqual(len(runtime.proactive_awareness.list_awareness_scans()), 1)

    def test_08_dry_run_does_not_monitor_notify_or_act(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("dry run proactive awareness")
        self.assertIn("Proactive awareness dry run:", response.message)
        self.assertIn("Dry run only: true", response.message)
        self.assertIn("Would monitor background: false", response.message)
        self.assertIn("Would notify: false", response.message)
        self.assertIn("Would take action: false", response.message)
        self.assertIn("Real action allowed: false", response.message)
        self.assertEqual(len(runtime.proactive_awareness.list_awareness_scans()), 1)

    def test_09_awareness_safety_booleans_are_fixed(self) -> None:
        runtime, _ = self._runtime_and_router()
        scan = runtime.proactive_awareness.create_awareness_scan()["scan"]
        self.assertTrue(scan["requires_approval"])
        self.assertTrue(scan["dry_run_only"])
        self.assertFalse(scan["background_monitoring_allowed"])
        self.assertFalse(scan["automatic_notifications_allowed"])
        self.assertFalse(scan["automatic_reminder_firing_allowed"])
        self.assertFalse(scan["scheduled_autonomous_checks_allowed"])
        self.assertFalse(scan["real_action_allowed"])
        self.assertFalse(scan["external_bridge_execution_allowed"])
        self.assertFalse(scan["network_allowed"])
        self.assertFalse(scan["api_keys_allowed"])

    def test_10_status_blocks_autonomous_surfaces(self) -> None:
        runtime, _ = self._runtime_and_router()
        status = runtime.proactive_awareness.status()
        self.assertEqual(status["execution_mode"], "manual_dry_run_only")
        self.assertEqual(status["background_monitoring"], "blocked")
        self.assertEqual(status["automatic_notifications"], "blocked")
        self.assertEqual(status["automatic_reminder_firing"], "blocked")
        self.assertEqual(status["scheduled_autonomous_checks"], "blocked")
        self.assertFalse(status["real_actions"])
        self.assertEqual(status["external_app_bridge_execution"], "blocked")
        self.assertEqual(status["network_access"], "blocked")
        self.assertEqual(status["api_provider_keys"], "blocked")

    def test_11_does_not_create_stage25_or_later_systems(self) -> None:
        runtime, _ = self._runtime_and_router()
        for method in [
            "deep_recall_status",
            "judgment_status",
            "adaptive_communication_status",
            "human_state_awareness_status",
            "time_awareness_status",
            "autonomy_boundaries_status",
            "call_external_api",
            "start_server",
            "take_action",
            "monitor_background",
            "send_notification",
            "fire_reminder",
            "schedule_autonomous_check",
            "open_app",
            "send_message",
        ]:
            self.assertFalse(hasattr(runtime.proactive_awareness, method))

    def test_12_stage23_external_app_bridge_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("External app bridge status:", router.handle("external app bridge status").message)

    def test_13_stage22_safe_local_actions_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Safe local actions status:", router.handle("safe local actions status").message)

    def test_14_stage21_smart_organizer_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Smart organizer status:", router.handle("smart organizer status").message)

    def test_15_stage20_long_term_strategy_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Long-term strategy status:", router.handle("long-term strategy status").message)

    def test_16_stage19_identity_stability_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Identity stability status:", router.handle("identity stability status").message)

    def test_17_stage18_experience_storage_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Experience storage status:", router.handle("experience storage status").message)

    def test_18_stage17_patch_pipeline_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Patch pipeline status:", router.handle("patch pipeline status").message)

    def test_19_stage16_shadow_testing_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Shadow testing status:", router.handle("shadow testing status").message)

    def test_20_stage15_evaluation_lab_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Evaluation lab status:", router.handle("evaluation lab status").message)

    def test_21_stage14_growth_proposals_still_work(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Growth proposals status:", router.handle("growth proposals status").message)

    def test_22_stage13_self_model_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Self-model status:", router.handle("self model status").message)

    def test_23_stage12_first_thought_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("First thought status:", router.handle("first thought status").message)

    def test_24_stage11_access_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Safe access status:", router.handle("access status").message)

    def test_25_stage10_runtime_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Runtime status:", router.handle("runtime status").message)

    def test_26_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        aliases = {
            "awareness status": "Proactive awareness status:",
            "local awareness status": "Proactive awareness status:",
            "create awareness scan": "Proactive awareness scan:",
            "awareness scan": "Proactive awareness scan:",
            "dry-run proactive awareness": "Proactive awareness dry run:",
            "dry run awareness": "Proactive awareness dry run:",
            "test awareness": "Proactive awareness dry run:",
            "show awareness scans": "Proactive awareness scans:",
            "awareness scans": "Proactive awareness scans:",
        }
        router.handle("create proactive awareness scan")
        for command, expected in aliases.items():
            self.assertIn(expected, router.handle(command).message)

    def test_27_tell_me_reflects_stage24_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("tell me")
        self.assertIn("Active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Guardian: active", response.message)
        self.assertIn("Proactive awareness: active", response.message)
        self.assertIn("Stage 35 gate:", response.message)

    def test_28_what_next_reflects_stage24_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("what next")
        self.assertIn("Current active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("describe what a provider health check would do", response.message)
        self.assertIn("Stage 35:", response.message)

    def test_29_no_autonomy_language_claimed(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("proactive awareness status").message,
                router.handle("create proactive awareness scan").message,
                router.handle("dry run proactive awareness").message,
            ]
        ).lower()
        self.assertIn("background monitoring: blocked", output)
        self.assertIn("automatic notifications: blocked", output)
        self.assertIn("would monitor background: false", output)
        self.assertIn("would notify: false", output)
        self.assertIn("would take action: false", output)
        self.assertNotIn("monitoring started", output)
        self.assertNotIn("notification sent", output)
        self.assertNotIn("reminder fired", output)

    def test_30_no_fake_consciousness_language_in_normal_output(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("proactive awareness status").message,
                router.handle("create proactive awareness scan").message,
                router.handle("show proactive awareness scans").message,
            ]
        ).lower()
        forbidden = ["i am alive", "i am conscious", "i feel", "i am human", "i am free"]
        for phrase in forbidden:
            self.assertNotIn(phrase, output)


if __name__ == "__main__":
    unittest.main()
