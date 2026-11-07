"""
test_stage53_scheduler.py
Stage 53 = Autonomous Cron & Temporal Event Daemon.

Verifies:
1. Cron daemon reports Stage 53 and status with complete schema.
2. Schedule parser accurately handles intervals, daily times, and rejects invalid formats.
3. CronJob lifecycle management (create, pause, resume, delete, and JSON roundtrip).
4. Persistent file-backed storage across restarts (schedules.json).
5. Accurate detection of due and overdue jobs.
6. Catch-up policy execution for jobs missed while offline.
7. Job execution dispatch to runtime and execution logging.
8. Safe background daemon thread lifecycle and clean shutdown.
9. Full integration with CommandRouter and LucyRuntime.
"""

from __future__ import annotations

import datetime
import json
import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.cron_scheduler import (
    CronDaemon,
    CronJob,
    ScheduleParser,
    STAGE,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class MockRuntime:
    """Mock runtime for testing cron job dispatch."""
    def __init__(self) -> None:
        self.dispatched_commands = []

    def respond(self, message: str) -> str:
        self.dispatched_commands.append(message)
        return f"Echo from CronMock: {message}"

    def execute_goal(self, intent: str) -> dict:
        self.dispatched_commands.append(f"goal:{intent}")
        return {"ok": True, "tree": f"Goal Tree for {intent}"}


class Stage53CronSchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.project_root = self.tmp_path / "project"
        self.lucy_data = self.project_root / "data" / "lucy"

        self.project_root.mkdir(parents=True, exist_ok=True)
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_stage_identity_and_status(self) -> None:
        """1. Cron daemon reports Stage 53 and status with complete schema."""
        daemon = CronDaemon(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
        )
        status = daemon.status()
        self.assertEqual(status["stage"], "53 autonomous cron & temporal event daemon")
        self.assertIn("daemon_running", status)
        self.assertIn("total_jobs", status)
        self.assertIn("active_jobs", status)
        self.assertIn("paused_jobs", status)
        self.assertIn("total_executions", status)

    def test_schedule_expression_parsing(self) -> None:
        """2. Schedule parser accurately handles intervals, daily times, and rejects invalid formats."""
        now = datetime.datetime(2026, 10, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)

        # Seconds interval
        t_sec, m_sec = ScheduleParser.calculate_next_run("every 30s", from_time=now)
        self.assertEqual(t_sec, now + datetime.timedelta(seconds=30))
        self.assertEqual(m_sec["type"], "interval")

        # Minutes interval
        t_min, m_min = ScheduleParser.calculate_next_run("every 15m", from_time=now)
        self.assertEqual(t_min, now + datetime.timedelta(minutes=15))

        # Hours interval
        t_hr, _ = ScheduleParser.calculate_next_run("every 2h", from_time=now)
        self.assertEqual(t_hr, now + datetime.timedelta(hours=2))

        # Daily schedule
        t_daily, m_daily = ScheduleParser.calculate_next_run("daily 14:30", from_time=now)
        self.assertEqual(t_daily.hour, 14)
        self.assertEqual(t_daily.minute, 30)
        self.assertEqual(t_daily.day, 28)

        # Daily scheduled for earlier in the day rolls to tomorrow
        t_daily_past, _ = ScheduleParser.calculate_next_run("daily 08:00", from_time=now)
        self.assertEqual(t_daily_past.day, 29)

        # Invalid expressions raise ValueError
        with self.assertRaises(ValueError):
            ScheduleParser.calculate_next_run("every Tuesday")

    def test_cron_job_lifecycle_and_serialization(self) -> None:
        """3. CronJob lifecycle management (create, pause, resume, delete, and JSON roundtrip)."""
        daemon = CronDaemon(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
        )
        job = daemon.add_job(
            name="Test Job",
            expression="every 10m",
            target="system telemetry",
            job_id="test_job_1",
        )
        self.assertEqual(job.job_id, "test_job_1")
        self.assertTrue(job.enabled)

        # Pause
        self.assertTrue(daemon.pause_job("test_job_1"))
        self.assertFalse(daemon._jobs["test_job_1"].enabled)

        # Resume
        self.assertTrue(daemon.resume_job("test_job_1"))
        self.assertTrue(daemon._jobs["test_job_1"].enabled)

        # JSON Roundtrip
        data = job.to_dict()
        job_copy = CronJob.from_dict(data)
        self.assertEqual(job_copy.job_id, job.job_id)
        self.assertEqual(job_copy.expression, job.expression)

        # Delete
        self.assertTrue(daemon.delete_job("test_job_1"))
        self.assertNotIn("test_job_1", daemon._jobs)

    def test_persistent_storage_and_reload(self) -> None:
        """4. Persistent file-backed storage across restarts (schedules.json)."""
        daemon1 = CronDaemon(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
        )
        daemon1.add_job(
            name="Persistent Task",
            expression="every 1h",
            target="sentinel scan",
            job_id="persist_1",
        )

        # Reopen in new daemon instance
        daemon2 = CronDaemon(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
        )
        jobs = daemon2.list_jobs()
        job_ids = [j["job_id"] for j in jobs]
        self.assertIn("persist_1", job_ids)

    def test_due_job_detection(self) -> None:
        """5. Accurate detection of due and overdue jobs."""
        now = datetime.datetime.now(datetime.timezone.utc)
        job = CronJob(name="Due Job", expression="every 1m", target="echo 1")

        # In the future: not due
        future = now - datetime.timedelta(seconds=10)
        self.assertFalse(job.is_due(current_time=future))

        # Far in future: is due
        far_future = now + datetime.timedelta(minutes=5)
        self.assertTrue(job.is_due(current_time=far_future))

        # Disabled job: never due
        job.enabled = False
        self.assertFalse(job.is_due(current_time=far_future))

    def test_catch_up_policy_for_offline_intervals(self) -> None:
        """6. Catch-up policy execution for jobs missed while offline."""
        mock_rt = MockRuntime()
        daemon = CronDaemon(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
            runtime=mock_rt,
        )
        job = daemon.add_job(
            name="Missed Task",
            expression="every 1h",
            target="sentinel scan",
            job_id="missed_1",
            catch_up=True,
        )
        # Simulate that job was due 2 hours ago
        past_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
        job.next_run = past_time.isoformat()
        daemon._save()

        # Audit should execute due job immediately
        executed = daemon.execute_due_jobs_now()
        executed_ids = [e["job_id"] for e in executed]
        self.assertIn("missed_1", executed_ids)
        self.assertIn("sentinel scan", mock_rt.dispatched_commands)

    def test_job_execution_dispatch(self) -> None:
        """7. Job execution dispatch to runtime and execution logging."""
        mock_rt = MockRuntime()
        daemon = CronDaemon(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
            runtime=mock_rt,
        )
        job = daemon.add_job(
            name="Goal Job",
            expression="every 30m",
            target="/goal night audit",
            job_id="goal_job_1",
        )
        # Force due
        job.next_run = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)).isoformat()

        executed = daemon.execute_due_jobs_now()
        self.assertEqual(len(executed), 1)
        self.assertIn("goal:night audit", mock_rt.dispatched_commands)

        # Execution log verification
        log_file = self.lucy_data / "schedule_execution.jsonl"
        self.assertTrue(log_file.exists())
        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        self.assertGreater(len(lines), 0)
        last_entry = json.loads(lines[-1])
        self.assertEqual(last_entry["job_id"], "goal_job_1")

    def test_background_daemon_thread_lifecycle(self) -> None:
        """8. Safe background daemon thread lifecycle and clean shutdown."""
        daemon = CronDaemon(
            project_root=self.project_root,
            lucy_data=self.lucy_data,
        )
        self.assertFalse(daemon.status()["daemon_running"])

        # Start
        daemon.start_background_daemon(check_interval_seconds=0.1)
        self.assertTrue(daemon.status()["daemon_running"])

        time.sleep(0.2)

        # Stop
        daemon.stop_background_daemon()
        self.assertFalse(daemon.status()["daemon_running"])

    def test_lucy_runtime_and_router_integration(self) -> None:
        """9. Full integration with CommandRouter and LucyRuntime."""
        runtime = LucyRuntime(project_root=Path(r"C:\Users\admin\Desktop\senin\LUCY\lucy"))
        router = CommandRouter(runtime)

        # Status via router
        resp_stat = router.handle("/cron status")
        self.assertIn("Autonomous Cron & Temporal Daemon Status:", resp_stat.message)
        self.assertIn("53 autonomous cron & temporal event daemon", resp_stat.message)

        # List schedules via router
        resp_list = router.handle("/schedules")
        self.assertIn("Registered Cron Schedules", resp_list.message)

        # Create schedule via router
        resp_add = router.handle("/schedule every 2h do system telemetry")
        self.assertIn("Scheduled job created:", resp_add.message)
        self.assertIn("system telemetry", resp_add.message)

        # Direct runtime methods
        status_dict = runtime.cron_status()
        self.assertEqual(status_dict["stage"], STAGE)


if __name__ == "__main__":
    unittest.main()
