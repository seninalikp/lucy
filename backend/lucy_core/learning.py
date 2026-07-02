"""
learning.py
Local self-learning loop for Lucy.

Lucy can save interaction traces and improvement proposals automatically. This
does not modify code and does not promote every trace into long-term memory.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


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
    "nvidia key",
    "setup nvidia key",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redact(text: str) -> tuple[str, bool]:
    lowered = text.lower()
    if any(term in lowered for term in SENSITIVE_TERMS):
        return "[redacted-sensitive-interaction]", True
    text = re.sub(r"sk-[A-Za-z0-9]{20,}", "[redacted-token]", text)
    text = re.sub(r"api[_ -]?key\s*[:=]\s*\S+", "api_key=[redacted]", text, flags=re.IGNORECASE)
    return text[:2000], False


class LearningSystem:
    def __init__(self, learning_dir: Path) -> None:
        self.learning_dir = learning_dir
        self.learning_dir.mkdir(parents=True, exist_ok=True)
        self.interactions_file = self.learning_dir / "interactions.jsonl"
        self.checkpoint_learning_file = self.learning_dir / "checkpoint_learning.jsonl"
        self.proposals_file = self.learning_dir / "improvement_proposals.json"
        self.lessons_file = self.learning_dir / "local_lessons.json"
        self.style_file = self.learning_dir / "talking_style.json"
        self._ensure_files()

    def _ensure_files(self) -> None:
        if not self.proposals_file.exists():
            self.proposals_file.write_text("[]", encoding="utf-8")
        if not self.lessons_file.exists():
            self.lessons_file.write_text("[]", encoding="utf-8")
        if not self.style_file.exists():
            self.style_file.write_text(
                json.dumps(
                    {
                        "version": "0.1.0",
                        "mode": "persistent_local_talking_style",
                        "created_at": _now(),
                        "updated_at": _now(),
                        "preferences": [
                            {
                                "id": "style_0001",
                                "timestamp": _now(),
                                "source": "system_default",
                                "text": "Be warm, direct, practical, and a little human without pretending to be conscious.",
                            }
                        ],
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

    def _read_json_list(self, path: Path) -> list[dict]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        return data if isinstance(data, list) else []

    def _write_json_list(self, path: Path, data: list[dict]) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _read_style_data(self) -> dict:
        try:
            data = json.loads(self.style_file.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        data.setdefault("version", "0.1.0")
        data.setdefault("mode", "persistent_local_talking_style")
        data.setdefault("created_at", _now())
        data.setdefault("updated_at", _now())
        data.setdefault("preferences", [])
        return data

    def _write_style_data(self, data: dict) -> None:
        data["updated_at"] = _now()
        self.style_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def record_interaction(self, user_text: str, response_text: str) -> dict:
        user_clean, user_redacted = _redact(user_text)
        response_clean, response_redacted = _redact(response_text)
        record = {
            "timestamp": _now(),
            "user_text": user_clean,
            "response_text": response_clean[:2000],
            "redacted": user_redacted or response_redacted,
        }
        with open(self.interactions_file, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def record_checkpoint_learning(self, checkpoint: dict, lesson: str) -> dict:
        reason_clean, reason_redacted = _redact(str(checkpoint.get("reason", "")))
        lesson_clean, lesson_redacted = _redact(lesson)
        record = {
            "timestamp": _now(),
            "checkpoint_id": str(checkpoint.get("checkpoint_id", "unknown")),
            "stage": str(checkpoint.get("stage", ""))[:240],
            "reason": reason_clean,
            "lesson": lesson_clean,
            "redacted": reason_redacted or lesson_redacted,
        }
        with open(self.checkpoint_learning_file, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def add_lesson(self, text: str, source: str = "user") -> dict:
        lesson_text, redacted = _redact(text.strip())
        if not lesson_text or redacted:
            return {"saved": False, "reason": "Lesson was empty or sensitive."}
        lessons = self._read_json_list(self.lessons_file)
        lesson = {
            "id": f"lesson_{len(lessons) + 1:04d}",
            "timestamp": _now(),
            "source": source,
            "text": lesson_text,
        }
        lessons.append(lesson)
        self._write_json_list(self.lessons_file, lessons)
        return {"saved": True, "lesson": lesson}

    def add_style_preference(self, text: str, source: str = "user") -> dict:
        preference_text, redacted = _redact(text.strip())
        if not preference_text or redacted:
            return {"saved": False, "reason": "Style preference was empty or sensitive."}

        data = self._read_style_data()
        preferences = data["preferences"]
        normalized = re.sub(r"\s+", " ", preference_text.lower()).strip()
        for item in preferences:
            existing = re.sub(r"\s+", " ", str(item.get("text", "")).lower()).strip()
            if existing == normalized:
                item["timestamp"] = _now()
                self._write_style_data(data)
                return {"saved": False, "duplicate": True, "preference": item}

        preference = {
            "id": f"style_{len(preferences) + 1:04d}",
            "timestamp": _now(),
            "source": source,
            "text": preference_text,
        }
        preferences.append(preference)
        self._write_style_data(data)
        return {"saved": True, "preference": preference}

    def style_status(self) -> dict:
        data = self._read_style_data()
        preferences = data.get("preferences", [])
        return {
            "mode": data.get("mode", "persistent_local_talking_style"),
            "file": str(self.style_file),
            "preferences": preferences,
            "preference_count": len(preferences),
            "updated_at": data.get("updated_at"),
        }

    def style_instruction(self, limit: int = 5) -> str:
        preferences = self.style_status()["preferences"][-limit:]
        return " ".join(str(item.get("text", "")).strip() for item in preferences if item.get("text"))

    def apply_talking_style(self, text: str) -> str:
        instruction = self.style_instruction().lower()
        styled = text

        if "casual" in instruction or "human" in instruction:
            styled = styled.replace("I do not", "I don't").replace("I am", "I'm")
        if ("warm" in instruction or "friendly" in instruction) and not styled.lower().startswith(
            ("i am blocking", "i'm blocking", "that needs approval")
        ):
            if not styled.lower().startswith(("got you", "got it")):
                styled = f"Got you. {styled}"
        if "short" in instruction or "concise" in instruction:
            paragraphs = [part.strip() for part in styled.split("\n\n") if part.strip()]
            styled = "\n\n".join(paragraphs[:2])

        return styled

    def add_proposal(self, title: str, detail: str, source: str = "learning_loop") -> dict:
        proposals = self._read_json_list(self.proposals_file)
        proposal = {
            "id": f"proposal_{len(proposals) + 1:04d}",
            "timestamp": _now(),
            "title": title.strip()[:160],
            "detail": detail.strip()[:1000],
            "source": source,
            "status": "open",
        }
        proposals.append(proposal)
        self._write_json_list(self.proposals_file, proposals)
        return proposal

    def status(self) -> dict:
        interactions = 0
        if self.interactions_file.exists():
            interactions = len([line for line in self.interactions_file.read_text(encoding="utf-8").splitlines() if line.strip()])
        checkpoint_lessons = 0
        if self.checkpoint_learning_file.exists():
            checkpoint_lessons = len(
                [
                    line
                    for line in self.checkpoint_learning_file.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
            )
        proposals = self._read_json_list(self.proposals_file)
        lessons = self._read_json_list(self.lessons_file)
        return {
            "learning_dir": str(self.learning_dir),
            "interactions": interactions,
            "checkpoint_lessons": checkpoint_lessons,
            "open_proposals": len([item for item in proposals if item.get("status") == "open"]),
            "local_lessons": len(lessons),
            "style_preferences": self.style_status()["preference_count"],
            "mode": "local_autosave_no_code_self_modification",
        }
