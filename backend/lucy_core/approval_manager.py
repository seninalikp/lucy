"""
approval_manager.py
Creates and manages approval request records.
No action is executed here. Approvals are records only.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApprovalManager:
    def __init__(self, approvals_dir: Path) -> None:
        self.approvals_dir = approvals_dir
        self.approvals_dir.mkdir(parents=True, exist_ok=True)
        self.approvals_file = approvals_dir / "approval_requests.json"
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.approvals_file.exists():
            self._write([])

    def _read(self) -> list[dict]:
        try:
            return json.loads(self.approvals_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _write(self, records: list[dict]) -> None:
        self.approvals_file.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def create_request(
        self,
        request_text: str,
        reason: str,
        risk_level: str = "medium",
    ) -> dict:
        """Create a new approval request record and persist it."""
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": _now(),
            "request_text": request_text,
            "reason": reason,
            "risk_level": risk_level,
            "status": "pending",
            "required_checkpoint": True,
            "reviewed_by": None,
            "reviewed_at": None,
            "review_note": None,
        }
        records = self._read()
        records.append(record)
        self._write(records)
        return record

    def list_all(self) -> list[dict]:
        return self._read()

    def list_pending(self) -> list[dict]:
        return [record for record in self._read() if record.get("status") == "pending"]

    def count(self) -> int:
        return len(self._read())

    def review(self, selector: str, status: str, note: str = "", reviewed_by: str = "user") -> dict:
        """Approve or reject a pending approval record by ID prefix."""
        status = status.lower().strip()
        if status not in {"approved", "rejected"}:
            return {"changed": False, "reason": "Review status must be approved or rejected."}

        cleaned = selector.strip()
        if not cleaned:
            return {"changed": False, "reason": "Approval ID was empty."}

        records = self._read()
        matches = [record for record in records if str(record.get("id", "")).startswith(cleaned)]
        if not matches:
            return {"changed": False, "reason": "No matching approval request found."}
        if len(matches) > 1:
            return {"changed": False, "reason": "Approval ID prefix matches more than one request."}

        record = matches[0]
        if record.get("status") != "pending":
            return {"changed": False, "reason": f"Approval is already {record.get('status')}."}

        record["status"] = status
        record["reviewed_by"] = reviewed_by
        record["reviewed_at"] = _now()
        record["review_note"] = note.strip() or None
        self._write(records)
        return {"changed": True, "approval": record}
