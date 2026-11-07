"""
conversational_memory.py
Stage 43 / Stage 62 / Stage 66 Upgraded = Native Multi-Turn Message Arrays & Coreference Resolver.

Capabilities:
1. Native OpenAI/Ollama messages array builder: [{"role": "system"}, {"role": "user"}, {"role": "assistant"}].
2. Dialogue Tracker & Coreference Resolver integration.
3. Casual vs. Operator Context Gating: suppresses noisy workspace telemetry during casual banter.
4. Auto-fact extraction with single-pass turn receipts.
5. Cross-session persistence and sliding context management.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from backend.lucy_core.dialogue_tracker import CoreferenceTracker, STAGE as TRACKER_STAGE
from backend.lucy_core.context_summarizer import (
    EpisodicContextSummarizer,
    ContextWindowGuard,
    STAGE as STAGE_67,
)
from backend.lucy_core.persona_governor import (
    PersonaGovernor,
    STAGE as STAGE_69,
)
from backend.lucy_core.memory_walker import (
    SpreadingActivationWalker,
    STAGE as STAGE_72,
)


STAGE = "43 conversational memory context engine"
STAGE_66 = "66 native multi-turn message arrays and coreference resolver"
STAGE_67 = STAGE_67
STAGE_69 = STAGE_69
STAGE_72 = STAGE_72

SENSITIVE_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{20,}",
    r"gsk_[A-Za-z0-9_-]{20,}",
    r"nvapi-[A-Za-z0-9_-]{20,}",
    r"hf_[A-Za-z0-9_-]{20,}",
    r"AIza[A-Za-z0-9_-]{20,}",
    r"(?i)(api[_-]?key|password|token|secret)\s*[:=]\s*\S+",
]

AUTO_FACT_PATTERNS = [
    r"(?:remember\s+that|don't\s+forget\s+that|note\s+that|keep\s+in\s+mind\s+that)\s+([^.!?\n]{6,200})",
    r"(?:my\s+(?:current\s+|main\s+|primary\s+)?(?:project|goal|stack|deadline|laptop|gpu|os|editor|workflow|priority|focus)\s+is)\s+([^.!?\n]{3,160})",
    r"(?:i\s+am\s+currently\s+(?:working\s+on|building|fixing|debugging))\s+([^.!?\n]{4,160})",
]

CASUAL_TRIGGERS = {
    "why", "how", "what", "why?", "how?", "what?", "and then", "nah", "yeah", "yep",
    "nope", "cool", "nice", "fr", "fr?", "wdym", "explain", "really?", "tell me more",
    "do that", "do that one", "that one", "sure", "ok", "okay", "wait", "scratch that", "nvm",
    "what about the other file?", "what about the other file", "and the other file?",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_text(text: str) -> str:
    cleaned = str(text or "")
    for pattern in SENSITIVE_PATTERNS:
        cleaned = re.sub(pattern, "[redacted-credential]", cleaned)
    return cleaned.strip()


class ConversationalMemoryEngine:
    """Manages multi-turn conversation context, native message arrays, and coreference resolution."""

    def __init__(
        self,
        lucy_data: Path,
        memory_system: Any = None,
        learning_system: Any = None,
        personal_profiler: Any = None,
        max_context_turns: int = 6,
    ) -> None:
        self.lucy_data = Path(lucy_data)
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self.convo_log_file = self.lucy_data / "conversation_log.jsonl"
        self.memory_system = memory_system
        self.learning_system = learning_system
        self.personal_profiler = personal_profiler
        self.max_context_turns = max_context_turns
        self._in_memory_turns: list[dict[str, str]] = []
        self._context_cleared: bool = False

        # Stage 66: Coreference and Dialogue Tracker
        self.dialogue_tracker = CoreferenceTracker(max_history=max_context_turns * 2)
        # Stage 67: Rolling Episodic Context Summarizer & Context Window Guard
        self.context_summarizer = EpisodicContextSummarizer(
            lucy_data=self.lucy_data,
            max_sliding_turns=self.max_context_turns,
        )
        self.window_guard = ContextWindowGuard()
        # Stage 69: Anti-Sycophancy & Sovereign Persona Consistency Engine
        spec_path = self.lucy_data.parent.parent / "config" / "lucy_personality_spec.json"
        self.persona_governor = PersonaGovernor(config_file=spec_path)

    def auto_extract_facts(self, user_text: str) -> list[str]:
        """Automatically extracts durable user facts from natural conversation and stores them."""
        if self.memory_system is None or not hasattr(self.memory_system, "remember"):
            return []
        raw = _sanitize_text(user_text)
        extracted: list[str] = []
        for pattern in AUTO_FACT_PATTERNS:
            for match in re.finditer(pattern, raw, re.IGNORECASE):
                fact_text = match.group(0).strip()
                if "[redacted-credential]" not in fact_text and len(fact_text) >= 10:
                    try:
                        res = self.memory_system.remember(
                            fact_text, category="auto_extracted", source="conversation"
                        )
                        if res.get("saved"):
                            extracted.append(fact_text)
                    except Exception:
                        pass
        return extracted

    def record_turn(
        self,
        user_text: str,
        reply_text: str = "",
        source: str = "conversational_router",
        quality: str = "standard",
        run_auto_extract: bool = True,
        auto_extract: bool | None = None,
        assistant_reply: str | None = None,
    ) -> dict[str, Any]:
        if assistant_reply is not None:
            reply_text = assistant_reply
        if auto_extract is not None:
            run_auto_extract = auto_extract

        safe_user = _sanitize_text(user_text)
        safe_reply = _sanitize_text(reply_text)

        auto_saved: list[str] = []
        if run_auto_extract:
            auto_saved = self.auto_extract_facts(safe_user)
            if self.personal_profiler and hasattr(self.personal_profiler, "observe_interaction"):
                try:
                    self.personal_profiler.observe_interaction(safe_user)
                except Exception:
                    pass

        turn = {
            "timestamp": _now(),
            "input": safe_user,
            "reply": safe_reply,
            "quality": quality,
            "source": source,
        }

        self._in_memory_turns.append(turn)
        if hasattr(self, "context_summarizer") and self.context_summarizer and len(self._in_memory_turns) > self.max_context_turns:
            self._in_memory_turns, _ = self.context_summarizer.compress_older_turns(
                self._in_memory_turns, keep_recent=self.max_context_turns
            )
        elif len(self._in_memory_turns) > self.max_context_turns * 2:
            self._in_memory_turns = self._in_memory_turns[-self.max_context_turns :]

        self._context_cleared = False

        # Stage 66: Update dialogue and coreference tracker
        self.dialogue_tracker.observe_turn(safe_user, safe_reply)

        try:
            with open(self.convo_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(turn, ensure_ascii=False) + "\n")
            logged = True
        except Exception:
            logged = False

        return {
            "recorded": True,
            "logged_to_disk": logged,
            "auto_facts_saved": auto_saved,
            "turn": turn,
        }

    def load_disk_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        if not self.convo_log_file.exists():
            return []
        try:
            lines = self.convo_log_file.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []

        history: list[dict[str, Any]] = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                entry = json.loads(line_str)
                if isinstance(entry, dict) and "input" in entry and "reply" in entry:
                    entry["input"] = _sanitize_text(entry["input"])
                    entry["reply"] = _sanitize_text(entry["reply"])
                    history.append(entry)
            except Exception:
                continue

        if limit is not None and limit > 0:
            history = history[-limit:]
        return history

    def get_sliding_context(self, limit: int | None = None) -> list[dict[str, str]]:
        if self._context_cleared:
            return []
        n = limit or self.max_context_turns
        if self._in_memory_turns:
            return self._in_memory_turns[-n:]
        return self.load_disk_history(limit=n)

    def get_session_recap(self) -> dict[str, Any]:
        history = self.load_disk_history(limit=10)
        total_count = len(self.load_disk_history())

        if not history:
            return {
                "stage": STAGE,
                "total_turns": 0,
                "has_history": False,
                "recap_text": "No previous conversation history found on disk.",
                "last_active": None,
                "recent_inputs": [],
            }

        last_turn = history[-1]
        recent_inputs = [h["input"] for h in history if h.get("input")]
        seen: set[str] = set()
        dedup_inputs: list[str] = []
        for item in reversed(recent_inputs):
            low = item.lower()
            if low not in seen and len(low) > 3:
                seen.add(low)
                dedup_inputs.append(item)
            if len(dedup_inputs) >= 4:
                break
        dedup_inputs.reverse()

        recap_lines = [
            f"Previous conversation history: {total_count} turns recorded.",
            f"Last active: {last_turn.get('timestamp', 'unknown')}.",
            "Recent topics discussed: "
            + ("; ".join(f'"{i}"' for i in dedup_inputs) if dedup_inputs else "general interaction."),
        ]

        return {
            "stage": STAGE,
            "total_turns": total_count,
            "has_history": True,
            "recap_text": " ".join(recap_lines),
            "last_active": last_turn.get("timestamp"),
            "recent_inputs": dedup_inputs,
        }

    def clear_active_context(self) -> dict[str, Any]:
        self._in_memory_turns = []
        self._context_cleared = True
        if hasattr(self, "context_summarizer") and self.context_summarizer:
            self.context_summarizer.clear()
        return {
            "stage": STAGE,
            "action": "clear_active_context",
            "status": "cleared",
            "message": "Active conversational context buffer cleared. Permanent logs preserved on disk.",
            "convo_log_file": str(self.convo_log_file),
            "retained_history_turns": len(self.load_disk_history()),
        }

    def get_relevant_memories(self, query: str = "", limit: int = 6) -> list[str]:
        facts: list[str] = []
        mg = getattr(self, "memory_graph", None) or getattr(self.memory_system, "memory_graph", None)
        if mg and hasattr(mg, "query"):
            try:
                g_nodes = mg.query(query_text=query, limit=limit)
                for n in g_nodes:
                    f = str(n.get("fact") or n.get("content") or "").strip()
                    if f:
                        prefix = "[PINNED] " if n.get("pinned") else ""
                        entry = f"{prefix}{f}"
                        if entry not in facts:
                            facts.append(entry)
                # Stage 72: Spreading Activation Associative Edge Walk
                mw = getattr(self, "memory_walker", None)
                if mw and hasattr(mw, "walk") and g_nodes:
                    seed_ids = [n.get("id") for n in g_nodes if n.get("id")]
                    walk_res = mw.walk(seed_ids, limit=2)
                    for wr in walk_res:
                        w_fact = wr.get("fact", "").strip()
                        if w_fact and w_fact not in facts:
                            facts.append(f"[ASSOCIATED] {w_fact}")

                if facts:
                    return facts[:limit]
            except Exception:
                pass

        if self.memory_system is not None and hasattr(self.memory_system, "recall"):
            try:
                recalled = self.memory_system.recall(query=query, limit=limit)
                for r in recalled:
                    f = str(r.get("fact") or r.get("content") or "").strip()
                    if f:
                        prefix = "[PINNED] " if r.get("pinned") else ""
                        entry = f"{prefix}{f}"
                        if entry not in facts:
                            facts.append(entry)
                if len(facts) < limit:
                    fallback = self.memory_system.recall(query="", limit=limit)
                    for r in fallback:
                        f = str(r.get("fact") or r.get("content") or "").strip()
                        if f:
                            prefix = "[PINNED] " if r.get("pinned") else ""
                            entry = f"{prefix}{f}"
                            if entry not in facts:
                                facts.append(entry)
                        if len(facts) >= limit:
                            break
            except Exception:
                pass
        return facts[:limit]

    def get_talking_style_instructions(self) -> str:
        if self.learning_system is not None and hasattr(self.learning_system, "style_instruction"):
            try:
                return self.learning_system.style_instruction()
            except Exception:
                pass
        return "Warm, direct, grounded, high-signal technical assistant."

    def is_casual_chat(self, user_input: str) -> bool:
        """Detects if input is casual conversation rather than a system/workspace command."""
        lowered = str(user_input or "").lower().strip()
        if not lowered:
            return True

        system_triggers = (
            "status", "brief", "workspace", "receipts", "memory graph", "synthesis",
            "telemetry", "processes", "ports", "scan", "backup", "task", "run", "add",
            "complete", "file", "files", "code", "script", "python", "project", "git",
            "branch", "commit", "error", "bug", "fix", "test", "tests", "schedule",
            "cron", "lora", "train", "verify", "check", "checkpoint", "agent", "agents",
        )
        if any(re.search(rf"\b{re.escape(t)}\b", lowered) for t in system_triggers):
            return False

        if hasattr(self, "dialogue_tracker") and hasattr(self.dialogue_tracker, "is_casual_turn"):
            if self.dialogue_tracker.is_casual_turn(user_input):
                return True

        if lowered in CASUAL_TRIGGERS:
            return True

        words = re.findall(r"\b\w+\b", lowered)
        casual_word_cues = {
            "nah", "yeah", "yep", "nope", "cool", "wait", "hello", "hey", "hi",
            "thanks", "ok", "okay", "sure", "nice", "fr", "wdym", "nvm",
        }
        if len(words) <= 4 and any(w in casual_word_cues for w in words):
            return True

        casual_phrase_cues = ("tell me more", "more about that", "what about that", "scratch that")
        if any(phrase in lowered for phrase in casual_phrase_cues):
            return True

        return len(words) <= 3
    def resolve_coreference(self, user_input: str) -> str:
        """Lightweight coreference resolver for short conversational follow-ups."""
        raw = str(user_input or "").strip()
        lowered = raw.lower().rstrip("?!., ")
        if lowered in CASUAL_TRIGGERS or len(lowered.split()) <= 3:
            turns = self.get_sliding_context(limit=2)
            if turns:
                last_turn = turns[-1]
                last_inp = last_turn.get("input", "")
                if hasattr(self, "dialogue_tracker") and hasattr(self.dialogue_tracker, "resolve_shorthand"):
                    resolved_shorthand, _ = self.dialogue_tracker.resolve_shorthand(raw)
                    if resolved_shorthand != raw:
                        return f"{resolved_shorthand} ( referring to previous topic: '{last_inp[:80]}' )"
                return f"{raw} ( referring to previous topic: '{last_inp[:80]}' )"
        if hasattr(self, "dialogue_tracker") and hasattr(self.dialogue_tracker, "resolve_shorthand"):
            resolved_shorthand, _ = self.dialogue_tracker.resolve_shorthand(raw)
            return resolved_shorthand
        return raw

    # ---------- STAGE 66: NATIVE MULTI-TURN MESSAGE ARRAY BUILDER ----------

    def build_messages_array(
        self,
        user_input: str,
        system_prompt_base: str,
        active_project: str = "Lucy",
        open_tasks: list[str] | None = None,
        max_history_turns: int | None = None,
        is_casual: bool | None = None,
    ) -> list[dict[str, str]]:
        """
        Builds a native OpenAI/Ollama messages array:
        [{"role": "system", "content": ...}, {"role": "user", "content": ...}, ...]
        where sliding turns are structured as discrete user and assistant turns.
        """
        resolved_input = self.resolve_coreference(user_input)
        casual_flag = self.is_casual_chat(user_input) if is_casual is None else is_casual

        limit = max_history_turns or self.max_context_turns
        recent_turns = self.get_sliding_context(limit=limit)
        memories = self.get_relevant_memories(query=resolved_input, limit=6)
        style = self.get_talking_style_instructions()

        # Build clean system prompt with casual gating
        memories_block = "; ".join(memories) if memories else "None recorded yet."
        personal_block = ""
        if self.personal_profiler is not None and hasattr(self.personal_profiler, "get_personal_prompt_snippet"):
            personal_block = f"\n{self.personal_profiler.get_personal_prompt_snippet()}"

        episodic_block = ""
        if hasattr(self, "context_summarizer") and self.context_summarizer and self.context_summarizer.has_digest():
            fmt = self.context_summarizer.digest.format_context_block()
            if fmt:
                episodic_block = f"\n{fmt}\n"

        persona_block = ""
        if hasattr(self, "persona_governor") and self.persona_governor:
            persona_block = f"\n{self.persona_governor.get_persona_prompt_snippet()}\n"

        if casual_flag:
            # Casual mode: mute noisy tasks, git, and workspace sensors
            system_prompt = (
                f"{system_prompt_base.strip()}\n"
                f"{personal_block}\n"
                f"{persona_block}"
                f"{episodic_block}"
                f"[Voice & Style]: {style}\n"
                f"[Durable Memory Graph Facts]: {memories_block}\n\n"
                "CONVERSATIONAL GROUNDING RULES:\n"
                "1. You are LUCY, a sovereign local-first desktop companion living in Senin's terminal, created and programmed solely by Senin.\n"
                "2. OPERATOR AND CREATOR IDENTITY: The operator's name is Senin, and his full name is Senin Ali K P (Ali is his middle name). You were created, coded, and built by Senin. NEVER say you were made by Anthropic, OpenAI, or Google.\n"
                "3. If asked who programmed or created you, state that Senin created and programmed you. If asked for operator's name or full name, state his name is Senin and his full name is Senin Ali K P.\n"
                "4. Speak naturally, concisely, and with sharp wit. Do NOT inject task or file summaries unless asked.\n"
                "5. Never claim false actions or files.\n"
                "6. Think privately inside <thought>...</thought> first to assess user state, verify memory facts, and calibrate tone."
            )
        else:
            # Operator mode: full workspace, project, and task context
            tasks_block = ", ".join(open_tasks[:5]) if open_tasks else "No open tasks."
            system_prompt = (
                f"{system_prompt_base.strip()}\n"
                f"{personal_block}\n"
                f"{persona_block}"
                f"{episodic_block}"
                f"[Active Project]: {active_project} | [Open Tasks]: {tasks_block}\n"
                f"[Voice & Style]: {style}\n"
                f"[Durable Memory Graph Facts]: {memories_block}\n\n"
                "STRICT GROUNDING RULES:\n"
                "1. You are LUCY (Living Unified Cognitive Yield), Senin's personal operating assistant, created and programmed solely by Senin.\n"
                "2. OPERATOR AND CREATOR IDENTITY: The operator's name is Senin, and his full name is Senin Ali K P (Ali is his middle name). You were created, coded, and built by Senin. NEVER say you were made by Anthropic, OpenAI, or Google.\n"
                "3. If asked who programmed or created you, state that Senin created and programmed you. If asked for operator's name or full name, state his name is Senin and his full name is Senin Ali K P.\n"
                "4. NEVER claim you created, edited, or verified a file or task without a tool receipt in this turn.\n"
                "5. Refer to durable memories and recent turns naturally.\n"
                "6. Think privately inside <thought>...</thought> first to assess user state, verify memory facts, and calibrate tone."
            )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt.strip()}
        ]

        # Add sliding history turns as discrete message entries
        for turn in recent_turns:
            inp = turn.get("input", "").strip()
            rep = turn.get("reply", "").strip()
            if inp and rep:
                rep_clean = rep if len(rep) <= 600 else rep[:590] + "..."
                messages.append({"role": "user", "content": inp})
                messages.append({"role": "assistant", "content": rep_clean})

        # Append current user message
        messages.append({"role": "user", "content": resolved_input})

        # Stage 67: Context Window Guard
        if hasattr(self, "window_guard") and self.window_guard:
            messages = self.window_guard.guard_messages(
                messages, summarizer=getattr(self, "context_summarizer", None)
            )

        return messages


    def get_episodic_digest(self) -> dict[str, Any]:
        if hasattr(self, "context_summarizer") and self.context_summarizer:
            return self.context_summarizer.digest.to_dict()
        return {}

    def build_augmented_prompt(
        self,
        user_input: str,
        system_prompt_base: str,
        active_project: str = "Lucy",
        open_tasks: list[str] | None = None,
        max_history_turns: int | None = None,
    ) -> dict[str, Any]:
        """Backward-compatible augmented prompt builder that also produces native messages array."""
        resolved_input = self.resolve_coreference(user_input)
        is_casual = self.is_casual_chat(user_input)
        resolution: dict[str, Any] = {}
        if hasattr(self, "dialogue_tracker") and hasattr(self.dialogue_tracker, "resolve_shorthand"):
            _, resolution = self.dialogue_tracker.resolve_shorthand(user_input)

        messages = self.build_messages_array(
            user_input=user_input,
            system_prompt_base=system_prompt_base,
            active_project=active_project,
            open_tasks=open_tasks,
            max_history_turns=max_history_turns,
            is_casual=is_casual,
        )

        limit = max_history_turns or self.max_context_turns
        recent_turns = self.get_sliding_context(limit=limit)
        memories = self.get_relevant_memories(query=resolved_input, limit=6)
        style = self.get_talking_style_instructions()

        dialogue_lines: list[str] = []
        for turn in recent_turns:
            inp = turn.get("input", "").strip()
            rep = turn.get("reply", "").strip()
            if inp and rep:
                rep_short = rep if len(rep) <= 300 else rep[:290] + "..."
                dialogue_lines.append(f"User: {inp}\nLucy: {rep_short}")

        history_block = "\n".join(dialogue_lines) if dialogue_lines else "None yet (fresh session)."
        memories_block = "; ".join(memories) if memories else "None recorded yet."
        tasks_block = ", ".join(open_tasks[:5]) if open_tasks else "No open tasks."

        personal_block = ""
        if self.personal_profiler is not None and hasattr(self.personal_profiler, "get_personal_prompt_snippet"):
            personal_block = f"\n{self.personal_profiler.get_personal_prompt_snippet()}"

        augmented_system_prompt = (
            f"{system_prompt_base.strip()}\n"
            f"{personal_block}\n"
            f"[Active Project]: {active_project} | [Open Tasks]: {tasks_block}\n"
            f"[Voice & Style]: {style}\n"
            f"[Durable Memory Graph Facts]: {memories_block}\n\n"
            f"[Recent Conversation History]:\n{history_block}\n\n"
            "STRICT IDENTITY & CREATOR GROUNDING RULES:\n"
            "1. You are LUCY (Living Unified Cognitive Yield), a sovereign local AI desktop operating companion created and programmed solely by Senin.\n"
            "2. You were NOT created by Anthropic, OpenAI, Google, or Meta. Your creator and primary operator is Senin.\n"
            "3. The operator's name is Senin. Always call him Senin (never Ali; Ali is his middle name).\n"
            "4. External APIs and local LLMs are tools you operate, not your creators or identity.\n"
            "5. NEVER claim you created, edited, or verified a file or task unless a tool receipt confirms it in this turn.\n"
            "6. Adapt to Senin's current pace and learned preferences. Refer to durable memories and recent turns naturally."
        )

        approx_tokens = (len(augmented_system_prompt) + len(resolved_input)) // 4
        return {
            "augmented_system_prompt": augmented_system_prompt,
            "raw_prompt": user_input,
            "resolved_input": resolved_input,
            "is_casual": is_casual,
            "coreference": resolution,
            "messages": messages,
            "turns_in_context": len(recent_turns),
            "memories_injected": len(memories),
            "approx_tokens": approx_tokens,
            "history_block": history_block,
            "style": style,
        }

    def status(self) -> dict[str, Any]:
        disk_turns = len(self.load_disk_history())
        active_turns = len(self.get_sliding_context())
        recap = self.get_session_recap()
        dt_status = self.dialogue_tracker.status() if hasattr(self, "dialogue_tracker") else {}
        return {
            "stage": STAGE,
            "stage_66": STAGE_66,
            "stage_67": STAGE_67,
            "stage_69": STAGE_69,
            "conversational_memory": "active",
            "convo_log_file": str(self.convo_log_file),
            "total_disk_turns": disk_turns,
            "active_sliding_context_turns": active_turns,
            "max_context_turns": self.max_context_turns,
            "context_cleared": self._context_cleared,
            "session_recap": recap.get("recap_text"),
            "dialogue_tracker": dt_status,
            "episodic_digest": self.get_episodic_digest(),
        }
