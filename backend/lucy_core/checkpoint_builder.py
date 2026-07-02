"""
checkpoint_builder.py
Safe batch checkpoint builder for Lucy.

This creates checkpoint records and local learning traces. It does not run
system commands, edit code, call paid APIs, or activate agents.
"""

from __future__ import annotations

import time


CHECKPOINT_FOCUS_AREAS = [
    {
        "name": "guardian",
        "reason": "Guardian safety boundary preserved.",
        "lesson": "Lucy should keep protected actions blocked while building.",
        "next_step": "Keep risky actions behind approval records.",
    },
    {
        "name": "memory",
        "reason": "Local memory remains the first source of truth.",
        "lesson": "Lucy should check local memory before using any external tool.",
        "next_step": "Prefer recall and memory audit before fallback.",
    },
    {
        "name": "projects",
        "reason": "Project tracker linked this checkpoint to Lucy.",
        "lesson": "Lucy should connect progress to the active project.",
        "next_step": "Keep tasks, summaries, and checkpoints aligned.",
    },
    {
        "name": "learning",
        "reason": "Local self-learning trace saved for this checkpoint.",
        "lesson": "Lucy can improve through saved lessons and proposals without self-modifying code.",
        "next_step": "Review checkpoint learning traces before promoting lessons.",
    },
    {
        "name": "api_tools",
        "reason": "External APIs remain tools, not Lucy's brain.",
        "lesson": "Lucy may use NVIDIA as fallback only after local memory misses.",
        "next_step": "Never store API keys or treat external output as truth by default.",
    },
    {
        "name": "desktop_ui",
        "reason": "Desktop UI path kept available for easier control.",
        "lesson": "Lucy should expose important controls without requiring long terminal sessions.",
        "next_step": "Use the desktop window for status, learning, health, and fallback commands.",
    },
    {
        "name": "health",
        "reason": "Runtime health remains part of the build loop.",
        "lesson": "Lucy should verify core files and safety flags after growth.",
        "next_step": "Run health checks after larger feature changes.",
    },
    {
        "name": "recovery",
        "reason": "Recovered checkpoint 023 reference remains separate from Lucy identity.",
        "lesson": "ELIE is a reference skeleton only, not Lucy herself.",
        "next_step": "Use recovered architecture as guidance, not as a replacement for source code.",
    },
    {
        "name": "operator_tools",
        "reason": "Safe operator tools stay read-only unless explicitly designed otherwise.",
        "lesson": "Lucy should inspect and summarize before taking action.",
        "next_step": "Keep file reads scoped to the project workspace.",
    },
    {
        "name": "overnight_run",
        "reason": "Overnight build mode saved progress without unsafe autonomy.",
        "lesson": "Long runs should create checkpoints and learning traces without executing risky actions.",
        "next_step": "Review the final health result and open proposals.",
    },
]


class CheckpointBuilder:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    def ensure_minimum(self, target_count: int = 100, pause_seconds: float = 0.0) -> dict:
        target = max(1, min(int(target_count), 500))
        pause = max(0.0, min(float(pause_seconds), 5.0))
        start_count = self.runtime.checkpoints.count()

        before_health = self.runtime.health()
        created: list[dict] = []
        learning_traces = 0

        while self.runtime.checkpoints.count() < target:
            next_number = self.runtime.checkpoints.count() + 1
            focus = CHECKPOINT_FOCUS_AREAS[(next_number - 1) % len(CHECKPOINT_FOCUS_AREAS)]
            checkpoint = self.runtime.create_checkpoint(
                reason=f"Overnight checkpoint {next_number:04d}: {focus['reason']}",
                files_changed_summary=(
                    "Batch checkpoint record created by Lucy's safe checkpoint builder. "
                    "No code or system files were changed by this checkpoint step."
                ),
                safety_status="safe_local_checkpoint_record",
                next_step=focus["next_step"],
            )
            trace = self.runtime.learning.record_checkpoint_learning(
                checkpoint,
                f"{focus['lesson']} Focus area: {focus['name']}.",
            )
            learning_traces += 1 if trace else 0
            created.append(
                {
                    "checkpoint_id": checkpoint["checkpoint_id"],
                    "focus": focus["name"],
                    "reason": checkpoint["reason"],
                }
            )
            if pause:
                time.sleep(pause)

        after_health = self.runtime.health()
        final_count = self.runtime.checkpoints.count()

        if created:
            self.runtime.learning.add_proposal(
                "Overnight checkpoint run complete",
                (
                    f"Lucy created {len(created)} checkpoint records, reached {final_count} total "
                    f"checkpoints, and saved {learning_traces} checkpoint learning traces. "
                    "Review health, learning status, and project summary before the next build."
                ),
                source="checkpoint_builder",
            )

        return {
            "target": target,
            "start_count": start_count,
            "final_count": final_count,
            "created_count": len(created),
            "learning_traces": learning_traces,
            "before_health_passed": before_health.all_passed,
            "after_health_passed": after_health.all_passed,
            "fallback_learning": "local_checkpoint_learning_no_automatic_api_calls",
            "created": created,
        }
