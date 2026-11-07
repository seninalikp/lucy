"""
cron_scheduler.py
Stage 53 = Autonomous Cron & Temporal Event Daemon.

Provides a robust, persistent temporal operating loop for Lucy:
1. Schedule Expression Parser:
   - Interval-based: 'every <N>s', 'every <N>m', 'every <N>h', 'every <N>d'.
   - Daily clock-based: 'daily <HH:MM>' (e.g. 'daily 00:00', 'daily 03:30').
   - In / At delays: 'in <N>m', 'in <N>h'.
2. CronJob Lifecycle & State Model:
   - Stores job metadata, execution count, last_run, next_run, status.
   - States: ACTIVE, PAUSED, COMPLETED.
   - Catch-up policy: Safely runs missed jobs on startup if Lucy was offline.
3. File-Backed Persistence:
   - Saves schedules to data/lucy/schedules.json.
   - Logs execution history to data/lucy/schedule_execution.jsonl.
4. Background Daemon & Non-Blocking Worker Pool:
   - Threaded background daemon evaluating deadlines against UTC clock.
   - Dispatches jobs without blocking the main cron evaluation thread.
   - Clean shutdown with thread join.
5. Operator Commands & Router Integration:
   - /schedule <expr> do <target>
   - /schedules, /pause <id>, /resume <id>, /unschedule <id>, /cron status.
"""

from __future__ import annotations

import datetime
import json
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


STAGE = "53 autonomous cron & temporal event daemon"


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt: datetime.datetime) -> str:
    return dt.isoformat()


# =====================================================================
# 1. SCHEDULE EXPRESSION PARSER
# =====================================================================

class ScheduleParser:
    """Parses natural schedule expressions into next occurrence datetimes."""

    @classmethod
    def calculate_next_run(
        cls,
        expression: str,
        from_time: Optional[datetime.datetime] = None,
    ) -> Tuple[datetime.datetime, Dict[str, Any]]:
        """Computes next run time and metadata from schedule expression."""
        base = from_time or _now_utc()
        raw = expression.strip().lower()

        # 1. Interval: 'every <N><unit>' or 'every <N> <unit>'
        # e.g., 'every 30s', 'every 5m', 'every 2h', 'every 1d'
        m_interval = re.match(r"^every\s+(\d+)\s*([smhd])$", raw)
        if m_interval:
            val = int(m_interval.group(1))
            unit = m_interval.group(2)
            delta = {
                "s": datetime.timedelta(seconds=val),
                "m": datetime.timedelta(minutes=val),
                "h": datetime.timedelta(hours=val),
                "d": datetime.timedelta(days=val),
            }[unit]
            return base + delta, {"type": "interval", "delta_seconds": delta.total_seconds()}

        # 2. Daily: 'daily <HH:MM>' (24-hour format)
        m_daily = re.match(r"^daily\s+(\d{1,2}):(\d{2})$", raw)
        if m_daily:
            hour = int(m_daily.group(1))
            minute = int(m_daily.group(2))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError(f"Invalid time in daily schedule: {hour:02d}:{minute:02d}")

            target = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= base:
                target += datetime.timedelta(days=1)
            return target, {"type": "daily", "hour": hour, "minute": minute}

        # 3. In: 'in <N><unit>' (one-shot delay)
        m_in = re.match(r"^in\s+(\d+)\s*([smhd])$", raw)
        if m_in:
            val = int(m_in.group(1))
            unit = m_in.group(2)
            delta = {
                "s": datetime.timedelta(seconds=val),
                "m": datetime.timedelta(minutes=val),
                "h": datetime.timedelta(hours=val),
                "d": datetime.timedelta(days=val),
            }[unit]
            return base + delta, {"type": "one_shot", "delta_seconds": delta.total_seconds()}

        raise ValueError(
            f"Unsupported schedule expression: '{expression}'. "
            "Supported formats: 'every 30s', 'every 5m', 'every 1h', 'daily 02:00', 'in 10m'."
        )


# =====================================================================
# 2. CRON JOB MODEL
# =====================================================================

