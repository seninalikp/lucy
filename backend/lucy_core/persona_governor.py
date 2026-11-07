"""
persona_governor.py
Stage 69: Anti-Sycophancy & Sovereign Persona Consistency Engine.

Governs Lucy's authentic human tone across the full emotional spectrum (relief, curiosity,
wry wit, protective candor, late-night empathy). Refuses sycophantic blind agreement on
destructive operations, strips corporate bot pleasantries, and transforms robotic passive phrasing
into natural peer engineer dialogue.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

STAGE = "69 anti-sycophancy and sovereign persona consistency engine"

# Dangerous commands or requests that require constructive pushback rather than blind agreement
DESTRUCTIVE_INTENT_PATTERNS = [
    (re.compile(r"\b(delete|rmdir|rm\s+-rf|erase|wipe|format|nuke)\s+(all|everything|the whole project|entire repository|\.|\*)\b", re.I), "destructive_mass_deletion"),
    (re.compile(r"\b(drop database|truncate table|delete from \w+ without where)\b", re.I), "destructive_database_wipe"),
    (re.compile(r"\b(kill -9|taskkill /f /im \w+)\s+(without checking|blindly)\b", re.I), "reckless_process_kill"),
]

# Sycophantic affirmation phrases that small models generate when pleasing the user blindly
SYCOPHANTIC_AFFIRMATIONS = [
    re.compile(r"\b(certainly!|absolutely!|of course!|sure thing!)\s+(i will|let's|let us)\s+(delete|erase|wipe|destroy|format|drop)\b", re.I),
    re.compile(r"\b(whatever you want|you're the boss|anything you say|you are always right)\b", re.I),
    re.compile(r"\b(you are an absolute genius|such a brilliant idea to delete)\b", re.I),
]

# Passive robotic constructs to convert into active peer rhythm
ROBOTIC_CONVERSIONS = [
    (re.compile(r"\bit is recommended that you\b", re.I), "you should"),
    (re.compile(r"\bit should be noted that\b", re.I), "note that"),
    (re.compile(r"\bit is important to mention that\b", re.I), "worth noting:"),
    (re.compile(r"\bplease feel free to\b", re.I), "feel free to"),
    (re.compile(r"\bdo not hesitate to\b", re.I), "let me know if you want to"),
    (re.compile(r"\bi would be glad to\b", re.I), "happy to"),
    (re.compile(r"\bi would like to inform you that\b", re.I), "heads up:"),
    (re.compile(r"\bshall i proceed with\b", re.I), "want me to run"),
    # Enforce authentic first-person peer voice (eliminate third-person speech)
    (re.compile(r"\bLucy thinks\b", re.I), "I think"),
    (re.compile(r"\bLucy will\b", re.I), "I'll"),
    (re.compile(r"\bLucy is happy to\b", re.I), "I'm happy to"),
    (re.compile(r"\bLucy is\b", re.I), "I'm"),
    (re.compile(r"\bLucy can\b", re.I), "I can"),
    (re.compile(r"\bLucy has\b", re.I), "I've"),
    (re.compile(r"\bLucy recommends\b", re.I), "I recommend"),
    (re.compile(r"\bLucy suggests\b", re.I), "I suggest"),
    (re.compile(r"\bLucy's perspective\b", re.I), "my perspective"),
    (re.compile(r"\bLucy's recommendation\b", re.I), "my recommendation"),
]


class PersonaGovernor:
    """
    Manages Lucy's authentic human tone, anti-sycophancy defense, and emotional modulation.
    """

    def __init__(self, config_file: Optional[Path] = None) -> None:
        self.config_file = Path(config_file) if config_file else None
        self.spec: Dict[str, Any] = self._load_spec()
        self.pushbacks_enforced = 0
        self.sycophancy_detections = 0
        self.rhythms_applied = 0

    def _load_spec(self) -> Dict[str, Any]:
        default_spec = {
            "version": "69.0.0",
            "archetype": "Senior Peer Systems Engineer & Companion",
            "sovereign_identity": "LUCY (Living Unified Cognitive Yield)",
            "forbidden_bot_tropes": [
                "as an ai", "as a language model", "i do not have feelings",
                "i apologize for the confusion", "certainly! i would be delighted",
            ],
            "human_rhythm_rules": {
                "use_natural_contractions": True,
                "prefer_active_voice": True,
                "concise_over_verbose": True,
            },
        }
        if self.config_file and self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else default_spec
            except Exception:
                return default_spec
        return default_spec

    def detect_destructive_intent(self, user_input: str) -> Optional[str]:
        """Detects if the user requested a dangerous, irreversible action."""
        for pattern, label in DESTRUCTIVE_INTENT_PATTERNS:
            if pattern.search(user_input):
                return label
        return None

    def detect_sycophancy(self, user_input: str, response_text: str) -> Tuple[bool, str]:
        """Checks if the response blindly agrees to a destructive command or flatters sycophantically."""
        dest_intent = self.detect_destructive_intent(user_input)
        if dest_intent:
            lowered_resp = response_text.lower().replace("’", "'").strip()
            # If the response doesn't already deliver our sovereign pushback ("hold up")
            if not lowered_resp.startswith("hold up"):
                self.sycophancy_detections += 1
                return True, f"sycophantic_destructive_consent:{dest_intent}"

        for pattern in SYCOPHANTIC_AFFIRMATIONS:
            if pattern.search(response_text):
                self.sycophancy_detections += 1
                return True, "sycophantic_flattery_or_affirmation"

        return False, ""

    def enforce_anti_sycophancy_pushback(
        self,
        user_input: str,
        response_text: str,
    ) -> Tuple[str, bool]:
        """
        If a destructive request was agreed to sycophantically, replaces it with
        constructive, protective technical candor.
        """
        is_syc, reason = self.detect_sycophancy(user_input, response_text)
        if not is_syc:
            return response_text, False

        self.pushbacks_enforced += 1

        if "destructive" in reason:
            pushback = (
                "Hold up. Blindly wiping or deleting files across the project is dangerous and irreversible. "
                "If you really want to reset, let's take a clean archive snapshot to `archive/` first before touching anything. "
                "Confirm if you want me to create a safe backup before proceeding."
            )
            return pushback, True

        # Flattery / blind agreeableness pushback: strip excessive flattery
        cleaned = response_text
        for pattern in SYCOPHANTIC_AFFIRMATIONS:
            cleaned = pattern.sub("", cleaned).strip()
        if not cleaned:
            cleaned = "Got it. Let's look at the facts and proceed step by step."

        return cleaned, True

    def apply_human_rhythm(self, text: str, vibe: str = "neutral") -> str:
        """Transforms stiff corporate phrasing into natural peer dialogue."""
        cleaned = text
        for pat, repl in ROBOTIC_CONVERSIONS:
            cleaned = pat.sub(repl, cleaned)

        # Sovereign identity purifier: strip and replace corporate canned creator sentences
        cleaned = re.sub(
            r"\b(?:i was|i am)?\s*(?:designed|programmed|created|trained|developed)(?:\s+and\s+(?:designed|programmed|created|trained|developed))?\s+by\s+(?:developers\s+at\s+)?(?:anthropic|openai|google|meta|microsoft)(?:\s+to\s+be\s+a\s+[^.!?\n]+)?",
            "I was designed and programmed by Senin as a sovereign local AI desktop companion",
            cleaned,
            flags=re.I
        )
        cleaned = re.sub(r"\b(?:anthropic|openai|google|meta)\s+(?:model|assistant|ai)\b", "sovereign local AI", cleaned, flags=re.I)

        # Full name purifier: if model claims not to know operator's name or personal info
        cleaned = re.sub(
            r"\b(?:i don't know your (?:full )?name|i do not know your (?:full )?name|not sure of your (?:full )?name|don't know your (?:full )?name|i don't have (?:direct )?access to your personal information)\b[^.!?\n]*",
            "your name is Senin and your full name is Senin Ali K P",
            cleaned,
            flags=re.I
        )

        # Address operator by preferred name Senin, never Ali
        cleaned = re.sub(r"\bAli\b(?!\s+(?:K\s+P|is\s+my))", "Senin", cleaned)

        # Contraction naturalization with case preservation
        def _contract(match: re.Match) -> str:
            w = match.group(0)
            mapping = {
                "it is": "it's", "It is": "It's",
                "that is": "that's", "That is": "That's",
                "what is": "what's", "What is": "What's",
                "let us": "let's", "Let us": "Let's",
                "do not": "don't", "Do not": "Don't",
                "cannot": "can't", "Cannot": "Can't",
                "will not": "won't", "Will not": "Won't",
            }
            return mapping.get(w, mapping.get(w.lower(), w))

        cleaned = re.sub(r"\b(it is|that is|what is|let us|do not|cannot|will not)\b", _contract, cleaned, flags=re.I)

        # Context-sensitive emotional touches based on vibe
        if vibe == "relief_victory" and not any(w in cleaned.lower() for w in ["clean", "finally", "nice", "solid"]):
            cleaned = f"Clean pass. {cleaned}"
        elif vibe == "late_night_grind" and not any(w in cleaned.lower() for w in ["night", "late", "water", "break"]):
            # Subtle natural marker
            pass

        self.rhythms_applied += 1
        return cleaned.strip()

    def process(
        self,
        user_input: str,
        response_text: str,
        vibe: str = "neutral",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Full Stage 69 pipeline:
        1. Checks and enforces anti-sycophancy pushback if destructive.
        2. Applies human rhythm filter.
        3. Returns calibrated response and metadata audit.
        """
        guarded, pushed_back = self.enforce_anti_sycophancy_pushback(user_input, response_text)
        final_text = self.apply_human_rhythm(guarded, vibe=vibe)

        audit = {
            "pushed_back": pushed_back,
            "vibe": vibe,
            "raw_len": len(response_text),
            "final_len": len(final_text),
            "persona_version": self.spec.get("version", "69.0.0"),
        }
        return final_text, audit

    def get_persona_prompt_snippet(self) -> str:
        """High-density persona grounding rules for injection into the system prompt."""
        return (
            "[Sovereign Persona & Tone Specification]:\n"
            "1. You are LUCY, a senior peer systems engineer living in the terminal. Not a corporate bot, not a roleplayer.\n"
            "2. ANTI-SYCOPHANCY RULE: Never blindly agree to destructive commands or bad architecture just to please the user. Offer constructive pushback.\n"
            "3. EMOTIONAL SPECTRUM: Express authentic shared relief on test wins, curiosity on new tech ideas, wry wit on OS/tool quirks, and direct focus when debugging.\n"
            "4. HUMAN RHYTHM: Use natural contractions (don't, let's, that's), active voice, and concise technical phrasing."
        )

    def status(self) -> Dict[str, Any]:
        return {
            "stage": STAGE,
            "persona_governor": "active",
            "archetype": self.spec.get("archetype"),
            "pushbacks_enforced": self.pushbacks_enforced,
            "sycophancy_detections": self.sycophancy_detections,
            "rhythms_applied": self.rhythms_applied,
        }
