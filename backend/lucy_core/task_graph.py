"""
backend/lucy_core/task_graph.py
Stage 80: Multi-Turn Operator Goal Decomposition & Task Graph Engine

Provides acyclic dependency task graph (DAG) decomposition, multi-turn progress
tracking, prerequisite resolution, and persistent goal resumability for Lucy's
sovereign terminal CLI.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

STAGE: int = 80


@dataclass
class TaskNode:
    task_id: str
    title: str
    description: str
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, BLOCKED, SKIPPED
    dependencies: List[str] = field(default_factory=list)
    assigned_tool: Optional[str] = None
    output_summary: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskNode:
        return cls(
            task_id=data.get("task_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=data.get("status", "PENDING"),
            dependencies=data.get("dependencies", []),
            assigned_tool=data.get("assigned_tool"),
            output_summary=data.get("output_summary"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at"),
        )


@dataclass
class GoalDAG:
    goal_id: str
    goal_description: str
    created_at: str
    updated_at: str
    nodes: Dict[str, TaskNode] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "goal_description": self.goal_description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "nodes": {tid: node.to_dict() for tid, node in self.nodes.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GoalDAG:
        nodes = {}
        for tid, n_raw in data.get("nodes", {}).items():
            nodes[tid] = TaskNode.from_dict(n_raw)
        return cls(
            goal_id=data.get("goal_id", ""),
            goal_description=data.get("goal_description", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            nodes=nodes,
        )

    def add_task(
        self,
        title: str,
        description: str = "",
        dependencies: Optional[List[str]] = None,
        assigned_tool: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> TaskNode:
        tid = task_id or f"t{len(self.nodes) + 1}"
        node = TaskNode(
            task_id=tid,
            title=title.strip(),
            description=description.strip() or title.strip(),
            status="PENDING",
            dependencies=dependencies or [],
            assigned_tool=assigned_tool,
        )
        self.nodes[tid] = node
        self.updated_at = datetime.now().isoformat()
        return node

    def get_ready_tasks(self) -> List[TaskNode]:
        """Returns tasks that are PENDING and have all prerequisites COMPLETED."""
        completed_ids = {tid for tid, n in self.nodes.items() if n.status == "COMPLETED"}
        ready: List[TaskNode] = []
        for node in self.nodes.values():
            if node.status in ("PENDING", "IN_PROGRESS"):
                # Check if all dependencies are completed
                if all(dep in completed_ids for dep in node.dependencies):
                    ready.append(node)
        return ready

    def mark_completed(self, task_id: str, summary: str = "") -> bool:
        if task_id not in self.nodes:
            return False
        node = self.nodes[task_id]
        node.status = "COMPLETED"
        node.completed_at = datetime.now().isoformat()
        if summary:
            node.output_summary = summary.strip()
        self.updated_at = datetime.now().isoformat()
        return True

    def mark_in_progress(self, task_id: str) -> bool:
        if task_id not in self.nodes:
            return False
        self.nodes[task_id].status = "IN_PROGRESS"
        self.updated_at = datetime.now().isoformat()
        return True

    def progress_percent(self) -> int:
        if not self.nodes:
            return 100
        done = sum(1 for n in self.nodes.values() if n.status in ("COMPLETED", "SKIPPED"))
        return int((done / len(self.nodes)) * 100.0)

    def is_all_completed(self) -> bool:
        if not self.nodes:
            return True
        return all(n.status in ("COMPLETED", "SKIPPED") for n in self.nodes.values())

    def format_terminal_summary(self) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| PROJECT TASK GRAPH & GOAL DAG (STAGE 80)                             |")
        lines.append("+----------------------------------------------------------------------+")
        desc = self.goal_description[:45]
        pct = self.progress_percent()
        done_count = sum(1 for n in self.nodes.values() if n.status == "COMPLETED")
        total_count = len(self.nodes)

        # Progress bar
        bar_len = 16
        filled = int((pct / 100.0) * bar_len)
        bar_str = "[" + "=" * filled + (" " * (bar_len - filled)) + "]"

        lines.append(f"| Goal: {desc:<46} | Progress: {pct:>3}% {bar_str} |")
        lines.append(f"| Tasks: {done_count}/{total_count} Completed{'':<43} |")
        lines.append("+----------------------------------------------------------------------+")
        lines.append(f"| {'STATUS':<7} | {'ID':<4} | {'TASK TITLE':<35} | {'DEPS':<12} |")
        lines.append("+---------+------+-------------------------------------+--------------+")

        status_icons = {
            "COMPLETED": "[X]",
            "IN_PROGRESS": "[>]",
            "PENDING": "[ ]",
            "BLOCKED": "[!]",
            "SKIPPED": "[-]",
        }

        ready_ids = {t.task_id for t in self.get_ready_tasks()}
        for node in self.nodes.values():
            icon = status_icons.get(node.status, "[ ]")
            if node.status == "PENDING" and node.task_id in ready_ids:
                icon = "[*]"  # Ready to run
            deps_str = ",".join(node.dependencies) or "none"
            lines.append(f"| {icon:<7} | {node.task_id:<4} | {node.title[:35]:<35} | {deps_str[:12]:<12} |")

        lines.append("+---------+------+-------------------------------------+--------------+")
        ready = self.get_ready_tasks()
        if ready:
            next_t = ready[0]
            lines.append(f"| NEXT READY STEP: [{next_t.task_id}] {next_t.title[:45]:<45} |")
            lines.append("+----------------------------------------------------------------------+")
        elif self.is_all_completed():
            lines.append("|  (Goal fully completed. All tasks executed successfully.)            |")
            lines.append("+----------------------------------------------------------------------+")

        return "\n".join(lines)


class GoalTaskGraphEngine:
    """
    Manages decomposing user intentions into TaskNodes, tracking active DAG execution,
    and persisting goal states across turns.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        storage_file: Optional[Path] = None,
        receipt_ledger: Optional[Any] = None,
    ) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.storage_file = storage_file or (self.project_root / "data" / "lucy" / "active_goal_dag.json")
        self.receipt_ledger = receipt_ledger

        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.active_dag: Optional[GoalDAG] = None
        self._load()

    def _load(self) -> None:
        if not self.storage_file.exists():
            return
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if raw:
                self.active_dag = GoalDAG.from_dict(raw)
        except Exception:
            self.active_dag = None

    def _save(self) -> None:
        try:
            if self.active_dag is None:
                if self.storage_file.exists():
                    self.storage_file.unlink()
                return
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self.active_dag.to_dict(), f, indent=2)
        except Exception:
            pass

    def create_plan(self, goal_description: str) -> GoalDAG:
        """
        Decomposes a goal string into a structured dependency DAG.
        """
        dag = GoalDAG(
            goal_id=f"goal_{uuid.uuid4().hex[:8]}",
            goal_description=goal_description.strip(),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        # Check for numbered or bulleted steps
        step_pattern = re.compile(r"(?:^|\n)(?:\d+[\.\)]|\*|\-)\s*([^\n]+)")
        extracted_steps = step_pattern.findall(goal_description)

        if len(extracted_steps) >= 2:
            prev_id: Optional[str] = None
            for idx, step_text in enumerate(extracted_steps, start=1):
                tid = f"t{idx}"
                deps = [prev_id] if prev_id else []
                dag.add_task(
                    title=step_text.strip(),
                    dependencies=deps,
                    task_id=tid,
                )
                prev_id = tid
        else:
            # Default structured software engineering pipeline decomposition
            t1 = dag.add_task(
                title=f"Analyze requirements & symbols: {goal_description[:30]}",
                dependencies=[],
                assigned_tool="codebase_indexer",
                task_id="t1",
            )
            t2 = dag.add_task(
                title=f"Draft & execute atomic patch",
                dependencies=["t1"],
                assigned_tool="atomic_patcher",
                task_id="t2",
            )
            t3 = dag.add_task(
                title=f"Run regression triage test suite",
                dependencies=["t2"],
                assigned_tool="test_triage",
                task_id="t3",
            )
            t4 = dag.add_task(
                title=f"Perform code review & commit proposal",
                dependencies=["t3"],
                assigned_tool="code_reviewer",
                task_id="t4",
            )

        self.active_dag = dag
        self._save()

        if self.receipt_ledger is not None:
            try:
                self.receipt_ledger.issue_receipt(
                    action_category="goal_decomposition",
                    operation="create_plan",
                    target=dag.goal_id,
                    verified_outcome=f"Decomposed goal into {len(dag.nodes)} steps",
                )
            except Exception:
                pass

        return dag

    def complete_task(self, task_id: str, summary: str = "") -> Tuple[bool, str]:
        if not self.active_dag:
            return False, "No active goal plan to update."
        ok = self.active_dag.mark_completed(task_id, summary=summary)
        if not ok:
            return False, f"Task '{task_id}' not found in active plan."
        self._save()

        if self.receipt_ledger is not None:
            try:
                self.receipt_ledger.issue_receipt(
                    action_category="goal_progress",
                    operation="complete_task",
                    target=task_id,
                    verified_outcome=f"Completed task {task_id}: {summary or 'Done'}",
                )
            except Exception:
                pass

        ready = self.active_dag.get_ready_tasks()
        next_hint = f" Next ready task: [{ready[0].task_id}] {ready[0].title}" if ready else " All tasks completed!"
        return True, f"Completed task {task_id}.{next_hint}"

    def get_next_task(self) -> Optional[TaskNode]:
        if not self.active_dag:
            return None
        ready = self.active_dag.get_ready_tasks()
        return ready[0] if ready else None

    def clear_plan(self) -> bool:
        self.active_dag = None
        self._save()
        return True

    def format_terminal_summary(self) -> str:
        if not self.active_dag:
            lines = []
            lines.append("+----------------------------------------------------------------------+")
            lines.append("| PROJECT TASK GRAPH & GOAL DAG (STAGE 80)                             |")
            lines.append("+----------------------------------------------------------------------+")
            lines.append("|  (No active goal plan. Use /plan <goal description> to initialize.)  |")
            lines.append("+----------------------------------------------------------------------+")
            return "\n".join(lines)
        return self.active_dag.format_terminal_summary()
