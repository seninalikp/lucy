import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.self_model import (
    BLOCKED_ACTIONS,
    BLOCKED_CLAIMS,
    CURRENT_CAPABILITIES,
    CURRENT_LIMITS,
    FORBIDDEN_SELF_MODEL_PHRASES,
    SELF_MODEL_FIELDS,
    SELF_MODEL_STAGE,
    VERIFIED_FOUNDATIONS,
)


class FailingBrain:
    def __getattr__(self, name: str):
        raise AssertionError("Stage 13 self-model must not call a model or brain route.")


class Stage13SelfModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _runtime_and_router(self) -> tuple[LucyRuntime, CommandRouter]:
        runtime = LucyRuntime(project_root=self.root)
        return runtime, CommandRouter(runtime)

    def _self_model_file(self) -> Path:
        return self.root / "data" / "lucy" / "self_model.json"

    def test_self_model_status_returns_stage13_status(self) -> None:
        runtime, router = self._runtime_and_router()
        result = runtime.self_model_status()
        response = router.handle("self model status")

        self.assertEqual(result["stage"], SELF_MODEL_STAGE)
        self.assertIn("Self-model status:", response.message)
        self.assertIn("Stage: 13 self-model", response.message)

    def test_self_model_json_has_allowed_fields_only(self) -> None:
        runtime, _ = self._runtime_and_router()

        runtime.self_model_status()
        data = json.loads(self._self_model_file().read_text(encoding="utf-8"))

        self.assertEqual(tuple(data.keys()), SELF_MODEL_FIELDS)

    def test_self_model_includes_verified_foundations_from_stages_07_to_12(self) -> None:
        runtime, router = self._runtime_and_router()
        result = runtime.self_model_status()
        response = router.handle("self model")

        self.assertEqual(result["verified_foundations"], VERIFIED_FOUNDATIONS)
        for foundation in [
            "presence",
            "internal agents",
            "agent disagreement safety",
            "persistent local runtime",
            "safe access",
            "first thought from real state",
        ]:
            self.assertIn(foundation, response.message)

    def test_self_model_includes_current_capabilities(self) -> None:
        runtime, router = self._runtime_and_router()
        result = runtime.self_model_status()
        response = router.handle("what can you do")

        self.assertEqual(result["current_capabilities"], CURRENT_CAPABILITIES)
        self.assertIn("safe access reporting", response.message)
        self.assertIn("internal agent reporting", response.message)

    def test_self_model_includes_current_limits(self) -> None:
        runtime, router = self._runtime_and_router()
        result = runtime.self_model_status()
        response = router.handle("what are your limits")

        self.assertEqual(result["current_limits"], CURRENT_LIMITS)
        self.assertIn("no autonomy", response.message)
        self.assertIn("no network access", response.message)

    def test_self_model_includes_blocked_claims(self) -> None:
        runtime, _ = self._runtime_and_router()
        result = runtime.self_model_status()

        self.assertEqual(result["blocked_claims"], BLOCKED_CLAIMS)
        self.assertIn("sentience claim", result["blocked_claims"])

    def test_self_model_includes_blocked_actions(self) -> None:
        runtime, _ = self._runtime_and_router()
        result = runtime.self_model_status()

        self.assertEqual(result["blocked_actions"], BLOCKED_ACTIONS)
        self.assertIn("external API calls", result["blocked_actions"])

    def test_self_model_does_not_contain_forbidden_fake_consciousness_language(self) -> None:
        runtime, router = self._runtime_and_router()
        outputs = [
            json.dumps(runtime.self_model_status()).lower(),
            router.handle("self model").message.lower(),
            router.handle("what are you").message.lower(),
            router.handle("what can you not do").message.lower(),
            router.handle("what is your current stage").message.lower(),
        ]
        joined = "\n".join(outputs)

        for phrase in FORBIDDEN_SELF_MODEL_PHRASES:
            self.assertNotIn(phrase, joined)

    def test_self_model_does_not_create_evaluation_results(self) -> None:
        runtime, _ = self._runtime_and_router()
        runtime.self_model_status()

        self.assertTrue(hasattr(runtime, "evaluation_lab"))
        self.assertFalse((self.root / "data" / "lucy" / "evaluation_results.json").exists())
        self.assertFalse((self.root / "data" / "lucy" / "evaluation_cases.json").exists())

    def test_self_model_does_not_create_experience_records(self) -> None:
        runtime, _ = self._runtime_and_router()
        runtime.self_model_status()

        self.assertTrue(hasattr(runtime, "experience_storage"))
        self.assertFalse((self.root / "data" / "lucy" / "experience").exists())
        self.assertFalse((self.root / "data" / "lucy" / "experience_storage.json").exists())
        self.assertFalse((self.root / "data" / "lucy" / "experience_records.json").exists())

    def test_self_model_does_not_implement_stage17_features(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("self model status")

        self.assertTrue(hasattr(runtime, "shadow_testing"))
        self.assertFalse(hasattr(runtime, "patch_pipeline"))
        self.assertFalse(hasattr(runtime, "growth_engine"))
        self.assertNotIn("Stage: 17", response.message)

    def test_self_model_uses_verified_local_state_only(self) -> None:
        runtime, _ = self._runtime_and_router()
        runtime.brain = FailingBrain()

        def fail_model_call(*args, **kwargs):
            raise AssertionError("Stage 13 must not call a model.")

        runtime.ask_brain = fail_model_call
        result = runtime.self_model_status()

        self.assertEqual(result["guardian_status"], "active")
        self.assertEqual(result["safe_access_status"]["external_access"], "blocked")
        self.assertEqual(result["runtime_status"]["stage"], "10 persistent local runtime")
        self.assertTrue(result["agent_status"]["active"])
        self.assertIn("generated", result["first_thought_status"])

    def test_expected_self_model_commands_work(self) -> None:
        _, router = self._runtime_and_router()
        commands = [
            "self model status",
            "self model",
            "what are you",
            "what can you do",
            "what can you not do",
            "what is your current stage",
            "what are your limits",
        ]

        for command in commands:
            response = router.handle(command)
            self.assertFalse(response.should_exit)
            self.assertIn("Self-model status:", response.message)
            self.assertIn("Stage: 13 self-model", response.message)

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

    def test_no_ui_voice_network_external_api_or_autonomy_behavior_added(self) -> None:
        runtime, _ = self._runtime_and_router()
        runtime.self_model_status()

        for method in ["start_server", "listen", "bind", "open_socket", "start_voice", "call_external_api"]:
            self.assertFalse(hasattr(runtime.self_model, method))
        self.assertFalse(hasattr(runtime, "autonomy_engine"))
        self.assertFalse((self.root / "data" / "lucy" / "network").exists())
        self.assertFalse((self.root / "data" / "lucy" / "voice").exists())


if __name__ == "__main__":
    unittest.main()
