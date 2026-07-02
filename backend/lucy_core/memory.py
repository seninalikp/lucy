"""
memory.py
Local JSON memory system for Lucy.

This stores only user-approved, useful facts. It is intentionally small,
auditable, and easy to edit by hand if needed.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


MEMORY_VERSION = "0.2.0"

MEMORY_TYPES = {
    "user_preference",
    "project_fact",
    "routine_fact",
    "technical_setup",
    "long_term_goal",
    "correction_anti_drift_rule",
    "important_life_context",
    "general",
}

SENSITIVE_KEYWORDS = {
    "api key",
    "password",
    "passphrase",
    "private key",
    "seed phrase",
    "secret",
    "credential",
    "wallet",
    "bank",
    "card number",
    "social security",
    "ssn",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _tokens(text: str) -> set[str]:
    return {part for part in re.split(r"[^a-z0-9_]+", text.lower()) if len(part) > 2}


def _infer_type(text: str, fallback: str = "general") -> str:
    lowered = text.lower()
    if fallback in MEMORY_TYPES and fallback != "general":
        return fallback
    if any(word in lowered for word in ["prefer", "preference", "call me", "talk to me"]):
        return "user_preference"
    if any(word in lowered for word in ["project", "checkpoint", "repository", "repo"]):
        return "project_fact"
    if any(word in lowered for word in ["routine", "sleep", "gym", "health", "daily"]):
        return "routine_fact"
    if any(word in lowered for word in ["python", "api", "config", "server", "provider", "port"]):
        return "technical_setup"
    if any(word in lowered for word in ["goal", "north star", "vision"]):
        return "long_term_goal"
    if any(word in lowered for word in ["do not", "don't", "anti-drift", "avoid", "correction"]):
        return "correction_anti_drift_rule"
    if any(word in lowered for word in ["family", "friend", "money pressure", "important"]):
        return "important_life_context"
    return "general"


def _tags(text: str, memory_type: str) -> list[str]:
    tags = {memory_type}
    for token in sorted(_tokens(text)):
        if len(tags) >= 8:
            break
        tags.add(token)
    return sorted(tags)


class MemorySystem:
    """Persistent local memory with simple recall and audit operations."""

    def __init__(self, memory_dir: Path) -> None:
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / "memory.json"
        self.short_term: list[str] = []
        self._ensure_file()

    def _default_data(self) -> dict:
        return {
            "version": MEMORY_VERSION,
            "mode": "local_json_approved_facts",
            "created_at": _now(),
            "updated_at": _now(),
            "memories": [],
        }

    def _ensure_file(self) -> None:
        if not self.memory_file.exists():
            self._write(self._default_data())

    def _read(self) -> dict:
        try:
            data = json.loads(self.memory_file.read_text(encoding="utf-8"))
        except Exception:
            data = self._default_data()
        data.setdefault("version", MEMORY_VERSION)
        data.setdefault("mode", "local_json_approved_facts")
        data.setdefault("memories", [])
        for item in data["memories"]:
            if "fact" not in item and "content" in item:
                item["fact"] = item["content"]
            if "content" not in item and "fact" in item:
                item["content"] = item["fact"]
            item.setdefault("type", item.get("category", "general"))
            if item["type"] not in MEMORY_TYPES:
                item["type"] = "general"
            item.setdefault("tags", _tags(item.get("fact", ""), item["type"]))
            item.setdefault("importance", 3)
            item.setdefault("status", "archived" if item.get("deleted") else "active")
        return data

    def _write(self, data: dict) -> None:
        data["updated_at"] = _now()
        self.memory_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _next_id(self, memories: list[dict]) -> str:
        highest = 0
        for item in memories:
            raw_id = str(item.get("id", ""))
            if raw_id.startswith("mem_"):
                try:
                    highest = max(highest, int(raw_id.split("_", 1)[1]))
                except ValueError:
                    continue
        return f"mem_{highest + 1:04d}"

    def _sensitive_hit(self, text: str) -> str | None:
        lowered = text.lower()
        for keyword in sorted(SENSITIVE_KEYWORDS):
            if keyword in lowered:
                return keyword
        return None

    def remember(self, fact: str, category: str = "general", source: str = "user") -> dict:
        """Save one approved memory fact, unless it is empty, sensitive, or duplicated."""
        cleaned = re.sub(r"\s+", " ", fact).strip()
        if not cleaned:
            return {"saved": False, "reason": "Memory text was empty."}

        sensitive = self._sensitive_hit(cleaned)
        if sensitive:
            return {
                "saved": False,
                "reason": f"Refused to store sensitive memory containing '{sensitive}'.",
            }

        data = self._read()
        memories = data["memories"]
        normalized = _normalize(cleaned)

        memory_type = _infer_type(cleaned, fallback=category.strip() or "general")

        for item in memories:
            if item.get("deleted") or item.get("status") == "archived":
                continue
            if item.get("normalized") == normalized:
                item["updated_at"] = _now()
                item["last_seen_at"] = _now()
                self._write(data)
                return {"saved": False, "duplicate": True, "memory": item}

        record = {
            "id": self._next_id(memories),
            "type": memory_type,
            "fact": cleaned,
            "content": cleaned,
            "tags": _tags(cleaned, memory_type),
            "importance": 3,
            "normalized": normalized,
            "category": memory_type,
            "source": source,
            "status": "active",
            "created_at": _now(),
            "updated_at": _now(),
            "last_seen_at": None,
            "deleted": False,
        }
        memories.append(record)
        self._write(data)
        return {"saved": True, "memory": record}

    def recall(self, query: str = "", limit: int = 8) -> list[dict]:
        """Return active memories, ranked by simple keyword overlap."""
        data = self._read()
        active = [
            item for item in data["memories"]
            if not item.get("deleted") and item.get("status", "active") == "active"
        ]
        cleaned = query.strip()
        if not cleaned:
            return active[:limit]

        query_tokens = _tokens(cleaned)
        matches: list[tuple[int, dict]] = []
        for item in active:
            text = item.get("fact", "")
            normalized = item.get("normalized", _normalize(text))
            score = 0
            if cleaned.lower() in normalized:
                score += 10
            score += len(query_tokens & _tokens(text))
            if score:
                matches.append((score, item))

        matches.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in matches[:limit]]

    def forget(self, query: str) -> dict:
        """Soft-delete memories matching a specific query. Refuses broad wipes."""
        cleaned = query.strip()
        if not cleaned:
            return {"forgotten": 0, "reason": "Give me a specific memory to forget."}

        if cleaned.lower() in {"all", "everything", "all memory", "memory"}:
            return {
                "forgotten": 0,
                "reason": "Broad memory wipes are blocked. Ask for one specific memory.",
            }

        data = self._read()
        matches = self.recall(cleaned, limit=20)
        forgotten_ids = {item["id"] for item in matches}
        for item in data["memories"]:
            if item.get("id") in forgotten_ids:
                item["deleted"] = True
                item["status"] = "archived"
                item["deleted_at"] = _now()
        if forgotten_ids:
            self._write(data)
        return {"forgotten": len(forgotten_ids), "ids": sorted(forgotten_ids)}

    def audit(self) -> dict:
        data = self._read()
        memories = data.get("memories", [])
        active = [
            item for item in memories
            if not item.get("deleted") and item.get("status", "active") == "active"
        ]
        deleted = [
            item for item in memories
            if item.get("deleted") or item.get("status") == "archived"
        ]
        categories: dict[str, int] = {}
        seen: set[str] = set()
        duplicate_count = 0
        for item in active:
            memory_type = item.get("type") or item.get("category", "general")
            categories[memory_type] = categories.get(memory_type, 0) + 1
            normalized = item.get("normalized", _normalize(item.get("fact", "")))
            if normalized in seen:
                duplicate_count += 1
            seen.add(normalized)

        return {
            "file": str(self.memory_file),
            "mode": data.get("mode", "unknown"),
            "total": len(memories),
            "active": len(active),
            "deleted": len(deleted),
            "duplicates": duplicate_count,
            "categories": categories,
            "updated_at": data.get("updated_at"),
        }

    def status(self) -> str:
        audit = self.audit()
        return (
            f"Memory active. Mode: {audit['mode']}. "
            f"Active facts: {audit['active']}. Deleted facts: {audit['deleted']}."
        )
