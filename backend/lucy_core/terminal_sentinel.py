"""
backend/lucy_core/terminal_sentinel.py
Stage 74: Proactive Terminal Sentinel & Non-Intrusive Status Broadcaster

Provides a lightweight, non-intrusive terminal pulse banner and workspace delta
audit for Lucy's sovereign CLI runtime without voice, UI, or intrusive spam.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

STAGE: int = 74


@dataclass
class FileDelta:
    path: str
    change_type: str  # "added", "modified", "deleted"
    mtime: float
    size: int


@dataclass
class SentinelPulse:
    timestamp: str
    git_branch: str
    git_dirty: bool
    git_changed_count: int
    ollama_online: bool
    ollama_model: str
    memory_nodes_count: int
    background_tasks_count: int
    synthesized_tools_count: int
    workspace_delta_count: int

    def to_one_line(self) -> str:
        git_status = f"{self.git_branch}*" if self.git_dirty else self.git_branch
        ollama_status = "Ollama:OK" if self.ollama_online else "Ollama:OFFLINE"
        return (
            f"[SENTINEL | {git_status} | {ollama_status} | MemNodes:{self.memory_nodes_count} "
            f"| Tools:{self.synthesized_tools_count} | Delta:{self.workspace_delta_count}]"
        )


class TerminalSentinel:
    """
    Tracks workspace deltas, checks local runtime health, and formats compact,
    non-intrusive status broadcasts for sovereign terminal interaction.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        runtime: Optional[Any] = None,
        receipt_ledger: Optional[Any] = None,
    ) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.runtime = runtime
        self.receipt_ledger = receipt_ledger
        self.banner_enabled: bool = False  # Off by default for clean non-intrusive terminal
        self._file_snapshots: Dict[str, float] = {}  # rel_path -> mtime
        self._last_pulse: Optional[SentinelPulse] = None

        self._ignore_dirs: Set[str] = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "venv",
            ".venv",
            "archive",
            "dumps",
            "node_modules",
        }
        self.take_snapshot()

    def take_snapshot(self) -> int:
        """
        Takes a fast mtime snapshot of tracked workspace files.
        """
        new_snap: Dict[str, float] = {}
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self._ignore_dirs]
            for f in files:
                if f.endswith((".pyc", ".pyo", ".tmp")):
                    continue
                fpath = Path(root) / f
                try:
                    rel = str(fpath.relative_to(self.project_root))
                    new_snap[rel] = fpath.stat().st_mtime
                except Exception:
                    pass
        self._file_snapshots = new_snap
        return len(self._file_snapshots)

    def detect_workspace_deltas(self) -> List[FileDelta]:
        """
        Computes files added, modified, or deleted since the last snapshot.
        """
        deltas: List[FileDelta] = []
        current_files: Dict[str, float] = {}

        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self._ignore_dirs]
            for f in files:
                if f.endswith((".pyc", ".pyo", ".tmp")):
                    continue
                fpath = Path(root) / f
                try:
                    rel = str(fpath.relative_to(self.project_root))
                    mtime = fpath.stat().st_mtime
                    size = fpath.stat().st_size
                    current_files[rel] = mtime

                    if rel not in self._file_snapshots:
                        deltas.append(FileDelta(path=rel, change_type="added", mtime=mtime, size=size))
                    elif mtime > self._file_snapshots[rel] + 0.001:
                        deltas.append(FileDelta(path=rel, change_type="modified", mtime=mtime, size=size))
                except Exception:
                    pass

        for prev_rel in self._file_snapshots:
            if prev_rel not in current_files:
                deltas.append(FileDelta(path=prev_rel, change_type="deleted", mtime=time.time(), size=0))

        return deltas

    def check_git_status(self) -> Dict[str, Any]:
        """
        Retrieves branch name and dirty file count safely without hanging.
        """
        try:
            branch_proc = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=1.5,
            )
            branch = branch_proc.stdout.strip() or "detached"

            status_proc = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=1.5,
            )
            dirty_lines = [l for l in status_proc.stdout.splitlines() if l.strip()]
            return {
                "branch": branch,
                "dirty": len(dirty_lines) > 0,
                "changed_count": len(dirty_lines),
            }
        except Exception:
            return {
                "branch": "local",
                "dirty": False,
                "changed_count": 0,
            }

    def check_ollama_health(self) -> Dict[str, Any]:
        """
        Probes local Ollama instance with short 500ms timeout.
        """
        try:
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags", headers={"User-Agent": "LucySentinel"})
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", [])]
                    primary = "qwen2.5:3b" if "qwen2.5:3b" in str(models) else (models[0] if models else "online")
                    return {"online": True, "model": primary}
        except Exception:
            pass
        return {"online": False, "model": "offline"}

    def pulse(self) -> SentinelPulse:
        """
        Gathers current system telemetry and builds a SentinelPulse record.
        """
        git_info = self.check_git_status()
        ollama_info = self.check_ollama_health()
        deltas = self.detect_workspace_deltas()

        mem_count = 0
        tasks_count = 0
        tools_count = 0

        if self.runtime is not None:
            if hasattr(self.runtime, "memory_graph"):
                try:
                    mem_count = len(self.runtime.memory_graph._read().get("nodes", []))
                except Exception:
                    pass
            if hasattr(self.runtime, "task_daemon"):
                try:
                    tasks_count = len(self.runtime.task_daemon.list_tasks(status="running"))
                except Exception:
                    pass
            if hasattr(self.runtime, "tool_synthesizer"):
                try:
                    tools_count = len(self.runtime.tool_synthesizer.tools)
                except Exception:
                    pass

        p = SentinelPulse(
            timestamp=datetime.now().isoformat(),
            git_branch=git_info["branch"],
            git_dirty=git_info["dirty"],
            git_changed_count=git_info["changed_count"],
            ollama_online=ollama_info["online"],
            ollama_model=ollama_info["model"],
            memory_nodes_count=mem_count,
            background_tasks_count=tasks_count,
            synthesized_tools_count=tools_count,
            workspace_delta_count=len(deltas),
        )
        self._last_pulse = p
        return p

    def toggle_banner(self) -> bool:
        self.banner_enabled = not self.banner_enabled
        return self.banner_enabled

    def format_terminal_dashboard(self) -> str:
        """
        Renders an ASCII-safe detailed dashboard for /sentinel terminal command.
        """
        p = self.pulse()
        deltas = self.detect_workspace_deltas()

        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| LUCY TERMINAL SENTINEL DASHBOARD (STAGE 74)                          |")
        lines.append("+----------------------------------------------------------------------+")
        lines.append(f"| Timestamp: {p.timestamp:<57} |")
        lines.append(f"| Git Branch: {p.git_branch:<24} | Dirty Tree: {str(p.git_dirty):<23} |")
        lines.append(f"| Ollama: {('ONLINE (' + p.ollama_model + ')') if p.ollama_online else 'OFFLINE':<28} | Active Tasks: {p.background_tasks_count:<21} |")
        lines.append(f"| Memory Nodes: {p.memory_nodes_count:<22} | Synthesized Tools: {p.synthesized_tools_count:<16} |")
        lines.append(f"| Workspace Deltas: {len(deltas):<18} | Auto-Pulse Banner: {('ENABLED' if self.banner_enabled else 'DISABLED'):<16} |")
        lines.append("+----------------------------------------------------------------------+")

        if deltas:
            lines.append("| RECENT WORKSPACE FILE DELTAS:                                        |")
            lines.append("+----------------------+------------+---------------------------------+")
            lines.append(f"| {'CHANGE':<20} | {'TYPE':<10} | {'PATH':<31} |")
            lines.append("+----------------------+------------+---------------------------------+")
            for d in deltas[:10]:
                lines.append(f"| {d.change_type.upper():<20} | {d.change_type:<10} | {d.path[-31:]:<31} |")
            if len(deltas) > 10:
                lines.append(f"| ... and {len(deltas) - 10} more files changed                                     |")
            lines.append("+----------------------------------------------------------------------+")
        else:
            lines.append("| Workspace files in sync with last snapshot.                          |")
            lines.append("+----------------------------------------------------------------------+")

        return "\n".join(lines)

    def format_diff_list(self) -> str:
        deltas = self.detect_workspace_deltas()
        if not deltas:
            return "No workspace file changes detected since last snapshot."
        lines = [f"Workspace Deltas ({len(deltas)} changes):"]
        for d in deltas:
            dt_str = datetime.fromtimestamp(d.mtime).strftime("%H:%M:%S")
            lines.append(f"  [{d.change_type.upper()}] {d.path} ({d.size} bytes, {dt_str})")
        return "\n".join(lines)
