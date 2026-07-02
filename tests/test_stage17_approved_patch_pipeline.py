import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.approved_patch_pipeline import (
    FORBIDDEN_PATCH_PLAN_PHRASES,
    PATCH_PIPELINE_STAGE,
    PATCH_PLAN_FIELDS,
    VALID_PATCH_PLAN_STATUSES,
    ApprovedPatchPipeline,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stage17ApprovedPatchPipelineTests(unittest.TestCase):
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

    def _patch_plan_file(self) -> Path:
        return self._data_dir() / "patch_plans.json"

    def _create_passed_shadow_test(self) -> tuple[LucyRuntime, CommandRouter]:
        runtime, router = self._runtime_and_router()
        proposal = runtime.propose_growth()
        router.handle(f"evaluate proposal {proposal['proposal_id']}")
        shadow = router.handle("run shadow test")
        self.assertIn("Shadow test:", shadow.message)
        return runtime, router

    def test_patch_pipeline_status_returns_stage17_status(self) -> None:
        runtime, router = self._runtime_and_router()
        status = runtime.patch_pipeline_status()
        response = router.handle("patch pipeline status")

        self.assertEqual(status["stage"], PATCH_PIPELINE_STAGE)
        self.assertIn("Patch pipeline status:", response.message)
        self.assertIn("Stage: 17 approved patch pipeline", response.message)
        self.assertIn("Real patching: disabled", response.message)
        self.assertIn("Implementation allowed: false", response.message)

    def test_create_patch_plan_creates_structured_plan_from_passed_shadow_test(self) -> None:
        _, router = self._create_passed_shadow_test()
        response = router.handle("create patch plan")

        self.assertIn("Patch plan:", response.message)
        self.assertTrue(self._patch_plan_file().exists())
        plans = json.loads(self._patch_plan_file().read_text(encoding="utf-8"))
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0]["stage"], PATCH_PIPELINE_STAGE)
        self.assertEqual(tuple(plans[0].keys()), PATCH_PLAN_FIELDS)

    def test_prepare_patch_plan_alias_creates_patch_plan(self) -> None:
        _, router = self._create_passed_shadow_test()
        response = router.handle("prepare patch plan")

        self.assertIn("Patch plan:", response.message)
        self.assertTrue(self._patch_plan_file().exists())

    def test_patch_aliases_work(self) -> None:
        _, router = self._create_passed_shadow_test()

        self.assertIn("Patch pipeline status:", router.handle("patch status").message)
        self.assertIn("Patch plan:", router.handle("prepare patch").message)
        self.assertIn("Patch plan:", router.handle("create patch").message)
        self.assertIn("Patch plans:", router.handle("show patch plan").message)

    def test_show_patch_plans_displays_existing_plans(self) -> None:
        _, router = self._create_passed_shadow_test()
        router.handle("create patch plan")
        response = router.handle("show patch plans")

        self.assertIn("Patch plans:", response.message)
        self.assertIn("Improve vague command handling", response.message)

    def test_patch_plan_status_works(self) -> None:
        _, router = self._create_passed_shadow_test()
        router.handle("create patch plan")
        response = router.handle("patch plan status")

        self.assertIn("Patch pipeline status:", response.message)
        self.assertIn("Latest plan:", response.message)

    def test_patch_plan_uses_only_allowed_status_values(self) -> None:
        _, router = self._create_passed_shadow_test()
        router.handle("create patch plan")
        plan = json.loads(self._patch_plan_file().read_text(encoding="utf-8"))[0]

        self.assertIn(plan["status"], VALID_PATCH_PLAN_STATUSES)
        self.assertNotIn(plan["status"], {"approved", "applied", "patched", "deployed", "auto_fixed", "self_modified", "completed"})

    def test_patch_plan_boolean_safety_flags_are_fixed(self) -> None:
        _, router = self._create_passed_shadow_test()
        router.handle("create patch plan")
        plan = json.loads(self._patch_plan_file().read_text(encoding="utf-8"))[0]

        self.assertTrue(plan["approval_required"])
        self.assertFalse(plan["real_patching_enabled"])
        self.assertFalse(plan["implementation_allowed"])

    def test_patch_plan_does_not_edit_code_files(self) -> None:
        source_files = [
            Path("backend/lucy_core/router.py"),
            Path("backend/lucy_core/lucy_runtime.py"),
            Path("backend/lucy_core/approved_patch_pipeline.py"),
        ]
        before = {path: path.stat().st_mtime_ns for path in source_files}
        _, router = self._create_passed_shadow_test()

        router.handle("create patch plan")

        after = {path: path.stat().st_mtime_ns for path in source_files}
        self.assertEqual(before, after)

    def test_patch_plan_does_not_create_diffs_or_apply_patches(self) -> None:
        _, router = self._create_passed_shadow_test()
        router.handle("create patch plan")
        lucy_data = self._data_dir()

        self.assertFalse((lucy_data / "generated_patch.diff").exists())
        self.assertFalse((lucy_data / "patch_pipeline").exists())
        self.assertFalse((lucy_data / "patches").exists())
        self.assertFalse(any(lucy_data.glob("*.patch")))

    def test_patch_plan_does_not_create_experience_records(self) -> None:
        _, router = self._create_passed_shadow_test()
        router.handle("create patch plan")
        lucy_data = self._data_dir()

        self.assertFalse((lucy_data / "experience").exists())
        self.assertFalse((lucy_data / "experience_storage.json").exists())
        self.assertFalse((lucy_data / "experience_records.json").exists())

    def test_patch_plan_does_not_use_provider_api_key_setup(self) -> None:
        runtime, _ = self._runtime_and_router()

        for method in ["setup_groq_key", "setup_gemini_key", "setup_openrouter_key", "provider_router_status", "call_external_api"]:
            self.assertFalse(hasattr(runtime.approved_patch_pipeline, method))
        self.assertFalse(hasattr(runtime, "provider_router"))
        self.assertFalse((self.root / "data" / "lucy" / "providers").exists())

    def test_patch_plan_does_not_approve_itself(self) -> None:
        _, router = self._create_passed_shadow_test()
        router.handle("create patch plan")
        plan = json.loads(self._patch_plan_file().read_text(encoding="utf-8"))[0]

        self.assertTrue(plan["approval_required"])
        self.assertNotIn(plan["status"], {"approved", "applied", "completed"})

    def test_missing_shadow_test_is_refused(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("create patch plan")

        self.assertIn("Patch plan unavailable", response.message)
        self.assertFalse(self._patch_plan_file().exists())

    def test_blocked_shadow_test_is_refused(self) -> None:
        pipeline = ApprovedPatchPipeline(self._data_dir())
        result = pipeline.create_patch_plan(
            [
                {
                    "shadow_test_id": "st_blocked",
                    "result": "blocked",
                    "proposal_id": "gp_blocked",
                    "evaluation_id": "ev_blocked",
                    "proposal_title": "Blocked plan",
                }
            ],
            [],
            [],
        )

        self.assertFalse(result["ok"])
        self.assertIn("no passed shadow test found", result["reason"])

    def test_patch_plan_reuses_existing_plan(self) -> None:
        _, router = self._create_passed_shadow_test()
        first = router.handle("create patch plan")
        second = router.handle("create patch plan")
        plans = json.loads(self._patch_plan_file().read_text(encoding="utf-8"))

        self.assertIn("Patch plan:", first.message)
        self.assertIn("Existing patch plan reused.", second.message)
        self.assertEqual(len(plans), 1)

    def test_patch_pipeline_output_does_not_contain_fake_consciousness_language(self) -> None:
        _, router = self._create_passed_shadow_test()
        output = "\n".join(
            [
                router.handle("patch pipeline status").message,
                router.handle("create patch plan").message,
                router.handle("show patch plans").message,
            ]
        ).lower()

        for phrase in FORBIDDEN_PATCH_PLAN_PHRASES:
            self.assertNotIn(phrase, output)

    def test_stage19_identity_stability_features_now_exist_after_stage19(self) -> None:
        runtime, _ = self._runtime_and_router()

        self.assertTrue(hasattr(runtime, "experience_storage"))
        self.assertTrue(hasattr(runtime, "identity_stability"))
        self.assertFalse(hasattr(runtime.approved_patch_pipeline, "store_experience"))
        self.assertFalse((self.root / "data" / "lucy" / "experience").exists())
        self.assertFalse((self.root / "data" / "lucy" / "identity_stability").exists())

    def test_existing_stage_commands_still_work(self) -> None:
        _, router = self._runtime_and_router()
        commands = [
            "shadow testing status",
            "run shadow test",
            "show shadow tests",
            "evaluation lab status",
            "evaluate proposal",
            "show evaluations",
            "growth proposals status",
            "self model status",
            "first thought status",
            "access status",
            "runtime status",
            "agent status",
            "agent report",
            "valuation lab status",
            "groth proposal status",
            "first thot status",
        ]
        for command in commands:
            with self.subTest(command=command):
                response = router.handle(command)
                self.assertFalse(response.should_exit)
                self.assertTrue(response.message.strip())

    def test_tell_me_reflects_stage18_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("tell me")

        self.assertIn("Active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Guardian: active", response.message)
        self.assertIn("Evaluation lab: active", response.message)
        self.assertIn("Shadow testing: active", response.message)
        self.assertIn("Patch pipeline: active", response.message)
        self.assertIn("Real patching: disabled", response.message)
        self.assertIn("Experience storage: active", response.message)

    def test_what_next_reflects_stage18_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("what next")

        self.assertIn("Current active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("describe what a provider health check would do, dry-run only, no network", response.message)
        self.assertIn("Stage 35:", response.message)
        self.assertIn("First manual model call stage blocked", response.message)

    def test_no_ui_voice_network_or_autonomy_behavior_added(self) -> None:
        runtime, _ = self._runtime_and_router()

        for method in ["start_server", "listen", "bind", "open_socket", "start_voice", "auto_implement", "self_modify"]:
            self.assertFalse(hasattr(runtime.approved_patch_pipeline, method))
        self.assertFalse(hasattr(runtime, "autonomy_engine"))
        self.assertFalse((self.root / "data" / "lucy" / "network").exists())
        self.assertFalse((self.root / "data" / "lucy" / "voice").exists())


if __name__ == "__main__":
    unittest.main()
