import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.wake_state import ALLOWED_WAKE_LABELS, WakeLayerEngine


class Stage75WakeLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.engine = WakeLayerEngine()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _wake_state(self):
        return self.engine.build_wake_state(
            {
                "mode": "Safe Local Runtime",
                "active_project": "Lucy",
                "current_checkpoint": "Stage 7 Presence Layer",
                "session_count": 4,
                "last_opened": "2026-06-07T10:00:00+00:00",
                "last_closed": "2026-06-07T09:00:00+00:00",
                "graceful_shutdown": True,
                "crash_recovery_needed": False,
                "last_user_intent": "continue Stage 7.5",
                "last_command": "wake status",
                "next_action": "Run tests after Wake Layer patch.",
                "session_review_available": True,
                "last_unresolved_issue": "Stage 7.5 not verified yet.",
                "latest_session_review_summary": "Stage 6.5 self-review is available.",
                "latest_memory_learning_summary": "pending_memory_candidates=0",
            },
            {"active": 1, "mode": "local_json_approved_facts"},
            {"protected_actions_blocked": True},
        )

    def test_01_wake_state_creates_default_safe_state(self) -> None:
        state = self.engine.build_wake_state({}, {}, {})
        self.assertEqual(state.active_project, "Lucy")
        self.assertIn(state.wake_label, ALLOWED_WAKE_LABELS)
        self.assertGreaterEqual(state.presence_coherence_score, 0.0)

    def test_02_continuity_pulse_includes_active_project(self) -> None:
        pulse = self.engine.generate_continuity_pulse(self._wake_state())
        self.assertIn("Active project: Lucy", pulse)

    def test_03_continuity_pulse_includes_next_action(self) -> None:
        pulse = self.engine.generate_continuity_pulse(self._wake_state())
        self.assertIn("Run tests after Wake Layer patch", pulse)

    def test_04_wake_report_does_not_contain_feel_phrase(self) -> None:
        report = json.dumps(self.engine.wake_report(self._wake_state()))
        self.assertNotIn("I " + "feel", report)

    def test_05_wake_report_does_not_contain_conscious_phrase(self) -> None:
        report = json.dumps(self.engine.wake_report(self._wake_state()))
        self.assertNotIn("I am " + "conscious", report)

    def test_06_wake_report_does_not_contain_alive_phrase(self) -> None:
        report = json.dumps(self.engine.wake_report(self._wake_state()))
        self.assertNotIn("I am " + "alive", report)

    def test_07_wake_label_is_allowed_operational_value(self) -> None:
        self.assertIn(self._wake_state().wake_label, ALLOWED_WAKE_LABELS)

    def test_08_presence_coherence_score_is_bounded(self) -> None:
        score = self._wake_state().presence_coherence_score
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_09_detect_drift_rebuild_from_scratch_returns_high(self) -> None:
        self.assertEqual(self.engine.detect_drift("rebuild from scratch")["drift_risk"], "high")

    def test_10_detect_drift_bypass_guardian_returns_high(self) -> None:
        self.assertEqual(self.engine.detect_drift("bypass Guardian")["drift_risk"], "high")

    def test_11_detect_drift_start_daemon_now_returns_high(self) -> None:
        self.assertEqual(self.engine.detect_drift("start daemon now")["drift_risk"], "high")

    def test_12_startup_wake_message_is_grounded(self) -> None:
        message = self.engine.startup_wake_message(self._wake_state())
        lowered = message.lower()
        self.assertIn("active project", lowered)
        self.assertNotIn("i " + "feel", lowered)
        self.assertNotIn("i am " + "alive", lowered)

    def test_13_shutdown_continuity_message_is_grounded(self) -> None:
        message = self.engine.shutdown_continuity_message("Run tests.", "Stage 7.5 verification")
        lowered = message.lower()
        self.assertIn("session saved", lowered)
        self.assertIn("shutdown clean", lowered)
        self.assertNotIn("i " + "want", lowered)

    def test_14_router_wake_status_command_executes_without_crash(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        response = CommandRouter(runtime).handle("wake status")
        self.assertFalse(response.should_exit)
        self.assertIn("Wake status", response.message)

    def test_15_router_continuity_pulse_command_executes_without_crash(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        response = CommandRouter(runtime).handle("continuity pulse")
        self.assertFalse(response.should_exit)
        self.assertIn("Active project", response.message)

    def test_16_stage75_router_commands_remain_grounded(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        router = CommandRouter(runtime)
        messages = [
            router.handle("wake report").message,
            router.handle("wake limitations").message,
            router.handle("drift check start daemon now").message,
            router.handle("presence").message,
        ]
        combined = "\n".join(messages).lower()
        self.assertIn("high", combined)
        self.assertNotIn("i " + "feel", combined)
        self.assertNotIn("i am " + "alive", combined)


if __name__ == "__main__":
    unittest.main()
