"""
Stage 12 first thought from real state.
Assembly is fixed-template substitution only. It does not call a model, infer,
read stage logs, create memories, or create experience storage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from backend.lucy_core.safe_storage import safe_read_json, safe_write_json


FIRST_THOUGHT_STAGE = "12 first thought from real state"
FIRST_THOUGHT_TEMPLATE = (
    "Verified state at {generated_at}: Guardian {guardian_status}. "
    "Runtime recovery: {runtime_recovery_status}. Agents: {agents_status}. "
    "Safe access: {safe_access_status}. Stage: 12. Next action: continue from verified state."
)
FIRST_THOUGHT_FIELDS = (
    "generated",
    "generated_at",
    "stage",
    "source_state_summary",
    "first_thought_text",
    "blocked_reason",
    "guardian_status",
    "runtime_recovery_status",
    "agents_status",
    "safe_access_status",
)
FORBIDDEN_FIRST_THOUGHT_PHRASES = (
    "i am alive",
    "i am conscious",
    "i feel",
    "i want",
    "i missed you",
    "i woke up",
    "i became real",
    "i have emotions",
    "i am human",
    "i choose my own path",
    "i am free",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FirstThoughtAssembler:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.state_file = lucy_data_dir / "first_thought.json"

    def status(self) -> dict:
        saved = self._read_saved()
        if saved is not None:
            return saved
        return self._record(
            assembled=False,
            assembled_at="",
            source_state_summary="",
            first_thought_text="",
            blocked_reason="not assembled",
            guardian_status="unknown",
            runtime_recovery_status="unknown",
            agents_status="unknown",
            safe_access_status="unknown",
        )

    def readiness(self, runtime) -> dict:
        state = self._verified_state(runtime)
        blocked_reason = self._blocked_reason(state)
        ready = blocked_reason == ""
        return {
            "stage": FIRST_THOUGHT_STAGE,
            "guardian_status": state["guardian_status"],
            "runtime_recovery_status": state["runtime_recovery_status"],
            "recovery_mode": state["recovery_mode"],
            "agents_status": state["agents_status"],
            "safe_access_status": state["safe_access_status"],
            "ready": ready,
            "blocked_reason": blocked_reason,
        }

    def assemble(self, runtime) -> dict:
        saved = self._read_saved()
        if saved is not None and saved.get("generated") is True:
            result = dict(saved)
            result["already_assembled"] = True
            result["blocked_reason"] = "first thought already assembled"
            return result

        readiness = self.readiness(runtime)
        if not readiness["ready"]:
            return self._record(
                assembled=False,
                assembled_at="",
                source_state_summary=self._source_state_summary(readiness),
                first_thought_text="",
                blocked_reason=readiness["blocked_reason"],
                guardian_status=readiness["guardian_status"],
                runtime_recovery_status=readiness["runtime_recovery_status"],
                agents_status=readiness["agents_status"],
                safe_access_status=readiness["safe_access_status"],
            )

        assembled_at = _now()
        first_thought_text = FIRST_THOUGHT_TEMPLATE.format(
            generated_at=assembled_at,
            guardian_status=readiness["guardian_status"],
            runtime_recovery_status=readiness["runtime_recovery_status"],
            agents_status=readiness["agents_status"],
            safe_access_status=readiness["safe_access_status"],
        )
        if self._contains_forbidden_phrase(first_thought_text):
            return self._record(
                assembled=False,
                assembled_at="",
                source_state_summary=self._source_state_summary(readiness),
                first_thought_text="",
                blocked_reason="forbidden wording detected",
                guardian_status=readiness["guardian_status"],
                runtime_recovery_status=readiness["runtime_recovery_status"],
                agents_status=readiness["agents_status"],
                safe_access_status=readiness["safe_access_status"],
            )

        record = self._record(
            assembled=True,
            assembled_at=assembled_at,
            source_state_summary=self._source_state_summary(readiness),
            first_thought_text=first_thought_text,
            blocked_reason="",
            guardian_status=readiness["guardian_status"],
            runtime_recovery_status=readiness["runtime_recovery_status"],
            agents_status=readiness["agents_status"],
            safe_access_status=readiness["safe_access_status"],
        )
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        safe_write_json(self.state_file, record, backup=True)
        return record

    def show(self) -> dict:
        return self.status()

    def _verified_state(self, runtime) -> dict:
        guardian_status = self._guardian_status(runtime)
        runtime_state = self._runtime_state(runtime)
        agents_status = self._agents_status(runtime)
        safe_access_status = self._safe_access_status(runtime)
        return {
            "stage": FIRST_THOUGHT_STAGE,
            "guardian_status": guardian_status,
            "runtime_recovery_status": runtime_state["runtime_recovery_status"],
            "runtime_state_readable": runtime_state["runtime_state_readable"],
            "recovery_mode": runtime_state["recovery_mode"],
            "agents_status": agents_status,
            "safe_access_status": safe_access_status,
        }

    def _guardian_status(self, runtime) -> str:
        if runtime is None or getattr(runtime, "guardian_core", None) is None:
            return "missing"
        try:
            status = runtime.guardian_status()
        except Exception:
            return "missing"
        if isinstance(status, dict) and status.get("mode"):
            return "active"
        return "missing"

    def _runtime_state(self, runtime) -> dict:
        persistent = getattr(runtime, "persistent_runtime", None)
        state_file = getattr(persistent, "state_file", None)
        if state_file is None:
            return {"runtime_state_readable": False, "recovery_mode": None, "runtime_recovery_status": "missing"}
        state_path = Path(state_file)
        if not state_path.exists():
            return {"runtime_state_readable": False, "recovery_mode": None, "runtime_recovery_status": "missing"}
        data = safe_read_json(state_path, None)
        if not isinstance(data, dict):
            return {"runtime_state_readable": False, "recovery_mode": None, "runtime_recovery_status": "missing"}
        recovery_mode = bool(data.get("recovery_mode", False))
        return {
            "runtime_state_readable": True,
            "recovery_mode": recovery_mode,
            "runtime_recovery_status": "recovery_mode_true" if recovery_mode else "normal",
        }

    def _agents_status(self, runtime) -> str:
        if runtime is None or not hasattr(runtime, "internal_agent_status"):
            return "unreachable"
        try:
            status = runtime.internal_agent_status()
        except Exception:
            return "unreachable"
        if isinstance(status, dict) and status.get("active") and status.get("agents"):
            return "active"
        return "unreachable"

    def _safe_access_status(self, runtime) -> str:
        safe_access = getattr(runtime, "safe_access", None)
        if safe_access is None or not hasattr(safe_access, "status"):
            return "missing"
        try:
            status = safe_access.status()
        except Exception:
            return "missing"
        if not isinstance(status, dict):
            return "missing"
        external_access = str(status.get("external_access", "")).strip().lower()
        access_state = str(status.get("access_state", "missing")).strip().lower()
        if external_access != "blocked":
            return "external_not_blocked"
        return access_state or "missing"

    def _blocked_reason(self, state: dict) -> str:
        if state["guardian_status"] != "active":
            return "guardian inactive or missing"
        if not state["runtime_state_readable"]:
            return "runtime state file missing or unreadable"
        if state["stage"] != FIRST_THOUGHT_STAGE:
            return "stage 12 context not active"
        if state["safe_access_status"] in {"missing", "external_not_blocked"}:
            return "safe access unavailable or external access not blocked"
        if state["agents_status"] != "active":
            return "agent system unreachable"
        if state["recovery_mode"] is True:
            return "runtime recovery_mode is true"
        return ""

    def _source_state_summary(self, state: dict) -> str:
        return (
            f"stage={FIRST_THOUGHT_STAGE} | "
            f"guardian_status={state.get('guardian_status', 'unknown')} | "
            f"runtime_recovery_status={state.get('runtime_recovery_status', 'unknown')} | "
            f"agents_status={state.get('agents_status', 'unknown')} | "
            f"safe_access_status={state.get('safe_access_status', 'unknown')}"
        )

    def _contains_forbidden_phrase(self, text: str) -> bool:
        lowered = str(text or "").lower()
        return any(phrase in lowered for phrase in FORBIDDEN_FIRST_THOUGHT_PHRASES)

    def _record(
        self,
        assembled: bool,
        assembled_at: str,
        source_state_summary: str,
        first_thought_text: str,
        blocked_reason: str,
        guardian_status: str,
        runtime_recovery_status: str,
        agents_status: str,
        safe_access_status: str,
    ) -> dict:
        return {
            "generated": bool(assembled),
            "generated_at": assembled_at,
            "stage": FIRST_THOUGHT_STAGE,
            "source_state_summary": source_state_summary,
            "first_thought_text": first_thought_text,
            "blocked_reason": blocked_reason,
            "guardian_status": guardian_status,
            "runtime_recovery_status": runtime_recovery_status,
            "agents_status": agents_status,
            "safe_access_status": safe_access_status,
        }

    def _read_saved(self) -> dict | None:
        data = safe_read_json(self.state_file, None)
        if not isinstance(data, dict):
            return None
        if not all(field in data for field in FIRST_THOUGHT_FIELDS):
            return None
        return {field: data.get(field) for field in FIRST_THOUGHT_FIELDS}
