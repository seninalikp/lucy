"""
proactive_briefer.py
Stage 58 = Proactive Session Briefer & Autonomous Follow-Through Engine.

Synthesizes Senin's active project tasks, temporal memory graph highlights,
recent workspace file edits, and last session recap into an immediate, grounded
executive briefing on startup or when asked `brief me` / `what now`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


STAGE = "58 proactive session briefer"


class ProactiveSessionBriefer:
    def __init__(self, runtime: Any) -> None:
        self.runtime = runtime

    def generate_brief(self) -> dict[str, Any]:
        proj = self.runtime.project_summary()
        open_tasks = proj.get("open_tasks", [])
        prof_status = self.runtime.personal_profiler.status()
        pace = prof_status.get("current_pace") or prof_status.get("current_mood_or_pace", "focused_operational")

        recent_files = []
        if hasattr(self.runtime, "workspace_sensor"):
            recent_files = self.runtime.workspace_sensor.recently_modified_files(limit=4)

        pinned_memories = []
        if hasattr(self.runtime, "memory_graph"):
            pinned_memories = self.runtime.memory_graph.query("", limit=4)

        recap = self.runtime.conversational_memory.get_session_recap()

        lines = [
            f"=== LUCY EXECUTIVE SESSION BRIEF ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}) ===",
            f"- Operator Pace:  {pace}",
            f"- Active Project: {proj.get('name', 'Lucy')} ({len(open_tasks)} open tasks)",
            f"- Primary Focus:  {proj.get('next_action', 'Ready for instruction.')}",
        ]

        if open_tasks:
            lines.append("\n[Priority Open Tasks]:")
            for t in open_tasks[:4]:
                t_id = t.get("id", "task") if isinstance(t, dict) else "task"
                t_text = t.get("text", str(t)) if isinstance(t, dict) else str(t)
                lines.append(f"  - [{t_id}] {t_text}")

        if recent_files:
            lines.append("\n[Recently Modified Workspace Files]:")
            for rf in recent_files:
                lines.append(f"  - {rf['path']} ({rf['modified_at']})")

        if pinned_memories:
            lines.append("\n[Active Memory Graph Nodes]:")
            for pm in pinned_memories[:3]:
                lines.append(f"  - [{pm['id']}] {pm['fact']}")

        if recap.get("has_history"):
            lines.append(f"\n[Last Session Continuity]:\n  {recap.get('recap_text')}")

        first_task = (
            open_tasks[0].get("text", str(open_tasks[0]))
            if (open_tasks and isinstance(open_tasks[0], dict))
            else (str(open_tasks[0]) if open_tasks else "")
        )
        recommended_next = (
            f"Finish task `{first_task}`"
            if open_tasks
            else "Run `workspace pulse` or tell me what feature we are building next."
        )
        lines.append(f"\n-> Recommended Immediate Step: {recommended_next}")

        return {
            "stage": STAGE,
            "brief_text": "\n".join(lines),
            "open_tasks_count": len(open_tasks),
            "recent_files_count": len(recent_files),
            "recommended_next": recommended_next,
        }

    def status(self) -> dict[str, Any]:
        return {
            "stage": STAGE,
            "proactive_briefer": "active",
        }
