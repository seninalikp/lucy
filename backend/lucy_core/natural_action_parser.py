"""

natural_action_parser.py

Stage 59 / Stage 62 Fixed = Natural-Language Multi-Intent Action Parser & Grounded Executor.

Fixes:

- Preserves full subject clauses when auto-extracting facts ("my primary focus is X").

- Executes once per turn before LLM generation and issues Stage 55 cryptographic receipts.

"""

from __future__ import annotations

import re

from typing import Any

STAGE = "59 natural language action parser"

NATURAL_TASK_ADD_PATTERNS = [

    r"(?:please\s+|can\s+you\s+|also\s+)?(?:add\s+a?\s*task|create\s+a?\s*task|put\s+on\s+my\s+todo\s+list|todo\s*:)\s+(?:to\s+|for\s+|that\s+)?['\"]?([^.!?\n;]{4,140})['\"]?",

    r"(?:i\s+need\s+to\s+remember\s+to|remind\s+me\s+to)\s+([^.!?\n;]{4,140})",

]

NATURAL_FOLDER_MAKE_PATTERNS = [
    r'''(?:please\s+|can\s+you\s+|also\s+)?(?:make|create|setup|build)\s+(?:an?\s+)?(?:new\s+)?(?:folder|directory)\s+(?:named\s+|called\s+|at\s+|for\s+)?['"`]?([a-zA-Z0-9_\-\./\\]{1,80})['"`]?''',
    r'''(?:mkdir)(?:\s+-p)?\s+['"`]?([a-zA-Z0-9_\-\./\\]{1,80})['"`]?''',
    r'''(?:create\s+)?new\s+folder\s+['"`]?([a-zA-Z0-9_\-\./\\]{1,80})['"`]?''',
]

NATURAL_SWARM_CONNECT_PATTERNS = [
    r"(?:please\s+|can\s+you\s+|also\s+)?(?:connect|link|hook\s+up)(?:\s+her|\s+lucy)?\s+(?:to\s+)?(?:the\s+)?(?:all\s+)?(?:ai\s+)?bots(?:\s+in\s+this\s+folder)?",
    r"(?:she\s+can\s+use|use)\s+(?:the\s+)?(?:ai\s+)?bots(?:\s+in\s+this\s+folder|\s+in\s+senin[/\\]ai)?",
    r"(?:connect\s+swarm|connect\s+all\s+bots|start\s+swarm|start\s+all\s+bots)",
]

NATURAL_WRITER_CONNECT_PATTERNS = [

    r"(?:please\s+|can\s+you\s+|also\s+)?(?:connect|link|hook\s+up)(?:\s+her|\s+lucy)?\s+(?:to\s+)?(?:the\s+)?writer\s*bot(?:\s+(?:so\s+)?she\s+can\s+use\s+it)?",

    r"(?:start|launch|run|boot)\s+(?:the\s+)?writer\s*bot",

    r"(?:connect\s+writer\s*bot|connect\s+writer)",

]

NATURAL_TASK_DONE_PATTERNS = [

    r"(?:i\s+(?:just\s+)?(?:finished|completed|did)\s+(?:the\s+)?task|mark\s+task\s+as\s+done|complete\s+the\s+task)\s+['\"]?([^.!?\n,;]{2,80})['\"]?",

]

CLI_PREFIXES = (

    "add task ", "complete task ", "done ", "remember ", "forget ",

    "alias ", "add alias ", "set alias ", "macro ", "schedule ", "/schedule ",

)

