"""
personal_profiler.py
Stage 44 = Personal Behavioral Profiler & Habit Engine (Real-Time Adaptation).

Actively tracks and learns user preferences, development cadence, shorthand aliases,
anti-drift rules, and active project states from natural conversation so Lucy adapts
dynamically to Senin Ali K P (Ali).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE = "44 personal profiler habit engine"
PROFILE_VERSION = "2.0.0"

DEFAULT_ALIASES = {
    "tv": "C:/Users/admin/Desktop/senin/android tv wallpaper",
    "drift": "C:/Users/admin/Desktop/senin/Drift-Music",
    "keys": "C:/Users/admin/Desktop/senin/api keys.txt",
    "ai": "C:/Users/admin/Desktop/senin/ai",
    "script": "C:/Users/admin/Desktop/senin/script",
    "dumps": "C:/Users/admin/Desktop/senin/LUCY/code_dumps",
    "lucy": "C:/Users/admin/Desktop/senin/LUCY/lucy",
    "spine": "data/spine.json",
    "runtime": "backend/lucy_core/lucy_runtime.py",
}

DEFAULT_ANTI_DRIFT = [
    "Do not build a Linux-style OS kernel; keep Lucy as a Windows terminal operator.",
    "Voice talking and 3D visualizer are postponed; focus strictly on terminal operator depth.",
    "Zero persona or private memory leaks to cloud workers.",
    "Standard library and verified tests first before promoting code.",
    "Lucy was designed and programmed solely by Senin as a sovereign desktop operating assistant; external APIs and local models are external tools, never Lucy's identity or creator.",
    "Always address the operator as Senin (never Ali; Ali is his middle name).",
    "Never hallucinate file existence or pretend stubbed code is finished.",
    "Prefer complete, production-ready code over truncated snippets.",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PersonalProfiler:
    """Tracks and enforces the user's personal preferences, coding habits, and anti-drift rules."""

    def __init__(self, lucy_data: Path, workspace_root: Path | None = None) -> None:
        self.lucy_data = Path(lucy_data)
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self.profile_file = self.lucy_data / "personal_profile.json"
        self.workspace_root = workspace_root
        self._ensure_profile()

    def _default_profile(self) -> dict[str, Any]:
        return {
            "version": PROFILE_VERSION,
            "stage": STAGE,
            "user_name": "Senin",
            "preferred_name": "Senin",
            "full_name": "Senin Ali K P",
            "creator": "Senin",
            "location": "Kozhikode, Kerala, India",
            "role": "AI Systems Builder, Software Developer, and Product Architect",
            "workspace_root": str(self.workspace_root or r"C:\Users\admin\Desktop\senin\LUCY\lucy"),
            "communication_preference": "Concise, technical, direct, zero boilerplate, grounded in real disk state.",
            "current_mood_or_pace": "focused_operational",
            "user_persona": {
                "brevity": "concise",
                "tone": "direct_technical",
                "explanation_depth": "minimal_unless_requested",
            },
            "coding_preferences": {
                "prefer_standard_library": True,
                "avoid_heavy_dependencies": True,
                "verify_with_ast_pytest": True,
                "custom_rules": [
                    "Use pure standard library Python whenever possible.",
                    "Preserve all existing comments and docstrings.",
                ],
            },
            "workspace_aliases": dict(DEFAULT_ALIASES),
            "aliases": dict(DEFAULT_ALIASES),
            "anti_drift_rules": list(DEFAULT_ANTI_DRIFT),
            "learned_preferences": list(DEFAULT_ANTI_DRIFT[-2:]),
            "learned_corrections": [],
            "frequent_commands": {},
            "stats": {
                "total_corrections_learned": 0,
                "total_interactions_analyzed": 0,
            },
            "created_at": _now(),
            "updated_at": _now(),
            "last_updated": _now(),
        }

    def _ensure_profile(self) -> None:
        if not self.profile_file.exists():
            self._write(self._default_profile())

    def _read(self) -> dict[str, Any]:
        try:
            data = json.loads(self.profile_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                default = self._default_profile()
                for k, v in default.items():
                    data.setdefault(k, v)
                data.setdefault("workspace_aliases", dict(DEFAULT_ALIASES))
                data.setdefault("aliases", data.get("workspace_aliases", dict(DEFAULT_ALIASES)))
                data.setdefault("anti_drift_rules", list(DEFAULT_ANTI_DRIFT))
                data.setdefault("learned_preferences", list(DEFAULT_ANTI_DRIFT[-2:]))
                data.setdefault("learned_corrections", [])
                data.setdefault("frequent_commands", {})
                data.setdefault("stats", {"total_corrections_learned": 0, "total_interactions_analyzed": 0})
                return data
        except Exception:
            pass
        return self._default_profile()

    def _write(self, data: dict[str, Any]) -> None:
        now_ts = _now()
        data["updated_at"] = now_ts
        data["last_updated"] = now_ts
        # Keep aliases synchronized
        if "workspace_aliases" in data:
            data.setdefault("aliases", {})
            for k, v in data["workspace_aliases"].items():
                data["aliases"].setdefault(k, v)
        if "aliases" in data:
            data.setdefault("workspace_aliases", {})
            for k, v in data["aliases"].items():
                data["workspace_aliases"].setdefault(k, v)

        self.profile_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def set_alias(self, alias: str, target: str) -> dict[str, Any]:
        """Registers shorthand alias (e.g. 'tv' -> 'android tv wallpaper')."""
        clean_alias = alias.strip().lower()
        clean_target = target.strip()
        if not clean_alias or not clean_target:
            return {"ok": False, "saved": False, "reason": "Alias and target cannot be empty."}
        data = self._read()
        data.setdefault("aliases", {})[clean_alias] = clean_target
        data.setdefault("workspace_aliases", {})[clean_alias] = clean_target
        self._write(data)
        return {"ok": True, "saved": True, "alias": clean_alias, "target": clean_target, "shortcut": clean_alias}

    def add_alias(self, shortcut: str, target_path: str) -> dict[str, Any]:
        """Alias for set_alias to maintain backwards compatibility."""
        return self.set_alias(shortcut, target_path)

    def resolve_alias(self, text: str) -> str:
        """Substitutes known aliases in user queries, including plain words and @alias / $alias tokens."""
        data = self._read()
        aliases = data.get("workspace_aliases", {})
        if not aliases:
            aliases = data.get("aliases", {})

        cleaned = text.strip().lower()
        if cleaned in aliases:
            return aliases[cleaned]

        reserved_command_phrases = {
            "anti drift rules", "anti drift", "drift report", "wake drift check",
            "show anti drift rules", "anti-drift rules", "drift music"
        }
        if any(phrase in cleaned for phrase in reserved_command_phrases):
            tokens = text.split()
            resolved = []
            for t in tokens:
                if t.startswith(("@", "$")):
                    clean_t = t.lstrip("@$").lower()
                    resolved.append(aliases.get(clean_t, t))
                else:
                    resolved.append(t)
            return " ".join(resolved)

        conversational_protected = {"lucy", "ai", "spine", "runtime"}
        words = text.split()
        resolved_words = []
        for w in words:
            clean_token = w.lstrip("@$").lower()
            if w.startswith(("@", "$")) and clean_token in aliases:
                resolved_words.append(aliases[clean_token])
            elif w.lower() in aliases and w.lower() not in conversational_protected:
                resolved_words.append(aliases[w.lower()])
            else:
                resolved_words.append(w)
        return " ".join(resolved_words)

    def detect_and_learn_correction(self, user_text: str) -> dict[str, Any] | None:
        """
        Analyzes user input in real time. If the user is issuing a correction or
        anti-drift directive (e.g. 'don't do X', 'never do Y', 'always do Z'),
        it automatically locks the rule into the profile.
        """
        raw = str(user_text or "").strip()
        if len(raw) < 6:
            return None

        data = self._read()
        data["stats"]["total_interactions_analyzed"] = data["stats"].get("total_interactions_analyzed", 0) + 1

        lowered = raw.lower()

        # Detection patterns for corrections and negative constraints
        correction_patterns = [
            (r"(?:don't|do not|never|stop)\s+([^.!?\n]{6,120})", "negative_constraint"),
            (r"(?:please\s+)?always\s+([^.!?\n]{6,120})", "mandatory_directive"),
            (r"(?:from now on|in the future)\s*,?\s*([^.!?\n]{6,120})", "future_directive"),
            (r"(?:make sure you|ensure that you)\s+([^.!?\n]{6,120})", "mandatory_directive"),
        ]

        extracted_rule = None
        rule_type = "correction"

        for pattern, r_type in correction_patterns:
            match = re.search(pattern, raw, re.IGNORECASE)
            if match:
                extracted_rule = match.group(0).strip().rstrip(". ") + "."
                rule_type = r_type
                break

        if not extracted_rule or len(extracted_rule) < 8:
            self._write(data)
            return None

        # Check for duplicates
        existing_rules = set(r.lower() for r in data["anti_drift_rules"])
        if extracted_rule.lower() in existing_rules:
            self._write(data)
            return None

        record = {
            "id": f"corr_{len(data['learned_corrections']) + 1:04d}",
            "timestamp": _now(),
            "raw_input": raw[:300],
            "extracted_rule": extracted_rule,
            "rule_type": rule_type,
        }

        data["learned_corrections"].append(record)
        data["anti_drift_rules"].append(extracted_rule)
        prefs = data.setdefault("learned_preferences", [])
        if extracted_rule not in prefs:
            prefs.append(extracted_rule)
            data["learned_preferences"] = prefs[-25:]

        data["stats"]["total_corrections_learned"] = data["stats"].get("total_corrections_learned", 0) + 1
        self._write(data)

        return {"learned": True, "correction": record}

    def observe_interaction(self, user_text: str) -> dict[str, Any]:
        """
        Automatically learns user preferences, pace signals, and alias definitions
        directly from natural language without requiring special CLI syntax.
        """
        raw = str(user_text or "").strip()
        lowered = raw.lower()
        updates: list[str] = []

        # 1. Trigger correction learning first so disk state is established
        correction_res = self.detect_and_learn_correction(raw)
        if correction_res and correction_res.get("learned"):
            updates.append(f"correction:{correction_res['correction']['extracted_rule'][:40]}")

        # Read latest disk data after correction
        data = self._read()

        # 2. Detect natural alias creation: "alias X to Y" or "shortcut X = Y"
        alias_match = re.search(
            r"(?:set\s+alias|add\s+alias|alias|shortcut)\s+([a-zA-Z0-9_\-]+)\s*(?:=|to|as)\s*([^\n,;]+)",
            raw,
            re.IGNORECASE,
        )
        if alias_match:
            alias_key = alias_match.group(1).strip().lower()
            alias_val = alias_match.group(2).strip().strip("'\"`")
            data.setdefault("aliases", {})[alias_key] = alias_val
            data.setdefault("workspace_aliases", {})[alias_key] = alias_val
            updates.append(f"alias:{alias_key}->{alias_val}")

        # 3. Detect explicit communication/workflow preferences
        pref_patterns = [
            r"(?:i prefer|always|never|from now on|make sure you|don't ever)\s+([^.!?\n]{8,140})",
        ]
        for pat in pref_patterns:
            m = re.search(pat, raw, re.IGNORECASE)
            if m:
                rule = m.group(0).strip().rstrip(". ") + "."
                prefs = data.setdefault("learned_preferences", [])
                if rule not in prefs:
                    prefs.append(rule)
                    data["learned_preferences"] = prefs[-25:]
                    updates.append(f"preference:{rule[:40]}")
                anti_drift = data.setdefault("anti_drift_rules", [])
                if rule not in anti_drift:
                    anti_drift.append(rule)

        # 4. Detect human state / operational pacing signals
        if any(w in lowered for w in ["quick", "fast", "short", "tldr", "in a hurry"]):
            data["current_mood_or_pace"] = "concise_rapid"
            updates.append("pace:concise_rapid")
        elif any(w in lowered for w in ["step by step", "explain", "confused", "slow down"]):
            data["current_mood_or_pace"] = "detailed_walkthrough"
            updates.append("pace:detailed_walkthrough")
        elif any(w in lowered for w in ["debug", "fix", "broken", "error", "not working"]):
            data["current_mood_or_pace"] = "deep_engineering_diagnostic"
            updates.append("pace:deep_engineering_diagnostic")

        # 5. Track command frequency
        first_word = lowered.split()[0] if lowered.split() else ""
        if first_word:
            freq = data.setdefault("frequent_commands", {})
            freq[first_word] = int(freq.get(first_word, 0)) + 1

        if updates:
            self._write(data)

        return {
            "adapted": bool(updates),
            "updates": updates,
            "pace": data.get("current_mood_or_pace"),
        }

    def add_anti_drift_rule(self, rule_text: str, source: str = "manual") -> dict[str, Any]:
        """Manually adds a high-priority anti-drift rule."""
        cleaned = str(rule_text or "").strip().rstrip(". ") + "."
        if len(cleaned) < 5:
            return {"saved": False, "reason": "Rule too short."}

        data = self._read()
        existing = [r.lower() for r in data["anti_drift_rules"]]
        if cleaned.lower() in existing:
            return {"saved": False, "duplicate": True}

        data["anti_drift_rules"].append(cleaned)
        prefs = data.setdefault("learned_preferences", [])
        if cleaned not in prefs:
            prefs.append(cleaned)
        self._write(data)
        return {"saved": True, "rule": cleaned, "source": source}

    def set_preference(self, category: str, key: str, value: Any) -> dict[str, Any]:
        """Updates a user persona or coding preference."""
        data = self._read()
        cat = category.strip().lower()
        if cat not in data:
            data[cat] = {}

        if isinstance(data[cat], dict):
            data[cat][key] = value
            self._write(data)
            return {"updated": True, "category": cat, "key": key, "value": value}

        return {"updated": False, "reason": f"Category '{cat}' is not a dictionary."}

    def get_personal_prompt_snippet(self) -> str:
        """
        Generates a concise, high-priority alignment prompt block
        injected into every Ollama conversational generation.
        """
        data = self._read()
        persona = data.get("user_persona", {})
        coding = data.get("coding_preferences", {})
        anti_drift = data.get("anti_drift_rules", [])
        aliases = data.get("workspace_aliases", data.get("aliases", {}))
        pace = data.get("current_mood_or_pace", "focused_operational")
        user_name = data.get("user_name", "Senin Ali K P (Ali)")

        user_name = data.get("preferred_name") or data.get("user_name", "Senin")
        full_name = data.get("full_name", "Senin Ali K P")
        creator = data.get("creator", "Senin")
        key_rules = "; ".join(anti_drift[:4]) if anti_drift else "Standard boundaries."
        key_aliases = ", ".join(f"{k}->{Path(v).name}" for k, v in list(aliases.items())[:5])

        snippet = (
            f"[User Personal Alignment & Habits]:\n"
            f"- Operator & Creator: {user_name} (Full Name: {full_name}; Always address as {user_name}, never Ali - Ali is middle name)\n"
            f"- Lucy Identity: Sovereign desktop AI designed and programmed solely by {creator}. External APIs and local LLMs are tools, not her identity or creator.\n"
            f"- Operational Pace: {pace}\n"
            f"- Style: Brevity={persona.get('brevity', 'concise')}, Tone={persona.get('tone', 'direct_technical')}\n"
            f"- Coding Rules: Stdlib preferred={coding.get('prefer_standard_library', True)}, Verify with AST/tests first.\n"
            f"- Anti-Drift Guardrails: {key_rules}\n"
            f"- Known Project Aliases: {key_aliases}"
        )
        return snippet

    def status(self) -> dict[str, Any]:
        """Returns status snapshot of personal profiler."""
        data = self._read()
        aliases = data.get("workspace_aliases", data.get("aliases", {}))
        anti_drift = data.get("anti_drift_rules", [])
        learned = data.get("learned_corrections", [])
        return {
            "stage": STAGE,
            "personal_profiler": "active",
            "profile_file": str(self.profile_file),
            "anti_drift_rules_count": len(anti_drift),
            "anti_drift_rules": anti_drift,
            "workspace_aliases_count": len(aliases),
            "workspace_aliases": aliases,
            "aliases": data.get("aliases", aliases),
            "learned_corrections_count": len(learned),
            "learned_corrections": learned,
            "user_persona": data.get("user_persona", {}),
            "coding_preferences": data.get("coding_preferences", {}),
            "current_mood_or_pace": data.get("current_mood_or_pace", "focused_operational"),
            "current_pace": data.get("current_mood_or_pace", "focused_operational"),
            "learned_preferences": data.get("learned_preferences", []),
            "frequent_commands": data.get("frequent_commands", {}),
            "stats": data.get("stats", {}),
        }
