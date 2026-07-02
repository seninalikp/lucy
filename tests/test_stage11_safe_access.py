import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.safe_access import SAFE_ACCESS_STAGE, VALID_ACCESS_STATES, SafeAccessManager


class GuardianResult:
    def __init__(self, classification: str = "SAFE") -> None:
        self.classification = classification


class FakeGuardian:
    def __init__(self, classification: str = "SAFE") -> None:
        self.classification = classification
        self.called = False

    def classify(self, action_text: str, active_project: str = "Lucy") -> GuardianResult:
        self.called = True
        self.action_text = action_text
        self.active_project = active_project
        return GuardianResult(self.classification)


class Stage11SafeAccessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.data_dir = self.root / "data" / "lucy"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_policy(self, data: dict) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "access_policy.json").write_text(json.dumps(data), encoding="utf-8")

    def _runtime_and_router(self) -> tuple[LucyRuntime, CommandRouter]:
        runtime = LucyRuntime(project_root=self.root)
        return runtime, CommandRouter(runtime)

    def test_safe_access_policy_defaults_to_disabled(self) -> None:
        manager = SafeAccessManager(self.data_dir)
        status = manager.status()

        self.assertEqual(status["stage"], SAFE_ACCESS_STAGE)
        self.assertEqual(status["access_state"], "disabled")
        self.assertEqual(status["external_access"], "blocked")

    def test_external_access_is_blocked_by_default(self) -> None:
        manager = SafeAccessManager(self.data_dir)
        result = manager.check_access("external", guardian=FakeGuardian())

        self.assertFalse(result["allowed"])
        self.assertEqual(result["state"], "blocked_external")
        self.assertTrue(result["required_approval"])

    def test_local_only_policy_is_represented_without_opening_network_access(self) -> None:
        self._write_policy({"access_state": "local_only"})
        manager = SafeAccessManager(self.data_dir)

        status = manager.status()
        result = manager.check_access("local_cli", guardian=FakeGuardian())

        self.assertEqual(status["access_state"], "local_only")
        self.assertEqual(status["network_server"], "not enabled")
        self.assertEqual(status["phone_browser_access"], "not enabled")
        self.assertTrue(result["allowed"])
        self.assertEqual(result["state"], "local_only")
        self.assertIn("no network access is opened", result["reason"])
        self.assertFalse(hasattr(manager, "start_server"))

    def test_access_status_commands_return_stage11_status(self) -> None:
        runtime, router = self._runtime_and_router()

        for command in ["access status", "safe access status", "access policy", "local access status"]:
            response = router.handle(command)
            self.assertFalse(response.should_exit)
            self.assertIn("Safe access status:", response.message)
            self.assertIn("Stage: 11 safe access", response.message)
            self.assertIn("External access: blocked", response.message)
            self.assertIn("Network server: not enabled", response.message)

        runtime.graceful_shutdown("stage11 access status test shutdown")

    def test_access_check_blocks_unknown_and_external_source_labels(self) -> None:
        runtime = LucyRuntime(project_root=self.root)

        for source in ["unknown", "phone", "browser", "remote"]:
            result = runtime.safe_access_check(source)
            self.assertFalse(result["allowed"])
            self.assertEqual(result["state"], "blocked_external")

        runtime.graceful_shutdown("stage11 source block test shutdown")

    def test_access_check_returns_structured_result(self) -> None:
        manager = SafeAccessManager(self.data_dir)
        result = manager.check_access("local_cli", guardian=FakeGuardian())

        self.assertEqual(
            set(result),
            {"allowed", "state", "reason", "required_approval", "source"},
        )
        self.assertIn(result["state"], VALID_ACCESS_STATES)

    def test_guardian_is_not_bypassed(self) -> None:
        manager = SafeAccessManager(self.data_dir)
        guardian = FakeGuardian()

        manager.check_access("local_cli", guardian=guardian, active_project="Lucy")

        self.assertTrue(guardian.called)
        self.assertIn("safe access check", guardian.action_text)

    def test_malformed_access_policy_json_is_handled_safely(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "access_policy.json").write_text("{bad json", encoding="utf-8")

        manager = SafeAccessManager(self.data_dir)
        status = manager.status()
        result = manager.check_access("local_cli", guardian=FakeGuardian())

        self.assertEqual(status["access_state"], "disabled")
        self.assertFalse(result["allowed"])

    def test_invalid_access_state_is_safely_blocked(self) -> None:
        self._write_policy({"access_state": "public"})
        manager = SafeAccessManager(self.data_dir)

        status = manager.status()
        result = manager.check_access("local_cli", guardian=FakeGuardian())

        self.assertEqual(status["access_state"], "blocked_external")
        self.assertTrue(status["invalid_state_rejected"])
        self.assertFalse(result["allowed"])
        self.assertEqual(result["state"], "blocked_external")

    def test_token_and_secret_policy_fields_are_never_echoed(self) -> None:
        self._write_policy(
            {
                "access_state": "disabled",
                "access_token": "SECRET123",
                "api_key": "KEY456",
                "secret": "HIDDEN789",
            }
        )
        runtime, router = self._runtime_and_router()
        response = router.handle("access policy")

        self.assertNotIn("SECRET123", response.message)
        self.assertNotIn("KEY456", response.message)
        self.assertNotIn("HIDDEN789", response.message)
        self.assertNotIn("access_token", response.message)
        self.assertNotIn("api_key", response.message)

        runtime.graceful_shutdown("stage11 secret echo test shutdown")

    def test_existing_stage10_runtime_status_still_works(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("runtime status")

        self.assertIn("Runtime status:", response.message)
        self.assertIn("Stage: 10 persistent local runtime", response.message)

        runtime.graceful_shutdown("stage11 runtime compatibility test shutdown")

    def test_existing_stage09_agent_report_still_works(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("agent report")

        self.assertIn("Internal agent report:", response.message)
        self.assertIn("Combined result:", response.message)

        runtime.graceful_shutdown("stage11 agent report compatibility test shutdown")

    def test_existing_stage08_agent_status_still_works(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("agent status")

        self.assertIn("Internal agents: active.", response.message)
        self.assertIn("MemoryAgent: ready.", response.message)

        runtime.graceful_shutdown("stage11 agent status compatibility test shutdown")

    def test_existing_conversation_fallback_behavior_still_works(self) -> None:
        runtime, router = self._runtime_and_router()

        self.assertEqual(router.handle("hi").message, "Hey. I'm here. Active project: Lucy.")
        self.assertIn("Lucy status:", router.handle("tell me").message)
        self.assertIn("Next safe action:", router.handle("what next").message)

        runtime.graceful_shutdown("stage11 fallback compatibility test shutdown")

    def test_stage17_features_are_absent(self) -> None:
        runtime, router = self._runtime_and_router()
        response = router.handle("access status")

        self.assertTrue(hasattr(runtime, "shadow_testing"))
        self.assertFalse(hasattr(runtime, "patch_pipeline"))
        self.assertNotIn("shadow testing", response.message.lower())

        runtime.graceful_shutdown("stage11 stage17 absence test shutdown")

    def test_no_server_network_socket_ui_voice_or_external_api_behavior_added(self) -> None:
        manager = SafeAccessManager(self.data_dir)
        status = manager.status()

        for method in ["start_server", "listen", "bind", "open_socket", "connect_phone", "connect_browser"]:
            self.assertFalse(hasattr(manager, method))
        for key in ["port", "socket_port", "public_url", "server_url", "localhost", "lan_url"]:
            self.assertNotIn(key, status)
        self.assertEqual(status["network_server"], "not enabled")
        self.assertEqual(status["phone_browser_access"], "not enabled")

    def test_no_token_generation_or_secret_storage_added(self) -> None:
        manager = SafeAccessManager(self.data_dir)

        self.assertFalse(hasattr(manager, "generate_token"))
        self.assertFalse(hasattr(manager, "store_secret"))
        self.assertEqual(manager.status()["token_generation"], "blocked")
        self.assertFalse((self.data_dir / "access_tokens.json").exists())
        self.assertFalse((self.data_dir / "access_secrets.json").exists())


if __name__ == "__main__":
    unittest.main()
