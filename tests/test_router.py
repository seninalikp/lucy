import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class RouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runtime = LucyRuntime(project_root=Path(self.temp_dir.name))
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_empty_input_does_not_crash(self) -> None:
        response = self.router.handle("")
        self.assertFalse(response.should_exit)
        self.assertIn("here", response.message.lower())

    def test_unknown_input_is_grounded(self) -> None:
        response = self.router.handle("can you fly my laptop")
        self.assertFalse(response.should_exit)
        self.assertIn("don't have enough context", response.message.lower())

    def test_basic_hi_fallback_does_not_crash(self) -> None:
        response = self.router.handle("hi")
        self.assertFalse(response.should_exit)
        self.assertIsInstance(response.message, str)
        self.assertEqual(response.message, "Hey. I'm here. Active project: Lucy.")

    def test_basic_hey_fallback_does_not_crash(self) -> None:
        response = self.router.handle("hey")
        self.assertFalse(response.should_exit)
        self.assertIsInstance(response.message, str)
        self.assertEqual(response.message, "Hey. I'm here. Active project: Lucy.")

    def test_greeting_typo_fallback_does_not_crash(self) -> None:
        response = self.router.handle("hyy")
        self.assertFalse(response.should_exit)
        self.assertEqual(response.message, "Hey. I'm here. Active project: Lucy.")

    def test_tell_me_returns_current_status(self) -> None:
        response = self.router.handle("tell me")
        self.assertFalse(response.should_exit)
        self.assertIn("Lucy status:", response.message)
        self.assertIn("Active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Next safe action:", response.message)

    def test_what_next_returns_stage33_gate(self) -> None:
        response = self.router.handle("what next")
        self.assertFalse(response.should_exit)
        self.assertIn("Next safe action:", response.message)
        self.assertIn("Stage 35:", response.message)
        self.assertIn("First manual model call stage blocked", response.message)

    def test_work_in_progress_acknowledgement(self) -> None:
        response = self.router.handle("ok we are work in progress okeee")
        self.assertFalse(response.should_exit)
        self.assertIn("Lucy is work in progress", response.message)
        self.assertIn("Current safe move", response.message)

    def test_short_vague_fallback_tracks_context(self) -> None:
        response = self.router.handle("later maybe")
        self.assertFalse(response.should_exit)
        self.assertIn("tracking this as context", response.message)

    def test_question_fallback_returns_contextual_help(self) -> None:
        response = self.router.handle("did we finish?")
        self.assertFalse(response.should_exit)
        self.assertIn("Lucy's status", response.message)
        self.assertIn("current stage", response.message)

    def test_bootstrap_reply_avoids_forbidden_phrases(self) -> None:
        forbidden = [
            "I feel",
            "I want",
            "I am alive",
            "I am conscious",
            "I experience",
            "I missed you",
        ]
        samples = [
            "hi",
            "hey",
            "hello",
            "hyy",
            "how are you",
            "what can you do",
            "what now?",
            "tell me",
            "ok we are work in progress okeee",
            "later maybe",
        ]
        for text in samples:
            reply = self.router.handle(text).message
            for phrase in forbidden:
                self.assertNotIn(phrase, reply)

    def test_conversation_log_written_after_fallback_response(self) -> None:
        response = self.router.handle("hi")
        log_file = Path(self.temp_dir.name) / "data" / "lucy" / "conversation_log.jsonl"

        self.assertTrue(log_file.exists())
        entries = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(entries[-1]["input"], "hi")
        self.assertEqual(entries[-1]["reply"], response.message)
        self.assertEqual(entries[-1]["quality"], "low")
        self.assertEqual(entries[-1]["source"], "fallback_v2")

    def test_sensitive_fallback_input_is_redacted_in_conversation_log(self) -> None:
        self.router.handle("my api key is 123")
        log_file = Path(self.temp_dir.name) / "data" / "lucy" / "conversation_log.jsonl"

        entries = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(entries[-1]["input"], "[redacted sensitive input]")
        self.assertEqual(entries[-1]["source"], "fallback_v2")

    def test_load_conversation_history_returns_list(self) -> None:
        self.router.handle("hey")
        history = self.runtime.load_conversation_history()

        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 1)

    def test_remember_command(self) -> None:
        response = self.router.handle("remember Lucy has a project tracker")
        self.assertIn("Remembered", response.message)

    def test_permanent_memory_command(self) -> None:
        response = self.router.handle("permanent memory")
        self.assertIn("Permanent memory", response.message)

    def test_daily_brief_command(self) -> None:
        response = self.router.handle("daily brief")
        self.assertIn("Daily brief", response.message)

    def test_daily_context_commands(self) -> None:
        checkin = self.router.handle('daily checkin energy=6 sleep=ok notes="foundation day"')
        self.assertIn("Daily check-in saved", checkin.message)

        today = self.router.handle("today log")
        self.assertIn("Today log", today.message)
        self.assertIn("foundation day", today.message)

        weekly = self.router.handle("weekly review")
        self.assertIn("Weekly review", weekly.message)

    def test_command_aliases_from_checkpoint_plan(self) -> None:
        self.router.handle("remember Lucy should use typed local memory")
        memory = self.router.handle("search memory typed")
        self.assertIn("Memory recall", memory.message)

        logs = self.router.handle("show logs")
        self.assertIn("Recent runtime logs", logs.message)

    def test_continuity_backup_commands(self) -> None:
        status = self.router.handle("continuity status")
        self.assertIn("Lucy continuity memory", status.message)

        backup = self.router.handle("backup memory")
        self.assertIn("Continuity backup created", backup.message)

    def test_workspace_command(self) -> None:
        response = self.router.handle("workspace")
        self.assertIn("Workspace", response.message)

    def test_reminder_command(self) -> None:
        response = self.router.handle("add reminder Install Python")
        self.assertIn("Added reminder", response.message)

    def test_approvals_command(self) -> None:
        self.router.handle("check run automation")
        response = self.router.handle("approvals")
        self.assertIn("Approval records", response.message)

    def test_recovered_command(self) -> None:
        response = self.router.handle("recovered")
        self.assertIn("Recovered Lucy architecture", response.message)

    def test_brain_status_command(self) -> None:
        response = self.router.handle("brain status")
        self.assertIn("Lucy brain router", response.message)

    def test_learning_status_command(self) -> None:
        response = self.router.handle("learning status")
        self.assertIn("Lucy learning loop", response.message)

    def test_style_commands(self) -> None:
        response = self.router.handle("learn style be concise and casual")
        self.assertIn("Talking style saved", response.message)
        status = self.router.handle("style status")
        self.assertIn("Adaptive communication status:", status.message)

    def test_memory_fallback_without_key(self) -> None:
        response = self.router.handle("memory fallback something unknown")
        self.assertIn("setup nvidia key", response.message.lower())

    def test_overnight_checkpoints_command(self) -> None:
        response = self.router.handle("overnight checkpoints 3")
        self.assertIn("Overnight checkpoint run", response.message)
        self.assertIn("Final total: 3", response.message)

    def test_exit_command(self) -> None:
        response = self.router.handle("exit")
        self.assertTrue(response.should_exit)


if __name__ == "__main__":
    unittest.main()
