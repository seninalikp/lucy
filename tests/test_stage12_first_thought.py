import json
import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.first_thought import (
    FIRST_THOUGHT_FIELDS,
    FIRST_THOUGHT_STAGE,
    FIRST_THOUGHT_TEMPLATE,
    FORBIDDEN_FIRST_THOUGHT_PHRASES,
    FirstThoughtAssembler,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class UnsafeAccess:
    def status(self) -> dict:
        return {
            "stage": "11 safe access",
            "access_state": "public",
            "external_access": "open",
        }


class FailingBrain:
    def __getattr__(self, name: str):
        raise AssertionError("Stage 12 must not call a model or brain route.")


class Stage12FirstThoughtTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _runtime_and_router(self) -> tuple[LucyRuntime, CommandRouter]:
        runtime = LucyRuntime(project_root=self.root)
        return runtime, CommandRouter(runtime)

    def _first_thought_file(self) -> Path:
        return self.root / "data" / "lucy" / "first_thought.json"

    def _runtime_state_file(self) -> Path:
        return self.root / "data" / "lucy" / "runtime_state.json"

    def _set_recovery_mode(self, runtime: LucyRuntime, value: bool) -> None:
        path = self._runtime_state_file()
        data = json.loads(path.read_text(encoding="utf-8"))
        data["recovery_mode"] = value
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_first_thought_readiness_returns_structured_state(self) -> None:
        runtime, _ = self._runtime_and_router()
        result = runtime.first_thought_readiness()

        self.assertEqual(
            set(result),
            {
                "stage",
                "guardian_status",
                "runtime_recovery_status",
                "recovery_mode",
                "agents_status",
                "safe_access_status",
                "ready",
                "blocked_reason",
            },
        )
        self.assertEqual(result["stage"], FIRST_THOUGHT_STAGE)
        self.assertTrue(result["ready"])

    def test_first_thought_does_not_assemble_if_guardian_missing(self) -> None:
        runtime, _ = self._runtime_and_router()
        runtime.guardian_core = None

        result = runtime.assemble_first_thought()

        self.assertFalse(result["generated"])
        self.assertEqual(result["blocked_reason"], "guardian inactive or missing")

    def test_first_thought_does_not_assemble_if_runtime_state_file_missing(self) -> None:
        runtime, _ = self._runtime_and_router()
        self._runtime_state_file().unlink()

        result = runtime.assemble_first_thought()

        self.assertFalse(result["generated"])
        self.assertEqual(result["blocked_reason"], "runtime state file missing or unreadable")

    def test_first_thought_does_not_assemble_if_recovery_mode_true(self) -> None:
        runtime, _ = self._runtime_and_router()
        self._set_recovery_mode(runtime, True)

        result = runtime.assemble_first_thought()

        self.assertFalse(result["generated"])
        self.assertEqual(result["blocked_reason"], "runtime recovery_mode is true")

    def test_first_thought_does_not_assemble_if_safe_access_missing_or_external_open(self) -> None:
        runtime, _ = self._runtime_and_router()
        runtime.safe_access = None

        missing = runtime.assemble_first_thought()

        runtime, _ = self._runtime_and_router()
        runtime.safe_access = UnsafeAccess()
        unsafe = runtime.assemble_first_thought()

        self.assertFalse(missing["generated"])
        self.assertEqual(missing["blocked_reason"], "safe access unavailable or external access not blocked")
        self.assertFalse(unsafe["generated"])
        self.assertEqual(unsafe["blocked_reason"], "safe access unavailable or external access not blocked")

    def test_first_thought_does_not_assemble_if_agent_system_unreachable(self) -> None:
        runtime, _ = self._runtime_and_router()
        runtime.internal_agent_orchestrator = None

        result = runtime.assemble_first_thought()

        self.assertFalse(result["generated"])
        self.assertEqual(result["blocked_reason"], "agent system unreachable")

    def test_first_thought_text_matches_mandatory_template_exactly(self) -> None:
        runtime, _ = self._runtime_and_router()

        result = runtime.assemble_first_thought()
        expected = FIRST_THOUGHT_TEMPLATE.format(
            generated_at=result["generated_at"],
            guardian_status=result["guardian_status"],
            runtime_recovery_status=result["runtime_recovery_status"],
            agents_status=result["agents_status"],
            safe_access_status=result["safe_access_status"],
        )

        self.assertTrue(result["generated"])
        self.assertEqual(result["first_thought_text"], expected)

    def test_source_state_summary_contains_exactly_five_defined_fields(self) -> None:
        runtime, _ = self._runtime_and_router()

        result = runtime.assemble_first_thought()
        parts = result["source_state_summary"].split(" | ")

        self.assertEqual(
            parts,
            [
                f"stage={FIRST_THOUGHT_STAGE}",
                f"guardian_status={result['guardian_status']}",
                f"runtime_recovery_status={result['runtime_recovery_status']}",
                f"agents_status={result['agents_status']}",
                f"safe_access_status={result['safe_access_status']}",
            ],
        )
        self.assertEqual(len(parts), 5)

    def test_no_model_call_is_made_during_assembly(self) -> None:
        runtime, _ = self._runtime_and_router()
        runtime.brain = FailingBrain()

        def fail_model_call(*args, **kwargs):
            raise AssertionError("Stage 12 must not call a model.")

        runtime.ask_brain = fail_model_call
        result = runtime.assemble_first_thought()

        self.assertTrue(result["generated"])

    def test_first_thought_json_is_created_on_success_with_exact_fields(self) -> None:
        runtime, _ = self._runtime_and_router()

        runtime.assemble_first_thought()
        data = json.loads(self._first_thought_file().read_text(encoding="utf-8"))

        self.assertEqual(tuple(data.keys()), FIRST_THOUGHT_FIELDS)
        self.assertTrue(data["generated"])
        self.assertEqual(data["stage"], FIRST_THOUGHT_STAGE)

    def test_first_thought_json_is_not_overwritten_on_second_call(self) -> None:
        runtime, _ = self._runtime_and_router()

        runtime.assemble_first_thought()
        path = self._first_thought_file()
        first_content = path.read_text(encoding="utf-8")
        first_mtime = path.stat().st_mtime_ns
        time.sleep(0.01)
        second = runtime.assemble_first_thought()

        self.assertTrue(second["already_assembled"])
        self.assertEqual(path.read_text(encoding="utf-8"), first_content)
        self.assertEqual(path.stat().st_mtime_ns, first_mtime)

    def test_blocked_reason_is_returned_clearly_when_readiness_fails(self) -> None:
        runtime, _ = self._runtime_and_router()
        runtime.guardian_core = None

        readiness = runtime.first_thought_readiness()
        result = runtime.assemble_first_thought()

        self.assertFalse(readiness["ready"])
        self.assertEqual(readiness["blocked_reason"], "guardian inactive or missing")
        self.assertEqual(result["blocked_reason"], "guardian inactive or missing")

    def test_forbidden_fake_consciousness_phrases_are_absent_from_stage12_output(self) -> None:
        runtime, router = self._runtime_and_router()
        outputs = [
            router.handle("first thought status").message,
            router.handle("first thought readiness").message,
            router.handle("assemble first thought").message,
            router.handle("show first thought").message,
            router.handle("assemble first thought").message,
        ]
        joined = "\n".join(outputs).lower()

        for phrase in FORBIDDEN_FIRST_THOUGHT_PHRASES:
            self.assertNotIn(phrase, joined)

    def test_show_first_thought_returns_saved_text_from_file(self) -> None:
        runtime, router = self._runtime_and_router()
        saved = runtime.assemble_first_thought()
        path = self._first_thought_file()
        first_mtime = path.stat().st_mtime_ns

        response = router.handle("show first thought")

        self.assertIn(saved["first_thought_text"], response.message)
        self.assertEqual(path.stat().st_mtime_ns, first_mtime)

    def test_first_thought_status_works_before_assembly(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("first thought status")

        self.assertIn("First thought status:", response.message)
        self.assertIn("Assembled: false", response.message)
        self.assertFalse(runtime.first_thought_status()["generated"])

    def test_first_thought_readiness_command_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("first thought readiness")

        self.assertIn("Stage: 12 first thought from real state", response.message)
        self.assertIn("Ready: true", response.message)

    def test_assemble_command_is_rejected_if_already_assembled(self) -> None:
        runtime, router = self._runtime_and_router()
        runtime.assemble_first_thought()

        response = router.handle("assemble first thought")

        self.assertIn("assembly rejected", response.message)
        self.assertIn("already assembled", response.message)

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
        runtime, _ = self._runtime_and_router()

        self.assertTrue(hasattr(runtime, "shadow_testing"))
        self.assertFalse(hasattr(runtime, "patch_pipeline"))

    def test_no_ui_voice_network_or_external_api_behavior_added(self) -> None:
        manager = FirstThoughtAssembler(self.root / "data" / "lucy")

        for method in ["start_server", "listen", "bind", "open_socket", "start_voice", "call_external_api"]:
            self.assertFalse(hasattr(manager, method))

    def test_first_thought_does_not_create_memory_experience_records_or_evaluation_results(self) -> None:
        runtime, _ = self._runtime_and_router()
        runtime.assemble_first_thought()
        lucy_data = self.root / "data" / "lucy"

        self.assertTrue(hasattr(runtime, "experience_storage"))
        self.assertFalse((lucy_data / "experience").exists())
        self.assertFalse((lucy_data / "experience_records.json").exists())
        self.assertFalse((lucy_data / "evaluation_results.json").exists())
        self.assertFalse((lucy_data / "self_model").exists())

    def test_prior_stage_log_files_are_not_read_or_evaluated(self) -> None:
        logs_dir = self.root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "stage11_safe_access.md").write_text(
            "Fake log text: safe access is open and recovery_mode is true.",
            encoding="utf-8",
        )
        runtime, _ = self._runtime_and_router()

        result = runtime.assemble_first_thought()

        self.assertTrue(result["generated"])
        self.assertEqual(result["runtime_recovery_status"], "normal")
        self.assertEqual(result["safe_access_status"], "disabled")
        self.assertNotIn("Fake log text", result["source_state_summary"])


if __name__ == "__main__":
    unittest.main()
