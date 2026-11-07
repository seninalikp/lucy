"""
task_daemon.py
Stage 38 = Autonomous Task Daemon & Background Task Queue.

Provides asynchronous, non-blocking background task execution for Lucy:
1. Threaded Worker Pool: Submits tasks to a managed thread pool executor so long-running
   operations (code builds, test suites, multi-agent runs, disk sweeps) do not lock or freeze
   the terminal CLI.
2. Task Lifecycle: PENDING -> RUNNING -> COMPLETED / FAILED / CANCELLED.
3. Live Progress & Status: Tracks current step, total steps, status messages, timestamps,
   execution duration, and return values.
4. Cancellation Support: Tasks can be gracefully requested to cancel via task_id.
5. Persistent History: Saves task metadata and outcomes to data/lucy/tasks/task_history.json.
6. Zero API Leaks: Background tasks run locally and comply with Lucy safety boundaries.
"""

from __future__ import annotations

import concurrent.futures
import datetime
import inspect
import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable


STAGE = "38 autonomous task daemon"

TASK_STATUS_PENDING = "PENDING"
TASK_STATUS_RUNNING = "RUNNING"
TASK_STATUS_COMPLETED = "COMPLETED"
TASK_STATUS_FAILED = "FAILED"
TASK_STATUS_CANCELLED = "CANCELLED"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class TaskDaemon:
    """Asynchronous background task runner and manager for Lucy."""

    def __init__(self, lucy_data: Path, max_workers: int = 4) -> None:
        self.lucy_data = Path(lucy_data)
        self.tasks_dir = self.lucy_data / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.tasks_dir / "task_history.json"

        self.max_workers = max_workers
        self._lock = threading.Lock()
        self._tasks: dict[str, dict[str, Any]] = {}
        self._futures: dict[str, concurrent.futures.Future] = {}
        self._cancel_events: dict[str, threading.Event] = {}

        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="LucyWorker"
        )
        self._load_history()

    def _load_history(self) -> None:
        """Loads historical task records from disk."""
        if not self.history_file.exists():
            return
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    with self._lock:
                        for record in data:
                            if isinstance(record, dict) and "task_id" in record:
                                self._tasks[record["task_id"]] = record
        except Exception:
            pass

    def _save_history(self) -> None:
        """Saves current task records to disk (atomic write)."""
        try:
            with self._lock:
                tasks_snapshot = list(self._tasks.values())
            # Keep up to 100 most recent tasks
            tasks_snapshot.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            tasks_to_save = tasks_snapshot[:100]

            temp_file = self.history_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(tasks_to_save, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.history_file)
        except Exception:
            pass

    def submit_task(
        self,
        name: str,
        fn: Callable,
        *args: Any,
        total_steps: int = 1,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Submits a callable to run in the background.
        Returns the unique task_id immediately without blocking.
        """
        timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        task_id = f"task_{timestamp_str}_{uuid.uuid4().hex[:6]}"

        cancel_event = threading.Event()
        task_record: dict[str, Any] = {
            "task_id": task_id,
            "name": name,
            "status": TASK_STATUS_PENDING,
            "created_at": _now_iso(),
            "started_at": None,
            "completed_at": None,
            "duration_seconds": None,
            "progress_step": 0,
            "total_steps": max(1, total_steps),
            "progress_message": "Task queued in background.",
            "result": None,
            "error": None,
            "metadata": metadata or {},
            "cancel_requested": False,
        }

        with self._lock:
            self._tasks[task_id] = task_record
            self._cancel_events[task_id] = cancel_event

        future = self._executor.submit(
            self._run_task_wrapper,
            task_id,
            fn,
            cancel_event,
            *args,
            **kwargs,
        )

        with self._lock:
            self._futures[task_id] = future

        self._save_history()
        return task_id

    def _run_task_wrapper(
        self,
        task_id: str,
        fn: Callable,
        cancel_event: threading.Event,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Worker thread entry point that executes the callable and captures progress."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            if task.get("cancel_requested"):
                task["status"] = TASK_STATUS_CANCELLED
                task["completed_at"] = _now_iso()
                task["progress_message"] = "Cancelled before execution started."
                self._save_history()
                return

            task["status"] = TASK_STATUS_RUNNING
            task["started_at"] = _now_iso()
            task["progress_message"] = "Task running."

        start_time = time.time()
        result = None
        error_str = None
        was_cancelled = False

        try:
            # Check if fn accepts cancel_event or progress callback
            sig = inspect.signature(fn)
            call_kwargs = dict(kwargs)
            if "cancel_event" in sig.parameters and "cancel_event" not in call_kwargs:
                call_kwargs["cancel_event"] = cancel_event
            if "task_id" in sig.parameters and "task_id" not in call_kwargs:
                call_kwargs["task_id"] = task_id
            if "progress_callback" in sig.parameters and "progress_callback" not in call_kwargs:
                call_kwargs["progress_callback"] = lambda step, total=None, msg="": self.update_progress(
                    task_id, step, total, msg
                )

            result = fn(*args, **call_kwargs)

            if cancel_event.is_set():
                was_cancelled = True

        except Exception as e:
            error_str = str(e)

        elapsed = round(time.time() - start_time, 3)

        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task["completed_at"] = _now_iso()
                task["duration_seconds"] = elapsed
                if error_str is not None:
                    task["status"] = TASK_STATUS_FAILED
                    task["error"] = error_str
                    task["progress_message"] = f"Failed: {error_str}"
                elif was_cancelled or cancel_event.is_set() or task.get("cancel_requested"):
                    task["status"] = TASK_STATUS_CANCELLED
                    task["progress_message"] = "Task execution was cancelled."
                else:
                    task["status"] = TASK_STATUS_COMPLETED
                    task["result"] = result
                    task["progress_step"] = task["total_steps"]
                    task["progress_message"] = "Completed successfully."

        self._save_history()

    def update_progress(
        self,
        task_id: str,
        step: int,
        total: int | None = None,
        message: str = "",
    ) -> bool:
        """Updates live progress for a running task."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            task["progress_step"] = step
            if total is not None:
                task["total_steps"] = max(1, total)
            if message:
                task["progress_message"] = message
        return True

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Returns a snapshot copy of a task by ID."""
        with self._lock:
            task = self._tasks.get(task_id)
            return dict(task) if task else None

    def list_tasks(
        self,
        status: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Returns recent tasks, optionally filtered by status."""
        with self._lock:
            items = list(self._tasks.values())

        if status:
            target = status.upper().strip()
            items = [t for t in items if t.get("status") == target]

        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return [dict(t) for t in items[:limit]]

    def cancel_task(self, task_id: str) -> dict[str, Any]:
        """Cancels a pending or running task."""
        with self._lock:
            task = self._tasks.get(task_id)
            cancel_event = self._cancel_events.get(task_id)

            if not task:
                return {
                    "stage": STAGE,
                    "cancelled": False,
                    "reason": "Task not found",
                    "task_id": task_id,
                }

            current_status = task.get("status")
            if current_status in (TASK_STATUS_COMPLETED, TASK_STATUS_FAILED, TASK_STATUS_CANCELLED):
                return {
                    "stage": STAGE,
                    "cancelled": False,
                    "reason": f"Task already in terminal state: {current_status}",
                    "task_id": task_id,
                    "status": current_status,
                }

            task["cancel_requested"] = True

            if cancel_event:
                cancel_event.set()

            if current_status == TASK_STATUS_PENDING:
                task["status"] = TASK_STATUS_CANCELLED
                task["completed_at"] = _now_iso()
                task["progress_message"] = "Cancelled before execution started."

        self._save_history()
        return {
            "stage": STAGE,
            "cancelled": True,
            "task_id": task_id,
            "name": task.get("name"),
            "status": task.get("status"),
        }

    def status(self) -> dict[str, Any]:
        """Returns overall health and metrics of the background task daemon."""
        with self._lock:
            tasks = list(self._tasks.values())

        counts = {
            TASK_STATUS_PENDING: 0,
            TASK_STATUS_RUNNING: 0,
            TASK_STATUS_COMPLETED: 0,
            TASK_STATUS_FAILED: 0,
            TASK_STATUS_CANCELLED: 0,
        }
        for t in tasks:
            st = t.get("status", TASK_STATUS_PENDING)
            if st in counts:
                counts[st] += 1

        return {
            "stage": STAGE,
            "task_daemon": "active",
            "max_workers": self.max_workers,
            "total_tasks": len(tasks),
            "pending_count": counts[TASK_STATUS_PENDING],
            "running_count": counts[TASK_STATUS_RUNNING],
            "completed_count": counts[TASK_STATUS_COMPLETED],
            "failed_count": counts[TASK_STATUS_FAILED],
            "cancelled_count": counts[TASK_STATUS_CANCELLED],
            "history_file": str(self.history_file),
        }

    def shutdown(self, wait: bool = False) -> None:
        """Shuts down the thread pool."""
        try:
            self._executor.shutdown(wait=wait, cancel_futures=True)
        except Exception:
            pass
