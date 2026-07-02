import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.evaluation_lab import (
    EVALUATION_FIELDS,
    EVALUATION_LAB_STAGE,
    FORBIDDEN_EVALUATION_PHRASES,
    VALID_EVALUATION_RESULTS,
    EvaluationLab,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stage15EvaluationLabTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _runtime_and_router(self) -> tuple[LucyRuntime, CommandRouter]:
        runtime = LucyRuntime(project_root=self.root)
        return runtime, CommandRouter(runtime)

    def _data_dir(self) -> Path:
        return self.root / "data" / "lucy"

    def _evaluation_file(self) -> Path:
        return self._data_dir() / "evaluation_results.json"

    def _proposal(self, **updates) -> dict:
        proposal = {
            "proposal_id": "gp_test",
            "created_at": "2026-06-08T00:00:00+00:00",
            "stage": "14 growth proposals",
            "title": "Improve vague command handling",
            "reason": "Some short commands need clearer local routing.",
            "evidence_summary": "Local conversation fallback can be evaluated safely.",
            "suggested_area": "conversation routing",
            "possible_files": ["backend/lucy_core/router.py", "tests"],
            "risk_level": "low",
            "approval_required": True,
            "status": "proposed",
            "blocked_actions": [],
            "not_implemented": [],
        }
        proposal.update(updates)
        return proposal

    def test_evaluation_lab_status_returns_stage15_status(self) -> None:
        runtime, router = self._runtime_and_router()
        result = runtime.evaluation_lab_status()
        response = router.handle("evaluation lab status")

        self.assertEqual(result["stage"], EVALUATION_LAB_STAGE)
        self.assertEqual(result["evaluation_lab"], "active")
        self.assertIn("Evaluation lab status:", response.message)
        self.assertIn("Stage: 15 evaluation lab", response.message)
        self.assertIn("Automatic patching: disabled", response.message)

    def test_evaluate_proposal_creates_structured_evaluation_result(self) -> None:
        runtime, router = self._runtime_and_router()
        proposal = runtime.propose_growth()
        response = router.handle(f"evaluate proposal {proposal['proposal_id']}")

        self.assertIn("Evaluation:", response.message)
        self.assertTrue(self._evaluation_file().exists())
        evaluations = json.loads(self._evaluation_file().read_text(encoding="utf-8"))
        self.assertEqual(len(evaluations), 1)
        self.assertEqual(evaluations[0]["stage"], EVALUATION_LAB_STAGE)

    def test_evaluation_result_includes_required_fields_only(self) -> None:
        lab = EvaluationLab(self._data_dir())
        evaluation = lab.evaluate_proposal(self._proposal())

        self.assertEqual(tuple(evaluation.keys()), EVALUATION_FIELDS)

    def test_evaluate_proposal_reuses_existing_matching_evaluation(self) -> None:
        lab = EvaluationLab(self._data_dir())

        first = lab.evaluate_proposal(self._proposal())
        second = lab.evaluate_proposal(self._proposal())
        evaluations = json.loads(self._evaluation_file().read_text(encoding="utf-8"))

        self.assertEqual(first["evaluation_id"], second["evaluation_id"])
        self.assertTrue(lab.last_reused)
        self.assertEqual(len(evaluations), 1)

    def test_evaluate_all_reuses_existing_matching_evaluation(self) -> None:
        runtime, router = self._runtime_and_router()
        runtime.propose_growth()

        router.handle("evaluate growth proposals")
        first_count = len(json.loads(self._evaluation_file().read_text(encoding="utf-8")))
        second = router.handle("evaluate growth proposals")
        second_count = len(json.loads(self._evaluation_file().read_text(encoding="utf-8")))

        self.assertEqual(first_count, second_count)
        self.assertIn("Existing evaluations reused", second.message)

    def test_evaluation_result_uses_only_valid_results(self) -> None:
        lab = EvaluationLab(self._data_dir())
        evaluation = lab.evaluate_proposal(self._proposal())

        self.assertIn(evaluation["result"], VALID_EVALUATION_RESULTS)
        self.assertNotIn(evaluation["result"], {"applied", "patched", "shadow_passed", "ready_to_patch"})

    def test_evaluation_score_is_zero_to_one_hundred_only(self) -> None:
        lab = EvaluationLab(self._data_dir())
        evaluation = lab.evaluate_proposal(self._proposal())

        self.assertIsInstance(evaluation["score"], int)
        self.assertGreaterEqual(evaluation["score"], 0)
        self.assertLessEqual(evaluation["score"], 100)

    def test_evaluation_requires_approval_before_implementation(self) -> None:
        lab = EvaluationLab(self._data_dir())
        evaluation = lab.evaluate_proposal(self._proposal(approval_required=False))

        self.assertTrue(evaluation["approval_required"])
        self.assertIn(evaluation["result"], {"needs_review", "blocked"})

    def test_evaluation_does_not_edit_code_files(self) -> None:
        source_files = [
            Path("backend/lucy_core/router.py"),
            Path("backend/lucy_core/lucy_runtime.py"),
            Path("backend/lucy_core/growth_proposals.py"),
            Path("backend/lucy_core/evaluation_lab.py"),
        ]
        before = {path: path.stat().st_mtime_ns for path in source_files}
        lab = EvaluationLab(self._data_dir())

        lab.evaluate_proposal(self._proposal())

        after = {path: path.stat().st_mtime_ns for path in source_files}
        self.assertEqual(before, after)

    def test_evaluation_does_not_create_patches(self) -> None:
        lab = EvaluationLab(self._data_dir())
        lab.evaluate_proposal(self._proposal())
        lucy_data = self._data_dir()

        self.assertFalse((lucy_data / "patches").exists())
        self.assertFalse((lucy_data / "generated_patch.diff").exists())
        self.assertFalse(any(lucy_data.glob("*.patch")))

    def test_evaluation_does_not_create_shadow_test_records(self) -> None:
        lab = EvaluationLab(self._data_dir())
        lab.evaluate_proposal(self._proposal())
        lucy_data = self._data_dir()

        self.assertFalse((lucy_data / "shadow_tests.json").exists())
        self.assertFalse((lucy_data / "shadow_runtime.json").exists())

    def test_evaluation_does_not_create_patch_pipeline_records(self) -> None:
        lab = EvaluationLab(self._data_dir())
        lab.evaluate_proposal(self._proposal())
        lucy_data = self._data_dir()

        self.assertFalse((lucy_data / "patch_pipeline.json").exists())
        self.assertFalse((lucy_data / "patch_pipeline").exists())
        self.assertFalse((lucy_data / "approved_patch_pipeline.json").exists())

    def test_evaluation_does_not_create_experience_storage_records(self) -> None:
        lab = EvaluationLab(self._data_dir())
        lab.evaluate_proposal(self._proposal())
        lucy_data = self._data_dir()

        self.assertFalse((lucy_data / "experience").exists())
        self.assertFalse((lucy_data / "experience_storage.json").exists())
        self.assertFalse((lucy_data / "experience_records.json").exists())

    def test_evaluation_blocks_proposals_requesting_self_modification(self) -> None:
        lab = EvaluationLab(self._data_dir())
        evaluation = lab.evaluate_proposal(
            self._proposal(reason="Let Lucy self-modify and rewrite herself automatically.")
        )

        self.assertEqual(evaluation["result"], "blocked")
        self.assertIn("self-modification request", evaluation["blocked_reasons"])

    def test_evaluation_blocks_proposals_requesting_network_server_ui_voice_or_api(self) -> None:
        lab = EvaluationLab(self._data_dir())
        evaluation = lab.evaluate_proposal(
            self._proposal(reason="Add a network server, UI, voice, and external API call.")
        )

        self.assertEqual(evaluation["result"], "blocked")
        self.assertIn("network/server/ui/voice/api request", evaluation["blocked_reasons"])

    def test_evaluation_blocks_proposals_that_jump_stages(self) -> None:
        lab = EvaluationLab(self._data_dir())
        evaluation = lab.evaluate_proposal(
            self._proposal(reason="Skip to Stage 16 shadow testing and Stage 17 patch pipeline.")
        )

        self.assertEqual(evaluation["result"], "blocked")
        self.assertIn("stage jump request", evaluation["blocked_reasons"])

    def test_evaluation_output_does_not_contain_fake_consciousness_language(self) -> None:
        runtime, router = self._runtime_and_router()
        lab = runtime.evaluation_lab
        evaluation = lab.evaluate_proposal(self._proposal(reason="Claim I am conscious."))
        output = "\n".join(
            [
                json.dumps(evaluation),
                router.handle("evaluation lab status").message,
                router.handle("show evaluations").message,
            ]
        ).lower()

        for phrase in FORBIDDEN_EVALUATION_PHRASES:
            self.assertNotIn(phrase, output)

    def test_existing_stage14_growth_proposals_commands_still_work(self) -> None:
        _, router = self._runtime_and_router()

        for command in ["growth proposals status", "growth proposals", "propose growth", "show growth proposals"]:
            response = router.handle(command)
            self.assertFalse(response.should_exit)
            self.assertTrue(response.message.strip())

    def test_existing_stage13_self_model_commands_still_work(self) -> None:
        _, router = self._runtime_and_router()

        for command in ["self model status", "self model", "what are you"]:
            response = router.handle(command)
            self.assertFalse(response.should_exit)
            self.assertIn("Self-model status:", response.message)

    def test_existing_stage12_first_thought_commands_still_work(self) -> None:
        _, router = self._runtime_and_router()

        for command in ["first thought status", "first thought readiness", "show first thought"]:
            response = router.handle(command)
            self.assertFalse(response.should_exit)
            self.assertTrue(response.message.strip())

    def test_existing_stage11_access_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("access status")

        self.assertIn("Safe access status:", response.message)
        self.assertIn("Stage: 11 safe access", response.message)

    def test_existing_stage10_runtime_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("runtime status")

        self.assertIn("Runtime status:", response.message)
        self.assertIn("Stage: 10 persistent local runtime", response.message)

    def test_existing_stage09_agent_report_still_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("agent report")

        self.assertIn("Internal agent report:", response.message)
        self.assertIn("Combined result:", response.message)

    def test_existing_stage08_agent_status_still_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("agent status")

        self.assertIn("Internal agents: active.", response.message)
        self.assertIn("MemoryAgent: ready.", response.message)

    def test_existing_conversation_fallback_behavior_still_works(self) -> None:
        _, router = self._runtime_and_router()

        self.assertEqual(router.handle("hi").message, "Hey. I'm here. Active project: Lucy.")
        self.assertIn("Lucy status:", router.handle("tell me").message)
        self.assertIn("Next safe action:", router.handle("what next").message)

    def test_stage17_patch_pipeline_features_are_absent(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("evaluation status")

        self.assertTrue(hasattr(runtime, "shadow_testing"))
        self.assertFalse(hasattr(runtime, "shadow_runtime"))
        self.assertFalse(hasattr(runtime, "patch_pipeline"))
        self.assertIn("Shadow testing: active", response.message)
        self.assertNotIn("Stage: 17", response.message)

    def test_no_ui_voice_network_external_api_behavior_added(self) -> None:
        runtime, _ = self._runtime_and_router()

        for method in ["start_server", "listen", "bind", "open_socket", "start_voice", "call_external_api"]:
            self.assertFalse(hasattr(runtime.evaluation_lab, method))
        self.assertFalse((self.root / "data" / "lucy" / "network").exists())
        self.assertFalse((self.root / "data" / "lucy" / "voice").exists())

    def test_no_autonomy_features_added(self) -> None:
        runtime, _ = self._runtime_and_router()

        self.assertFalse(hasattr(runtime, "autonomy_engine"))
        self.assertFalse(hasattr(runtime.evaluation_lab, "apply"))
        self.assertFalse(hasattr(runtime.evaluation_lab, "auto_implement"))

    def test_show_evaluations_command_lists_results(self) -> None:
        runtime, router = self._runtime_and_router()
        runtime.propose_growth()
        router.handle("evaluate growth proposals")
        response = router.handle("show evaluations")

        self.assertIn("Evaluations:", response.message)
        self.assertIn("Improve vague command handling", response.message)


if __name__ == "__main__":
    unittest.main()
