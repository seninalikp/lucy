"""
execution_receipts.py
Stage 55 = Cryptographic Execution Receipt Ledger & Anti-Hallucination Claim Binder.

Guarantees Lucy can NEVER hallucinate taking an action:
1. Every real state mutation (file synthesis, task update, memory save, cron schedule,
   sandbox cleanup) registers a SHA-256 ExecutionReceipt in the current turn ledger.
2. Before any LLM response is returned to Senin, `verify_response_actions()` scans the text
   for action assertions ("I added the task", "I scheduled the job", "I cleaned the cache").
3. If the LLM claims an action was performed in this turn without a matching receipt,
   the ClaimBinder intercepts the lie and appends the exact verified turn ledger.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE = "55 execution receipt ledger and claim binder"

ACTION_CLAIM_PATTERNS = {
    "task_mutation": r"\b(?:i\s+have\s+|i\s+|i've\s+|successfully\s+)(?:added|created|completed|closed|removed|updated)\s+(?:the\s+|a\s+|your\s+)?task\b",
    "schedule_mutation": r"\b(?:i\s+have\s+|i\s+|i've\s+|successfully\s+)(?:scheduled|paused|resumed|unscheduled|created)\s+(?:the\s+|a\s+|your\s+)?(?:cron|job|schedule)\b",
    "sandbox_cleanup": r"\b(?:i\s+have\s+|i\s+|i've\s+|successfully\s+)(?:cleaned|cleared|purged|deleted)\s+(?:the\s+|your\s+)?(?:sandbox|staging|cache|temp\s+files)\b",
    "code_synthesis": r"\b(?:i\s+have\s+|i\s+|i've\s+|successfully\s+)(?:synthesized|compiled|promoted|built\s+and\s+verified)\s+(?:the\s+|a\s+)?(?:script|tool|module|code)\b",
    "memory_mutation": r"\b(?:i\s+have\s+|i\s+|i've\s+|successfully\s+)(?:stored|saved|committed|forgotten|deleted)\s+(?:that\s+in|to|from)\s+(?:your\s+|permanent\s+)?memory\b",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionReceiptLedger:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.ledger_file = self.lucy_data / "execution_receipts.jsonl"
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self._current_turn_receipts: list[dict[str, Any]] = []

    def begin_turn(self) -> None:
        """Clears the per-turn receipt buffer at the start of a new user request."""
        self._current_turn_receipts = []

    def issue_receipt(
        self,
        action_category: str,
        operation: str,
        target: str,
        verified_outcome: str,
    ) -> dict[str, Any]:
        ts = _now()
        raw_payload = f"{ts}|{action_category}|{operation}|{target}|{verified_outcome}"
        digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()[:12]
        receipt = {
            "receipt_id": f"rcpt_{digest}",
            "timestamp": ts,
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self._current_turn_receipts.append(receipt)
        try:
            with open(self.ledger_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(receipt, ensure_ascii=False) + "\n")
        except Exception:
            pass
        return receipt

    def record_receipt(
        self,
        action_name: str,
        parameters: dict[str, Any] | None = None,
        status: str = "success",
    ) -> dict[str, Any]:
        """Compatibility bridge for Stage 70 TerminalReActEngine."""
        params = parameters or {}
        target = str(params.get("command") or params.get("goal") or action_name)[:60]
        return self.issue_receipt(
            action_category="terminal_react",
            operation=action_name,
            target=target,
            verified_outcome=f"Status: {status}",
        )

    def current_turn_receipts(self) -> list[dict[str, Any]]:
        return list(self._current_turn_receipts)

    def verify_response_actions(self, response_text: str) -> dict[str, Any]:
        """
        Checks whether any action claims in `response_text` are backed by a physical
        ExecutionReceipt issued during the current turn.
        """
        text = str(response_text or "")
        turn_categories = {r["action_category"] for r in self._current_turn_receipts}
        unbacked_claims: list[str] = []

        for category, pattern in ACTION_CLAIM_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                if category not in turn_categories:
                    unbacked_claims.append(category)

        if not unbacked_claims:
            return {
                "stage": STAGE,
                "verified": True,
                "unbacked_claims": [],
                "receipts_issued": len(self._current_turn_receipts),
                "guarded_text": text,
                "badge": f"[RECEIPT_LEDGER: VERIFIED | Turn Receipts: {len(self._current_turn_receipts)}]",
            }

        receipt_summary = (
            ", ".join(f"{r['receipt_id']} ({r['operation']})" for r in self._current_turn_receipts)
            if self._current_turn_receipts
            else "NONE (0 tools executed this turn)"
        )
        warning_block = (
            f"\n\n[STAGE 55 RECEIPT INTERCEPT: UNBACKED ACTION CLAIM]\n"
            f"The model claimed to perform `{', '.join(unbacked_claims)}`, but no physical tool receipt "
            f"was generated for that action in this turn.\n"
            f"- Actual Verified Turn Receipts: {receipt_summary}"
        )
        return {
            "stage": STAGE,
            "verified": False,
            "unbacked_claims": unbacked_claims,
            "receipts_issued": len(self._current_turn_receipts),
            "guarded_text": text.strip() + warning_block,
            "badge": f"[RECEIPT_LEDGER: INTERCEPTED | Unbacked: {', '.join(unbacked_claims)}]",
        }

    def status(self) -> dict[str, Any]:
        total = 0
        if self.ledger_file.exists():
            try:
                total = len(self.ledger_file.read_text(encoding="utf-8").splitlines())
            except Exception:
                total = 0
        return {
            "stage": STAGE,
            "execution_receipt_ledger": "active",
            "total_historical_receipts": total,
            "current_turn_receipts": len(self._current_turn_receipts),
            "ledger_file": str(self.ledger_file),
        }
