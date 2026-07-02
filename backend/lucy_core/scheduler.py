"""
scheduler.py
Context-aware task ranking for Lucy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable


@dataclass
class ScheduledTask:
    task_id: str
    title: str
    priority: int = 3
    complexity: int = 3
    deadline: str | None = None
    project: str = "Lucy"
    status: str = "open"


class ContextScheduler:
    def rank(self, tasks: Iterable[ScheduledTask | dict], context: dict | None = None) -> list[dict]:
        context = context or {}
        energy = self._bounded_int(context.get("energy", 6), default=6)
        active_project = str(context.get("active_project", "Lucy"))

        ranked: list[dict] = []
        for raw_task in tasks:
            task = self._coerce_task(raw_task)
            if task.status != "open":
                continue

            score = float(task.priority) * 10
            reasons = [f"priority {task.priority}"]

            deadline_pressure = self._deadline_pressure(task.deadline)
            if deadline_pressure:
                score += deadline_pressure
                reasons.append(f"deadline pressure {deadline_pressure}")

            if task.project.lower() == active_project.lower():
                score += 8
                reasons.append("active project match")

            if energy < 5 and task.complexity > 3:
                penalty = (task.complexity - energy) * 4
                score -= penalty
                reasons.append("downranked for low energy/high complexity")
            elif energy >= 7 and task.complexity >= 4:
                score += 4
                reasons.append("energy supports complex work")

            score -= max(0, task.complexity - 1)
            ranked.append(
                {
                    "task_id": task.task_id,
                    "title": task.title,
                    "score": round(score, 2),
                    "priority_reason": "; ".join(reasons),
                    "recommended": False,
                    "project": task.project,
                    "complexity": task.complexity,
                }
            )

        ranked.sort(key=lambda item: item["score"], reverse=True)
        if ranked:
            ranked[0]["recommended"] = True
        return ranked

    def next_recommended(self, tasks: Iterable[ScheduledTask | dict], context: dict | None = None) -> dict | None:
        ranked = self.rank(tasks, context=context)
        return ranked[0] if ranked else None

    def _coerce_task(self, raw_task: ScheduledTask | dict) -> ScheduledTask:
        if isinstance(raw_task, ScheduledTask):
            return raw_task
        return ScheduledTask(
            task_id=str(raw_task.get("task_id") or raw_task.get("id") or "task_unknown"),
            title=str(raw_task.get("title") or raw_task.get("text") or "Untitled task"),
            priority=self._bounded_int(raw_task.get("priority", 3), default=3),
            complexity=self._bounded_int(raw_task.get("complexity", 3), default=3),
            deadline=raw_task.get("deadline") or raw_task.get("due"),
            project=str(raw_task.get("project") or raw_task.get("project_name") or "Lucy"),
            status=str(raw_task.get("status") or "open"),
        )

    def _bounded_int(self, value, default: int) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return default
        return max(1, min(number, 10))

    def _deadline_pressure(self, deadline: str | None) -> int:
        if not deadline:
            return 0
        try:
            target = datetime.fromisoformat(str(deadline).replace("Z", "+00:00")).date()
        except ValueError:
            try:
                target = date.fromisoformat(str(deadline))
            except ValueError:
                return 0
        days = (target - datetime.now(timezone.utc).date()).days
        if days < 0:
            return 12
        if days == 0:
            return 10
        if days <= 2:
            return 7
        if days <= 7:
            return 4
        return 0
