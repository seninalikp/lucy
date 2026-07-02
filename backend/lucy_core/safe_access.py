"""
Stage 11 safe access policy foundation.
This is policy/status/check logic only. It does not open sockets, bind ports,
start servers, generate tokens, or create an access audit log.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.lucy_core.guardian import BLOCKED, REQUIRES_MANUAL_CONFIRMATION
from backend.lucy_core.safe_storage import safe_read_json, safe_write_json


SAFE_ACCESS_STAGE = "11 safe access"
SAFE_ACCESS_POLICY_VERSION = "0.1.0"
VALID_ACCESS_STATES = ("disabled", "local_only", "blocked_external", "needs_approval")
LOCAL_SOURCE_LABELS = {"local", "local_cli", "lucy_terminal", "runtime", "terminal"}
EXTERNAL_SOURCE_MARKERS = {
    "browser",
    "external",
    "internet",
    "lan",
    "phone",
    "public",
    "remote",
    "server",
    "socket",
    "unknown",
    "web",
}


@dataclass
class AccessCheckResult:
    allowed: bool
    state: str
    reason: str
    required_approval: bool
    source: str

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "state": self.state,
            "reason": self.reason,
            "required_approval": self.required_approval,
            "source": self.source,
        }


class SafeAccessManager:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.policy_file = lucy_data_dir / "access_policy.json"
        self.lucy_data_dir.mkdir(parents=True, exist_ok=True)
        if not self.policy_file.exists():
            self._write(self._default_policy())

    def _default_policy(self) -> dict:
        return {
            "version": SAFE_ACCESS_POLICY_VERSION,
            "stage": SAFE_ACCESS_STAGE,
            "access_state": "disabled",
            "local_only_policy": "prepared",
            "external_access": "blocked",
            "network_server": "not enabled",
            "phone_browser_access": "not enabled",
            "token_generation": "blocked",
            "future_access_changes_require_approval": True,
            "source_policy": "caller_supplied_label_only",
        }

    def _read(self) -> dict:
        data = safe_read_json(self.policy_file, self._default_policy())
        if not isinstance(data, dict):
            data = self._default_policy()
        return self._sanitize_policy(data)

    def _write(self, data: dict) -> dict:
        safe_write_json(self.policy_file, data, backup=True)
        return data

    def _sanitize_policy(self, data: dict) -> dict:
        default = self._default_policy()
        sanitized = dict(default)
        for key in default:
            if key in data:
                sanitized[key] = data[key]

        sanitized["version"] = SAFE_ACCESS_POLICY_VERSION
        sanitized["stage"] = SAFE_ACCESS_STAGE
        state = str(sanitized.get("access_state", "disabled")).strip().lower()
        if state not in VALID_ACCESS_STATES:
            sanitized["access_state"] = "blocked_external"
            sanitized["invalid_state_rejected"] = True
        else:
            sanitized["access_state"] = state

        sanitized["external_access"] = "blocked"
        sanitized["network_server"] = "not enabled"
        sanitized["phone_browser_access"] = "not enabled"
        sanitized["token_generation"] = "blocked"
        sanitized["future_access_changes_require_approval"] = bool(
            sanitized.get("future_access_changes_require_approval", True)
        )
        sanitized["source_policy"] = "caller_supplied_label_only"
        return sanitized

    def status(self) -> dict:
        policy = self._read()
        policy["file"] = str(self.policy_file)
        return policy

    def check_access(
        self,
        source: str = "unknown",
        guardian=None,
        active_project: str = "Lucy",
    ) -> dict:
        policy = self._read()
        source_label = self._normalize_source(source)

        guardian_result = self._guardian_check(source_label, guardian, active_project)
        if guardian_result == BLOCKED:
            return AccessCheckResult(
                allowed=False,
                state="blocked_external",
                reason="Guardian blocked the access check.",
                required_approval=True,
                source=source_label,
            ).to_dict()
        if guardian_result == REQUIRES_MANUAL_CONFIRMATION:
            return AccessCheckResult(
                allowed=False,
                state="needs_approval",
                reason="Guardian requires approval before access changes.",
                required_approval=True,
                source=source_label,
            ).to_dict()

        if self._is_external_or_unknown(source_label):
            return AccessCheckResult(
                allowed=False,
                state="blocked_external",
                reason="External or unknown source labels are blocked in Stage 11.",
                required_approval=True,
                source=source_label,
            ).to_dict()

        state = policy.get("access_state", "disabled")
        if state == "disabled":
            return AccessCheckResult(
                allowed=False,
                state="disabled",
                reason="Safe access is disabled by default in Stage 11.",
                required_approval=True,
                source=source_label,
            ).to_dict()
        if state == "local_only":
            return AccessCheckResult(
                allowed=True,
                state="local_only",
                reason="Local-only policy label accepted; no network access is opened.",
                required_approval=False,
                source=source_label,
            ).to_dict()
        if state == "needs_approval":
            return AccessCheckResult(
                allowed=False,
                state="needs_approval",
                reason="Access policy requires approval before use.",
                required_approval=True,
                source=source_label,
            ).to_dict()

        return AccessCheckResult(
            allowed=False,
            state="blocked_external",
            reason="Access policy blocks external access.",
            required_approval=True,
            source=source_label,
        ).to_dict()

    def _guardian_check(self, source_label: str, guardian, active_project: str) -> str:
        if guardian is None or not hasattr(guardian, "classify"):
            return ""
        try:
            result = guardian.classify(
                f"safe access check source label {source_label}",
                active_project=active_project or "Lucy",
            )
            return str(getattr(result, "classification", "") or "")
        except Exception:
            return BLOCKED

    def _normalize_source(self, source: str) -> str:
        cleaned = " ".join(str(source or "unknown").strip().lower().split())
        return cleaned or "unknown"

    def _is_external_or_unknown(self, source_label: str) -> bool:
        if source_label in LOCAL_SOURCE_LABELS:
            return False
        return True

