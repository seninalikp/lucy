"""
context_summarizer.py
Stage 67: Rolling Episodic Context Summarizer & Context Window Guard.

Maintains an on-the-fly, zero-latency Episodic Session Digest for older conversation turns
that slide out of the verbatim message array. Ensures local Ollama models (e.g. qwen2.5:3b)
retain deep context across 50+ turn sessions without token bloat, hallucinations, or forgotten threads.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

STAGE = "67 rolling episodic context summarizer"

# Maximum token budget target for local models (e.g., qwen2.5:3b)
DEFAULT_MAX_CONTEXT_TOKENS = 2500
APPROX_CHARS_PER_TOKEN = 4.0

DECISION_MARKERS = [
    re.compile(r"\b(we will|let's|i will|let us|decided to|switching to|using|switch to|set|configured|chose)\b\s+([^.!?\n]+)", re.I),
    re.compile(r"\b(my favorite|my primary|my main|my stack|my project|my editor)\s+is\s+([^.!?\n]+)", re.I),
]

EMOTION_VIBE_MARKERS = {
    "focused_debugging": ["error", "traceback", "failed", "bug", "fix", "exception", "broken", "issue"],
    "relief_satisfaction": ["finally", "fixed", "worked", "passed", "perfect", "clean", "great", "awesome", "nice"],
    "casual_banter": ["hey", "yo", "bro", "lucy", "what's up", "how are you", "cool", "haha", "lol", "fun"],
    "philosophical_strategy": ["architecture", "sovereign", "vision", "roadmap", "future", "long term", "strategy"],
    "late_night_grind": ["midnight", "late", "tired", "grind", "sleep", "2 am", "3 am", "night"],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def estimate_tokens(text: str) -> int:
    """Fast, deterministic token estimation without heavy tokenizer dependencies."""
    if not text:
        return 0
    return max(1, int(len(text) / APPROX_CHARS_PER_TOKEN))


class EpisodicSessionDigest:
    """Structured representation of older conversational turns."""

    def __init__(self) -> None:
        self.summary_points: List[str] = []
        self.key_entities: List[str] = []
        self.decisions_made: List[str] = []
        self.vibe_spectrum: Set[str] = set()
        self.total_compressed_turns: int = 0
        self.last_compressed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary_points": self.summary_points,
            "key_entities": self.key_entities,
            "decisions_made": self.decisions_made,
            "vibe_spectrum": sorted(list(self.vibe_spectrum)),
            "total_compressed_turns": self.total_compressed_turns,
            "last_compressed_at": self.last_compressed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EpisodicSessionDigest:
        digest = cls()
        digest.summary_points = list(data.get("summary_points", []))
        digest.key_entities = list(data.get("key_entities", []))
        digest.decisions_made = list(data.get("decisions_made", []))
        digest.vibe_spectrum = set(data.get("vibe_spectrum", []))
        digest.total_compressed_turns = int(data.get("total_compressed_turns", 0))
        digest.last_compressed_at = data.get("last_compressed_at")
        return digest

    def format_context_block(self) -> str:
        """Renders a high-density, low-token context frame for system prompt injection."""
        if self.total_compressed_turns == 0 and not self.summary_points:
            return ""

        lines = [
            f"[Session Episodic Memory ({self.total_compressed_turns} earlier turns compressed)]:"
        ]
        if self.summary_points:
            recap = "; ".join(self.summary_points[-5:])
            lines.append(f"- Flow: {recap}")
        if self.decisions_made:
            decs = "; ".join(self.decisions_made[-4:])
            lines.append(f"- Decisions: {decs}")
        if self.key_entities:
            ents = ", ".join(self.key_entities[-8:])
            lines.append(f"- Key Subjects: {ents}")
        if self.vibe_spectrum:
            vibes = ", ".join(sorted(list(self.vibe_spectrum)))
            lines.append(f"- Dynamic Tone: {vibes}")

        return "\n".join(lines)


class EpisodicContextSummarizer:
    """
    Manages the rolling compression of older turns into an EpisodicSessionDigest,
    preventing working memory amnesia while respecting token limits.
    """

    def __init__(
        self,
        lucy_data: Optional[Path] = None,
        max_sliding_turns: int = 5,
        max_token_budget: int = DEFAULT_MAX_CONTEXT_TOKENS,
    ) -> None:
        self.lucy_data = Path(lucy_data) if lucy_data else None
        self.max_sliding_turns = max_sliding_turns
        self.max_token_budget = max_token_budget
        self.digest = EpisodicSessionDigest()
        self.persisted_file: Optional[Path] = None

        if self.lucy_data:
            self.persisted_file = self.lucy_data / "episodic_digest.json"
            self.load()

    def has_digest(self) -> bool:
        return self.digest.total_compressed_turns > 0 or bool(self.digest.summary_points)

    def load(self) -> None:
        if self.persisted_file and self.persisted_file.exists():
            try:
                data = json.loads(self.persisted_file.read_text(encoding="utf-8"))
                self.digest = EpisodicSessionDigest.from_dict(data)
            except Exception:
                self.digest = EpisodicSessionDigest()

    def save(self) -> None:
        if self.persisted_file:
            try:
                self.persisted_file.parent.mkdir(parents=True, exist_ok=True)
                self.persisted_file.write_text(
                    json.dumps(self.digest.to_dict(), indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            except Exception:
                pass

    def extract_turn_signals(self, user_text: str, reply_text: str) -> Dict[str, Any]:
        """Extracts key subjects, decisions, and tone from a single turn."""
        combined = f"{user_text}\n{reply_text}"
        lowered = combined.lower()

        # 1. Decisions
        decisions: List[str] = []
        for pat in DECISION_MARKERS:
            for match in pat.finditer(combined):
                snippet = match.group(0).strip()
                if len(snippet) > 8 and len(snippet) < 90:
                    decisions.append(snippet)

        # 2. Key Entities (capitalized phrases, file names, port numbers, tool names)
        entities: Set[str] = set()
        # Find path-like or code terms
        for match in re.finditer(r"\b[A-Za-z0-9_-]+\.(py|json|md|bat|sh|txt|html|js)\b", combined):
            entities.add(match.group(0))
        # Find port numbers
        for match in re.finditer(r"\b(port\s+\d+|localhost:\d+|127\.0\.0\.1:\d+)\b", combined, re.I):
            entities.add(match.group(0))
        # Find notable capitalized multi-word subjects (e.g., Drift Music, Neovim, Ollama)
        for match in re.finditer(r"\b([A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+)?)\b", user_text):
            val = match.group(0).strip()
            if len(val) >= 4 and val.lower() not in {"what", "where", "when", "how", "this", "that", "user", "lucy", "okay"}:
                entities.add(val)

        # 3. Tone / Emotional Vibe
        detected_vibes: Set[str] = set()
        for vibe_name, keywords in EMOTION_VIBE_MARKERS.items():
            if any(kw in lowered for kw in keywords):
                detected_vibes.add(vibe_name)

        # 4. Turn Summary line
        clean_user = user_text.strip().replace("\n", " ")
        if len(clean_user) > 60:
            clean_user = clean_user[:57] + "..."
        summary_point = f"Discussed '{clean_user}'"

        return {
            "summary_point": summary_point,
            "entities": sorted(list(entities)),
            "decisions": decisions,
            "vibes": detected_vibes,
        }

    def compress_older_turns(self, turns: List[Dict[str, str]], keep_recent: int = 5) -> Tuple[List[Dict[str, str]], EpisodicSessionDigest]:
        """
        Takes the full in-memory history turns. If len(turns) > keep_recent,
        compresses the oldest turns into the running episodic digest and returns
        only the remaining verbatim recent turns.
        """
        if len(turns) <= keep_recent:
            return turns, self.digest

        to_compress = turns[:-keep_recent]
        remaining_verbatim = turns[-keep_recent:]

        for turn in to_compress:
            inp = turn.get("input", "").strip()
            rep = turn.get("reply", "").strip()
            if not inp:
                continue

            signals = self.extract_turn_signals(inp, rep)
            
            # Add summary point
            sp = signals["summary_point"]
            if sp and sp not in self.digest.summary_points:
                self.digest.summary_points.append(sp)
                if len(self.digest.summary_points) > 12:
                    self.digest.summary_points.pop(0)

            # Add entities
            for ent in signals["entities"]:
                if ent not in self.digest.key_entities:
                    self.digest.key_entities.append(ent)
                    if len(self.digest.key_entities) > 16:
                        self.digest.key_entities.pop(0)

            # Add decisions
            for dec in signals["decisions"]:
                if dec not in self.digest.decisions_made:
                    self.digest.decisions_made.append(dec)
                    if len(self.digest.decisions_made) > 8:
                        self.digest.decisions_made.pop(0)

            # Add vibes
            self.digest.vibe_spectrum.update(signals["vibes"])
            self.digest.total_compressed_turns += 1

        self.digest.last_compressed_at = _now_iso()
        self.save()

        return remaining_verbatim, self.digest

    def clear(self) -> None:
        """Resets the active episodic digest."""
        self.digest = EpisodicSessionDigest()
        if self.persisted_file and self.persisted_file.exists():
            try:
                self.persisted_file.unlink()
            except Exception:
                pass


class ContextWindowGuard:
    """
    Enforces strict token limits on native message arrays before dispatching to local Ollama.
    Dynamically trims or truncates verbose assistant replies to prevent slow generation or context overflow.
    """

    def __init__(self, max_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS) -> None:
        self.max_tokens = max_tokens

    def estimate_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        total = 0
        for m in messages:
            content = m.get("content", "")
            total += estimate_tokens(content) + 4  # overhead per message
        return total

    def guard_messages(
        self,
        messages: List[Dict[str, str]],
        summarizer: Optional[EpisodicContextSummarizer] = None,
    ) -> List[Dict[str, str]]:
        """
        Checks total tokens. If budget exceeded:
        1. Truncates any excessively long past assistant responses (> 400 chars).
        2. Drops the oldest historical user/assistant pair if still over budget.
        Always preserves system prompt (index 0) and current user input (last index).
        """
        current_tokens = self.estimate_messages_tokens(messages)
        if current_tokens <= self.max_tokens or len(messages) <= 2:
            return messages

        guarded = list(messages)

        # Step 1: Compress verbose assistant turns in history (indices 1 to len-2)
        for i in range(1, len(guarded) - 1):
            if guarded[i].get("role") == "assistant":
                content = guarded[i].get("content", "")
                if len(content) > 350:
                    guarded[i]["content"] = content[:340] + " ...[truncated for brevity]"

        current_tokens = self.estimate_messages_tokens(guarded)
        if current_tokens <= self.max_tokens or len(guarded) <= 3:
            return guarded

        # Step 2: Drop oldest conversation turns if still over budget
        # guarded[0] = system, guarded[-1] = user current turn.
        # History is in guarded[1:-1]
        while self.estimate_messages_tokens(guarded) > self.max_tokens and len(guarded) > 3:
            # Drop the oldest user or assistant turn
            guarded.pop(1)

        return guarded
