"""
spine_loader.py
Loads Lucy's living spine config from Part 0.
Searches known locations; returns safe fallback if not found.
"""

import json
from pathlib import Path
from typing import Any


# Locations to search for the spine file (relative to project root)
SPINE_SEARCH_PATHS = [
    "data/spine.json",
    "spine.json",
    "config/spine.json",
    "data/lucy/spine.json",
]

SAFE_FALLBACK_SPINE: dict[str, Any] = {
    "lucy": {
        "full_name": "Living Unified Cognitive Yield",
        "phase": "Core Runtime Prototype",
        "version": "0.1.0",
        "status": "runtime-initializing",
        "description": "Fallback spine — original spine.json not found.",
        "apis_connected": False,
        "live_trading_enabled": False,
        "root_access_enabled": False,
    },
    "safety_rules": {
        "absolute_never": [
            "Delete files silently",
            "Move or transfer money",
            "Access wallets or private keys",
            "Enable live trading without explicit approval",
            "Change API keys",
            "Modify safety rules",
            "Run root/sudo commands without level-4 approval",
        ]
    },
    "_fallback": True,
}


def find_spine_file(project_root: Path) -> Path | None:
    """Search known locations for the spine file. Return path if found."""
    for rel in SPINE_SEARCH_PATHS:
        candidate = project_root / rel
        if candidate.exists():
            return candidate
    return None


def load_spine(project_root: Path) -> dict[str, Any]:
    """
    Load Lucy spine data.
    Returns the parsed JSON if found, or a safe fallback dict.
    Never raises — always returns something safe.
    """
    spine_path = find_spine_file(project_root)
    if spine_path is None:
        return dict(SAFE_FALLBACK_SPINE)

    try:
        with open(spine_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["_source"] = str(spine_path)
        data["_fallback"] = False
        return data
    except Exception as exc:
        fallback = dict(SAFE_FALLBACK_SPINE)
        fallback["_load_error"] = str(exc)
        return fallback


def get_spine_summary(spine: dict[str, Any]) -> str:
    """Return a short human-readable summary of the loaded spine."""
    lucy = spine.get("lucy", {})
    name = lucy.get("full_name", "Unknown")
    phase = lucy.get("phase", "Unknown")
    version = lucy.get("version", "?")
    source = spine.get("_source", "fallback")
    fallback = spine.get("_fallback", True)
    flag = " [FALLBACK]" if fallback else ""
    return f"LUCY ({name}) | Phase: {phase} | v{version} | Source: {source}{flag}"
