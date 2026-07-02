"""
projects.py
Local project tracker for Lucy.

The tracker keeps one active project, simple tasks, notes, and checkpoints.
It stores JSON only and does not perform file or system actions.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


PROJECTS_VERSION = "0.2.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectTracker:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.lucy_data_dir.mkdir(parents=True, exist_ok=True)
        self.projects_file = self.lucy_data_dir / "projects.json"
        self._ensure_file()

    def _default_data(self) -> dict:
        return {
            "version": PROJECTS_VERSION,
            "active_project": "Lucy",
            "created_at": _now(),
            "updated_at": _now(),
            "projects": {
                "Lucy": {
                    "name": "Lucy",
                    "status": "active_foundation",
                    "summary": (
                        "Local-first JARVIS-style operating assistant foundation. "
                        "Focused on safety, memory, projects, logs, and terminal use."
                    ),
                    "next_action": "Stabilize Checkpoint 1 with tests and logs.",
                    "notes": [],
                    "tasks": [
                        {
                            "id": "task_0001",
                            "text": "Restore Lucy backup into the local project folder.",
                            "status": "done",
                            "created_at": _now(),
                            "completed_at": _now(),
                        },
                        {
                            "id": "task_0002",
                            "text": "Build local memory, project tracker, router, and terminal chat.",
                            "status": "open",
                            "created_at": _now(),
                            "completed_at": None,
                        },
                    ],
                    "checkpoints": [],
                    "updated_at": _now(),
                }
            },
        }

    def _ensure_file(self) -> None:
        if not self.projects_file.exists():
            self._write(self._default_data())

    def _read(self) -> dict:
        try:
            data = json.loads(self.projects_file.read_text(encoding="utf-8"))
        except Exception:
            data = self._default_data()
        data.setdefault("version", PROJECTS_VERSION)
        data.setdefault("active_project", "Lucy")
        data.setdefault("projects", {})
        if "Lucy" not in data["projects"]:
            data["projects"]["Lucy"] = self._default_data()["projects"]["Lucy"]
        return data

    def _write(self, data: dict) -> None:
        data["updated_at"] = _now()
        self.projects_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _next_task_id(self, tasks: list[dict]) -> str:
        highest = 0
        for task in tasks:
            raw_id = str(task.get("id", ""))
            if raw_id.startswith("task_"):
                try:
                    highest = max(highest, int(raw_id.split("_", 1)[1]))
                except ValueError:
                    continue
        return f"task_{highest + 1:04d}"

    def _get_project(self, data: dict, name: str | None = None) -> dict:
        project_name = (name or data.get("active_project") or "Lucy").strip()
        projects = data["projects"]
        if project_name not in projects:
            projects[project_name] = {
                "name": project_name,
                "status": "active",
                "summary": "",
                "next_action": "",
                "notes": [],
                "tasks": [],
                "checkpoints": [],
                "updated_at": _now(),
            }
        return projects[project_name]

    def list_projects(self) -> list[dict]:
        data = self._read()
        active_name = data.get("active_project", "Lucy")
        result = []
        for project in data["projects"].values():
            tasks = project.get("tasks", [])
            open_count = sum(1 for task in tasks if task.get("status") == "open")
            done_count = sum(1 for task in tasks if task.get("status") == "done")
            result.append(
                {
                    "name": project.get("name", "Unknown"),
                    "status": project.get("status", "unknown"),
                    "active": project.get("name") == active_name,
                    "open_tasks": open_count,
                    "done_tasks": done_count,
                    "next_action": project.get("next_action", ""),
                }
            )
        return sorted(result, key=lambda item: (not item["active"], item["name"].lower()))

    def set_active_project(self, name: str) -> dict:
        cleaned = name.strip()
        if not cleaned:
            return {"changed": False, "reason": "Project name was empty."}
        data = self._read()
        project = self._get_project(data, cleaned)
        data["active_project"] = project["name"]
        project["updated_at"] = _now()
        self._write(data)
        return {"changed": True, "project": project}

    def add_task(self, text: str, project_name: str | None = None) -> dict:
        cleaned = text.strip()
        if not cleaned:
            return {"added": False, "reason": "Task text was empty."}
        data = self._read()
        project = self._get_project(data, project_name)
        task = {
            "id": self._next_task_id(project.setdefault("tasks", [])),
            "text": cleaned,
            "status": "open",
            "created_at": _now(),
            "completed_at": None,
        }
        project["tasks"].append(task)
        project["next_action"] = cleaned
        project["updated_at"] = _now()
        self._write(data)
        return {"added": True, "project": project["name"], "task": task}

    def complete_task(self, selector: str, project_name: str | None = None) -> dict:
        cleaned = selector.strip()
        if not cleaned:
            return {"completed": False, "reason": "Tell me which task to complete."}
        data = self._read()
        project = self._get_project(data, project_name)
        open_tasks = [task for task in project.get("tasks", []) if task.get("status") == "open"]

        selected: dict | None = None
        if cleaned.isdigit():
            index = int(cleaned) - 1
            if 0 <= index < len(open_tasks):
                selected = open_tasks[index]
        else:
            lowered = cleaned.lower()
            for task in open_tasks:
                if cleaned == task.get("id") or lowered in task.get("text", "").lower():
                    selected = task
                    break

        if selected is None:
            return {"completed": False, "reason": "No matching open task found."}

        selected["status"] = "done"
        selected["completed_at"] = _now()
        project["updated_at"] = _now()

        remaining = [task for task in project.get("tasks", []) if task.get("status") == "open"]
        project["next_action"] = remaining[0]["text"] if remaining else "Review project status and choose the next step."
        self._write(data)
        return {"completed": True, "project": project["name"], "task": selected}

    def show_tasks(self, project_name: str | None = None, include_done: bool = False) -> dict:
        data = self._read()
        project = self._get_project(data, project_name)
        tasks = project.get("tasks", [])
        if not include_done:
            tasks = [task for task in tasks if task.get("status") == "open"]
        return {"project": project["name"], "tasks": tasks}

    def summary(self, project_name: str | None = None) -> dict:
        data = self._read()
        project = self._get_project(data, project_name)
        tasks = project.get("tasks", [])
        open_tasks = [task for task in tasks if task.get("status") == "open"]
        done_tasks = [task for task in tasks if task.get("status") == "done"]
        return {
            "name": project["name"],
            "status": project.get("status", "unknown"),
            "summary": project.get("summary", ""),
            "next_action": project.get("next_action", ""),
            "open_tasks": open_tasks,
            "done_tasks": done_tasks,
            "checkpoints": project.get("checkpoints", []),
        }

    def add_checkpoint(self, checkpoint_id: str, reason: str, project_name: str | None = None) -> None:
        data = self._read()
        project = self._get_project(data, project_name)
        project.setdefault("checkpoints", []).append(
            {
                "checkpoint_id": checkpoint_id,
                "reason": reason,
                "timestamp": _now(),
            }
        )
        project["updated_at"] = _now()
        self._write(data)

    def daily_brief(self) -> dict:
        data = self._read()
        project = self._get_project(data)
        tasks = [task for task in project.get("tasks", []) if task.get("status") == "open"]
        return {
            "active_project": project["name"],
            "status": project.get("status", "unknown"),
            "next_action": project.get("next_action", ""),
            "top_tasks": tasks[:5],
            "project_count": len(data.get("projects", {})),
        }
