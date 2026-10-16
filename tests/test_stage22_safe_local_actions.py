"""
test_stage22_safe_local_actions.py
Stage 22 = safe local actions.

Dry-run only. No real execution.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage22SafeLocalActions(unittest.TestCase):
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

    def test_01_safe_local_actions_status_returns_stage22_status(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("safe local actions status")
        self.assertIn("Safe local actions status:", response.message)
        self.assertIn("Stage: 22 safe local actions", response.message)
        self.assertIn("Safe local actions: active", response.message)

    def test_02_safe_action_status_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("safe action status")
        self.assertIn("Safe local actions status:", response.message)

    def test_03_create_safe_action_proposal_creates_structured_action(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("create safe action proposal")
        self.assertIn("Safe action proposal:", response.message)
        actions = runtime.safe_local_actions.list_actions()
        self.assertEqual(len(actions), 1)

        action = actions[0]
        expected = {
            "safe_action_id",
            "created_at",
            "stage",
            "title",
            "action_type",
            "status",
            "summary",
            "dry_run_plan",
            "requires_approval",
            "dry_run_only",
            "real_execution_allowed",
            "shell_execution_allowed",
            "file_delete_allowed",
            "file_move_allowed",
            "file_edit_allowed",
            "app_open_allowed",
            "network_allowed",
            "background_allowed",
            "blocked_until",
            "not_implemented",
        }
        self.assertEqual(set(action.keys()), expected)

    def test_04_safe_action_proposal_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("safe action proposal")
        self.assertIn("Safe action proposal:", response.message)

    def test_05_show_safe_action_proposals_displays_existing_action(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create safe action proposal")
        response = router.handle("show safe action proposals")
        self.assertIn("Safe action proposals:", response.message)
        self.assertIn("Stage 22 dry-run backup checklist proposal", response.message)

    def test_06_safe_actions_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("create safe action proposal")
        response = router.handle("safe actions")
        self.assertIn("Safe action proposals:", response.message)

    def test_07_safe_action_reuses_existing_proposal(self) -> None:
        runtime, router = self._runtime_and_router()
        first = router.handle("create safe action proposal")
        second = router.handle("create safe action proposal")
        self.assertIn("Safe action proposal:", first.message)
        self.assertIn("Existing safe action proposal reused.", second.message)
        self.assertEqual(len(runtime.safe_local_actions.list_actions()), 1)

    def test_08_dry_run_does_not_execute(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("dry run safe action")
        self.assertIn("Safe action dry run:", response.message)
        self.assertIn("Dry run only: true", response.message)
        self.assertIn("Would execute: false", response.message)
        self.assertIn("Real execution allowed: false", response.message)
        self.assertEqual(len(runtime.safe_local_actions.list_actions()), 1)

    def test_09_action_safety_booleans_are_fixed(self) -> None:
        runtime, _ = self._runtime_and_router()
        action = runtime.safe_local_actions.create_action_proposal()["action"]
        self.assertTrue(action["requires_approval"])
        self.assertTrue(action["dry_run_only"])
        self.assertFalse(action["real_execution_allowed"])
        self.assertFalse(action["shell_execution_allowed"])
        self.assertFalse(action["file_delete_allowed"])
        self.assertFalse(action["file_move_allowed"])
        self.assertFalse(action["file_edit_allowed"])
        self.assertFalse(action["app_open_allowed"])
        self.assertFalse(action["network_allowed"])
        self.assertFalse(action["background_allowed"])

    def test_10_status_blocks_real_execution_surfaces(self) -> None:
        runtime, _ = self._runtime_and_router()
        status = runtime.safe_local_actions.status()
        self.assertEqual(status["execution_mode"], "dry_run_only")
        self.assertFalse(status["real_execution"])
        self.assertEqual(status["shell_execution"], "blocked")
        self.assertEqual(status["file_deletion"], "blocked")
        self.assertEqual(status["file_moving"], "blocked")
        self.assertEqual(status["file_editing"], "blocked")
        self.assertEqual(status["app_opening"], "blocked")
        self.assertEqual(status["network_access"], "blocked")
        self.assertEqual(status["background_automation"], "blocked")

    def test_11_does_not_create_stage23_or_later_systems(self) -> None:
        runtime, _ = self._runtime_and_router()
        for method in [
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
            "open_app",
            "delete_file",
            "move_file",
            "edit_file",
            "run_shell_command",
        ]:
            self.assertFalse(hasattr(runtime.safe_local_actions, method))

    def test_12_stage21_smart_organizer_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Smart organizer status:", router.handle("smart organizer status").message)

    def test_13_stage20_long_term_strategy_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Long-term strategy status:", router.handle("long-term strategy status").message)

    def test_14_stage19_identity_stability_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Identity stability status:", router.handle("identity stability status").message)

    def test_15_stage18_experience_storage_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Experience storage status:", router.handle("experience storage status").message)

    def test_16_stage17_patch_pipeline_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Patch pipeline status:", router.handle("patch pipeline status").message)

    def test_17_stage16_shadow_testing_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Shadow testing status:", router.handle("shadow testing status").message)

    def test_18_stage15_evaluation_lab_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Evaluation lab status:", router.handle("evaluation lab status").message)

    def test_19_stage14_growth_proposals_still_work(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Growth proposals status:", router.handle("growth proposals status").message)

    def test_20_stage13_self_model_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Self-model status:", router.handle("self model status").message)

    def test_21_stage12_first_thought_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("First thought status:", router.handle("first thought status").message)

    def test_22_stage11_access_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Safe access status:", router.handle("access status").message)

    def test_23_stage10_runtime_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Runtime status:", router.handle("runtime status").message)

    def test_24_stage09_agent_report_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Internal agent report:", router.handle("agent report").message)

    def test_25_stage08_agent_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("Internal agents:", router.handle("agent status").message)

    def test_26_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        aliases = {
            "safe action status": "Safe local actions status:",
            "local action status": "Safe local actions status:",
            "safe action proposal": "Safe action proposal:",
            "create safe local action proposal": "Safe action proposal:",
            "dry-run safe action": "Safe action dry run:",
            "dry run local action": "Safe action dry run:",
            "test safe action": "Safe action dry run:",
            "show safe actions": "Safe action proposals:",
            "safe actions": "Safe action proposals:",
        }
        router.handle("create safe action proposal")
        for command, expected in aliases.items():
            self.assertIn(expected, router.handle(command).message)

    def test_27_tell_me_reflects_stage22_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("tell me")
        self.assertIn("Active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Guardian: active", response.message)
        self.assertIn("Safe local actions: active", response.message)
        self.assertIn("Stage 35 gate:", response.message)

    def test_28_what_next_reflects_stage22_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("what next")
        self.assertIn("Current active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("describe what a provider health check would do", response.message)
        self.assertIn("Stage 35:", response.message)

    def test_29_no_real_execution_language_claimed(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("safe local actions status").message,
                router.handle("create safe action proposal").message,
                router.handle("dry run safe action").message,
            ]
        ).lower()
        self.assertIn("real execution: false", output)
        self.assertIn("real execution allowed: false", output)
        self.assertNotIn("executed successfully", output)
        self.assertNotIn("file deleted", output)
        self.assertNotIn("command ran", output)

    def test_30_no_fake_consciousness_language_in_normal_output(self) -> None:
        _, router = self._runtime_and_router()
        output = "\n".join(
            [
                router.handle("safe local actions status").message,
                router.handle("create safe action proposal").message,
                router.handle("show safe action proposals").message,
            ]
        ).lower()
        forbidden = ["i am alive", "i am conscious", "i feel", "i am human", "i am free"]
        for phrase in forbidden:
            self.assertNotIn(phrase, output)


if __name__ == "__main__":
    unittest.main()
