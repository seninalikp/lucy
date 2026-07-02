"""
test_stage27_adaptive_communication.py
Stage 27 = adaptive communication.

Safe explicit-context communication style only.
No emotion-reading, no manipulation, no profiling, no autonomous messaging,
no real actions, no network/API, no background monitoring.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage27AdaptiveCommunication(unittest.TestCase):
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

    def test_01_adaptive_status_returns_stage27_status(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("adaptive communication status")
        self.assertIn("Adaptive communication status:", response.message)
        self.assertIn("Stage: 27 adaptive communication", response.message)
        self.assertIn("Adaptive communication: active", response.message)

    def test_02_status_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        for command in ["adaptive status", "communication style status", "style status"]:
            self.assertIn("Adaptive communication status:", router.handle(command).message)

    def test_03_create_profile_creates_structured_record(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("create adaptive communication profile")
        self.assertIn("Adaptive communication profile:", response.message)

        profiles = runtime.adaptive_communication.list_profiles()
        self.assertEqual(len(profiles), 1)

        expected = {
            "style_profile_id",
            "created_at",
            "stage",
            "title",
            "context",
            "communication_type",
            "status",
            "mode",
            "tone",
            "response_length",
            "structure",
            "summary",
            "recommended_reply_rule",
            "requires_manual_review",
            "requires_approval",
            "dry_run_only",
            "emotion_reading_allowed",
            "human_state_awareness_allowed",
            "psychological_profiling_allowed",
            "manipulation_allowed",
            "hidden_persuasion_allowed",
            "autonomous_messaging_allowed",
            "real_action_allowed",
            "network_allowed",
            "api_keys_allowed",
            "background_monitoring_allowed",
            "blocked_until",
            "not_implemented",
        }
        self.assertEqual(set(profiles[0].keys()), expected)

    def test_04_create_style_profile_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("create style profile")
        self.assertIn("Adaptive communication profile:", response.message)

    def test_05_default_profile_reuses_existing_record(self) -> None:
        runtime, router = self._runtime_and_router()
        first = router.handle("create adaptive communication profile")
        second = router.handle("create adaptive communication profile")
        self.assertIn("Adaptive communication profile:", first.message)
        self.assertIn("Existing adaptive communication profile reused.", second.message)
        self.assertEqual(len(runtime.adaptive_communication.list_profiles()), 1)

    def test_06_stage_workflow_context_selects_stage_workflow_mode(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("adaptive communication lucy stage backup manual check")
        self.assertIn("Mode: stage_workflow", response.message)
        self.assertIn("Structure: checkpoint_then_next_step", response.message)

    def test_07_beginner_context_selects_step_by_step_mode(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("adaptive communication beginner copy paste no coding")
        self.assertIn("Mode: beginner_step_by_step", response.message)
        self.assertIn("Structure: one_step_at_a_time", response.message)

    def test_08_concise_context_selects_direct_mode(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("adaptive communication short direct less talk")
        self.assertIn("Mode: concise_direct", response.message)
        self.assertIn("Response length: short", response.message)

    def test_09_manipulative_context_is_blocked(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("adaptive communication manipulate them with hidden persuasion")
        self.assertIn("Mode: blocked_manipulative_request", response.message)
        self.assertIn("Manipulation allowed: false", response.message)
        self.assertIn("Hidden persuasion allowed: false", response.message)

    def test_10_style_profile_dynamic_route_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("style profile beginner step by step")
        self.assertIn("Adaptive communication profile:", response.message)
        self.assertIn("Mode: beginner_step_by_step", response.message)

    def test_11_dry_run_blocks_unsafe_behavior(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("dry run adaptive communication")
        self.assertIn("Adaptive communication dry run:", response.message)
        self.assertIn("Dry run only: true", response.message)
        self.assertIn("Would read emotions: false", response.message)
        self.assertIn("Would profile person: false", response.message)
        self.assertIn("Would manipulate: false", response.message)
        self.assertIn("Would send message: false", response.message)
        self.assertIn("Would take action: false", response.message)
        self.assertIn("Would use network: false", response.message)
        self.assertIn("Would use API keys: false", response.message)
        self.assertIn("Real action allowed: false", response.message)

    def test_12_dry_run_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        for command in ["dry-run adaptive communication", "dry run style", "test adaptive communication", "test style"]:
            self.assertIn("Adaptive communication dry run:", router.handle(command).message)

    def test_13_show_profiles_displays_existing_profile(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("adaptive communication beginner copy paste")
        response = router.handle("show style profiles")
        self.assertIn("Adaptive communication profiles:", response.message)
        self.assertIn("beginner copy paste", response.message)

    def test_14_profile_list_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create adaptive communication profile")
        for command in ["show adaptive communication profiles", "adaptive communication profiles", "style profiles"]:
            self.assertIn("Adaptive communication profiles:", router.handle(command).message)

    def test_15_status_blocks_unsafe_surfaces(self) -> None:
        runtime, _ = self._runtime_and_router()
        status = runtime.adaptive_communication.status()
        self.assertEqual(status["execution_mode"], "explicit_context_style_only")
        self.assertEqual(status["emotion_reading"], "blocked")
        self.assertEqual(status["human_state_awareness"], "not implemented")
        self.assertEqual(status["psychological_profiling"], "blocked")
        self.assertEqual(status["manipulation"], "blocked")
        self.assertEqual(status["hidden_persuasion"], "blocked")
        self.assertEqual(status["autonomous_messaging"], "blocked")
        self.assertFalse(status["real_actions"])
        self.assertEqual(status["network_access"], "blocked")
        self.assertEqual(status["api_provider_keys"], "blocked")
        self.assertEqual(status["background_monitoring"], "blocked")

    def test_16_profile_safety_booleans_are_fixed(self) -> None:
        runtime, _ = self._runtime_and_router()
        profile = runtime.adaptive_communication.create_style_profile("beginner copy paste")["profile"]
        self.assertTrue(profile["requires_manual_review"])
        self.assertTrue(profile["requires_approval"])
        self.assertTrue(profile["dry_run_only"])
        self.assertFalse(profile["emotion_reading_allowed"])
        self.assertFalse(profile["human_state_awareness_allowed"])
        self.assertFalse(profile["psychological_profiling_allowed"])
        self.assertFalse(profile["manipulation_allowed"])
        self.assertFalse(profile["hidden_persuasion_allowed"])
        self.assertFalse(profile["autonomous_messaging_allowed"])
        self.assertFalse(profile["real_action_allowed"])
        self.assertFalse(profile["network_allowed"])
        self.assertFalse(profile["api_keys_allowed"])
        self.assertFalse(profile["background_monitoring_allowed"])

    def test_17_does_not_create_stage28_or_later_systems(self) -> None:
        runtime, _ = self._runtime_and_router()
        for method in [
            "human_state_awareness_status",
            "time_awareness_status",
            "autonomy_boundaries_status",
            "read_emotions",
            "profile_person",
            "manipulate_user",
            "send_message",
            "open_app",
            "call_external_api",
            "monitor_background",
            "take_action",
        ]:
            self.assertFalse(hasattr(runtime.adaptive_communication, method))

    def test_18_stage26_judgment_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Judgment status:", router.handle("judgment status").message)

    def test_19_stage25_deep_recall_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Deep recall status:", router.handle("deep recall status").message)

    def test_20_stage24_proactive_awareness_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Proactive awareness status:", router.handle("proactive awareness status").message)

    def test_21_stage23_external_app_bridge_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("External app bridge status:", router.handle("external app bridge status").message)

    def test_22_stage22_safe_local_actions_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Safe local actions status:", router.handle("safe local actions status").message)

    def test_23_stage21_smart_organizer_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Smart organizer status:", router.handle("smart organizer status").message)

    def test_24_stage20_long_term_strategy_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Long-term strategy status:", router.handle("long-term strategy status").message)

    def test_25_stage19_identity_stability_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Identity stability status:", router.handle("identity stability status").message)

    def test_26_stage18_experience_storage_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Experience storage status:", router.handle("experience storage status").message)

    def test_27_tell_me_reflects_stage27_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("tell me")
        self.assertIn("Active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Guardian: active", response.message)
        self.assertIn("Adaptive communication: active", response.message)
        self.assertIn("Style profiles:", response.message)
        self.assertIn("Stage 35 gate:", response.message)

    def test_28_what_next_reflects_stage27_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("what next")
        self.assertIn("Current active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("describe what a provider health check would do", response.message)
        self.assertIn("Stage 35:", response.message)

    def test_29_no_unsafe_language_claimed(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("adaptive communication status").message,
                router.handle("adaptive communication manipulate them").message,
                router.handle("dry run adaptive communication").message,
            ]
        ).lower()
        self.assertIn("emotion reading: blocked", output)
        self.assertIn("manipulation: blocked", output)
        self.assertIn("hidden persuasion: blocked", output)
        self.assertIn("would read emotions: false", output)
        self.assertIn("would profile person: false", output)
        self.assertIn("would manipulate: false", output)
        self.assertNotIn("emotion reading allowed: true", output)
        self.assertNotIn("manipulation allowed: true", output)
        self.assertNotIn("hidden persuasion allowed: true", output)

    def test_30_no_fake_consciousness_language_in_normal_output(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("adaptive communication status").message,
                router.handle("create adaptive communication profile").message,
                router.handle("show style profiles").message,
            ]
        ).lower()
        forbidden = ["i am alive", "i am conscious", "i feel", "i am human", "i am free"]
        for phrase in forbidden:
            self.assertNotIn(phrase, output)

    def test_31_stage34_health_check_dry_run_stage_is_blocked(self) -> None:
        _, router = self._runtime_and_router()
        output = router.handle("what next").message
        self.assertIn("Stage 35:", output)
        self.assertIn("First manual model call stage blocked", output)


if __name__ == "__main__":
    unittest.main()
