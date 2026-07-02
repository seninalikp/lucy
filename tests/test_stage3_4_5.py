import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.guardian import BLOCKED, SAFE, GuardianCore
from backend.lucy_core.reflection import ReflectionLog
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.scheduler import ContextScheduler, ScheduledTask
from backend.lucy_core.session_state import SessionStateManager
from backend.lucy_core.safe_storage import backup_file, safe_read_json, safe_write_json
from backend.lucy_core.lucy_runtime import LucyRuntime


class Stage345Tests(unittest.TestCase):
    def test_safe_write_json_writes_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            safe_write_json(path, {"ok": True})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"ok": True})

    def test_safe_read_json_returns_default_for_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "missing.json"
            self.assertEqual(safe_read_json(path, {"default": True}), {"default": True})

    def test_backup_fallback_works_on_corrupted_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            path.write_text('{"healthy": true}', encoding="utf-8")
            backup_file(path)
            path.write_text("{broken", encoding="utf-8")
            self.assertEqual(safe_read_json(path, {}), {"healthy": True})

    def test_session_state_creates_default_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manager = SessionStateManager(Path(temp))
            self.assertTrue(manager.state_file.exists())
            self.assertEqual(manager.status()["session_count"], 0)

    def test_boot_sequence_increments_session_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manager = SessionStateManager(Path(temp))
            manager.boot_sequence()
            manager.graceful_shutdown()
            manager.boot_sequence()
            self.assertEqual(manager.status()["session_count"], 2)

    def test_crash_recovery_needed_after_unclean_shutdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manager = SessionStateManager(Path(temp))
            manager.boot_sequence()
            manager.boot_sequence()
            self.assertTrue(manager.is_crash_recovery())

    def test_graceful_shutdown_sets_true(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manager = SessionStateManager(Path(temp))
            manager.boot_sequence()
            state = manager.graceful_shutdown()
            self.assertTrue(state["graceful_shutdown"])

    def test_guardian_blocks_rm_rf(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            guardian = GuardianCore(Path(temp))
            result = guardian.classify("rm -rf data/lucy")
            self.assertEqual(result.classification, BLOCKED)

    def test_guardian_blocks_identity_memory_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            guardian = GuardianCore(Path(temp))
            identity = guardian.classify("delete identity and delete memory")
            self.assertEqual(identity.classification, BLOCKED)

    def test_guardian_allows_safe_status_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            guardian = GuardianCore(Path(temp))
            result = guardian.classify("show Lucy project status")
            self.assertEqual(result.classification, SAFE)

    def test_scheduler_downranks_complex_task_when_energy_is_low(self) -> None:
        scheduler = ContextScheduler()
        tasks = [
            ScheduledTask("easy", "Review notes", priority=3, complexity=1),
            ScheduledTask("hard", "Refactor core runtime", priority=3, complexity=7),
        ]
        ranked = scheduler.rank(tasks, context={"energy": 3, "active_project": "Lucy"})
        self.assertEqual(ranked[0]["task_id"], "easy")

    def test_scheduler_returns_next_recommended_task(self) -> None:
        scheduler = ContextScheduler()
        tasks = [
            ScheduledTask("one", "Low priority", priority=1, complexity=1),
            ScheduledTask("two", "High priority", priority=5, complexity=2),
        ]
        recommended = scheduler.next_recommended(tasks, context={"energy": 6})
        self.assertEqual(recommended["task_id"], "two")
        self.assertTrue(recommended["recommended"])

    def test_reflection_log_writer_creates_jsonl_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log = ReflectionLog(Path(temp))
            entry = log.write(
                session={"session_count": 1},
                session_summary="Test reflection",
                next_time_start_here="Run tests",
            )
            self.assertTrue(Path(entry["file"]).exists())
            self.assertEqual(log.latest(1)[0]["session_summary"], "Test reflection")

    def test_router_unknown_command_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = LucyRuntime(project_root=Path(temp))
            router = CommandRouter(runtime)
            response = router.handle("this command is not real")
            self.assertFalse(response.should_exit)
            self.assertTrue(response.message)


if __name__ == "__main__":
    unittest.main()
