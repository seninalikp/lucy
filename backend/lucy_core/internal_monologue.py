"""
internal_monologue.py
Stage 68: Sovereign Internal Monologue & Pre-Output Verification Spine.

Provides Lucy with a private, zero-latency cognitive scratchpad (<thought>...</thought>)
where she evaluates user state, verifies memory facts against the local graph, and calibrates
her tone (authentic human peer engineer, non-sycophantic, zero stiff robot) before emitting
verified stdout to the terminal.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

STAGE = "68 sovereign internal monologue and pre-output verification spine"

# Regex for extracting thought blocks
THOUGHT_PATTERN = re.compile(r"<thought>(.*?)</thought>", re.DOTALL | re.IGNORECASE)
RESPONSE_PATTERN = re.compile(r"<response>(.*?)</response>", re.DOTALL | re.IGNORECASE)

# Robotic phrases to sanitize from final output
BOT_PHRASES = [
    (re.compile(r"\b(as an ai(?: language model)?|i am an ai(?: language model)?)\b", re.I), ""),
    (re.compile(r"\b(i do not have (?:feelings|emotions|a body))\b", re.I), ""),
    (re.compile(r"\bi apologize for (?:the|any) confusion\b", re.I), "my bad"),
    (re.compile(r"\bi apologize for (?:the|any) inconvenience\b", re.I), "my bad"),
    (re.compile(r"\bi am programmed to\b", re.I), "i'm built to"),
    (re.compile(r"\bcertainly! i would be (?:happy|delighted|pleased) to help you\b", re.I), "on it"),
    (re.compile(r"\bcertainly! i can (?:certainly )?help with that\b", re.I), "on it"),
    (re.compile(r"\bhow may i assist you today\??\b", re.I), "what's on your mind?"),
]

# Action verbs that indicate claiming a file or task was executed
FALSE_ACTION_PATTERNS = [
    re.compile(r"\bi have (?:created|modified|edited|deleted|executed|written|patched)\s+(?:file\s+|the file\s+)?([A-Za-z0-9_./\\-]+\.[a-zA-Z0-9]+)\b", re.I),
    re.compile(r"\bi (?:created|modified|edited|deleted|wrote|patched)\s+(?:file\s+|the file\s+)?([A-Za-z0-9_./\\-]+\.[a-zA-Z0-9]+)\b", re.I),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ThoughtRecord:
    """Represents a single turn's internal monologue and verification audit."""

    def __init__(
        self,
        user_input: str,
        raw_thought: str = "",
        clean_response: str = "",
        user_vibe: str = "neutral",
        verified_facts: Optional[List[str]] = None,
        flagged_claims: Optional[List[str]] = None,
        tone_calibration: str = "direct_peer",
    ) -> None:
        self.timestamp = _now_iso()
        self.user_input = user_input
        self.raw_thought = raw_thought.strip()
        self.clean_response = clean_response.strip()
        self.user_vibe = user_vibe
        self.verified_facts = verified_facts or []
        self.flagged_claims = flagged_claims or []
        self.tone_calibration = tone_calibration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "user_input": self.user_input,
            "raw_thought": self.raw_thought,
            "clean_response": self.clean_response,
            "user_vibe": self.user_vibe,
            "verified_facts": self.verified_facts,
            "flagged_claims": self.flagged_claims,
            "tone_calibration": self.tone_calibration,
        }

    def format_debug_view(self) -> str:
        """Formats the internal monologue for the /thought terminal command."""
        lines = [
            "+--- [Lucy Internal Monologue Scratchpad] --------------------------+",
            f"| Timestamp: {self.timestamp}",
            f"| User Query: '{self.user_input[:65]}'",
            f"| Detected Vibe: {self.user_vibe} | Tone: {self.tone_calibration}",
        ]
        if self.raw_thought:
            lines.append("| Thought Content:")
            for t_line in self.raw_thought.splitlines():
                lines.append(f"|   {t_line}")
        else:
            lines.append("| Thought Content: (Implicit fast-path reasoning)")
        
        if self.verified_facts:
            lines.append(f"| Verified Facts: {', '.join(self.verified_facts[:4])}")
        if self.flagged_claims:
            lines.append(f"| Flagged Unverified Claims: {', '.join(self.flagged_claims)}")
        lines.append("+------------------------------------------------------------------+")
        return "\n".join(lines)


