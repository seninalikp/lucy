"""
live_workspace_context.py
Stage 57 = Live Workspace Context & Git/File Diff Sensor.

Eliminates workspace blindness by inspecting physical project files and Git state:
1. Detects the most recently modified files in the workspace.
2. Runs read-only `git status --short` and `git branch --show-current` if inside a Git repo.
3. Injects a concise `[Live Physical Workspace State]` summary into Lucy's prompt so
   she always knows what Senin is actively coding or debugging.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE = "57 live workspace context sensor"

IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "continuity", "logs", "checkpoints", "data",
}


class LiveWorkspaceSensor:
    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)

    def recently_modified_files(self, limit: int = 6) -> list[dict[str, Any]]:
        files: list[tuple[float, Path]] = []
        if not self.project_root.exists():
            return []

        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in {".py", ".json", ".md", ".html", ".js", ".css", ".sh", ".bat"}:
                continue
            try:
                mtime = path.stat().st_mtime
                files.append((mtime, path))
            except OSError:
                continue

        files.sort(key=lambda pair: pair[0], reverse=True)
        result: list[dict[str, Any]] = []
        for mtime, p in files[:limit]:
            rel = str(p.relative_to(self.project_root)).replace("\\", "/")
            iso_time = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            result.append({"path": rel, "modified_at": iso_time, "size_bytes": p.stat().st_size})
        return result

    def git_pulse(self) -> dict[str, Any]:
        try:
            branch_proc = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            status_proc = subprocess.run(
                ["git", "status", "--short"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            if branch_proc.returncode != 0:
                return {"is_git_repo": False, "branch": "none", "modified_count": 0, "changed_files": []}

            branch = branch_proc.stdout.strip() or "detached"
            lines = [line.strip() for line in status_proc.stdout.splitlines() if line.strip()]
            return {
                "is_git_repo": True,
                "branch": branch,
                "modified_count": len(lines),
                "changed_files": lines[:10],
            }
        except Exception:
            return {"is_git_repo": False, "branch": "none", "modified_count": 0, "changed_files": []}

    def build_workspace_prompt_snippet(self) -> str:
        recent = self.recently_modified_files(limit=5)
        git = self.git_pulse()
        recent_str = ", ".join(f"{r['path']} ({r['modified_at']})" for r in recent) if recent else "No recent files."
        if git.get("is_git_repo"):
            git_str = f"Branch: {git['branch']} | Uncommitted changes: {git['modified_count']}"
        else:
            git_str = "Local directory (Git not initialized)"
        return (
            f"[Live Physical Workspace State (Stage 57)]:\n"
            f"- Git Status: {git_str}\n"
            f"- Recently Touched Files: {recent_str}"
        )

    def scan_workspace(self, limit: int = 6) -> dict[str, Any]:
        return {
            "stage": STAGE,
            "live_workspace_sensor": "active",
            "git": self.git_pulse(),
            "recent_files": self.recently_modified_files(limit=limit),
        }

    def status(self) -> dict[str, Any]:
        return self.scan_workspace(limit=5)
