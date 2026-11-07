"""
workspace_sentinel.py
Stage 49 = Proactive Workspace Sentinel & Habit Watchdog.

Monitors the user's workspace (C:\\Users\\admin\\Desktop\\senin\\) in the background:
1. File Change Detector:
   - Pure Python standard library file tracking (mtime, size, fast header hashing).
   - Detects newly added, modified, and deleted files across approved paths.
2. Proactive AST Syntax Validator:
   - Whenever a Python file is modified or saved, automatically validates AST syntax.
   - Detects missing colons, invalid indents, or unclosed brackets before execution.
   - Queues non-intrusive proactive alerts for the user.
3. Habit & Folder Frequency Tracker:
   - Tracks which folders and tools the user edits most frequently.
   - Automatically updates personal habits in PersonalProfiler (Stage 44).
4. Non-Blocking Alert Queue:
   - Buffers proactive alerts and delivers them cleanly on the next prompt.
"""

from __future__ import annotations

import ast
import datetime
import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any


STAGE = "49 proactive workspace sentinel"
DEFAULT_WATCH_ROOT = Path(r"C:\Users\admin\Desktop\senin")
IGNORE_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules", "lib", ".tmp"}


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _fast_hash(path: Path) -> str:
    """Computes SHA256 of first 4KB of file for fast change detection."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(4096)
            return hashlib.sha256(chunk).hexdigest()[:16]
    except Exception:
        return ""


class WorkspaceSentinel:
    """Proactive background file watcher and AST syntax checker."""

    def __init__(
        self,
        project_root: Path,
        lucy_data: Path,
        watch_root: Path | None = None,
        profiler: Any = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.lucy_data = Path(lucy_data)
        self.watch_root = Path(watch_root) if watch_root else DEFAULT_WATCH_ROOT
        self.profiler = profiler

        self.state_file = self.lucy_data / "workspace_sentinel_state.json"
        self._snapshots: dict[str, dict[str, Any]] = {}
        self._alerts_queue: list[str] = []
        self._folder_hits: dict[str, int] = {}
        self.scan_count = 0
        self.total_syntax_errors_caught = 0

        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        self._load_state()

    def _load_state(self) -> None:
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                self._snapshots = data.get("snapshots", {})
                self._folder_hits = data.get("folder_hits", {})
                self.scan_count = data.get("scan_count", 0)
                self.total_syntax_errors_caught = data.get("total_syntax_errors_caught", 0)
            except Exception:
                pass

    def _save_state(self) -> None:
        data = {
            "stage": STAGE,
            "updated_at": _now(),
            "watch_root": str(self.watch_root),
            "scan_count": self.scan_count,
            "total_syntax_errors_caught": self.total_syntax_errors_caught,
            "tracked_files_count": len(self._snapshots),
            "folder_hits": self._folder_hits,
            "snapshots": self._snapshots,
        }
        try:
            self.state_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def validate_python_syntax(self, path: Path) -> dict[str, Any]:
        """Validates Python syntax in memory without executing code."""
        try:
            code = path.read_text(encoding="utf-8", errors="ignore")
            ast.parse(code, filename=str(path))
            return {"valid": True, "error": None}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": {
                    "message": e.msg,
                    "lineno": e.lineno,
                    "offset": e.offset,
                    "text": (e.text or "").strip(),
                },
            }
        except Exception as e:
            return {"valid": False, "error": {"message": str(e), "lineno": 0}}

    def scan_once(self) -> dict[str, Any]:
        """Performs a single pass over the watched directory to detect file changes."""
        with self._lock:
            self.scan_count += 1
            current_files: dict[str, dict[str, Any]] = {}
            created = []
            modified = []
            syntax_alerts = []

            base = self.watch_root if self.watch_root.exists() else self.project_root

            try:
                for root, dirs, files in os.walk(base):
                    dirs[:] = [d for d in dirs if not d.startswith(".") and d not in IGNORE_DIRS]

                    for f in files:
                        if f.startswith("."):
                            continue

                        fp = Path(root) / f
                        try:
                            st = fp.stat()
                            mtime = st.st_mtime
                            size = st.st_size
                            rel = str(fp)

                            # Record folder hit
                            folder_key = str(Path(root).name)
                            self._folder_hits[folder_key] = self._folder_hits.get(folder_key, 0) + 1

                            file_meta = {
                                "name": f,
                                "path": rel,
                                "mtime": mtime,
                                "size": size,
                                "fhash": _fast_hash(fp),
                            }
                            current_files[rel] = file_meta

                            if rel not in self._snapshots:
                                created.append(rel)
                                # Validate Python syntax on new files
                                if f.endswith(".py"):
                                    res = self.validate_python_syntax(fp)
                                    if not res["valid"]:
                                        err = res["error"]
                                        alert = f"[Sentinel Alert] Syntax error in new file '{f}': Line {err.get('lineno')} - {err.get('message')}"
                                        self._alerts_queue.append(alert)
                                        syntax_alerts.append(alert)
                                        self.total_syntax_errors_caught += 1
                            else:
                                prev = self._snapshots[rel]
                                if prev.get("mtime") != mtime or prev.get("size") != size or prev.get("fhash") != file_meta["fhash"]:
                                    modified.append(rel)
                                    # Validate Python syntax on modified files
                                    if f.endswith(".py"):
                                        res = self.validate_python_syntax(fp)
                                        if not res["valid"]:
                                            err = res["error"]
                                            alert = f"[Sentinel Alert] Syntax error in modified file '{f}': Line {err.get('lineno')} - {err.get('message')}"
                                            self._alerts_queue.append(alert)
                                            syntax_alerts.append(alert)
                                            self.total_syntax_errors_caught += 1
                        except Exception:
                            continue
            except Exception:
                pass

            deleted = [k for k in self._snapshots if k not in current_files]

            # Update snapshots
            self._snapshots = current_files
            self._save_state()

            # Update habit tracker in profiler if top folders change
            if self.profiler is not None and hasattr(self.profiler, "set_preference"):
                top_folder = sorted(self._folder_hits.items(), key=lambda x: x[1], reverse=True)
                if top_folder:
                    self.profiler.set_preference("observed_patterns", "active_workspace_folder", top_folder[0][0])

            return {
                "stage": STAGE,
                "scan_index": self.scan_count,
                "created_count": len(created),
                "created": created[:10],
                "modified_count": len(modified),
                "modified": modified[:10],
                "deleted_count": len(deleted),
                "deleted": deleted[:10],
                "syntax_alerts_caught": len(syntax_alerts),
                "total_tracked": len(current_files),
            }

    def consume_alerts(self) -> list[str]:
        """Retrieves and flushes all pending sentinel alerts."""
        with self._lock:
            alerts = list(self._alerts_queue)
            self._alerts_queue.clear()
            return alerts

    def start_background_watcher(self, interval_seconds: float = 30.0) -> dict[str, Any]:
        """Launches background thread for autonomous periodic workspace checks."""
        with self._lock:
            if self._running:
                return {"started": False, "status": "already_running"}

            self._running = True

            def _loop():
                while self._running:
                    try:
                        self.scan_once()
                    except Exception:
                        pass
                    time.sleep(interval_seconds)

            self._thread = threading.Thread(target=_loop, daemon=True, name="WorkspaceSentinelThread")
            self._thread.start()

            return {
                "started": True,
                "status": "running",
                "interval_seconds": interval_seconds,
                "watch_root": str(self.watch_root),
            }

    def stop_background_watcher(self) -> dict[str, Any]:
        """Stops the background sentinel thread cleanly."""
        with self._lock:
            if not self._running:
                return {"stopped": False, "status": "not_running"}

            self._running = False

        if self._thread and self._thread.is_alive():
            try:
                self._thread.join(timeout=1.5)
            except Exception:
                pass

        return {"stopped": True, "status": "stopped"}

    def status(self) -> dict[str, Any]:
        """Returns snapshot of sentinel status and habit metrics."""
        top_folders = sorted(self._folder_hits.items(), key=lambda x: x[1], reverse=True)[:5]
        return {
            "stage": STAGE,
            "workspace_sentinel": "active",
            "is_background_running": self._running,
            "watch_root": str(self.watch_root),
            "scan_count": self.scan_count,
            "tracked_files": len(self._snapshots),
            "pending_alerts_count": len(self._alerts_queue),
            "pending_alerts": list(self._alerts_queue),
            "total_syntax_errors_caught": self.total_syntax_errors_caught,
            "top_active_folders": top_folders,
        }
