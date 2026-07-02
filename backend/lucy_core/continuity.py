"""
continuity.py
Safe local continuity backups for Lucy.

The continuity layer protects Lucy's durable local context across normal app
restarts and laptop reboots. It does not back up secrets, API keys, provider
vaults, or the full machine.
"""

from __future__ import annotations

import json
import random
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


CONTINUITY_VERSION = "0.1.0"
MAX_BACKUPS = 20
MAX_FILE_BYTES = 2_000_000
AUTO_BACKUP_MIN_CHANGES = 3
AUTO_BACKUP_MAX_CHANGES = 7
STARTUP_BACKUP_COOLDOWN_HOURS = 12

EXCLUDED_PARTS = {
    "secure",
    "knowledge",
    "ops",
    "logs",
    "continuity",
    "__pycache__",
}

SENSITIVE_MARKERS = {
    ".env",
    "api_key",
    "apikey",
    "password",
    "passphrase",
    "private_key",
    "secret",
    "seed",
    "token",
    "wallet",
    "credential",
}

INCLUDED_ROOT_FILES = {
    "projects.json",
    "reminders.json",
    "runtime_state.json",
    "agent_registry.json",
    "recovered_architecture.json",
}

INCLUDED_DIRS = {
    "memory",
    "daily",
    "cognition",
    "learning",
    "approvals",
    "checkpoints",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _clean_reason(reason: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in reason.lower()).strip("_")
    return cleaned[:48] or "manual"


class ContinuityBackup:
    """Rolling local snapshots of Lucy's non-secret continuity state."""

    def __init__(self, lucy_data_dir: Path, retention: int = MAX_BACKUPS) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.continuity_dir = lucy_data_dir / "continuity"
        self.backups_dir = self.continuity_dir / "backups"
        self.state_file = self.continuity_dir / "continuity_state.json"
        self.retention = max(3, retention)
        self.random = random.SystemRandom()
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_state()

    def _default_state(self) -> dict:
        return {
            "version": CONTINUITY_VERSION,
            "mode": "local_non_secret_rolling_backups",
            "created_at": _now(),
            "updated_at": _now(),
            "change_counter": 0,
            "next_auto_backup_after": self._next_interval(),
            "last_backup_at": None,
            "last_backup_path": None,
            "total_backups_created": 0,
        }

    def _next_interval(self) -> int:
        return self.random.randint(AUTO_BACKUP_MIN_CHANGES, AUTO_BACKUP_MAX_CHANGES)

    def _ensure_state(self) -> None:
        if not self.state_file.exists():
            self._write_state(self._default_state())

    def _read_state(self) -> dict:
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            data = self._default_state()
        data.setdefault("version", CONTINUITY_VERSION)
        data.setdefault("mode", "local_non_secret_rolling_backups")
        data.setdefault("change_counter", 0)
        data.setdefault("next_auto_backup_after", self._next_interval())
        data.setdefault("last_backup_at", None)
        data.setdefault("last_backup_path", None)
        data.setdefault("total_backups_created", 0)
        return data

    def _write_state(self, data: dict) -> None:
        data["updated_at"] = _now()
        self.continuity_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _relative(self, path: Path) -> str:
        return str(path.relative_to(self.lucy_data_dir)).replace("\\", "/")

    def _is_sensitive(self, relative: str) -> bool:
        lowered = relative.lower()
        parts = set(lowered.split("/"))
        if parts & EXCLUDED_PARTS:
            return True
        return any(marker in lowered for marker in SENSITIVE_MARKERS)

    def _should_include(self, path: Path) -> bool:
        if not path.is_file():
            return False
        try:
            relative = self._relative(path)
        except ValueError:
            return False
        if self._is_sensitive(relative):
            return False
        parts = relative.split("/")
        if len(parts) == 1:
            return parts[0] in INCLUDED_ROOT_FILES
        return parts[0] in INCLUDED_DIRS

    def _iter_continuity_files(self) -> tuple[list[Path], list[dict]]:
        included: list[Path] = []
        skipped: list[dict] = []
        if not self.lucy_data_dir.exists():
            return included, [{"path": str(self.lucy_data_dir), "reason": "lucy data directory missing"}]

        for path in sorted(self.lucy_data_dir.rglob("*")):
            if not path.is_file():
                continue
            try:
                relative = self._relative(path)
            except ValueError:
                continue
            if not self._should_include(path):
                if self._is_sensitive(relative):
                    skipped.append({"path": relative, "reason": "secret_or_excluded_area"})
                continue
            try:
                size = path.stat().st_size
            except OSError:
                skipped.append({"path": relative, "reason": "unreadable"})
                continue
            if size > MAX_FILE_BYTES:
                skipped.append({"path": relative, "reason": "too_large"})
                continue
            included.append(path)
        return included, skipped

    def snapshot(self, reason: str = "manual", trigger: str = "manual") -> dict:
        files, skipped = self._iter_continuity_files()
        if not files:
            return {
                "created": False,
                "reason": "No continuity files were available to back up.",
                "files": 0,
                "skipped": skipped,
            }

        backup_name = f"lucy_continuity_{_stamp()}_{_clean_reason(reason)}.zip"
        out = self.backups_dir / backup_name
        manifest = {
            "version": CONTINUITY_VERSION,
            "created_at": _now(),
            "reason": reason,
            "trigger": trigger,
            "lucy_data_dir": str(self.lucy_data_dir),
            "included_files": [],
            "skipped": skipped,
            "excluded": sorted(EXCLUDED_PARTS | SENSITIVE_MARKERS),
            "note": "Secrets, provider vaults, logs, knowledge indexes, and backup folders are excluded.",
        }

        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                relative = self._relative(path)
                archive.write(path, relative)
                manifest["included_files"].append(relative)
            archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

        state = self._read_state()
        state["change_counter"] = 0
        state["next_auto_backup_after"] = self._next_interval()
        state["last_backup_at"] = manifest["created_at"]
        state["last_backup_path"] = str(out)
        state["total_backups_created"] = int(state.get("total_backups_created", 0)) + 1
        self._write_state(state)
        removed = self._prune_old_backups()

        return {
            "created": True,
            "path": str(out),
            "files": len(files),
            "skipped": skipped,
            "removed_old_backups": removed,
            "reason": reason,
            "trigger": trigger,
            "next_auto_backup_after": state["next_auto_backup_after"],
        }

    def maybe_auto_backup(self, reason: str) -> dict:
        state = self._read_state()
        state["change_counter"] = int(state.get("change_counter", 0)) + 1
        threshold = int(state.get("next_auto_backup_after", self._next_interval()))
        if state["change_counter"] < threshold:
            self._write_state(state)
            return {
                "created": False,
                "reason": "Auto backup threshold not reached.",
                "change_counter": state["change_counter"],
                "next_auto_backup_after": threshold,
            }
        return self.snapshot(reason=reason, trigger="auto_change_threshold")

    def startup_backup(self) -> dict:
        state = self._read_state()
        existing = self.list_backups()
        if not existing:
            return self.snapshot(reason="startup bootstrap continuity", trigger="startup")

        last = _parse_time(state.get("last_backup_at"))
        if last is None:
            return self.snapshot(reason="startup missing backup timestamp", trigger="startup")

        age = datetime.now(timezone.utc) - last
        if age >= timedelta(hours=STARTUP_BACKUP_COOLDOWN_HOURS):
            return self.snapshot(reason="startup continuity refresh", trigger="startup")

        return {
            "created": False,
            "reason": "Startup backup cooldown active.",
            "last_backup_at": state.get("last_backup_at"),
            "last_backup_path": state.get("last_backup_path"),
        }

    def _prune_old_backups(self) -> int:
        backups = sorted(self.backups_dir.glob("lucy_continuity_*.zip"), key=lambda path: path.stat().st_mtime)
        removed = 0
        while len(backups) > self.retention:
            oldest = backups.pop(0)
            try:
                oldest.unlink()
                removed += 1
            except OSError:
                continue
        return removed

    def list_backups(self, limit: int = 5) -> list[dict]:
        backups = sorted(
            self.backups_dir.glob("lucy_continuity_*.zip"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        result = []
        for path in backups[:limit]:
            try:
                size = path.stat().st_size
                modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
            except OSError:
                continue
            result.append({"path": str(path), "size": size, "modified_at": modified})
        return result

    def status(self) -> dict:
        state = self._read_state()
        backups = self.list_backups(limit=8)
        return {
            "mode": state.get("mode"),
            "continuity_dir": str(self.continuity_dir),
            "state_file": str(self.state_file),
            "backup_count": len(list(self.backups_dir.glob("lucy_continuity_*.zip"))),
            "latest_backups": backups,
            "change_counter": state.get("change_counter", 0),
            "next_auto_backup_after": state.get("next_auto_backup_after"),
            "last_backup_at": state.get("last_backup_at"),
            "last_backup_path": state.get("last_backup_path"),
            "retention": self.retention,
            "excluded": sorted(EXCLUDED_PARTS | SENSITIVE_MARKERS),
            "survives": "Lucy app restarts and normal laptop reboots.",
            "does_not_survive": "Full disk wipe/factory reset unless exported to an external folder first.",
        }
