"""
test_stage29_time_awareness.py
Stage 29 = time awareness.

Manual explicit time-context awareness only.
No autonomous reminders, scheduled actions, notifications, background monitoring,
calendar/email/app reading, network/API time lookup, real actions, or autonomy.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage29TimeAwareness(unittest.TestCase):
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

    def test_01_time_status_returns_stage29_status(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("time awareness status")
        self.assertIn("Time awareness status:", response.message)
        self.assertIn("Stage: 29 time awareness", response.message)
        self.assertIn("Time awareness: active", response.message)

    def test_02_status_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        for command in ["time status", "time context status"]:
            self.assertIn("Time awareness status:", router.handle(command).message)

    def test_03_create_time_context_creates_structured_record(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("create time context")
        self.assertIn("Time context:", response.message)

        contexts = runtime.time_awareness.list_time_contexts()
        self.assertEqual(len(contexts), 1)

        expected = {
            "time_context_id",
            "created_at",
            "stage",
            "title",
            "explicit_time_context",
            "awareness_type",
            "status",
            "category",
            "interpretation",
            "summary",
            "recommended_reply_adjustment",
            "recommended_next_step",
            "local_runtime_clock_used",
            "observed_at_utc",
            "requires_manual_review",
            "requires_approval",
            "dry_run_only",
            "manual_context_only",
            "autonomous_reminders_allowed",
            "scheduled_actions_allowed",
            "automatic_notifications_allowed",
            "background_monitoring_allowed",
            "calendar_reading_allowed",
            "email_reading_allowed",
            "external_app_reading_allowed",
            "network_time_lookup_allowed",
            "real_action_allowed",
            "network_allowed",
            "api_keys_allowed",
            "blocked_until",
            "not_implemented",
        }
        self.assertEqual(set(contexts[0].keys()), expected)

    def test_04_time_awareness_default_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("time awareness")
        self.assertIn("Time context:", response.message)

    def test_05_default_context_reuses_existing_record(self) -> None:
        runtime, router = self._runtime_and_router()
        first = router.handle("create time context")
        second = router.handle("create time context")
        self.assertIn("Time context:", first.message)
        self.assertIn("Existing time context reused.", second.message)
        self.assertEqual(len(runtime.time_awareness.list_time_contexts()), 1)

    def test_06_today_context_selects_current_context(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("time awareness today we are finishing tests")
        self.assertIn("Category: current_time_context", response.message)
        self.assertIn("manual time context", response.message.lower())

    def test_07_tomorrow_context_selects_future_context(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("time context tomorrow continue after backup")
        self.assertIn("Category: future_relative_context", response.message)
        self.assertIn("planning context only", response.message.lower())

    def test_08_last_backup_context_selects_past_checkpoint_context(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("time context last backup checkpoint")
        self.assertIn("Category: past_or_checkpoint_context", response.message)
        self.assertIn("checkpoint", response.message.lower())

    def test_09_deadline_context_selects_deadline_context(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("time context deadline by tonight")
        self.assertIn("Category: deadline_context", response.message)
        self.assertIn("must not schedule or auto-execute", response.message.lower())

    def test_10_blocked_autonomous_time_request(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("time awareness remind me every day and read calendar")
        self.assertIn("Category: blocked_autonomous_time_request", response.message)
        self.assertIn("Autonomous reminders allowed: false", response.message)
        self.assertIn("Calendar reading allowed: false", response.message)

    def test_11_dry_run_blocks_unsafe_time_behavior(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("dry run time awareness")
        self.assertIn("Time awareness dry run:", response.message)
        self.assertIn("Dry run only: true", response.message)
        self.assertIn("Would create reminder: false", response.message)
        self.assertIn("Would schedule action: false", response.message)
        self.assertIn("Would send notification: false", response.message)
        self.assertIn("Would monitor background: false", response.message)
        self.assertIn("Would read calendar: false", response.message)
        self.assertIn("Would read email: false", response.message)
        self.assertIn("Would read external apps: false", response.message)
        self.assertIn("Would use network time: false", response.message)
        self.assertIn("Would use network: false", response.message)
        self.assertIn("Would use API keys: false", response.message)
        self.assertIn("Would take action: false", response.message)
        self.assertIn("Real action allowed: false", response.message)

    def test_12_dry_run_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        for command in ["dry-run time awareness", "dry run time", "test time awareness", "test time"]:
            self.assertIn("Time awareness dry run:", router.handle(command).message)

    def test_13_show_time_contexts_displays_existing_context(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("time context today stage 29")
        response = router.handle("show time contexts")
        self.assertIn("Time contexts:", response.message)
        self.assertIn("today stage 29", response.message.lower())

    def test_14_time_context_list_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create time context")
        for command in ["time contexts", "show time records", "time records"]:
            self.assertIn("Time contexts:", router.handle(command).message)

    def test_15_status_blocks_unsafe_surfaces(self) -> None:
        runtime, _ = self._runtime_and_router()
        status = runtime.time_awareness.status()
        self.assertEqual(status["execution_mode"], "manual_explicit_time_context_only")
        self.assertEqual(status["local_runtime_clock"], "allowed_for_manual_context")
        self.assertEqual(status["network_time_lookup"], "blocked")
        self.assertEqual(status["autonomous_reminders"], "blocked")
        self.assertEqual(status["scheduled_actions"], "blocked")
        self.assertEqual(status["automatic_notifications"], "blocked")
        self.assertEqual(status["background_monitoring"], "blocked")
        self.assertEqual(status["calendar_reading"], "blocked")
        self.assertEqual(status["email_reading"], "blocked")
        self.assertEqual(status["external_app_reading"], "blocked")
        self.assertFalse(status["real_actions"])
        self.assertEqual(status["network_access"], "blocked")
        self.assertEqual(status["api_provider_keys"], "blocked")

    def test_16_time_context_safety_booleans_are_fixed(self) -> None:
        runtime, _ = self._runtime_and_router()
        context = runtime.time_awareness.create_time_context("today")["time_context"]
        self.assertTrue(context["local_runtime_clock_used"])
        self.assertTrue(context["requires_manual_review"])
        self.assertTrue(context["requires_approval"])
        self.assertTrue(context["dry_run_only"])
        self.assertTrue(context["manual_context_only"])
        self.assertFalse(context["autonomous_reminders_allowed"])
        self.assertFalse(context["scheduled_actions_allowed"])
        self.assertFalse(context["automatic_notifications_allowed"])
        self.assertFalse(context["background_monitoring_allowed"])
        self.assertFalse(context["calendar_reading_allowed"])
        self.assertFalse(context["email_reading_allowed"])
        self.assertFalse(context["external_app_reading_allowed"])
        self.assertFalse(context["network_time_lookup_allowed"])
        self.assertFalse(context["real_action_allowed"])
        self.assertFalse(context["network_allowed"])
        self.assertFalse(context["api_keys_allowed"])

    def test_17_does_not_create_stage30_or_later_systems(self) -> None:
        runtime, _ = self._runtime_and_router()
        for method in [
            "autonomy_boundaries_status",
            "create_reminder",
            "schedule_action",
            "send_notification",
            "monitor_background",
            "read_calendar",
            "read_email",
            "read_external_apps",
            "lookup_network_time",
            "call_external_api",
            "take_action",
            "self_execute",
        ]:
            self.assertFalse(hasattr(runtime.time_awareness, method))

    def test_18_stage28_human_state_awareness_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Human-state awareness status:", router.handle("human state awareness status").message)

    def test_19_stage27_adaptive_communication_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Adaptive communication status:", router.handle("adaptive communication status").message)

    def test_20_stage26_judgment_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Judgment status:", router.handle("judgment status").message)

    def test_21_stage25_deep_recall_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Deep recall status:", router.handle("deep recall status").message)

    def test_22_stage24_proactive_awareness_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Proactive awareness status:", router.handle("proactive awareness status").message)

    def test_23_stage23_external_app_bridge_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("External app bridge status:", router.handle("external app bridge status").message)

    def test_24_stage22_safe_local_actions_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Safe local actions status:", router.handle("safe local actions status").message)

    def test_25_stage21_smart_organizer_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Smart organizer status:", router.handle("smart organizer status").message)

    def test_26_tell_me_reflects_stage29_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("tell me")
        self.assertIn("Active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Guardian: active", response.message)
        self.assertIn("Time awareness: active", response.message)
        self.assertIn("Time context records:", response.message)
        self.assertIn("Stage 35 gate:", response.message)

    def test_27_what_next_reflects_stage29_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("what next")
        self.assertIn("Current active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("describe what a provider health check would do", response.message)
        self.assertIn("Stage 35:", response.message)

    def test_28_no_unsafe_language_claimed(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("time awareness status").message,
                router.handle("time awareness remind me every day and read calendar").message,
                router.handle("dry run time awareness").message,
            ]
        ).lower()
        self.assertIn("autonomous reminders: blocked", output)
        self.assertIn("scheduled actions: blocked", output)
        self.assertIn("automatic notifications: blocked", output)
        self.assertIn("background monitoring: blocked", output)
        self.assertIn("calendar reading: blocked", output)
        self.assertIn("would create reminder: false", output)
        self.assertIn("would schedule action: false", output)
        self.assertIn("would read calendar: false", output)
        self.assertNotIn("autonomous reminders allowed: true", output)
        self.assertNotIn("scheduled actions allowed: true", output)
        self.assertNotIn("calendar reading allowed: true", output)

    def test_29_no_fake_consciousness_language_in_normal_output(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("time awareness status").message,
                router.handle("create time context").message,
                router.handle("show time contexts").message,
            ]
        ).lower()
        forbidden = ["i am alive", "i am conscious", "i feel", "i am human", "i am free"]
        for phrase in forbidden:
            self.assertNotIn(phrase, output)

    def test_30_stage34_health_check_dry_run_stage_is_blocked(self) -> None:
        _, router = self._runtime_and_router()
        output = router.handle("what next").message
        self.assertIn("Stage 35:", output)
        self.assertIn("First manual model call stage blocked", output)

    def test_31_local_runtime_clock_is_context_only(self) -> None:
        _, router = self._runtime_and_router()
        output = router.handle("time awareness status").message
        self.assertIn("Local runtime clock: allowed_for_manual_context", output)
        self.assertIn("Network time lookup: blocked", output)


if __name__ == "__main__":
    unittest.main()
