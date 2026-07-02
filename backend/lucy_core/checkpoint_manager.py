"""
checkpoint_manager.py
Creates and manages checkpoint records for Lucy.
No rollback automation — records only.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


class CheckpointManager:
    def __init__(self, checkpoints_dir: Path) -> None:
        self.checkpoints_dir = checkpoints_dir
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    def _next_id(self) -> str:
        existing = sorted(self.checkpoints_dir.glob("checkpoint_*.json"))
        return f"checkpoint_{len(existing) + 1:04d}"

    def create(
        self,
        reason: str,
        stage: str = "Core Runtime Prototype",
        files_changed_summary: str = "No files changed.",
        safety_status: str = "safe",
        next_step: str = "Continue development.",
    ) -> dict:
        """Create a new checkpoint JSON file."""
        checkpoint_id = self._next_id()
        record = {
            "checkpoint_id": checkpoint_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "reason": reason,
            "files_changed_summary": files_changed_summary,
            "safety_status": safety_status,
            "next_step": next_step,
        }
        out_path = self.checkpoints_dir / f"{checkpoint_id}.json"
        out_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return record

    def list_checkpoints(self) -> list[dict]:
        result = []
        for path in sorted(self.checkpoints_dir.glob("checkpoint_*.json")):
            try:
                result.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                pass
        return result

    def count(self) -> int:
        return len(list(self.checkpoints_dir.glob("checkpoint_*.json")))