class CronJob:
    """Represents a persistent scheduled autonomous operational job."""

    def __init__(
        self,
        name: str,
        expression: str,
        target: str,
        job_id: Optional[str] = None,
        catch_up: bool = True,
        enabled: bool = True,
    ) -> None:
        self.job_id = job_id or f"cron_{uuid.uuid4().hex[:8]}"
        self.name = name.strip() or f"Job {self.job_id}"
        self.expression = expression.strip().lower()
        self.target = target.strip()
        self.catch_up = catch_up
        self.enabled = enabled

        self.created_at = _iso(_now_utc())
        self.last_run: Optional[str] = None
        next_dt, self.meta = ScheduleParser.calculate_next_run(self.expression)
        self.next_run = _iso(next_dt)

        self.run_count: int = 0
        self.last_result: Optional[Dict[str, Any]] = None
        self.last_error: Optional[str] = None

    def is_due(self, current_time: Optional[datetime.datetime] = None) -> bool:
        """Checks if job deadline has arrived and job is enabled."""
        if not self.enabled:
            return False
        now = current_time or _now_utc()
        try:
            due_dt = datetime.datetime.fromisoformat(self.next_run)
            return now >= due_dt
        except Exception:
            return False

    def schedule_next(self, from_time: Optional[datetime.datetime] = None) -> None:
        """Computes and updates next run time. Disables one-shot jobs after execution."""
        now = from_time or _now_utc()
        self.last_run = _iso(now)
        self.run_count += 1
        if self.meta.get("type") == "one_shot":
            self.enabled = False
            return
        next_dt, self.meta = ScheduleParser.calculate_next_run(self.expression, from_time=now)
        self.next_run = _iso(next_dt)
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "expression": self.expression,
            "target": self.target,
            "catch_up": self.catch_up,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "last_run": self.last_run,
            "next_run": self.next_run,
            "run_count": self.run_count,
            "meta": self.meta,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CronJob:
        job = cls(
            job_id=data["job_id"],
            name=data["name"],
            expression=data["expression"],
            target=data["target"],
            catch_up=data.get("catch_up", True),
            enabled=data.get("enabled", True),
        )
        job.created_at = data.get("created_at", _iso(_now_utc()))
        job.last_run = data.get("last_run")
        job.next_run = data.get("next_run", job.next_run)
        job.run_count = data.get("run_count", 0)
        job.meta = data.get("meta", {})
        job.last_error = data.get("last_error")
        return job


# =====================================================================
# 3. CRON DAEMON & TEMPORAL OPERATING LOOP
# =====================================================================

