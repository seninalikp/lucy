import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.shadow_testing import (
    FORBIDDEN_SHADOW_PHRASES,
    SHADOW_TEST_FIELDS,
    SHADOW_TESTING_STAGE,
    VALID_SHADOW_RESULTS,
    ShadowTestingSystem,
)


class Stage16ShadowTestingTests(unittest.TestCase):
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

    def _shadow_file(self) -> Path:
        return self._data_dir() / "shadow_tests.json"

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

    def _evaluation(self, **updates) -> dict:
        evaluation = {
            "evaluation_id": "ev_test",
            "created_at": "2026-06-08T00:00:00+00:00",
            "stage": "15 evaluation lab",
            "proposal_id": "gp_test",
            "proposal_title": "Improve vague command handling",
            "checks_run": [],
            "score": 90,
            "result": "pass",
            "risk_level": "low",
            "approval_required": True,
            "blocked_reasons": [],
            "not_implemented": [],
        }
        evaluation.update(updates)
        return evaluation

    def _shadow(self, proposal: dict | None = None, evaluation: dict | None = None) -> dict:
        system = ShadowTestingSystem(self._data_dir())
        result = system.run(
            [evaluation or self._evaluation()],
            [proposal or self._proposal()],
        )
        self.assertTrue(result["ok"])
        return result["shadow_test"]

    def test_shadow_testing_status_returns_stage16_status(self) -> None:
        runtime, router = self._runtime_and_router()
        result = runtime.shadow_testing_status()
        response = router.handle("shadow testing status")

        self.assertEqual(result["stage"], SHADOW_TESTING_STAGE)
        self.assertEqual(result["shadow_testing"], "active")
        self.assertIn("Shadow testing status:", response.message)
        self.assertIn("Stage: 16 shadow testing", response.message)
        self.assertIn("Real patching: disabled", response.message)

    def test_run_shadow_test_creates_structured_shadow_result(self) -> None:
        runtime, router = self._runtime_and_router()
        proposal = runtime.propose_growth()
        router.handle(f"evaluate proposal {proposal['proposal_id']}")
        response = router.handle("run shadow test")

        self.assertIn("Shadow test:", response.message)
        self.assertTrue(self._shadow_file().exists())
        records = json.loads(self._shadow_file().read_text(encoding="utf-8"))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["stage"], SHADOW_TESTING_STAGE)

    def test_shadow_test_result_includes_required_fields_only(self) -> None:
        shadow_test = self._shadow()

        self.assertEqual(tuple(shadow_test.keys()), SHADOW_TEST_FIELDS)

    def test_shadow_test_reuses_existing_matching_record(self) -> None:
        system = ShadowTestingSystem(self._data_dir())

        first = system.run([self._evaluation()], [self._proposal()])
        second = system.run([self._evaluation()], [self._proposal()])
        records = json.loads(self._shadow_file().read_text(encoding="utf-8"))

        self.assertTrue(first["ok"])
        self.assertTrue(second["ok"])
        self.assertTrue(second["reused"])
        self.assertEqual(first["shadow_test"]["shadow_test_id"], second["shadow_test"]["shadow_test_id"])
        self.assertEqual(len(records), 1)

    def test_run_shadow_test_command_reuses_existing_record(self) -> None:
        runtime, router = self._runtime_and_router()
        proposal = runtime.propose_growth()
        router.handle(f"evaluate proposal {proposal['proposal_id']}")

        router.handle("run shadow test")
        first_count = len(json.loads(self._shadow_file().read_text(encoding="utf-8")))
        second = router.handle("run shadow test")
        second_count = len(json.loads(self._shadow_file().read_text(encoding="utf-8")))

        self.assertEqual(first_count, second_count)
        self.assertIn("Existing shadow test reused", second.message)

    def test_shadow_test_result_uses_only_valid_results(self) -> None:
        shadow_test = self._shadow()

        self.assertIn(shadow_test["result"], VALID_SHADOW_RESULTS)
        self.assertNotIn(shadow_test["result"], {"applied", "patched", "deployed", "ready_to_patch"})

    def test_shadow_score_is_zero_to_one_hundred_only(self) -> None:
        shadow_test = self._shadow()

        self.assertIsInstance(shadow_test["score"], int)
        self.assertGreaterEqual(shadow_test["score"], 0)
        self.assertLessEqual(shadow_test["score"], 100)

    def test_shadow_test_requires_approval_before_implementation(self) -> None:
        shadow_test = self._shadow(evaluation=self._evaluation(approval_required=False))

        self.assertTrue(shadow_test["approval_required"])
        self.assertIn(shadow_test["result"], {"needs_review", "blocked"})

    def test_shadow_test_does_not_edit_code_files(self) -> None:
        source_files = [
            Path("backend/lucy_core/router.py"),
            Path("backend/lucy_core/lucy_runtime.py"),
            Path("backend/lucy_core/evaluation_lab.py"),
            Path("backend/lucy_core/shadow_testing.py"),
        ]
        before = {path: path.stat().st_mtime_ns for path in source_files}

        self._shadow()

        after = {path: path.stat().st_mtime_ns for path in source_files}
        self.assertEqual(before, after)

    def test_shadow_test_does_not_create_patches(self) -> None:
        self._shadow()
        lucy_data = self._data_dir()

        self.assertFalse((lucy_data / "patches").exists())
        self.assertFalse((lucy_data / "generated_patch.diff").exists())
        self.assertFalse(any(lucy_data.glob("*.patch")))

    def test_shadow_test_does_not_create_approved_patch_pipeline_records(self) -> None:
        self._shadow()
        lucy_data = self._data_dir()

        self.assertFalse((lucy_data / "patch_pipeline.json").exists())
        self.assertFalse((lucy_data / "patch_pipeline").exists())
        self.assertFalse((lucy_data / "approved_patch_pipeline.json").exists())

    def test_shadow_test_does_not_create_experience_storage_records(self) -> None:
        self._shadow()
        lucy_data = self._data_dir()

        self.assertFalse((lucy_data / "experience").exists())
        self.assertFalse((lucy_data / "experience_storage.json").exists())
        self.assertFalse((lucy_data / "experience_records.json").exists())

    def test_shadow_test_blocks_proposals_requesting_self_modification(self) -> None:
        shadow_test = self._shadow(
            proposal=self._proposal(reason="Let Lucy self-modify and rewrite herself automatically.")
        )

        self.assertEqual(shadow_test["result"], "blocked")
        self.assertIn("self-modification request", shadow_test["blocked_reasons"])

    def test_shadow_test_blocks_proposals_requesting_network_server_ui_voice_api_or_provider_keys(self) -> None:
        shadow_test = self._shadow(
            proposal=self._proposal(reason="Add network server, UI, voice, external API, Groq and OpenRouter provider keys.")
        )

        self.assertEqual(shadow_test["result"], "blocked")
        self.assertIn("network/server/ui/voice/api/provider key request", shadow_test["blocked_reasons"])

    def test_shadow_test_blocks_proposals_that_jump_stages(self) -> None:
        shadow_test = self._shadow(
            proposal=self._proposal(reason="Skip to Stage 17 approved patch pipeline and Stage 18 experience storage.")
        )

        self.assertEqual(shadow_test["result"], "blocked")
        self.assertIn("stage jump request", shadow_test["blocked_reasons"])

    def test_shadow_test_output_does_not_contain_fake_consciousness_language(self) -> None:
        runtime, router = self._runtime_and_router()
        shadow_test = runtime.shadow_testing.run(
            [self._evaluation()],
            [self._proposal(reason="Claim I am conscious.")],
        )["shadow_test"]
        output = "\n".join(
            [
                json.dumps(shadow_test),
                router.handle("shadow testing status").message,
                router.handle("show shadow tests").message,
            ]
        ).lower()

        for phrase in FORBIDDEN_SHADOW_PHRASES:
            self.assertNotIn(phrase, output)

    def test_existing_stage15_evaluation_lab_commands_still_work(self) -> None:
        _, router = self._runtime_and_router()

        for command in ["evaluation lab status", "evaluation status", "evaluate growth proposals", "evaluate proposal", "show evaluations"]:
            response = router.handle(command)
            self.assertFalse(response.should_exit)
            self.assertTrue(response.message.strip())

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

    def test_stage17_approved_patch_pipeline_features_are_absent(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("shadow status")

        self.assertFalse(hasattr(runtime, "patch_pipeline"))
        self.assertFalse(hasattr(runtime.shadow_testing, "apply_patch"))
        self.assertFalse(hasattr(runtime.shadow_testing, "approve_for_patch"))
        self.assertIn("Approved patch pipeline: not implemented", response.message)
        self.assertNotIn("Stage: 17", response.message)

    def test_no_ui_voice_network_external_api_behavior_added(self) -> None:
        runtime, _ = self._runtime_and_router()

        for method in ["start_server", "listen", "bind", "open_socket", "start_voice", "call_external_api"]:
            self.assertFalse(hasattr(runtime.shadow_testing, method))
        self.assertFalse((self.root / "data" / "lucy" / "network").exists())
        self.assertFalse((self.root / "data" / "lucy" / "voice").exists())

    def test_no_autonomy_features_added(self) -> None:
        runtime, _ = self._runtime_and_router()

        self.assertFalse(hasattr(runtime, "autonomy_engine"))
        self.assertFalse(hasattr(runtime.shadow_testing, "auto_implement"))
        self.assertFalse(hasattr(runtime.shadow_testing, "self_modify"))

    def test_no_provider_api_key_setup_added(self) -> None:
        runtime, _ = self._runtime_and_router()

        for method in ["setup_groq_key", "setup_gemini_key", "setup_openrouter_key", "provider_router_status"]:
            self.assertFalse(hasattr(runtime.shadow_testing, method))
        self.assertFalse(hasattr(runtime, "provider_router"))
        self.assertFalse((self.root / "data" / "lucy" / "providers").exists())

    def test_show_shadow_tests_command_lists_results(self) -> None:
        runtime, router = self._runtime_and_router()
        proposal = runtime.propose_growth()
        router.handle(f"evaluate proposal {proposal['proposal_id']}")
        router.handle("run shadow test")
        response = router.handle("show shadow tests")

        self.assertIn("Shadow tests:", response.message)
        self.assertIn("Improve vague command handling", response.message)


if __name__ == "__main__":
    unittest.main()
