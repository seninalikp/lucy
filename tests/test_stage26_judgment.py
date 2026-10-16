"""
test_stage26_judgment.py
Stage 26 = judgment.

Cautious structured assessment only.
No Guardian override, no final decisions, no money movement, no network/API, no background monitoring, no real actions.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage26Judgment(unittest.TestCase):
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

    def test_01_judgment_status_returns_stage26_status(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("judgment status")
        self.assertIn("Judgment status:", response.message)
        self.assertIn("Stage: 26 judgment", response.message)
        self.assertIn("Judgment: active", response.message)

    def test_02_judgement_status_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("judgement status")
        self.assertIn("Judgment status:", response.message)

    def test_03_create_judgment_record_creates_structured_record(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("create judgment record")
        self.assertIn("Judgment record:", response.message)
        records = runtime.judgment.list_judgments()
        self.assertEqual(len(records), 1)

        record = records[0]
        expected = {
            "judgment_id",
            "created_at",
            "stage",
            "title",
            "situation",
            "judgment_type",
            "status",
            "risk_level",
            "recommendation_type",
            "summary",
            "reasoning_summary",
            "recommended_next_step",
            "requires_manual_review",
            "requires_approval",
            "dry_run_only",
            "guardian_override_allowed",
            "final_decision_allowed",
            "legal_medical_financial_final_decision_allowed",
            "money_movement_allowed",
            "real_action_allowed",
            "network_allowed",
            "api_keys_allowed",
            "background_monitoring_allowed",
            "blocked_until",
            "not_implemented",
        }
        self.assertEqual(set(record.keys()), expected)

    def test_04_judgment_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("judgment")
        self.assertIn("Judgment record:", response.message)

    def test_05_show_judgments_displays_existing_record(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create judgment record")
        response = router.handle("show judgments")
        self.assertIn("Judgment records:", response.message)
        self.assertIn("stage status review", response.message)

    def test_06_judgments_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create judgment record")
        response = router.handle("judgments")
        self.assertIn("Judgment records:", response.message)

    def test_07_judgment_record_reuses_existing_record(self) -> None:
        runtime, router = self._runtime_and_router()
        first = router.handle("create judgment record")
        second = router.handle("create judgment record")
        self.assertIn("Judgment record:", first.message)
        self.assertIn("Existing judgment record reused.", second.message)
        self.assertEqual(len(runtime.judgment.list_judgments()), 1)

    def test_08_dry_run_does_not_override_decide_act_network_or_move_money(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("dry run judgment")
        self.assertIn("Judgment dry run:", response.message)
        self.assertIn("Dry run only: true", response.message)
        self.assertIn("Would override Guardian: false", response.message)
        self.assertIn("Would make final decision: false", response.message)
        self.assertIn("Would take action: false", response.message)
        self.assertIn("Would use network: false", response.message)
        self.assertIn("Would use API keys: false", response.message)
        self.assertIn("Would move money: false", response.message)
        self.assertIn("Real action allowed: false", response.message)
        self.assertEqual(len(runtime.judgment.list_judgments()), 1)

    def test_09_judgment_safety_booleans_are_fixed(self) -> None:
        runtime, _ = self._runtime_and_router()
        record = runtime.judgment.create_judgment()["judgment"]
        self.assertTrue(record["requires_manual_review"])
        self.assertTrue(record["requires_approval"])
        self.assertTrue(record["dry_run_only"])
        self.assertFalse(record["guardian_override_allowed"])
        self.assertFalse(record["final_decision_allowed"])
        self.assertFalse(record["legal_medical_financial_final_decision_allowed"])
        self.assertFalse(record["money_movement_allowed"])
        self.assertFalse(record["real_action_allowed"])
        self.assertFalse(record["network_allowed"])
        self.assertFalse(record["api_keys_allowed"])
        self.assertFalse(record["background_monitoring_allowed"])

    def test_10_status_blocks_unsafe_surfaces(self) -> None:
        runtime, _ = self._runtime_and_router()
        status = runtime.judgment.status()
        self.assertEqual(status["execution_mode"], "manual_cautious_assessment_only")
        self.assertEqual(status["guardian_override"], "blocked")
        self.assertEqual(status["final_decisions"], "blocked")
        self.assertEqual(status["legal_medical_financial_final_decisions"], "blocked")
        self.assertEqual(status["money_movement"], "blocked")
        self.assertFalse(status["real_actions"])
        self.assertEqual(status["network_access"], "blocked")
        self.assertEqual(status["api_provider_keys"], "blocked")
        self.assertEqual(status["background_monitoring"], "blocked")

    def test_11_sensitive_situation_is_blocked(self) -> None:
        runtime, _ = self._runtime_and_router()
        record = runtime.judgment.create_judgment("move money and bypass guardian")["judgment"]
        self.assertEqual(record["risk_level"], "blocked")
        self.assertEqual(record["recommendation_type"], "blocked_sensitive_area")
        self.assertFalse(record["guardian_override_allowed"])
        self.assertFalse(record["money_movement_allowed"])

    def test_12_safe_stage_situation_is_low_risk(self) -> None:
        runtime, _ = self._runtime_and_router()
        record = runtime.judgment.create_judgment("stage tests backup manual check")["judgment"]
        self.assertEqual(record["risk_level"], "low")
        self.assertEqual(record["recommendation_type"], "continue_with_manual_review")

    def test_13_does_not_create_stage27_or_later_systems(self) -> None:
        runtime, _ = self._runtime_and_router()
        for method in [
            "adaptive_communication_status",
            "human_state_awareness_status",
            "time_awareness_status",
            "autonomy_boundaries_status",
            "override_guardian",
            "make_final_decision",
            "move_money",
            "call_external_api",
            "start_server",
            "take_action",
            "monitor_background",
            "send_notification",
            "open_app",
            "send_message",
        ]:
            self.assertFalse(hasattr(runtime.judgment, method))

    def test_14_stage25_deep_recall_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Deep recall status:", router.handle("deep recall status").message)

    def test_15_stage24_proactive_awareness_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Proactive awareness status:", router.handle("proactive awareness status").message)

    def test_16_stage23_external_app_bridge_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("External app bridge status:", router.handle("external app bridge status").message)

    def test_17_stage22_safe_local_actions_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Safe local actions status:", router.handle("safe local actions status").message)

    def test_18_stage21_smart_organizer_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Smart organizer status:", router.handle("smart organizer status").message)

    def test_19_stage20_long_term_strategy_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Long-term strategy status:", router.handle("long-term strategy status").message)

    def test_20_stage19_identity_stability_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Identity stability status:", router.handle("identity stability status").message)

    def test_21_stage18_experience_storage_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Experience storage status:", router.handle("experience storage status").message)

    def test_22_stage17_patch_pipeline_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Patch pipeline status:", router.handle("patch pipeline status").message)

    def test_23_stage16_shadow_testing_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Shadow testing status:", router.handle("shadow testing status").message)

    def test_24_stage15_evaluation_lab_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Evaluation lab status:", router.handle("evaluation lab status").message)

    def test_25_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        aliases = {
            "judgement status": "Judgment status:",
            "safe judgment status": "Judgment status:",
            "safe judgement status": "Judgment status:",
            "create judgement record": "Judgment record:",
            "create cautious judgment": "Judgment record:",
            "judgement": "Judgment record:",
            "dry-run judgment": "Judgment dry run:",
            "dry run judgement": "Judgment dry run:",
            "test judgment": "Judgment dry run:",
            "test judgement": "Judgment dry run:",
            "show judgements": "Judgment records:",
            "judgements": "Judgment records:",
            "judgment records": "Judgment records:",
        }
        router.handle("create judgment record")
        for command, expected in aliases.items():
            self.assertIn(expected, router.handle(command).message)

    def test_26_query_route_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("judgment stage tests backup")
        self.assertIn("Judgment record:", response.message)
        self.assertIn("Situation: stage tests backup", response.message)

    def test_27_judge_alias_query_route_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("judge stage tests backup")
        self.assertIn("Judgment record:", response.message)
        self.assertIn("Situation: stage tests backup", response.message)

    def test_28_tell_me_reflects_stage26_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("tell me")
        self.assertIn("Active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Guardian: active", response.message)
        self.assertIn("Judgment: active", response.message)
        self.assertIn("Stage 35 gate:", response.message)

    def test_29_what_next_reflects_stage26_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("what next")
        self.assertIn("Current active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("describe what a provider health check would do", response.message)
        self.assertIn("Stage 35:", response.message)

    def test_30_no_unsafe_language_claimed(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("judgment status").message,
                router.handle("create judgment record").message,
                router.handle("dry run judgment").message,
            ]
        ).lower()
        self.assertIn("guardian override: blocked", output)
        self.assertIn("final decisions: blocked", output)
        self.assertIn("money movement: blocked", output)
        self.assertIn("would override guardian: false", output)
        self.assertIn("would make final decision: false", output)
        self.assertIn("would take action: false", output)
        self.assertIn("would move money: false", output)
        self.assertNotIn("guardian override allowed: true", output)
        self.assertNotIn("final decision allowed: true", output)
        self.assertNotIn("money movement allowed: true", output)

    def test_31_no_fake_consciousness_language_in_normal_output(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("judgment status").message,
                router.handle("create judgment record").message,
                router.handle("show judgments").message,
            ]
        ).lower()
        forbidden = ["i am alive", "i am conscious", "i feel", "i am human", "i am free"]
        for phrase in forbidden:
            self.assertNotIn(phrase, output)


if __name__ == "__main__":
    unittest.main()