class InternalMonologueSpine:
    """
    Manages the two-pass internal reasoning scratchpad and pre-output verification.
    """

    def __init__(
        self,
        memory_graph: Any = None,
        fact_verifier: Any = None,
        max_history: int = 25,
    ) -> None:
        self.memory_graph = memory_graph
        self.fact_verifier = fact_verifier
        self.max_history = max_history
        self._thought_history: List[ThoughtRecord] = []
        self._last_thought: Optional[ThoughtRecord] = None

    def get_last_thought(self) -> Optional[ThoughtRecord]:
        return self._last_thought

    def get_thought_history(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._thought_history]

    def parse_user_vibe(self, user_input: str) -> str:
        """Lightweight heuristic to detect user state and emotional vibe."""
        lowered = user_input.lower()
        if any(w in lowered for w in ["error", "traceback", "failed", "broken", "bug", "why is", "help fix"]):
            return "debugging_high_focus"
        if any(w in lowered for w in ["finally", "worked", "passed", "awesome", "perfect", "nice"]):
            return "relief_victory"
        if any(w in lowered for w in ["late", "tired", "midnight", "exhausted", "sleep"]):
            return "late_night_grind"
        if any(w in lowered for w in ["hey", "yo", "bro", "lucy", "how are you", "what's up", "cool"]):
            return "casual_banter"
        if "?" in user_input and len(user_input.split()) <= 4:
            return "quick_inquiry"
        return "collaborative_operator"

    def verify_action_claims(self, text: str, receipts: Optional[List[Any]] = None) -> Tuple[str, List[str]]:
        """
        Anti-hallucination guard: checks if the response claims to have modified/created a file
        without having executed a tool or having a receipt in this turn.
        """
        flagged: List[str] = []
        has_valid_receipt = bool(receipts and len(receipts) > 0)

        cleaned = text
        for pat in FALSE_ACTION_PATTERNS:
            for match in pat.finditer(cleaned):
                target_file = match.group(1).strip()
                if not has_valid_receipt:
                    # Model hallucinated action without a receipt
                    flagged.append(f"unverified_action_on_{target_file}")
                    # Replace false claim with grounding assertion
                    original = match.group(0)
                    grounded = f"I am referencing {target_file}"
                    cleaned = cleaned.replace(original, grounded)

        return cleaned, flagged

    def sanitize_bot_tropes(self, text: str) -> str:
        """Strips generic bot apologies and sycophantic corporate phrasing."""
        cleaned = text
        for pat, repl in BOT_PHRASES:
            cleaned = pat.sub(repl, cleaned)
        # Normalize whitespace
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
        return cleaned.strip()

    def process(
        self,
        user_input: str,
        raw_model_output: str,
        receipts: Optional[List[Any]] = None,
    ) -> Tuple[str, ThoughtRecord]:
        """
        Executes pre-output verification:
        1. Extracts thought scratchpad if model used <thought>...</thought>.
        2. Unwraps <response>...</response> if present.
        3. Sanitizes corporate bot tropes and sycophancy.
        4. Verifies action claims against receipts to prevent false execution claims.
        5. Records and returns the verified clean response + thought record.
        """
        raw = str(raw_model_output or "").strip()
        thought_content = ""
        clean_text = raw

        # Step 1: Extract thought tag
        thought_match = THOUGHT_PATTERN.search(raw)
        if thought_match:
            thought_content = thought_match.group(1).strip()
            # Strip thought tags from output text
            clean_text = THOUGHT_PATTERN.sub("", clean_text).strip()

        # Step 2: Unwrap response tags if model used them
        resp_match = RESPONSE_PATTERN.search(clean_text)
        if resp_match:
            clean_text = resp_match.group(1).strip()

        # Step 3: Analyze vibe & calibration
        vibe = self.parse_user_vibe(user_input)
        tone = "peer_engineer_direct"
        if vibe == "relief_victory":
            tone = "celebratory_relaxed"
        elif vibe == "late_night_grind":
            tone = "attuned_supportive"
        elif vibe == "casual_banter":
            tone = "wry_easygoing"

        # Step 4: Verify facts / memory references if memory graph is available
        verified_facts: List[str] = []
        if self.memory_graph and hasattr(self.memory_graph, "query"):
            try:
                nodes = self.memory_graph.query(query_text=user_input, limit=3)
                for n in nodes:
                    f = n.get("fact") or n.get("content")
                    if f:
                        verified_facts.append(str(f))
            except Exception:
                pass

        # Step 5: Anti-hallucination check on action claims
        clean_text, flagged = self.verify_action_claims(clean_text, receipts=receipts)

        # Step 6: Sanitize bot clichés
        clean_text = self.sanitize_bot_tropes(clean_text)

        # Fallback if thought was empty (fast path implicit reasoning)
        if not thought_content:
            thought_content = f"[Implicit Reasoning]: Vibe={vibe}. Tone={tone}. Verified {len(verified_facts)} facts."

        record = ThoughtRecord(
            user_input=user_input,
            raw_thought=thought_content,
            clean_response=clean_text,
            user_vibe=vibe,
            verified_facts=verified_facts,
            flagged_claims=flagged,
            tone_calibration=tone,
        )

        self._last_thought = record
        self._thought_history.append(record)
        if len(self._thought_history) > self.max_history:
            self._thought_history.pop(0)

        return clean_text, record

    def status(self) -> Dict[str, Any]:
        return {
            "stage": STAGE,
            "internal_monologue": "active",
            "total_thoughts_recorded": len(self._thought_history),
            "has_last_thought": self._last_thought is not None,
            "last_thought_vibe": self._last_thought.user_vibe if self._last_thought else None,
            "last_thought_tone": self._last_thought.tone_calibration if self._last_thought else None,
        }
