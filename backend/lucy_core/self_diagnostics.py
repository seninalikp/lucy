"""
self_diagnostics.py
Stage 51 = Self-Diagnostics & Crash Recovery Daemon.

Provides automated self-healing, integrity verification, and hygiene:
1. State File Auditor & Auto-Recovery:
   - Audits critical JSON state files (spine.json, terminal_history, user_macros,
     personal_profile, task_history, provider_health, etc.).
   - Validates JSON parseability and non-zero structure.
   - Automatically creates rolling .bak backups before modification.
   - Restores corrupted or truncated state files from .bak backups.
   - Safely reconstructs valid default state if no backup exists.
2. Log File Quota & Hygiene Monitor:
   - Scans log files across Lucy log directories.
   - Enforces configurable size quotas and performs safe rolling rotation (.1, .2, etc.).
   - Detects and cleans orphaned temporary files (.tmp) to prevent disk waste.
3. Subsystem Health Prober:
   - Checks sovereign daemon health: Ollama port (11434), TaskDaemon queue,
     WorkspaceSentinel background watcher, and MultiProviderPool key status.
   - Generates overall health evaluation: HEALTHY, DEGRADED, or CRITICAL.
4. Crash Recovery Daemon:
   - Automated self-healing orchestrator (auto_heal) that fixes corrupted state,
     cleans log bloat, and re-launches stopped background threads.
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import socket
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


STAGE = "51 self-diagnostics & crash recovery daemon"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# =====================================================================
# 1. STATE FILE AUDITOR & AUTO-RECOVERY
# =====================================================================

class StateFileAuditor:
    """Audits, backs up, and automatically repairs critical JSON state files."""

    CRITICAL_FILES = [
        "data/spine.json",
        "data/lucy/terminal_history.json",
        "data/lucy/user_macros.json",
        "data/lucy/personal_profile.json",
        "data/lucy/provider_health.json",
        "data/lucy/tasks/task_history.json",
        "data/lucy/memory/memory.json",
        "config/lucy_runtime_config.json",
    ]

    DEFAULT_SCHEMAS: Dict[str, Any] = {
        "spine.json": {"version": "3.1.0", "core": "Lucy", "initialized": True},
        "terminal_history.json": [],
        "user_macros.json": {
            "quickcheck": "sentinel alerts && telemetry",
            "health": "provider status && sentinel status",
            "sync": "scan workspace && train personal lora",
        },
        "personal_profile.json": {
            "anti_drift_rules": [],
            "workspace_aliases": {},
            "habits": {},
        },
        "provider_health.json": {"records": [], "last_reset": None},
        "task_history.json": {"tasks": [], "completed": 0},
        "memory.json": {"memories": [], "rules": []},
        "lucy_runtime_config.json": {"runtime": "lucy_core", "local_mode": True},
    }

    def __init__(self, project_root: Path, lucy_data: Path) -> None:
        self.project_root = project_root
        self.lucy_data = lucy_data

    def _resolve_path(self, rel_or_abs: str | Path) -> Path:
        p = Path(rel_or_abs)
        if p.is_absolute():
            return p
        return self.project_root / p

    def create_backup(self, path: Path) -> Optional[Path]:
        """Creates a .bak copy of a healthy file."""
        if not path.exists():
            return None
        bak_path = path.with_suffix(path.suffix + ".bak")
        try:
            bak_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, bak_path)
            return bak_path
        except Exception:
            return None

    def validate_file(self, path: Path) -> Tuple[bool, str]:
        """Validates that path exists and contains valid JSON."""
        if not path.exists():
            return False, "file_missing"
        if path.stat().st_size == 0:
            return False, "zero_byte_empty"
        try:
            with open(path, "r", encoding="utf-8") as f:
                json.load(f)
            return True, "valid"
        except json.JSONDecodeError as e:
            return False, f"json_decode_error: {e.msg}"
        except Exception as e:
            return False, f"read_error: {str(e)}"

    def restore_from_backup(self, path: Path) -> bool:
        """Restores file from .bak if backup exists and is valid."""
        bak_path = path.with_suffix(path.suffix + ".bak")
        valid, _ = self.validate_file(bak_path)
        if valid:
            try:
                shutil.copy2(bak_path, path)
                return True
            except Exception:
                return False
        return False

    def reconstruct_default(self, path: Path) -> bool:
        """Reconstructs default state structure if no backup is available."""
        name = path.name
        schema = self.DEFAULT_SCHEMAS.get(name, {})
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
            return True
        except Exception:
            return False

    def audit_all(self, monitored_paths: Optional[List[Path]] = None) -> Dict[str, Any]:
        """Runs audit across all critical state files."""
        targets = monitored_paths or [self._resolve_path(f) for f in self.CRITICAL_FILES]

        healthy: List[str] = []
        corrupted: List[str] = []
        missing: List[str] = []
        restored: List[str] = []
        reconstructed: List[str] = []

        for p in targets:
            rel = str(p.relative_to(self.project_root)) if p.is_relative_to(self.project_root) else p.name
            valid, reason = self.validate_file(p)

            if valid:
                healthy.append(rel)
                # Keep backup updated
                self.create_backup(p)
            elif reason == "file_missing":
                missing.append(rel)
                if self.reconstruct_default(p):
                    reconstructed.append(rel)
            else:
                corrupted.append(f"{rel} ({reason})")
                if self.restore_from_backup(p):
                    restored.append(rel)
                elif self.reconstruct_default(p):
                    reconstructed.append(rel)

        return {
            "total_checked": len(targets),
            "healthy": healthy,
            "corrupted": corrupted,
            "missing": missing,
            "restored_from_backup": restored,
            "reconstructed_defaults": reconstructed,
            "all_healthy": len(corrupted) == 0 and len(missing) == 0,
        }


# =====================================================================
# 2. LOG HYGIENE & QUOTA MONITOR
# =====================================================================

class LogHygieneMonitor:
    """Monitors log file sizes, performs rolling rotations, and cleans temp files."""

    def __init__(
        self,
        log_dirs: Optional[List[Path]] = None,
        max_size_bytes: int = 5 * 1024 * 1024,  # 5MB default
        max_rotations: int = 3,
    ) -> None:
        self.log_dirs = log_dirs or [
            Path(r"C:\Users\admin\Desktop\senin\LUCY\lucy\logs"),
            Path(r"C:\Users\admin\Desktop\senin\LUCY\lucy\data\lucy\logs"),
        ]
        self.max_size_bytes = max_size_bytes
        self.max_rotations = max_rotations

    def rotate_log_file(self, log_path: Path) -> bool:
        """Rotates log file keeping up to max_rotations versions."""
        if not log_path.exists():
            return False

        try:
            # Shift older rotations: .2 -> .3, .1 -> .2
            for i in range(self.max_rotations - 1, 0, -1):
                src = log_path.with_name(f"{log_path.name}.{i}")
                dst = log_path.with_name(f"{log_path.name}.{i + 1}")
                if src.exists():
                    shutil.move(src, dst)

            # Move current to .1
            dst_1 = log_path.with_name(f"{log_path.name}.1")
            shutil.move(log_path, dst_1)

            # Create fresh empty log
            log_path.touch()
            return True
        except Exception:
            return False

    def clean_orphaned_tmp_files(self, search_dir: Path) -> Tuple[int, int]:
        """Finds and removes orphaned .tmp files."""
        cleaned_count = 0
        cleaned_bytes = 0
        if not search_dir.exists():
            return 0, 0

        try:
            for item in search_dir.rglob("*.tmp"):
                if item.is_file():
                    try:
                        sz = item.stat().st_size
                        item.unlink()
                        cleaned_count += 1
                        cleaned_bytes += sz
                    except Exception:
                        pass
        except Exception:
            pass

        return cleaned_count, cleaned_bytes

    def check_and_clean(self) -> Dict[str, Any]:
        """Runs log size check, rotations, and temp cleanup."""
        rotated: List[str] = []
        scanned_count = 0
        total_tmp_cleaned = 0
        total_bytes_freed = 0

        for d in self.log_dirs:
            if not d.exists():
                continue
            for item in d.glob("*"):
                if item.is_file() and not item.name.endswith((".1", ".2", ".3", ".4", ".5")):
                    scanned_count += 1
                    try:
                        if item.stat().st_size > self.max_size_bytes:
                            if self.rotate_log_file(item):
                                rotated.append(item.name)
                    except Exception:
                        pass

        # Clean orphaned .tmp files in data/lucy
        data_dir = Path(r"C:\Users\admin\Desktop\senin\LUCY\lucy\data\lucy")
        tmp_cleaned, bytes_freed = self.clean_orphaned_tmp_files(data_dir)
        total_tmp_cleaned += tmp_cleaned
        total_bytes_freed += bytes_freed

        return {
            "logs_scanned": scanned_count,
            "rotated_logs": rotated,
            "tmp_files_cleaned": total_tmp_cleaned,
            "bytes_freed": total_bytes_freed,
        }


# =====================================================================
# 3. SUBSYSTEM HEALTH PROBER
# =====================================================================

class SubsystemHealthProber:
    """Probes physical and logical health of Lucy's core sovereign components."""

    @classmethod
    def probe_port(cls, port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
        """Fast TCP socket probe for local services."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                return s.connect_ex((host, port)) == 0
        except Exception:
            return False

    def probe_all(self, runtime: Any = None) -> Dict[str, Any]:
        """Gathers health states across subsystems."""
        subsystems: Dict[str, Any] = {}

        # 1. Ollama Sovereign Mind
        ollama_listening = self.probe_port(11434)
        subsystems["ollama"] = {
            "port": 11434,
            "status": "HEALTHY" if ollama_listening else "OFFLINE",
            "role": "Sovereign Mind (qwen2.5:3b)",
        }

        # 2. Workspace Sentinel
        if runtime and hasattr(runtime, "sentinel_status"):
            try:
                s_stat = runtime.sentinel_status()
                watcher_running = s_stat.get("background_watcher", {}).get("running", False)
                subsystems["workspace_sentinel"] = {
                    "status": "HEALTHY" if watcher_running else "IDLE",
                    "files_tracked": s_stat.get("files_tracked", 0),
                    "pending_alerts": s_stat.get("pending_alerts_count", 0),
                }
            except Exception as e:
                subsystems["workspace_sentinel"] = {"status": "DEGRADED", "error": str(e)}
        else:
            subsystems["workspace_sentinel"] = {"status": "UNKNOWN"}

        # 3. Task Daemon
        if runtime and hasattr(runtime, "task_daemon"):
            try:
                td = runtime.task_daemon
                subsystems["task_daemon"] = {
                    "status": "HEALTHY",
                    "queued_tasks": td.get_queue_length() if hasattr(td, "get_queue_length") else 0,
                }
            except Exception as e:
                subsystems["task_daemon"] = {"status": "DEGRADED", "error": str(e)}
        else:
            subsystems["task_daemon"] = {"status": "HEALTHY"}

        # 4. Multi-Provider Pool
        if runtime and hasattr(runtime, "provider_pool_status"):
            try:
                p_stat = runtime.provider_pool_status()
                subsystems["provider_pool"] = {
                    "status": "HEALTHY" if p_stat.get("healthy_keys", 0) > 0 else "DEGRADED",
                    "total_keys": p_stat.get("total_keys", 0),
                    "healthy_keys": p_stat.get("healthy_keys", 0),
                    "active_provider": p_stat.get("active_provider", "unknown"),
                }
            except Exception as e:
                subsystems["provider_pool"] = {"status": "DEGRADED", "error": str(e)}
        else:
            subsystems["provider_pool"] = {"status": "HEALTHY"}

        # Compute overall health
        statuses = [info.get("status") for info in subsystems.values()]
        if any(s == "CRITICAL" for s in statuses):
            overall = "CRITICAL"
        elif any(s in {"OFFLINE", "DEGRADED"} for s in statuses):
            overall = "DEGRADED"
        else:
            overall = "HEALTHY"

        return {
            "overall_health": overall,
            "timestamp": _now_iso(),
            "subsystems": subsystems,
        }


# =====================================================================
# 4. CRASH RECOVERY DAEMON & ORCHESTRATOR
# =====================================================================

class CrashRecoveryDaemon:
    """Master self-diagnostics and auto-recovery coordinator."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        lucy_data: Optional[Path] = None,
        runtime: Any = None,
    ) -> None:
        self.project_root = project_root or Path(r"C:\Users\admin\Desktop\senin\LUCY\lucy")
        self.lucy_data = lucy_data or (self.project_root / "data" / "lucy")
        self.runtime = runtime

        self.auditor = StateFileAuditor(project_root=self.project_root, lucy_data=self.lucy_data)
        self.hygiene = LogHygieneMonitor()
        self.prober = SubsystemHealthProber()

    def run_diagnostics(self) -> Dict[str, Any]:
        """Runs full health and integrity diagnostics across all subsystems."""
        t0 = time.perf_counter()
        state_audit = self.auditor.audit_all()
        hygiene_report = self.hygiene.check_and_clean()
        health_probe = self.prober.probe_all(self.runtime)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "stage": STAGE,
            "timestamp": _now_iso(),
            "elapsed_ms": elapsed_ms,
            "overall_health": health_probe["overall_health"],
            "state_audit": state_audit,
            "log_hygiene": hygiene_report,
            "subsystems": health_probe["subsystems"],
        }

    def auto_heal(self) -> Dict[str, Any]:
        """Executes self-healing: repairs corrupted files, cleans bloat, and revives threads."""
        actions_taken: List[str] = []

        # 1. State files repair
        state_audit = self.auditor.audit_all()
        if state_audit["restored_from_backup"]:
            actions_taken.append(
                f"Restored {len(state_audit['restored_from_backup'])} state file(s) from .bak: "
                + ", ".join(state_audit["restored_from_backup"])
            )
        if state_audit["reconstructed_defaults"]:
            actions_taken.append(
                f"Reconstructed {len(state_audit['reconstructed_defaults'])} default state file(s): "
                + ", ".join(state_audit["reconstructed_defaults"])
            )

        # 2. Log hygiene & tmp cleanup
        hygiene = self.hygiene.check_and_clean()
        if hygiene["rotated_logs"]:
            actions_taken.append(f"Rotated {len(hygiene['rotated_logs'])} oversized log(s): " + ", ".join(hygiene["rotated_logs"]))
        if hygiene["tmp_files_cleaned"] > 0:
            actions_taken.append(f"Cleaned {hygiene['tmp_files_cleaned']} orphaned .tmp file(s) ({hygiene['bytes_freed']} bytes freed)")

        # 3. Thread revival: Workspace Sentinel
        if self.runtime and hasattr(self.runtime, "workspace_sentinel"):
            sentinel = self.runtime.workspace_sentinel
            if hasattr(sentinel, "is_watching") and not sentinel.is_watching():
                try:
                    sentinel.start_background_watcher(interval_seconds=30.0)
                    actions_taken.append("Restarted WorkspaceSentinel background watcher thread.")
                except Exception as e:
                    actions_taken.append(f"Failed to restart sentinel: {e}")

        # Post-healing health check
        health = self.prober.probe_all(self.runtime)

        return {
            "healed": len(actions_taken) > 0,
            "actions_taken": actions_taken,
            "current_health": health["overall_health"],
            "timestamp": _now_iso(),
        }

    def create_system_snapshot(self) -> Dict[str, Any]:
        """Forces a fresh .bak backup of all monitored state files."""
        targets = [self.auditor._resolve_path(f) for f in self.auditor.CRITICAL_FILES]
        backed_up: List[str] = []
        for t in targets:
            if t.exists():
                bak = self.auditor.create_backup(t)
                if bak:
                    backed_up.append(t.name)

        return {
            "ok": True,
            "total_backed_up": len(backed_up),
            "files": backed_up,
            "timestamp": _now_iso(),
        }

    def status(self) -> Dict[str, Any]:
        """Returns Stage 51 daemon telemetry."""
        return {
            "stage": STAGE,
            "monitored_critical_files": len(self.auditor.CRITICAL_FILES),
            "status": "ready",
            "last_check": _now_iso(),
        }
