"""
tools.py
Safe local tools for Lucy.

These tools are read-only and scoped to the Lucy project folder unless stated
otherwise. They do not run arbitrary shell commands.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path


TEXT_SUFFIXES = {
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".toml",
    ".ts",
    ".yml",
    ".yaml",
}

SKIP_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
}

SENSITIVE_NAME_PARTS = {
    ".env",
    "secret",
    "password",
    "passwd",
    "credential",
    "private_key",
    "seed",
    "wallet",
}


class SafeToolbox:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def _resolve_inside_project(self, raw_path: str) -> Path:
        candidate = (self.project_root / raw_path).resolve()
        if candidate != self.project_root and self.project_root not in candidate.parents:
            raise ValueError("Path is outside Lucy's project folder.")
        return candidate

    def _is_sensitive_name(self, path: Path) -> bool:
        lowered = str(path).replace("\\", "/").lower()
        return any(part in lowered for part in SENSITIVE_NAME_PARTS)

    def _iter_files(self) -> list[Path]:
        files: list[Path] = []
        for root, dirs, names in os.walk(self.project_root):
            dirs[:] = [dirname for dirname in dirs if dirname not in SKIP_DIRS]
            root_path = Path(root)
            for name in names:
                path = root_path / name
                if self._is_sensitive_name(path):
                    continue
                files.append(path)
        return files

    def workspace_tree(self, limit: int = 120) -> dict:
        files = sorted(self._iter_files(), key=lambda path: str(path.relative_to(self.project_root)).lower())
        rows = []
        for path in files[:limit]:
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            rows.append(
                {
                    "path": str(path.relative_to(self.project_root)).replace("\\", "/"),
                    "size": size,
                }
            )
        return {
            "root": str(self.project_root),
            "shown": len(rows),
            "total": len(files),
            "files": rows,
        }

    def find_files(self, query: str, limit: int = 40) -> dict:
        cleaned = query.strip().lower()
        if not cleaned:
            return {"matches": [], "reason": "Search query was empty."}
        matches = []
        for path in self._iter_files():
            relative = str(path.relative_to(self.project_root)).replace("\\", "/")
            if cleaned in relative.lower():
                matches.append(relative)
            if len(matches) >= limit:
                break
        return {"query": query, "matches": matches, "limit": limit}

    def search_text(self, query: str, limit: int = 30) -> dict:
        cleaned = query.strip()
        if not cleaned:
            return {"matches": [], "reason": "Search query was empty."}
        lowered = cleaned.lower()
        matches = []
        for path in self._iter_files():
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if self._is_sensitive_name(path):
                continue
            try:
                if path.stat().st_size > 500_000:
                    continue
                for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                    if lowered in line.lower():
                        matches.append(
                            {
                                "path": str(path.relative_to(self.project_root)).replace("\\", "/"),
                                "line": line_number,
                                "text": line.strip()[:220],
                            }
                        )
                        if len(matches) >= limit:
                            return {"query": query, "matches": matches, "limit": limit}
            except OSError:
                continue
        return {"query": query, "matches": matches, "limit": limit}

    def read_text_file(self, raw_path: str, max_chars: int = 5000) -> dict:
        try:
            path = self._resolve_inside_project(raw_path)
        except ValueError as exc:
            return {"read": False, "reason": str(exc)}
        if not path.exists() or not path.is_file():
            return {"read": False, "reason": "File does not exist."}
        if self._is_sensitive_name(path):
            return {"read": False, "reason": "Refused to read a sensitive-looking file name."}
        if path.suffix.lower() not in TEXT_SUFFIXES:
            return {"read": False, "reason": "Only text-like project files can be read by this command."}
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return {"read": False, "reason": f"Could not read file: {exc}"}
        truncated = len(text) > max_chars
        return {
            "read": True,
            "path": str(path.relative_to(self.project_root)).replace("\\", "/"),
            "text": text[:max_chars],
            "truncated": truncated,
            "chars": min(len(text), max_chars),
        }

    def system_snapshot(self) -> dict:
        disk = shutil.disk_usage(self.project_root)
        return {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "project_root": str(self.project_root),
            "cwd": os.getcwd(),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
        }

    def log_tail(self, log_path: Path, limit: int = 10) -> list[dict]:
        if not log_path.exists():
            return []
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        result = []
        for line in lines[-limit:]:
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                result.append({"raw": line})
        return result