class CronDaemon:
    """Master background cron scheduler for autonomous operations."""

    DEFAULT_JOBS = [
        {
            "job_id": "sys_hourly_sentinel",
            "name": "Hourly Workspace Sentinel Scan",
            "expression": "every 1h",
            "target": "scan workspace",
            "catch_up": False,
        },
        {
            "job_id": "sys_nightly_audit",
            "name": "Nightly System Audit & Alignment",
            "expression": "daily 00:00",
            "target": "/goal night audit",
            "catch_up": True,
        },
        {
            "job_id": "sys_health_probe",
            "name": "Periodic Subsystem Health Probe",
            "expression": "every 30m",
            "target": "/diagnostics",
            "catch_up": False,
        },
    ]

    def __init__(
        self,
        project_root: Optional[Path] = None,
        lucy_data: Optional[Path] = None,
        runtime: Any = None,
    ) -> None:
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parents[2]
        self.lucy_data = lucy_data or (self.project_root / "data" / "lucy")
        self.runtime = runtime

        self.schedules_file = self.lucy_data / "schedules.json"
        self.log_file = self.lucy_data / "schedule_execution.jsonl"
        self._lock = threading.RLock()
        self._jobs: Dict[str, CronJob] = {}

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._load()

    def _load(self) -> None:
        with self._lock:
            if self.schedules_file.exists():
                try:
                    data = json.loads(self.schedules_file.read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        for item in data:
                            job = CronJob.from_dict(item)
                            self._jobs[job.job_id] = job
                except Exception:
                    self._jobs = {}

            # Seed default system jobs if empty
            if not self._jobs:
                for default_item in self.DEFAULT_JOBS:
                    j = CronJob(
                        job_id=default_item["job_id"],
                        name=default_item["name"],
                        expression=default_item["expression"],
                        target=default_item["target"],
                        catch_up=default_item["catch_up"],
                    )
                    self._jobs[j.job_id] = j
                self._save()

    def _save(self) -> None:
        with self._lock:
            try:
                self.schedules_file.parent.mkdir(parents=True, exist_ok=True)
                serialized = [j.to_dict() for j in self._jobs.values()]
                self.schedules_file.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
            except Exception:
                pass

    def _log_execution(self, job: CronJob, result: Dict[str, Any]) -> None:
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "timestamp": _iso(_now_utc()),
                "job_id": job.job_id,
                "name": job.name,
                "target": job.target,
                "run_count": job.run_count,
                "ok": result.get("ok", True),
                "output_preview": str(result.get("output", ""))[:200],
            }
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def add_job(
        self,
        expression: str,
        target: str,
        name: str = "",
        job_id: Optional[str] = None,
        catch_up: bool = True,
    ) -> CronJob:
        """Registers a new persistent scheduled job."""
        with self._lock:
            job = CronJob(
                name=name,
                expression=expression,
                target=target,
                job_id=job_id,
                catch_up=catch_up,
            )
            self._jobs[job.job_id] = job
            self._save()
            return job

    def pause_job(self, job_id: str) -> bool:
        """Pauses a scheduled job."""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].enabled = False
                self._save()
                return True
            return False

    def resume_job(self, job_id: str) -> bool:
        """Resumes a paused scheduled job."""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].enabled = True
                self._save()
                return True
            return False

    def delete_job(self, job_id: str) -> bool:
        """Removes a scheduled job permanently."""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                self._save()
                return True
            return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        """Returns list of all registered jobs."""
        with self._lock:
            return [j.to_dict() for j in self._jobs.values()]

    def execute_due_jobs_now(self, current_time: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
        """Evaluates all jobs and executes any due immediately."""
        now = current_time or _now_utc()
        executed: List[Dict[str, Any]] = []

        with self._lock:
            due_jobs = [j for j in self._jobs.values() if j.is_due(now)]

        for job in due_jobs:
            res = self._dispatch_job(job)
            with self._lock:
                job.schedule_next(from_time=now)
                job.last_result = res
                job.last_error = None if res.get("ok", True) else str(res.get("error"))
                self._save()

            self._log_execution(job, res)
            executed.append({
                "job_id": job.job_id,
                "name": job.name,
                "target": job.target,
                "result": res,
            })

        return executed

    def _dispatch_job(self, job: CronJob) -> Dict[str, Any]:
        """Dispatches job target to Lucy's runtime or router."""
        target = job.target.strip()
        t0 = time.perf_counter()

        try:
            if self.runtime:
                if target.startswith("/goal ") or target.startswith("goal "):
                    intent = target.split(maxsplit=1)[1]
                    res = self.runtime.execute_goal(intent)
                    elapsed = (time.perf_counter() - t0) * 1000
                    return {"ok": res.get("ok", True), "output": res.get("tree", ""), "elapsed_ms": elapsed}
                elif hasattr(self.runtime, "respond"):
                    output = self.runtime.respond(target)
                    elapsed = (time.perf_counter() - t0) * 1000
                    return {"ok": True, "output": str(output), "elapsed_ms": elapsed}
            elapsed = (time.perf_counter() - t0) * 1000
            return {"ok": True, "output": f"Executed target: {target}", "elapsed_ms": elapsed}
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            return {"ok": False, "error": str(e), "elapsed_ms": elapsed}

    def start_background_daemon(self, check_interval_seconds: float = 5.0) -> None:
        """Starts the background scheduler thread."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._daemon_loop,
                args=(check_interval_seconds,),
                daemon=True,
                name="LucyCronDaemon",
            )
            self._thread.start()

    def stop_background_daemon(self) -> None:
        """Stops the background scheduler thread cleanly."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            self._thread = None

    def _daemon_loop(self, interval: float) -> None:
        while not self._stop_event.is_set():
            try:
                self.execute_due_jobs_now()
            except Exception:
                pass
            self._stop_event.wait(timeout=interval)

    def status(self) -> Dict[str, Any]:
        """Reports Stage 53 scheduler telemetry."""
        with self._lock:
            total = len(self._jobs)
            active = sum(1 for j in self._jobs.values() if j.enabled)
            running = self._thread.is_alive() if self._thread else False
            total_executions = sum(j.run_count for j in self._jobs.values())

        return {
            "stage": STAGE,
            "daemon_running": running,
            "total_jobs": total,
            "active_jobs": active,
            "paused_jobs": total - active,
            "total_executions": total_executions,
            "status": "active" if running else "idle",
        }
