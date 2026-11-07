"""
dialogue_tracker.py
Stage 66 = Native Multi-Turn Dialogue Tracker & Coreference Resolver.

Maintains active conversational state across turns:
1. Tracks current conversation topic, last statement, active entities, and questions.
2. Resolves ambiguous shorthand follow-ups ("why?", "do that", "how?", "fr?", "the other one").
3. Classifies turns as CASUAL (banter, brainstorming, philosophy) vs. OPERATOR (system tasks, tools, files).
4. Provides context gating to mute noisy physical workspace telemetry during casual chat.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple


STAGE = "66 native multi-turn message arrays and coreference resolver"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Stopwords excluded from entity extraction
ENTITY_STOPWORDS: Set[str] = {
    "the", "a", "an", "is", "are", "was", "were", "this", "that", "these", "those",
    "and", "but", "for", "with", "from", "into", "about", "your", "mine", "ours",
    "will", "would", "could", "should", "have", "been", "here", "there", "what",
    "when", "where", "which", "who", "whom", "whose", "why", "how", "okay", "yeah",
    "sure", "well", "just", "also", "very", "much", "more", "most", "some", "any",
}

# Regex patterns identifying casual conversation vs. system operator work
CASUAL_GREETINGS = {
    "hi", "hey", "hello", "yo", "sup", "what's up", "good morning", "good evening",
    "good afternoon", "howdy", "hii", "heyy", "hyy", "bro", "lucy", "hey lucy",
}

CASUAL_PHRASES = [
    r"^(?:how\s+are\s+you|how's\s+it\s+going|what\s+are\s+you\s+thinking|tell\s+me\s+about\s+yourself)",
    r"^(?:what\s+do\s+you\s+think|what's\s+your\s+take|your\s+opinion|do\s+you\s+like|any\s+thoughts)",
    r"^(?:thanks|thank\s+you|appreciate\s+it|nice|cool|awesome|great|lol|haha|lmao)",
    r"^(?:tell\s+me\s+a\s+joke|can\s+we\s+chat|let's\s+talk|who\s+are\s+you)",
]

OPERATOR_INDICATORS = [
    r"\b(?:run|execute|test|scan|diagnos|heal|backup|search|kill|probe|chain|schedule|cron)\b",
    r"\b(?:git|commit|push|pull|branch|merge|status|diff|checkout)\b",
    r"\b(?:pip|python|node|npm|uv|docker|ollama|curl|http)\b",
    r"\b(?:add\s+task|create\s+task|todo:|complete\s+task|mark\s+done)\b",
    r"\b(?:remember\s+that|pin\s+memory|unpin\s+memory|forget)\b",
    r"[/\\][\w.-]+",  # file paths like /foo/bar or foo\bar
    r"\b[\w-]+\.(?:py|json|txt|md|yml|yaml|toml|sh|bat|rs|ts|js|go)\b",  # file extensions
]


@dataclass
class DialogueTurnSnapshot:
    turn_id: int
    user_text: str
    reply_text: str
    topic: str
    entities: List[str]
    is_casual: bool
    timestamp: str = field(default_factory=_now)


class CoreferenceTracker:
    """Tracks active conversational entities and resolves ambiguous shorthand follow-ups."""

    def __init__(self, max_history: int = 10) -> None:
        self.max_history = max_history
        self._turns: List[DialogueTurnSnapshot] = []
        self._current_topic: str = ""
        self._active_entities: List[str] = []
        self._last_user_question: Optional[str] = None
        self._last_assistant_statement: Optional[str] = None
        self._last_suggested_action: Optional[str] = None

    def extract_entities(self, text: str) -> List[str]:
        """Extracts key nouns, technical terms, file names, and quoted strings."""
        if not text:
            return []
        entities: List[str] = []

        # 1. Quoted terms
        for q in re.findall(r"['\"]([^'\"]{2,50})['\"]", text):
            entities.append(q.strip())

        # 2. File-like tokens (e.g. main.py, config.json)
        for f in re.findall(r"\b[\w-]+\.[a-zA-Z0-9]{1,6}\b", text):
            if f.lower() not in entities:
                entities.append(f)

        # 3. Capitalized words or acronyms (e.g. PostgreSQL, Ollama, LoRA, AST)
        for cap in re.findall(r"\b[A-Z][a-zA-Z0-9_]{2,}\b", text):
            if cap.lower() not in ENTITY_STOPWORDS and cap not in entities:
                entities.append(cap)

        # 4. Technical keywords
        tech_words = [
            "database", "postgres", "postgresql", "sqlite", "redis", "mongodb",
            "fastapi", "flask", "django", "react", "vue", "docker", "gpu", "cuda",
            "telemetry", "sentinel", "orchestrator", "receipt", "prompt", "token",
        ]
        lowered = text.lower()
        for tw in tech_words:
            if tw in lowered and tw not in [e.lower() for e in entities]:
                entities.append(tw)

        return entities[:8]

    def is_casual_turn(self, user_text: str) -> bool:
        """Determines if turn is casual conversation / brainstorming vs. system operator work."""
        raw = str(user_text or "").strip()
        lowered = re.sub(r"\s+", " ", raw.lower()).rstrip("?!., ")

        # 1. Exact greeting match
        if lowered in CASUAL_GREETINGS or any(lowered == f"hey {g}" for g in CASUAL_GREETINGS):
            return True

        # Check for operator indicators first
        for pat in OPERATOR_INDICATORS:
            if re.search(pat, raw, re.IGNORECASE):
                return False

        # Leading greetings (e.g. "hey lucy, how's your day going?")
        for g in CASUAL_GREETINGS:
            if lowered.startswith(f"{g} ") or lowered.startswith(f"{g},"):
                return True

        # 2. Casual conversational phrases
        for pat in CASUAL_PHRASES:
            if re.search(pat, lowered):
                return True

        # 3. Questions asking how someone is doing or opinion
        if re.search(r"\b(?:how's\s+it\s+going|how\s+are\s+you|how's\s+your\s+day|how\s+do\s+you\s+feel)\b", lowered):
            return True

        # 4. Short conversational remarks (< 6 words without code or path)
        words = raw.split()
        if len(words) <= 5 and not any(ch in raw for ch in ("/", "\\", "_", "(", ")")):
            casual_words = {"why", "how", "fr", "really", "what", "nice", "cool", "sure", "ok", "okay", "yeah", "nah", "thanks"}
            if any(w.lower().rstrip("?!.,") in casual_words for w in words):
                return True

        # 5. Question of opinion or explanation
        if re.match(r"^(?:why|what\s+if|how\s+come|explain|tell\s+me|can\s+we\s+chat)\b", lowered):
            return True

        return False

    def observe_turn(self, user_text: str, reply_text: str) -> DialogueTurnSnapshot:
        """Records a completed turn, updating active topic and entities."""
        safe_user = str(user_text or "").strip()
        safe_reply = str(reply_text or "").strip()
        is_casual = self.is_casual_turn(safe_user)

        # Extract entities from both sides
        user_entities = self.extract_entities(safe_user)
        reply_entities = self.extract_entities(safe_reply)
        combined = user_entities + [e for e in reply_entities if e not in user_entities]

        # Prepend new entities while preserving relative order
        new_active = []
        for e in combined:
            if e not in new_active:
                new_active.append(e)
        for e in self._active_entities:
            if e not in new_active:
                new_active.append(e)
        self._active_entities = new_active[:10]

        # Update topic
        if not is_casual and user_entities:
            self._current_topic = user_entities[0]
        elif safe_user.endswith("?"):
            self._last_user_question = safe_user
            if not self._current_topic and user_entities:
                self._current_topic = user_entities[0]
        elif len(safe_user.split()) >= 4 and not is_casual:
            self._current_topic = " ".join(safe_user.split()[:5])

        # Record last assistant statement & potential suggested action
        if safe_reply:
            first_sentence = re.split(r"[.!?\n]", safe_reply)[0].strip()
            self._last_assistant_statement = first_sentence if first_sentence else safe_reply[:100]

            # Look for suggestions like "We could use X", "I suggest X", "Try X"
            sugg_match = re.search(r"(?:suggest|recommend|we\s+could|try|how\s+about)\s+([^.!?\n]+)", safe_reply, re.IGNORECASE)
            if sugg_match:
                self._last_suggested_action = sugg_match.group(1).strip()

        turn_snapshot = DialogueTurnSnapshot(
            turn_id=len(self._turns) + 1,
            user_text=safe_user,
            reply_text=safe_reply,
            topic=self._current_topic,
            entities=list(self._active_entities),
            is_casual=is_casual,
        )
        self._turns.append(turn_snapshot)
        if len(self._turns) > self.max_history:
            self._turns.pop(0)

        return turn_snapshot

    def resolve_shorthand(self, user_text: str) -> Tuple[str, dict[str, Any]]:
        """
        Detects ambiguous shorthand follow-ups and returns (annotated_input, resolution_metadata).
        Examples:
          "why?" -> "why? [Context: referring to previous statement: 'PostgreSQL is recommended']"
          "do that one" -> "do that one [Context: referring to suggested action: 'migrate database to postgres']"
          "what about the other file?" -> "what about the other file? [Context: referring to secondary entity: 'memory_graph.py']"
        """
        raw = str(user_text or "").strip()
        lowered = re.sub(r"\s+", " ", raw.lower()).rstrip("?!., ")

        resolution: dict[str, Any] = {
            "is_shorthand": False,
            "shorthand_type": None,
            "bound_target": None,
            "annotated_input": raw,
        }

        if not self._turns:
            return raw, resolution

        # Pattern 1: "why?" / "why though?" / "why is that?" / "how come?"
        if lowered in {"why", "why though", "why so", "why is that", "how come", "fr", "really"}:
            target = self._last_assistant_statement or self._current_topic
            if target:
                resolution["is_shorthand"] = True
                resolution["shorthand_type"] = "inquiry_justification"
                resolution["bound_target"] = target
                resolution["annotated_input"] = f"{raw} [Context: user is asking for justification regarding '{target}']"
                return resolution["annotated_input"], resolution

        # Pattern 2: "do that" / "do that one" / "let's do that" / "run it" / "proceed with that"
        if lowered in {"do that", "do that one", "let's do that", "run it", "proceed with that", "go ahead", "yes do it"}:
            target = self._last_suggested_action or self._current_topic
            if target:
                resolution["is_shorthand"] = True
                resolution["shorthand_type"] = "action_affirmation"
                resolution["bound_target"] = target
                resolution["annotated_input"] = f"{raw} [Context: user affirms action to '{target}']"
                return resolution["annotated_input"], resolution

        # Pattern 3: "what about the other one?" / "what about the other file?" / "and the other?"
        if any(p in lowered for p in ["the other one", "other file", "the second one", "and the other"]):
            if len(self._active_entities) >= 2:
                secondary = self._active_entities[1]
                resolution["is_shorthand"] = True
                resolution["shorthand_type"] = "alternate_entity"
                resolution["bound_target"] = secondary
                resolution["annotated_input"] = f"{raw} [Context: user refers to secondary entity '{secondary}']"
                return resolution["annotated_input"], resolution

        # Pattern 4: "nah change it" / "scratch that" / "change that" / "not that one"
        if lowered in {"nah change it", "scratch that", "change that", "not that one", "instead of that"}:
            target = self._active_entities[0] if self._active_entities else self._current_topic
            if target:
                resolution["is_shorthand"] = True
                resolution["shorthand_type"] = "retraction_pivot"
                resolution["bound_target"] = target
                resolution["annotated_input"] = f"{raw} [Context: user retracts/replaces previous choice '{target}']"
                return resolution["annotated_input"], resolution

        # Pattern 5: "and then?" / "what next?" / "then what?"
        if lowered in {"and then", "what next", "then what", "what's next", "after that"}:
            target = self._current_topic
            if target:
                resolution["is_shorthand"] = True
                resolution["shorthand_type"] = "continuation"
                resolution["bound_target"] = target
                resolution["annotated_input"] = f"{raw} [Context: user asks for the next step following '{target}']"
                return resolution["annotated_input"], resolution

        return raw, resolution

    def status(self) -> dict[str, Any]:
        return {
            "stage": STAGE,
            "dialogue_tracker": "active",
            "tracked_turns": len(self._turns),
            "current_topic": self._current_topic or "general",
            "active_entities": list(self._active_entities),
            "last_statement": self._last_assistant_statement,
            "last_suggested_action": self._last_suggested_action,
        }
