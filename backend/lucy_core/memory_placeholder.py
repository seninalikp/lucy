"""
memory_placeholder.py
Safe placeholder for Lucy's future memory system.

Rules enforced here:
- No raw personal memory dumps
- No sensitive data stored automatically
- Only approved lessons can enter Lucy
- Agent raw logs stay inside agents
- Reports come before approved Lucy lessons
"""

import json
from datetime import datetime, timezone
from pathlib import Path


MEMORY_RULES = {
    "version": "0.1.0",
    "mode": "approved_lessons_only_placeholder",
    "rules": [
        "No raw personal data may be stored automatically.",
        "No sensitive data (credentials, keys, health info) may be stored.",
        "Only lessons explicitly approved by the user may enter Lucy memory.",
        "Agent raw logs stay local to each agent — not dumped into Lucy.",
        "Agent reports are submitted first; lessons extracted after review.",
        "Memory cannot be cleared, wiped, or overwritten without approval.",
        "Memory rules themselves cannot be changed without approval + checkpoint.",
    ],
    "approved_lessons_allowed": True,
    "raw_memory_dump_allowed": False,
    "sensitive_data_allowed": False,
    "agent_log_injection_allowed": False,
}

APPROVED_LESSONS_TEMPLATE = {
    "version": "0.1.0",
    "lessons": [],
    "note": (
        "This file will hold only lessons that have been explicitly reviewed "
        "and approved. It is empty until the first lesson is approved."
    ),
}


class MemoryPlaceholder:
    def __init__(self, memory_dir: Path) -> None:
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.rules_file = memory_dir / "memory_rules.json"
        self.lessons_file = memory_dir / "approved_lessons.json"
        self._ensure_files()

    def _ensure_files(self) -> None:
        if not self.rules_file.exists():
            self.rules_file.write_text(
                json.dumps(MEMORY_RULES, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        if not self.lessons_file.exists():
            self.lessons_file.write_text(
                json.dumps(APPROVED_LESSONS_TEMPLATE, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def get_rules(self) -> dict:
        try:
            return json.loads(self.rules_file.read_text(encoding="utf-8"))
        except Exception:
            return dict(MEMORY_RULES)

    def get_lesson_count(self) -> int:
        try:
            data = json.loads(self.lessons_file.read_text(encoding="utf-8"))
            return len(data.get("lessons", []))
        except Exception:
            return 0

    def status(self) -> str:
        count = self.get_lesson_count()
        return (
            f"Memory placeholder active. Mode: approved_lessons_only. "
            f"Approved lessons: {count}. Raw dumps: disabled."
        )
