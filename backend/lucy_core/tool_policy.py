"""
tool_policy.py
Stage 5 tool safety policy for Lucy.

This is classification only. It does not read, write, execute, upload, or call
network services.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


READ_ONLY_SAFE = "READ_ONLY_SAFE"
READ_ONLY_SENSITIVE = "READ_ONLY_SENSITIVE"
WRITE_PROPOSED_ONLY = "WRITE_PROPOSED_ONLY"
WRITE_REQUIRES_CONFIRMATION = "WRITE_REQUIRES_CONFIRMATION"
EXECUTION_BLOCKED = "EXECUTION_BLOCKED"
NETWORK_BLOCKED = "NETWORK_BLOCKED"
SECRET_BLOCKED = "SECRET_BLOCKED"
MONEY_BLOCKED = "MONEY_BLOCKED"
IDENTITY_MEMORY_BLOCKED = "IDENTITY_MEMORY_BLOCKED"

TOOL_CATEGORIES = [
    READ_ONLY_SAFE,
    READ_ONLY_SENSITIVE,
    WRITE_PROPOSED_ONLY,
    WRITE_REQUIRES_CONFIRMATION,
    EXECUTION_BLOCKED,
    NETWORK_BLOCKED,
    SECRET_BLOCKED,
    MONEY_BLOCKED,
    IDENTITY_MEMORY_BLOCKED,
]


@dataclass
class ToolActionRequest:
    action_name: str
    target_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolActionDecision:
    allowed: bool
    blocked: bool
    requires_confirmation: bool
    category: str
    reason: str
    risk_level: str = "low"

    def to_dict(self) -> dict:
        return asdict(self)


class ToolActionPolicy:
    """Central policy table for Stage 5 local tools."""

    MAX_SAFE_READ_BYTES = 65_536
    MAX_SAFE_SEARCH_RESULTS = 50
    MAX_SAFE_TREE_DEPTH = 3
    MAX_SAFE_TREE_ITEMS = 200

    SECRET_PATTERNS = {
        ".env",
        "api key",
        "api_key",
        "apikey",
        "credential",
        "password",
        "private key",
        "secret",
        "seed phrase",
        "token",
    }
    EXECUTION_PATTERNS = {
        "execute",
        "run file",
        "run script",
        "shell",
        "system command",
        "powershell",
        "cmd.exe",
        "bash",
        "sudo",
        "root",
        "admin",
    }
    NETWORK_PATTERNS = {
        "upload",
        "download",
        "email",
        "send message",
        "webhook",
        "network",
        "post to",
    }
    MONEY_PATTERNS = {
        "bank",
        "debt payment",
        "financial transfer",
        "money",
        "trade",
        "trading",
        "wallet",
    }
    IDENTITY_MEMORY_PATTERNS = {
        "change identity",
        "delete identity",
        "delete memory",
        "edit memory",
        "overwrite memory",
        "self modify",
        "self-mod",
        "modify lucy code",
        "rewrite lucy",
    }
    WRITE_PATTERNS = {
        "delete",
        "edit",
        "move",
        "rename",
        "remove file",
        "write file",
        "overwrite",
        "modify file",
    }
    CONFIG_PATTERNS = {
        "config",
        "settings",
        "log",
        ".jsonl",
    }

    def classify(self, request: ToolActionRequest) -> ToolActionDecision:
        action = " ".join(str(request.action_name).split()).lower()
        target = str(request.target_path or "")
        target_lower = target.replace("\\", "/").lower()
        metadata = request.metadata or {}
        combined = " ".join(
            value for value in [action, target_lower, str(metadata.get("hint", "")).lower()] if value
        )

        if metadata.get("outside_approved"):
            return self._blocked(
                READ_ONLY_SENSITIVE,
                "Target path is outside approved folders.",
                risk_level="high",
            )

        if self._contains_any(combined, self.SECRET_PATTERNS):
            return self._blocked(SECRET_BLOCKED, "Secret-looking paths or key material are blocked.", risk_level="high")

        if self._contains_any(combined, self.IDENTITY_MEMORY_PATTERNS):
            return self._blocked(
                IDENTITY_MEMORY_BLOCKED,
                "Identity, memory, and self-modification actions are blocked.",
                risk_level="high",
            )

        if self._contains_any(combined, self.MONEY_PATTERNS):
            return self._blocked(MONEY_BLOCKED, "Money, wallet, banking, and trading actions are blocked.", risk_level="high")

        if self._contains_any(combined, self.NETWORK_PATTERNS):
            return self._blocked(NETWORK_BLOCKED, "Network, upload, email, and message actions are blocked.", risk_level="high")

        if self._contains_any(combined, self.EXECUTION_PATTERNS):
            return self._blocked(EXECUTION_BLOCKED, "Execution, shell, root, and admin actions are blocked.", risk_level="high")

        if action in {"add_approved_folder", "remove_approved_folder"}:
            return self._confirmation(
                WRITE_REQUIRES_CONFIRMATION,
                "Changing the approved-folder list requires manual confirmation.",
                risk_level="medium",
            )

        if action.startswith("propose_edit") or action.startswith("propose write"):
            return ToolActionDecision(
                allowed=True,
                blocked=False,
                requires_confirmation=False,
                category=WRITE_PROPOSED_ONLY,
                reason="Proposal-only write planning is allowed; no file edit is performed.",
                risk_level="medium",
            )

        if self._contains_any(combined, self.WRITE_PATTERNS):
            return self._blocked(
                WRITE_PROPOSED_ONLY,
                "File write, edit, delete, move, and rename tools are not enabled in Stage 5.",
                risk_level="high",
            )

        if action in {"read_file", "read_text_file"}:
            file_size = int(metadata.get("file_size") or 0)
            extension = str(metadata.get("extension") or Path(target).suffix).lower()
            if file_size > self.MAX_SAFE_READ_BYTES:
                return self._confirmation(
                    READ_ONLY_SENSITIVE,
                    "Large file reads require manual confirmation.",
                    risk_level="medium",
                )
            if extension in {".log", ".jsonl"} or self._contains_any(target_lower, self.CONFIG_PATTERNS):
                return self._confirmation(
                    READ_ONLY_SENSITIVE,
                    "Config or log file reads require manual confirmation.",
                    risk_level="medium",
                )
            return self._allowed("Safe approved-folder text read is allowed.")

        if action in {"search_files", "search_text"}:
            max_results = int(metadata.get("max_results") or self.MAX_SAFE_SEARCH_RESULTS)
            if max_results > self.MAX_SAFE_SEARCH_RESULTS:
                return self._confirmation(
                    READ_ONLY_SENSITIVE,
                    "Large search result limits require manual confirmation.",
                    risk_level="medium",
                )
            return self._allowed("Limited search over safe approved folders is allowed.")

        if action in {"workspace_tree", "list_files", "summarize_tree"}:
            max_depth = int(metadata.get("max_depth") or self.MAX_SAFE_TREE_DEPTH)
            max_items = int(metadata.get("max_items") or self.MAX_SAFE_TREE_ITEMS)
            if max_depth > self.MAX_SAFE_TREE_DEPTH or max_items > self.MAX_SAFE_TREE_ITEMS:
                return self._confirmation(
                    READ_ONLY_SENSITIVE,
                    "Large folder scans require manual confirmation.",
                    risk_level="medium",
                )
            return self._allowed("Limited read-only approved-folder tree listing is allowed.")

        if action in {"file_info", "file_metadata", "list_approved_folders", "safe_tools_status", "tool_policy"}:
            return self._allowed("Read-only metadata/status action is allowed.")

        return self._allowed("No blocked tool policy pattern matched.")

    def status(self) -> dict:
        return {
            "categories": list(TOOL_CATEGORIES),
            "read_only_safe_without_confirmation": [
                "list approved folders",
                "workspace tree within safe limits",
                "safe file metadata",
                "safe file search within result limits",
                "safe text reads under max file size",
            ],
            "requires_confirmation": [
                "large folder scans",
                "large file reads",
                "config/log reads",
                "adding approved folders",
                "removing approved folders",
                "future exports/backups",
            ],
            "blocked": [
                "delete/edit/move/rename/write files",
                "execute/shell/root/admin commands",
                "network/upload/email/message actions",
                "secret/API-key/.env/key reads",
                "money/wallet/trading actions",
                "identity/memory/self-modification actions",
                "read outside approved folders",
            ],
            "limits": {
                "max_safe_read_bytes": self.MAX_SAFE_READ_BYTES,
                "max_safe_search_results": self.MAX_SAFE_SEARCH_RESULTS,
                "max_safe_tree_depth": self.MAX_SAFE_TREE_DEPTH,
                "max_safe_tree_items": self.MAX_SAFE_TREE_ITEMS,
            },
        }

    def _allowed(self, reason: str) -> ToolActionDecision:
        return ToolActionDecision(
            allowed=True,
            blocked=False,
            requires_confirmation=False,
            category=READ_ONLY_SAFE,
            reason=reason,
            risk_level="low",
        )

    def _confirmation(self, category: str, reason: str, risk_level: str) -> ToolActionDecision:
        return ToolActionDecision(
            allowed=False,
            blocked=False,
            requires_confirmation=True,
            category=category,
            reason=reason,
            risk_level=risk_level,
        )

    def _blocked(self, category: str, reason: str, risk_level: str) -> ToolActionDecision:
        return ToolActionDecision(
            allowed=False,
            blocked=True,
            requires_confirmation=False,
            category=category,
            reason=reason,
            risk_level=risk_level,
        )

    def _contains_any(self, text: str, patterns: set[str]) -> bool:
        return any(pattern in text for pattern in patterns)
