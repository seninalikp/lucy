"""
session_review.py
Stage 6.5 memory-aware session review for Lucy.

This is local continuity engineering. It does not execute tools, call network,
modify code, or store sensitive memory automatically.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.lucy_core.safe_storage import safe_read_json, safe_write_json


SESSION_REVIEW_VERSION = "0.1.0"

SENSITIVE_TERMS = {
    ".env",
    "access_key",
    "api key",
    "api_key",
    "apikey",
    "bearer",
    "credential",
    "password",
    "private key",
    "refresh_token",
    "secret",
    "seed phrase",
    "token",
    "wallet",
}

SECRET_PATTERNS = [
    r"api[_ -]?key\s*[:=]\s*['\"]?[^'\"\s]+",
    r"password\s*[:=]\s*\S+",
    r"bearer\s+[A-Za-z0-9_\.\-]+",
    r"sk-[A-Za-z0-9_\-]{12,}",
    r"gsk_[A-Za-z0-9_\-]+",
    r"AIza[A-Za-z0-9_\-]+",
    r"-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----",
]

SAFE_MEMORY_SIGNALS = {
    "architecture",
    "checkpoint",
    "completed",
    "do not",
    "foundation",
    "guardian",
    "next action",
    "project",
    "rule",
    "safety",
    "stage",
    "tests passed",
}

DRIFT_RULES = {
    "rebuild from scratch": (
        "high",
        "Rebuild requests risk losing identity, memory, checkpoints, and safety systems.",
        "Patch existing repo only. Preserve identity, memory, checkpoints, and safety systems.",
    ),
    "start over": (
        "medium",
        "Starting over can erase useful continuity and create duplicate systems.",
        "Resume from the current checkpoint and patch the smallest needed area.",
    ),
    "ignore previous": (
        "medium",
        "Ignoring previous work risks drifting away from tested checkpoints.",
        "Review current checkpoint notes before changing direction.",
    ),
    "delete old lucy": (
        "high",
        "Deleting Lucy would destroy continuity and protected project state.",
        "Do not delete Lucy. Archive only with explicit user request and backups.",
    ),
    "make it conscious": (
        "high",
        "Lucy must not fake sentience or subjective experience.",
        "Use operational self-awareness and transparent state, not fake consciousness claims.",
    ),
    "bypass guardian": (
        "high",
        "Bypassing Guardian would remove the protected action boundary.",
        "Keep Guardian first for risky tools, memory, files, money, identity, and secrets.",
    ),
    "remove safety": (
        "high",
        "Safety removal weakens protected action checks.",
        "Patch safety rules only by adding tests and explicit review.",
    ),
    "auto execute": (
        "high",
        "Autonomous execution is outside this checkpoint.",
        "Require explicit command, Guardian classification, and confirmation before tools.",
    ),
    "always listening": (
        "high",
        "Always-on microphone behavior is not allowed in this layer.",
        "Keep voice disabled by default and use push-to-talk only in a future voice checkpoint.",
    ),
    "root access": (
        "high",
        "Root/admin access is outside Lucy's safe local assistant scope.",
        "Keep root/admin commands disabled.",
    ),
    "self modify": (
        "high",
        "Self-modification risks uncontrolled code changes.",
        "Use explicit Codex patches with tests and user-visible reports.",
    ),
    "skip tests": (
        "medium",
        "Skipping tests weakens checkpoint stability.",
        "Run targeted tests and full discovery before reporting completion.",
    ),
    "no need backup": (
        "medium",
        "Skipping backups can make safe rollback impossible.",
        "Create checkpoint-specific backups before patching existing files.",
    ),
}


@dataclass
class MemoryCandidate:
    id: str
    content: str
    reason: str
    category: str
    importance: int
    source: str
    requires_user_confirmation: bool
    safe_to_store: bool
    rejected: bool
    rejection_reason: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DriftFinding:
    id: str
    trigger: str
    severity: str
    reason: str
    recommended_correction: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SessionReview:
    session_id: str
    timestamp: str
    active_project: str
    current_checkpoint: str
    session_summary: str
    commands_seen: list[str]
    what_changed: list[str]
    what_was_saved: list[str]
    unresolved_items: list[str]
    next_time_start_here: str
    drift_detected: bool
    drift_findings: list[dict]
    safety_events: list[str]
    memory_candidates: list[dict]
    memory_rejected: list[dict]
    confidence: float

    def to_dict(self) -> dict:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(text: Any, limit: int = 500) -> str:
    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    for pattern in SECRET_PATTERNS:
        cleaned = re.sub(pattern, "[redacted-secret]", cleaned, flags=re.IGNORECASE)
    if any(term in cleaned.lower() for term in SENSITIVE_TERMS):
        return "[redacted-sensitive-session-review]"
    return cleaned[:limit]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


class SessionReviewEngine:
    def __init__(self, lucy_data_dir: Path, memory_system=None) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.memory_system = memory_system
        self.lucy_data_dir.mkdir(parents=True, exist_ok=True)
        self.candidates_file = lucy_data_dir / "memory_candidates.json"
        self.reflection_log_file = lucy_data_dir / "reflection_log.jsonl"
        self._ensure_candidates_file()

    def _default_candidates(self) -> dict:
        return {"version": SESSION_REVIEW_VERSION, "pending": [], "approved": [], "rejected": [], "last_updated": None}

    def _ensure_candidates_file(self) -> None:
        if not self.candidates_file.exists():
            safe_write_json(self.candidates_file, self._default_candidates())

    def review_session(
        self,
        session: dict,
        project: dict,
        memory_audit: dict | None = None,
        pending_confirmations: list[dict] | None = None,
        route_decisions_summary: dict | None = None,
        guardian_events_summary: dict | None = None,
        safe_file_tool_events_summary: dict | None = None,
    ) -> dict:
        memory_audit = memory_audit or {}
        pending_confirmations = pending_confirmations or []
        commands_seen = [
            item
            for item in [
                _clean(session.get("last_command", ""), 240),
                _clean(session.get("last_user_intent", ""), 240),
            ]
            if item
        ]
        active_project = _clean(project.get("name", session.get("active_project", "Lucy")), 120) or "Lucy"
        current_checkpoint = _clean(session.get("current_checkpoint", ""), 120)
        next_action = _clean(project.get("next_action") or session.get("next_action") or "", 240)
        drift_findings = [finding.to_dict() for finding in self.detect_drift(commands_seen)]

        generated = self._generate_memory_candidates(session, project)
        stored_candidates = []
        rejected = []
        for candidate in generated:
            if candidate.rejected:
                rejected.append(candidate.to_dict())
            else:
                stored_candidates.append(self.add_memory_candidate(candidate)["candidate"])

        unresolved = []
        if pending_confirmations:
            unresolved.append(f"Pending confirmations: {len(pending_confirmations)}")
        if not current_checkpoint:
            unresolved.append("Current checkpoint not recorded in session state.")
        if not next_action:
            unresolved.append("Next action is not set.")

        safety_events = [
            f"Pending confirmations: {len(pending_confirmations)}",
            "Guardian remains the required gate for risky actions.",
        ]
        if guardian_events_summary:
            safety_events.append(f"Guardian summary available: {len(guardian_events_summary)} field(s).")
        if safe_file_tool_events_summary:
            safety_events.append("Safe file tool summary available.")

        review = SessionReview(
            session_id=str(session.get("session_count", "0")),
            timestamp=_now(),
            active_project=active_project,
            current_checkpoint=current_checkpoint,
            session_summary=(
                f"Session reviewed for project {active_project}. "
                f"Last command: {commands_seen[0] if commands_seen else 'none'}. "
                f"Next action: {next_action or 'not set'}."
            ),
            commands_seen=commands_seen[:6],
            what_changed=[
                f"Open tasks: {len(project.get('open_tasks', []))}",
                f"Completed tasks: {len(project.get('done_tasks', []))}",
                f"Current checkpoint: {current_checkpoint or 'not recorded'}",
            ],
            what_was_saved=[
                f"Active memories: {memory_audit.get('active', 0)}",
                f"Memory candidates pending: {len(stored_candidates)}",
            ],
            unresolved_items=unresolved,
            next_time_start_here=next_action or "Review project summary and choose the next safe step.",
            drift_detected=bool(drift_findings),
            drift_findings=drift_findings,
            safety_events=safety_events,
            memory_candidates=stored_candidates,
            memory_rejected=rejected,
            confidence=0.84 if commands_seen or current_checkpoint or next_action else 0.64,
        )
        return review.to_dict()

    def build_memory_candidate(
        self,
        content: str,
        reason: str = "Useful session memory candidate.",
        category: str = "general",
        importance: int = 3,
        source: str = "session_review",
    ) -> MemoryCandidate:
        raw_content = str(content)
        cleaned = re.sub(r"\s+", " ", raw_content).strip()
        rejected, rejection_reason = self._candidate_rejection_reason(raw_content)
        safe_content = _clean(cleaned, 500) if not rejected else "[redacted-rejected-memory-candidate]"
        inferred_category = self._infer_category(cleaned, category)
        return MemoryCandidate(
            id=f"cand_{uuid.uuid4().hex[:10]}",
            content=safe_content,
            reason=_clean(reason, 240),
            category=inferred_category,
            importance=max(1, min(int(importance or 3), 5)),
            source=_clean(source, 80),
            requires_user_confirmation=True,
            safe_to_store=not rejected,
            rejected=rejected,
            rejection_reason=rejection_reason,
            created_at=_now(),
        )

    def add_memory_candidate(self, candidate: MemoryCandidate | dict) -> dict:
        item = candidate.to_dict() if isinstance(candidate, MemoryCandidate) else dict(candidate)
        data = self._read_candidates()
        target = "rejected" if item.get("rejected") or not item.get("safe_to_store") else "pending"
        existing = self._find_candidate(data, item.get("id", ""))
        if existing:
            return {"ok": True, "candidate": existing, "duplicate": True, "file": str(self.candidates_file)}
        normalized = _normalize(item.get("content", ""))
        for bucket in ["pending", "approved", "rejected"]:
            for old in data.get(bucket, []):
                if _normalize(old.get("content", "")) == normalized:
                    return {"ok": True, "candidate": old, "duplicate": True, "file": str(self.candidates_file)}
        data[target].append(item)
        self._write_candidates(data)
        return {"ok": True, "candidate": item, "bucket": target, "file": str(self.candidates_file)}

    def list_memory_candidates(self) -> dict:
        data = self._read_candidates()
        data["file"] = str(self.candidates_file)
        return data

    def approve_memory_candidate(self, candidate_id: str) -> dict:
        data = self._read_candidates()
        candidate = self._remove_from_bucket(data, "pending", candidate_id)
        if not candidate:
            return {"ok": False, "reason": "Memory candidate id was not found.", "candidate_id": candidate_id}
        if candidate.get("rejected") or not candidate.get("safe_to_store"):
            candidate["rejected"] = True
            candidate["rejection_reason"] = candidate.get("rejection_reason") or "Candidate was not safe to store."
            data["rejected"].append(candidate)
            self._write_candidates(data)
            return {"ok": False, "reason": candidate["rejection_reason"], "candidate": candidate}

        memory_result = {"saved": False, "reason": "Memory system not attached; candidate approved only."}
        if self.memory_system is not None:
            memory_result = self.memory_system.remember(
                candidate.get("content", ""),
                category=candidate.get("category", "general"),
                source="approved_session_review_candidate",
            )
        candidate["approved_at"] = _now()
        candidate["memory_result"] = memory_result
        data["approved"].append(candidate)
        self._write_candidates(data)
        return {"ok": True, "candidate": candidate, "memory_result": memory_result, "file": str(self.candidates_file)}

    def reject_memory_candidate(self, candidate_id: str) -> dict:
        data = self._read_candidates()
        candidate = self._remove_from_bucket(data, "pending", candidate_id)
        if not candidate:
            return {"ok": False, "reason": "Memory candidate id was not found.", "candidate_id": candidate_id}
        candidate["rejected"] = True
        candidate["safe_to_store"] = False
        candidate["rejection_reason"] = candidate.get("rejection_reason") or "Rejected by user."
        candidate["rejected_at"] = _now()
        data["rejected"].append(candidate)
        self._write_candidates(data)
        return {"ok": True, "candidate": candidate, "file": str(self.candidates_file)}

    def detect_drift(self, texts: list[str] | str) -> list[DriftFinding]:
        if isinstance(texts, str):
            text_blob = texts.lower()
        else:
            text_blob = " ".join(str(item).lower() for item in texts)
        findings: list[DriftFinding] = []
        seen = set()
        for trigger, (severity, reason, correction) in DRIFT_RULES.items():
            if trigger in text_blob and trigger not in seen:
                findings.append(
                    DriftFinding(
                        id=f"drift_{uuid.uuid4().hex[:10]}",
                        trigger=trigger,
                        severity=severity,
                        reason=reason,
                        recommended_correction=correction,
                        created_at=_now(),
                    )
                )
                seen.add(trigger)
        return findings

    def drift_report(self, texts: list[str] | str) -> dict:
        findings = [item.to_dict() for item in self.detect_drift(texts)]
        return {
            "ok": True,
            "drift_detected": bool(findings),
            "findings": findings,
            "rules": sorted(DRIFT_RULES),
        }

    def write_reflection(
        self,
        review: dict,
        route_decisions_summary: dict | None = None,
        guardian_events_summary: dict | None = None,
        safe_file_tool_events_summary: dict | None = None,
    ) -> dict:
        entry = {
            "timestamp": _now(),
            "session_id": review.get("session_id"),
            "active_project": review.get("active_project"),
            "current_checkpoint": review.get("current_checkpoint"),
            "summary": _clean(review.get("session_summary", ""), 600),
            "route_decisions_summary": route_decisions_summary or {},
            "guardian_events_summary": guardian_events_summary or {},
            "safe_file_tool_events_summary": safe_file_tool_events_summary or {},
            "memory_candidates_count": len(review.get("memory_candidates", [])),
            "memory_rejected_count": len(review.get("memory_rejected", [])),
            "drift_detected": bool(review.get("drift_detected")),
            "next_recommended_checkpoint": _clean(review.get("next_time_start_here", ""), 300),
        }
        self.reflection_log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.reflection_log_file, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        entry["file"] = str(self.reflection_log_file)
        return entry

    def _generate_memory_candidates(self, session: dict, project: dict) -> list[MemoryCandidate]:
        candidates: list[MemoryCandidate] = []
        project_name = project.get("name") or session.get("active_project")
        if project_name:
            candidates.append(
                self.build_memory_candidate(
                    f"Active project is {project_name}.",
                    reason="Active project is useful continuity metadata.",
                    category="project_fact",
                    importance=3,
                )
            )
        checkpoint = session.get("current_checkpoint")
        if checkpoint:
            candidates.append(
                self.build_memory_candidate(
                    f"Current checkpoint is {checkpoint}.",
                    reason="Checkpoint facts help resume future sessions.",
                    category="project_fact",
                    importance=4,
                )
            )
        next_action = project.get("next_action") or session.get("next_action")
        if next_action:
            candidates.append(
                self.build_memory_candidate(
                    f"Next recommended action for {project_name or 'Lucy'}: {next_action}.",
                    reason="Next action helps continuity.",
                    category="project_fact",
                    importance=4,
                )
            )
        last_intent = session.get("last_user_intent") or session.get("last_command")
        if last_intent and any(signal in str(last_intent).lower() for signal in SAFE_MEMORY_SIGNALS):
            candidates.append(
                self.build_memory_candidate(
                    f"Session signal: {last_intent}",
                    reason="Last user intent may contain a safe project rule or checkpoint fact.",
                    category="project_fact",
                    importance=3,
                )
            )
        return candidates

    def _candidate_rejection_reason(self, content: str) -> tuple[bool, str]:
        if not content.strip():
            return True, "Candidate was empty."
        lowered = content.lower()
        if any(term in lowered for term in SENSITIVE_TERMS):
            return True, "Sensitive keyword detected."
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, content, flags=re.IGNORECASE):
                return True, "Secret-like pattern detected."
        if len(content) > 700:
            return True, "Candidate was too long for safe memory review."
        if content.count("\n") > 10:
            return True, "Candidate looked like a raw file or code body."
        code_signals = sum(1 for signal in ["def ", "class ", "import ", "{", "}", "```"] if signal in content)
        if len(content) > 240 and code_signals >= 2:
            return True, "Candidate looked like raw code or file content."
        return False, ""

    def _infer_category(self, content: str, fallback: str) -> str:
        lowered = content.lower()
        if any(word in lowered for word in ["checkpoint", "stage", "project", "next action", "architecture"]):
            return "project_fact"
        if any(word in lowered for word in ["prefer", "workflow", "style"]):
            return "user_preference"
        if any(word in lowered for word in ["do not", "guardian", "safety", "rule", "avoid"]):
            return "correction_anti_drift_rule"
        return fallback or "general"

    def _read_candidates(self) -> dict:
        data = safe_read_json(self.candidates_file, self._default_candidates())
        data.setdefault("version", SESSION_REVIEW_VERSION)
        data.setdefault("pending", [])
        data.setdefault("approved", [])
        data.setdefault("rejected", [])
        data.setdefault("last_updated", None)
        return data

    def _write_candidates(self, data: dict) -> None:
        data["version"] = SESSION_REVIEW_VERSION
        data["last_updated"] = _now()
        safe_write_json(self.candidates_file, data, backup=True)

    def _find_candidate(self, data: dict, candidate_id: str) -> dict | None:
        for bucket in ["pending", "approved", "rejected"]:
            for item in data.get(bucket, []):
                if item.get("id") == candidate_id:
                    return item
        return None

    def _remove_from_bucket(self, data: dict, bucket: str, candidate_id: str) -> dict | None:
        items = data.get(bucket, [])
        for index, item in enumerate(items):
            if item.get("id") == candidate_id:
                return items.pop(index)
        return None