class NaturalActionParser:

    """Detects and executes embedded assistant actions inside natural conversation."""

    def __init__(self, runtime: Any) -> None:

        self.runtime = runtime

    def parse_and_execute(self, user_text: str) -> dict[str, Any]:

        raw = str(user_text or "").strip()

        lowered = raw.lower()

        executed_actions: list[dict[str, Any]] = []

        if lowered.startswith(CLI_PREFIXES):

            return {"stage": STAGE, "actions_executed": 0, "actions": [], "summary_block": ""}

                # 0. Detect natural swarm or writer bot connection requests
        for pat in NATURAL_SWARM_CONNECT_PATTERNS:
            if re.search(pat, raw, re.IGNORECASE):
                if hasattr(self.runtime, "connect_swarm"):
                    s_res = self.runtime.connect_swarm()
                    executed_actions.append({
                        "type": "swarm_connected",
                        "id": "senin_ai_swarm",
                        "detail": s_res.get("message", "Connected to Senin AI Swarm in senin/ai"),
                        "online_count": s_res.get("online_count", 0),
                        "sovereignty": "Lucy is sovereign master; bots are subordinate worker tools.",
                    })
                break

        for pat in NATURAL_WRITER_CONNECT_PATTERNS:

            if re.search(pat, raw, re.IGNORECASE):

                if hasattr(self.runtime, "connect_writer_bot"):

                    w_res = self.runtime.connect_writer_bot()

                    executed_actions.append({

                        "type": "writer_connected",

                        "id": "writer_bot",

                        "detail": w_res.get("message", "Connected to Writer Bot on port 5820"),

                        "online": w_res.get("online", False),

                    })

                break

        # 4. Detect natural folder creation

        for pat in NATURAL_FOLDER_MAKE_PATTERNS:

            for match in re.finditer(pat, raw, re.IGNORECASE):

                folder_name = match.group(1).strip().rstrip(".,;\"'")

                if folder_name.lower() in ("called", "named", "for", "at", "an", "a", "the", "new"):

                    continue

                if folder_name and hasattr(self.runtime, "create_folder"):

                    f_res = self.runtime.create_folder(folder_name)

                    if f_res.get("ok"):

                        executed_actions.append({

                            "type": "folder_created",

                            "id": f_res.get("relative_path", folder_name),

                            "detail": f_res.get("path", folder_name),

                        })

        # 1. Detect natural task creation

        for pat in NATURAL_TASK_ADD_PATTERNS:

            for match in re.finditer(pat, raw, re.IGNORECASE):

                raw_task = match.group(1).strip()

                task_text = re.split(

                    r",\s*(?:and|also|then|remember|note|plus)\b",

                    raw_task,

                    flags=re.IGNORECASE,

                )[0].strip().rstrip(".,;\"'")

                if len(task_text) >= 4 and hasattr(self.runtime, "projects"):

                    res = self.runtime.projects.add_task(task_text)

                    if not isinstance(res, dict) or res.get("added", True):

                        task = res.get("task", res) if isinstance(res, dict) else {}

                        executed_actions.append({

                            "type": "task_added",

                            "id": task.get("id", "task"),

                            "detail": task.get("text", task_text),

                        })

                        if getattr(self.runtime, "receipt_ledger", None):

                            self.runtime.receipt_ledger.issue_receipt(

                                action_category="task_mutation",

                                operation="add_task",

                                target=str(task.get("id", "task")),

                                verified_outcome=f"Added task: {task_text}",

                            )

        # 2. Detect natural task completion

        for pat in NATURAL_TASK_DONE_PATTERNS:

            for match in re.finditer(pat, raw, re.IGNORECASE):

                selector = match.group(1).strip().rstrip(".,;\"'")

                if selector and hasattr(self.runtime, "projects"):

                    res = self.runtime.projects.complete_task(selector)

                    if isinstance(res, dict) and res.get("completed"):

                        t = res.get("task", res)

                        executed_actions.append({

                            "type": "task_completed",

                            "id": t.get("id", selector),

                            "detail": t.get("text", selector),

                        })

                        if getattr(self.runtime, "receipt_ledger", None):

                            self.runtime.receipt_ledger.issue_receipt(

                                action_category="task_mutation",

                                operation="complete_task",

                                target=str(t.get("id", selector)),

                                verified_outcome=f"Completed task: {t.get('text', selector)}",

                            )

        # 3. Detect natural memory facts (preserving subject context)

        mem_patterns = [

            (r"(?:remember\s+that|don't\s+forget\s+that|note\s+that|keep\s+in\s+mind\s+that)\s+([^.!?\n]{6,200})", 1),

            (r"(?:my\s+(?:current\s+|main\s+|primary\s+)?(?:project|goal|stack|deadline|laptop|gpu|os|editor|workflow|priority|focus)\s+is\s+[^.!?\n]{3,160})", 0),

            (r"(?:i\s+am\s+currently\s+(?:working\s+on|building|fixing|debugging)\s+[^.!?\n]{4,160})", 0),

        ]

        saved_facts: list[str] = []

        for pat, group_idx in mem_patterns:

            for match in re.finditer(pat, raw, re.IGNORECASE):

                fact_candidate = match.group(group_idx).strip().rstrip(".,;\"'")

                if len(fact_candidate) >= 8 and fact_candidate.lower() not in saved_facts:

                    saved_facts.append(fact_candidate.lower())

                    if hasattr(self.runtime, "remember"):

                        self.runtime.remember(fact_candidate, category="auto_extracted", source="conversation")

                    executed_actions.append({

                        "type": "memory_saved",

                        "id": "memory_graph",

                        "detail": fact_candidate,

                    })

                    if getattr(self.runtime, "receipt_ledger", None):

                        self.runtime.receipt_ledger.issue_receipt(

                            action_category="memory_mutation",

                            operation="remember_fact",

                            target="memory_graph",

                            verified_outcome=f"Saved fact: {fact_candidate}",

                        )

        # 4. Personal Profiler & Workflow Correction Learning (once per turn)

        if hasattr(self.runtime, "personal_profiler"):

            prof_res = self.runtime.personal_profiler.observe_interaction(raw)

            for upd in prof_res.get("updates", []):

                executed_actions.append({

                    "type": "profile_adapted",

                    "id": "personal_profiler",

                    "detail": upd,

                })

        if hasattr(self.runtime, "workflow_learner"):

            corr_res = self.runtime.workflow_learner.observe_for_corrections(raw)

            for rule in corr_res.get("rules_added", []):

                executed_actions.append({

                    "type": "correction_locked",

                    "id": "workflow_learner",

                    "detail": rule,

                })

        summary_lines = []

        if executed_actions:

            summary_lines.append("[Verified Turn Actions Already Executed (Stage 59)]:")

            for act in executed_actions:

                summary_lines.append(f"- {act['type']} ({act['id']}): {act['detail']}")

        return {

            "stage": STAGE,

            "actions_executed": len(executed_actions),

            "actions": executed_actions,

            "summary_block": "\n".join(summary_lines),

        }

    def status(self) -> dict[str, Any]:

        return {

            "stage": STAGE,

            "natural_action_parser": "active",

            "capabilities": [

                "natural_task_add",

                "natural_task_complete",

                "auto_memory_upsert",

                "auto_alias_and_pace_adaptation",

                "auto_correction_guardrail_lock",

            ],

        }
