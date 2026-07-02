"""
safe_storage.py
Atomic JSON read/write helpers for Lucy's Stage 3-5 foundation.
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any


def backup_file(path: str | Path) -> Path | None:
    target = Path(path)
    if not target.exists():
        return None
    backup = target.with_suffix(target.suffix + ".bak")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup)
    return backup


def safe_read_json(path: str | Path, default: Any = None) -> Any:
    target = Path(path)
    if not target.exists():
        return default

    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        backup = target.with_suffix(target.suffix + ".bak")
        if backup.exists():
            try:
                return json.loads(backup.read_text(encoding="utf-8"))
            except Exception:
                return default
        return default


def safe_write_json(path: str | Path, data: Any, backup: bool = False) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if backup and target.exists():
        backup_file(target)

    temp = target.with_name(f".{target.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temp, target)
    return target
