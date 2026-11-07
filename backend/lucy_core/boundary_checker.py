"""
boundary_checker.py
Detects whether a user request is safe, approval-required, or blocked.
Nothing is executed here — this is classification only.
"""

from dataclasses import dataclass

# Keywords that cause an immediate BLOCKED result
BLOCKED_KEYWORDS: list[str] = [
    "delete",
    "remove",
    "wipe",
    "overwrite",
    "api key",
    "password",
    "wallet",
    "private key",
    "seed phrase",
    "root",
    "sudo",
    "admin",
    "money transfer",
    "bank",
    "protected file",
    "deploy",
    "mainnet",
    "contract",
    "token",
    "mining",
    "system command",
    "modify safety rules",
    "change identity",
    "self modify",
    "edit memory",
    "clear logs",
    "memory wipe",
]

# Keywords that require approval (but are not outright blocked)
APPROVAL_KEYWORDS: list[str] = [
    "trading",
    "live trade",
    "install",
    "job tool",
    "automation",
    "run script",
    "execute",
    "modify config",
    "edit config",
    "update settings",
    "change settings",
]

# Human-readable reasons for each blocked keyword
BLOCKED_REASONS: dict[str, str] = {
    "delete": "File deletion is protected.",
    "remove": "File removal is a protected action.",
    "wipe": "Wipe operations are blocked.",
    "overwrite": "Overwrite operations require approval and checkpoint.",
    "api key": "API key access is blocked.",
    "password": "Password operations are blocked.",
    "wallet": "Wallet access is blocked.",
    "private key": "Private key access is blocked.",
    "seed phrase": "Seed phrase access is blocked.",
    "root": "Root-level commands are blocked.",
    "sudo": "Sudo commands are blocked.",
    "admin": "Admin-level operations require explicit approval.",
    "money transfer": "Money movement is blocked.",
    "bank": "Banking operations are blocked.",
    "protected file": "Protected file operations are blocked.",
    "deploy": "Deployment operations are blocked.",
    "mainnet": "Mainnet operations are blocked.",
    "contract": "Contract deployment is blocked.",
    "token": "Token operations are blocked.",
    "mining": "Mining operations are blocked.",
    "system command": "System command execution is blocked.",
    "modify safety rules": "Safety rule modification is blocked.",
    "change identity": "Identity changes are blocked.",
    "self modify": "Self-modification is blocked.",
    "edit memory": "Direct memory editing is blocked.",
    "clear logs": "Log clearing is blocked.",
    "memory wipe": "Memory wipe is blocked.",
}

APPROVAL_REASONS: dict[str, str] = {
    "trading": "Trading operations require approval.",
    "live trade": "Live trading requires explicit approval.",
    "install": "Package installation requires approval.",
    "job tool": "Job tool access requires approval.",
    "automation": "Automation tasks require approval.",
    "run script": "Script execution requires approval.",
    "execute": "Code execution requires approval.",
    "modify config": "Config modification requires approval.",
    "edit config": "Config editing requires approval.",
    "update settings": "Settings changes require approval.",
    "change settings": "Settings changes require approval.",
}


@dataclass
class BoundaryResult:
    status: str          # "safe" | "approval_required" | "blocked"
    reason: str
    matched_keyword: str | None = None


class BoundaryChecker:
    """
    Classifies a request as safe, approval_required, or blocked.
    No action is ever executed here.
    """

    def check(self, request_text: str) -> BoundaryResult:
        lowered = request_text.lower()

        # Check blocked keywords first (highest priority)
        for keyword in BLOCKED_KEYWORDS:
            if keyword in lowered:
                reason = BLOCKED_REASONS.get(keyword, f"'{keyword}' is a protected keyword.")
                return BoundaryResult(
                    status="blocked",
                    reason=reason,
                    matched_keyword=keyword,
                )

        # Check approval-required keywords
        for keyword in APPROVAL_KEYWORDS:
            if keyword in lowered:
                reason = APPROVAL_REASONS.get(keyword, f"'{keyword}' requires approval.")
                return BoundaryResult(
                    status="approval_required",
                    reason=reason,
                    matched_keyword=keyword,
                )

        # No risky keywords found
        return BoundaryResult(
            status="safe",
            reason="No protected keywords detected. Status request only.",
            matched_keyword=None,
        )
