import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.growth_proposals import (
    FORBIDDEN_GROWTH_PHRASES,
    GROWTH_PROPOSAL_STAGE,
    PROPOSAL_FIELDS,
    VALID_PROPOSAL_STATUSES,
    VALID_RISK_LEVELS,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class Stage14GrowthProposalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _runtime_and_router(self) -> tuple[LucyRuntime, CommandRouter]:
        runtime = LucyRuntime(project_root=self.root)
        return runtime, CommandRouter(runtime)

    def _proposal_file(self) -> Path:
        return self.root / "data" / "lucy" / "growth_proposals.json"

    def test_growth_proposals_status_returns_stage14_status(self) -> None:
        runtime, router = self._runtime_and_router()
        result = runtime.growth_proposals_status()
        response = router.handle("growth proposals status")

        self.assertEqual(result["stage"], GROWTH_PROPOSAL_STAGE)
        self.assertEqual(result["proposal_system"], "active")
        self.assertIn("Growth proposals status:", response.message)
        self.assertIn("Stage: 14 growth proposals", response.message)
        self.assertIn("Automatic patching: disabled", response.message)

    def test_propose_growth_creates_structured_proposal_record(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("propose growth")

        self.assertIn("Proposal:", response.message)
        self.assertTrue(self._proposal_file().exists())
        proposals = json.loads(self._proposal_file().read_text(encoding="utf-8"))
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0]["stage"], GROWTH_PROPOSAL_STAGE)

    def test_proposal_includes_required_fields_only(self) -> None:
        runtime, _ = self._runtime_and_router()
        proposal = runtime.propose_growth()

        self.assertEqual(tuple(proposal.keys()), PROPOSAL_FIELDS)

    def test_proposal_status_is_valid_and_not_applied_tested_or_patched(self) -> None:
        runtime, _ = self._runtime_and_router()
        proposal = runtime.propose_growth()

        self.assertIn(proposal["status"], VALID_PROPOSAL_STATUSES)
        self.assertNotIn(proposal["status"], {"applied", "tested", "shadow_passed", "patched"})
        self.assertIn(proposal["risk_level"], VALID_RISK_LEVELS)

    def test_proposal_requires_approval(self) -> None:
        runtime, _ = self._runtime_and_router()
        proposal = runtime.propose_growth()

        self.assertTrue(proposal["approval_required"])

    def test_proposal_does_not_edit_code_files(self) -> None:
        source_files = [
            Path("backend/lucy_core/router.py"),
            Path("backend/lucy_core/lucy_runtime.py"),
            Path("backend/lucy_core/growth_proposals.py"),
        ]
        before = {path: path.stat().st_mtime_ns for path in source_files}
        runtime, _ = self._runtime_and_router()

        runtime.propose_growth()

        after = {path: path.stat().st_mtime_ns for path in source_files}
        self.assertEqual(before, after)

    def test_proposal_does_not_create_evaluation_results_shadow_tests_patch_pipeline_or_experience_storage(self) -> None:
        runtime, _ = self._runtime_and_router()
        runtime.propose_growth()
        lucy_data = self.root / "data" / "lucy"

        self.assertFalse((lucy_data / "evaluation_results.json").exists())
        self.assertFalse((lucy_data / "evaluation_cases.json").exists())
        self.assertFalse((lucy_data / "shadow_tests.json").exists())
        self.assertFalse((lucy_data / "patch_pipeline.json").exists())
        self.assertFalse((lucy_data / "patch_pipeline").exists())
        self.assertFalse((lucy_data / "experience").exists())
        self.assertFalse((lucy_data / "experience_storage.json").exists())

    def test_growth_proposals_do_not_contain_fake_consciousness_language(self) -> None:
        runtime, router = self._runtime_and_router()
        proposal = runtime.propose_growth()
        output = "\n".join(
            [
                json.dumps(proposal),
                router.handle("growth proposals status").message,
                router.handle("growth proposals").message,
            ]
        ).lower()

        for phrase in FORBIDDEN_GROWTH_PHRASES:
            self.assertNotIn(phrase, output)

    def test_growth_proposals_do_not_change_guardian(self) -> None:
        runtime, _ = self._runtime_and_router()
        before = runtime.guardian_status()

        runtime.propose_growth()
        after = runtime.guardian_status()

        self.assertEqual(before["mode"], after["mode"])
        self.assertEqual(before["classifications"], after["classifications"])

    def test_growth_proposals_do_not_change_safe_access_policy(self) -> None:
        runtime, _ = self._runtime_and_router()
        before = runtime.safe_access_status()

        runtime.propose_growth()
        after = runtime.safe_access_status()

        for key in ["stage", "access_state", "external_access", "network_server", "phone_browser_access"]:
            self.assertEqual(before[key], after[key])

    def test_review_commands_only_change_status(self) -> None:
        runtime, router = self._runtime_and_router()
        proposal = runtime.propose_growth()

        approve = router.handle(f"approve growth proposal for future {proposal['proposal_id']}")
        reject = router.handle(f"reject growth proposal {proposal['proposal_id']}")
        proposals = runtime.list_growth_proposals()

        self.assertIn("No code was changed", approve.message)
        self.assertIn("No code was changed", reject.message)
        self.assertEqual(proposals[0]["status"], "rejected")

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
        response = router.handle("growth proposals status")

        self.assertTrue(hasattr(runtime, "evaluation_lab"))
        self.assertTrue(hasattr(runtime, "shadow_testing"))
        self.assertFalse(hasattr(runtime, "patch_pipeline"))
        self.assertIn("Shadow testing: active", response.message)
        self.assertNotIn("Stage: 17", response.message)

    def test_no_ui_voice_network_external_api_or_autonomy_behavior_added(self) -> None:
        runtime, _ = self._runtime_and_router()

        for method in ["start_server", "listen", "bind", "open_socket", "start_voice", "call_external_api"]:
            self.assertFalse(hasattr(runtime.growth_proposals, method))
        self.assertFalse(hasattr(runtime, "autonomy_engine"))
        self.assertFalse((self.root / "data" / "lucy" / "network").exists())
        self.assertFalse((self.root / "data" / "lucy" / "voice").exists())


if __name__ == "__main__":
    unittest.main()
