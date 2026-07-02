"""
cognition.py
Transparent local cognition state for Lucy.

This is not consciousness. It gives Lucy persistent vision, drives, and working
reflections so her responses have continuity without pretending to be alive.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


COGNITION_VERSION = "0.1.0"
MAX_REFLECTIONS = 80

SENSITIVE_TERMS = {
    "api key",
    "password",
    "private key",
    "seed phrase",
    "wallet",
    "otp",
    "token",
    "secret",
    "credential",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(text: str, limit: int = 500) -> tuple[str, bool]:
    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    lowered = cleaned.lower()
    if any(term in lowered for term in SENSITIVE_TERMS):
        return "[redacted-sensitive-cognition-input]", True
    cleaned = re.sub(r"sk-[A-Za-z0-9]{20,}", "[redacted-token]", cleaned)
    cleaned = re.sub(r"gsk_[A-Za-z0-9_\-]+", "[redacted-token]", cleaned)
    cleaned = re.sub(r"AIza[A-Za-z0-9_\-]+", "[redacted-token]", cleaned)
    return cleaned[:limit], False


class CognitionCore:
    def __init__(self, cognition_dir: Path) -> None:
        self.cognition_dir = cognition_dir
        self.cognition_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.cognition_dir / "inner_state.json"
        self._ensure_file()

    def _default_state(self) -> dict:
        return {
            "version": COGNITION_VERSION,
            "mode": "transparent_local_cognition_not_consciousness",
            "created_at": _now(),
            "updated_at": _now(),
            "vision": {
                "north_star": "Become a stable local operating assistant for Senin: useful, careful, and grounded.",
                "identity_boundary": "Lucy is not ELIE, Ray, ARES, VANTA, LEDGER, or HAVEN. Agents stay separate.",
                "build_philosophy": "Foundation first. Guardian before tools. Memory before personality. Projects before agents.",
            },
            "drives": [
                "Protect Senin's files, secrets, money, and attention.",
                "Remember durable preferences and project facts only when safe.",
                "Prefer clear next actions over hype.",
                "Stay local and testable before becoming powerful.",
                "Use external providers as tools, not identity.",
            ],
            "current_focus": {
                "project": "Lucy",
                "next_action": "Stabilize memory, Guardian, project context, and chat continuity.",
                "risk": "Do not fake consciousness or activate unsafe autonomy.",
            },
            "reflections": [],
        }

    def _ensure_file(self) -> None:
        if not self.state_file.exists():
            self._write(self._default_state())

    def _read(self) -> dict:
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            data = self._default_state()
        default = self._default_state()
        data.setdefault("version", COGNITION_VERSION)
        data.setdefault("mode", default["mode"])
        data.setdefault("vision", default["vision"])
        data.setdefault("drives", default["drives"])
        data.setdefault("current_focus", default["current_focus"])
        data.setdefault("reflections", [])
        return data

    def _write(self, data: dict) -> None:
        data["updated_at"] = _now()
        self.state_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def status(self) -> dict:
        data = self._read()
        return {
            "file": str(self.state_file),
            "mode": data.get("mode"),
            "vision": data.get("vision", {}),
            "drives": data.get("drives", []),
            "current_focus": data.get("current_focus", {}),
            "reflection_count": len(data.get("reflections", [])),
            "latest_reflections": data.get("reflections", [])[-5:],
            "updated_at": data.get("updated_at"),
        }

    def vision(self) -> dict:
        data = self._read()
        return {
            "vision": data.get("vision", {}),
            "drives": data.get("drives", []),
            "current_focus": data.get("current_focus", {}),
        }

    def reflect(self, trigger: str, user_text: str, context: dict) -> dict:
        data = self._read()
        project = context.get("project", {})
        memory = context.get("memory", {})
        knowledge = context.get("knowledge", {})
        open_tasks = project.get("open_tasks", [])

        cleaned_user, redacted = _clean(user_text)
        focus = {
            "project": project.get("name", "Lucy"),
            "next_action": project.get("next_action") or self._infer_next_action(project, memory, knowledge),
            "risk": self._infer_risk(cleaned_user, context),
        }
        data["current_focus"] = focus

        thought = {
            "id": f"thought_{len(data.get('reflections', [])) + 1:04d}",
            "timestamp": _now(),
            "trigger": trigger,
            "user_signal": cleaned_user[:240],
            "redacted": redacted,
            "observation": self._observation(project, memory, knowledge),
            "priority": focus["next_action"],
            "boundary": focus["risk"],
            "open_task_count": len(open_tasks),
        }
        data["reflections"].append(thought)
        data["reflections"] = data["reflections"][-MAX_REFLECTIONS:]
        self._write(data)
        return thought

    def inner_prompt(self, limit: int = 3) -> str:
        data = self._read()
        vision = data.get("vision", {})
        focus = data.get("current_focus", {})
        reflections = data.get("reflections", [])[-limit:]
        lines = [
            "Lucy cognition state:",
            f"- Mode: {data.get('mode')}",
            f"- North star: {vision.get('north_star', '')}",
            f"- Identity boundary: {vision.get('identity_boundary', '')}",
            f"- Current focus: {focus.get('next_action', '')}",
            f"- Current risk: {focus.get('risk', '')}",
            "- Recent working reflections:",
        ]
        if not reflections:
            lines.append("  - No reflections recorded yet.")
        for item in reflections:
            lines.append(f"  - {item.get('observation', '')} Priority: {item.get('priority', '')}")
        return "\n".join(lines)

    def _infer_next_action(self, project: dict, memory: dict, knowledge: dict) -> str:
        if project.get("next_action"):
            return str(project["next_action"])
        if project.get("open_tasks"):
            return str(project["open_tasks"][0].get("text", "Review the active project tasks."))
        if not knowledge.get("available"):
            return "Build or refresh local knowledge before adding more power."
        if memory.get("active", 0) < 10:
            return "Keep improving durable memory with safe, approved facts."
        return "Keep Lucy stable, useful, tested, and grounded."

    def _infer_risk(self, user_text: str, context: dict) -> str:
        lowered = user_text.lower()
        if "conscious" in lowered or "sentient" in lowered or "alive" in lowered:
            return "Be honest: build persistent cognition, not fake consciousness."
        if any(word in lowered for word in ["agent", "voice", "desktop", "control", "auto"]):
            return "Avoid autonomy creep; permission before power."
        if context.get("pending_approvals", 0):
            return "Pending approvals exist; do not bypass Guardian."
        return "Stay inside safe local assistant boundaries."

    def _observation(self, project: dict, memory: dict, knowledge: dict) -> str:
        pieces = [
            f"Active project is {project.get('name', 'Lucy')}.",
            f"Open tasks: {len(project.get('open_tasks', []))}.",
            f"Active memories: {memory.get('active', 0)}.",
        ]
        if knowledge.get("available"):
            counts = knowledge.get("counts", {})
            pieces.append(f"AI Collections indexed files: {counts.get('total_files', 0)}.")
        return " ".join(pieces)
