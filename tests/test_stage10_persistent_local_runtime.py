import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.persistent_runtime import PersistentLocalRuntime, RUNTIME_STAGE
from backend.lucy_core.router import CommandRouter


class Stage10PersistentLocalRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_runtime_state_file_is_created_if_missing(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        state_file = self.root / "data" / "lucy" / "runtime_state.json"

        self.assertTrue(state_file.exists())
        self.assertEqual(runtime.runtime_status()["file"], str(state_file))

    def test_startup_marks_clean_shutdown_false_while_running(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        status = runtime.runtime_status()

        self.assertEqual(status["stage"], RUNTIME_STAGE)
        self.assertFalse(status["clean_shutdown"])
        self.assertEqual(status["last_command"], "startup")

    def test_normal_shutdown_marks_clean_shutdown_true(self) -> None:
        runtime = LucyRuntime(project_root=self.root)

        runtime.graceful_shutdown("test shutdown")
        status = runtime.runtime_status()

        self.assertTrue(status["clean_shutdown"])
        self.assertFalse(status["recovery_mode"])
        self.assertIsNotNone(status["shutdown_at"])

    def test_unclean_previous_shutdown_is_detected(self) -> None:
        LucyRuntime(project_root=self.root)
        restarted = LucyRuntime(project_root=self.root)
        status = restarted.runtime_status()

        self.assertFalse(status["previous_shutdown_clean"])

    def test_recovery_mode_true_after_simulated_unclean_shutdown(self) -> None:
        LucyRuntime(project_root=self.root)
        restarted = LucyRuntime(project_root=self.root)
        status = restarted.runtime_status()

        self.assertTrue(status["recovery_mode"])
        self.assertFalse(status["previous_shutdown_clean"])

    def test_runtime_heartbeat_updates_timestamp_and_last_command(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        first = runtime.runtime_status()["last_heartbeat"]
        time.sleep(0.001)

        runtime.record_interaction("heartbeat test command", "ok")
        status = runtime.runtime_status()

        self.assertNotEqual(status["last_heartbeat"], first)
        self.assertEqual(status["last_command"], "heartbeat test command")
        self.assertFalse(status["clean_shutdown"])

    def test_runtime_status_command_returns_stage10_status(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        response = CommandRouter(runtime).handle("runtime status")

        self.assertFalse(response.should_exit)
        self.assertIn("Runtime status:", response.message)
        self.assertIn("Stage: 10 persistent local runtime", response.message)
        self.assertIn("Recovery mode:", response.message)

    def test_existing_stage08_agent_commands_still_work(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        router = CommandRouter(runtime)

        for command in ["agent status", "agent cycle test"]:
            response = router.handle(command)
            self.assertFalse(response.should_exit)
            self.assertTrue(response.message.strip())

    def test_existing_stage09_disagreement_safety_still_works(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        response = CommandRouter(runtime).handle("agent report")

        self.assertIn("Combined result:", response.message)
        self.assertIn("Stage: 09 agent disagreement safety", response.message)

    def test_existing_conversation_fallback_behavior_still_works(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        router = CommandRouter(runtime)

        self.assertEqual(router.handle("hi").message, "Hey. I'm here. Active project: Lucy.")
        self.assertIn("Lucy status:", router.handle("tell me").message)
        self.assertIn("Next safe action:", router.handle("what next").message)

    def test_stage17_features_are_absent(self) -> None:
        runtime = LucyRuntime(project_root=self.root)

        self.assertTrue(hasattr(runtime, "shadow_testing"))
        self.assertFalse(hasattr(runtime, "patch_pipeline"))
        self.assertFalse(hasattr(runtime, "phone_access"))
        self.assertFalse(hasattr(runtime, "browser_access"))

    def test_no_network_server_daemon_ui_voice_or_external_api_behavior_added(self) -> None:
        runtime = LucyRuntime(project_root=self.root)
        status = runtime.runtime_status()
        forbidden = {"network", "server", "daemon", "ui", "voice", "external_api", "socket", "service"}

        self.assertTrue(forbidden.isdisjoint(status.keys()))

    def test_persistent_runtime_does_not_create_experience_records(self) -> None:
        runtime = LucyRuntime(project_root=self.root)

        self.assertTrue(hasattr(runtime, "experience_storage"))
        self.assertFalse((self.root / "data" / "lucy" / "experience").exists())
        self.assertFalse((self.root / "data" / "lucy" / "experience_records.json").exists())

    def test_direct_persistent_runtime_does_not_create_extra_storage_systems(self) -> None:
        data_dir = self.root / "data" / "lucy"
        persistent = PersistentLocalRuntime(data_dir)
        persistent.start()

        self.assertTrue((data_dir / "runtime_state.json").exists())
        self.assertFalse((data_dir / "runtime.db").exists())


if __name__ == "__main__":
    unittest.main()
