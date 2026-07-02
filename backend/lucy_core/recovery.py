"""
recovery.py
Recovered Lucy architecture references.

These records are reconstructed from ELIE's memory files. They are reference
history, not proof that the original Lucy code is present locally.
"""

from __future__ import annotations

import json
from pathlib import Path


class RecoveryReference:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.reference_file = lucy_data_dir / "recovered_architecture.json"

    def load(self) -> dict:
        if not self.reference_file.exists():
            return {"source": "missing", "checkpoints": []}
        try:
            return json.loads(self.reference_file.read_text(encoding="utf-8"))
        except Exception:
            return {"source": "unreadable", "checkpoints": []}

    def checkpoints(self) -> list[dict]:
        return self.load().get("checkpoints", [])

    def summary(self) -> dict:
        data = self.load()
        checkpoints = data.get("checkpoints", [])
        return {
            "source": data.get("source", "unknown"),
            "highest_recovered_checkpoint": data.get("highest_recovered_checkpoint", "unknown"),
            "confidence": data.get("confidence", "reference_only"),
            "checkpoint_count": len(checkpoints),
            "notes": data.get("notes", []),
        }
