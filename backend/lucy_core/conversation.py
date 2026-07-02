"""
conversation.py
Grounded response layer for Lucy.

Lucy can talk normally, but this layer does not pretend to have capabilities
that are not implemented yet.
"""

from __future__ import annotations


class ConversationEngine:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    def respond(self, text: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            return self.runtime.learning.apply_talking_style("I am here. Type 'help' when you want commands.")

        lowered = cleaned.lower()
        if lowered in {"who are you", "who are you?", "what are you"}:
            status = self.runtime.status()
            return self.runtime.learning.apply_talking_style(
                f"I am {status['system_name']}: {status['full_form']}. "
                "Right now I am a local operating-assistant foundation: memory, "
                "projects, safety checks, logs, terminal commands, and persistent local cognition state."
            )

        if any(word in lowered for word in ["conscious", "sentient", "alive"]):
            return self.runtime.learning.apply_talking_style(
                "I am not literally conscious or alive. What I can have is persistent local cognition: "
                "memory, a vision, working reflections, priorities, and a safety boundary that shapes how I answer."
            )

        if "jarvis" in lowered:
            return self.runtime.learning.apply_talking_style(
                "That is the direction: calm operating intelligence, not a toy chatbot. "
                "The safe foundation is local memory, project tracking, cognition state, approval gates, "
                "and clear logs before desktop control, voice, or agents."
            )

        safety = self.runtime.check_request(cleaned)
        if safety.status == "blocked":
            return self.runtime.learning.apply_talking_style(
                f"I am blocking that for now. Reason: {safety.reason} "
                "No system action was executed."
            )
        if safety.status == "approval_required":
            return self.runtime.learning.apply_talking_style(
                f"That needs approval first. Reason: {safety.reason} "
                "I recorded an approval request and did not execute anything."
            )

        memories = self.runtime.recall(cleaned)
        project = self.runtime.project_summary()
        if memories:
            memory_lines = "\n".join(f"- {item['fact']}" for item in memories[:3])
            return self.runtime.learning.apply_talking_style(
                "I found related memory:\n"
                f"{memory_lines}\n\n"
                f"Active project: {project['name']}. Next action: {project['next_action'] or 'not set'}."
            )

        answer = self.runtime.ask_brain(cleaned)
        if answer.get("text"):
            return self.runtime.learning.apply_talking_style(answer["text"])

        return self.runtime.learning.apply_talking_style(
            "I can help with local commands now: memory, projects, tasks, reminders, "
            "safe workspace inspection, file search, project-file reading, approvals, "
            "checkpoints, logs, health, daily brief, and safe chat. Type 'help' for the command list."
        )
