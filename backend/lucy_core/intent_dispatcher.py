"""
intent_dispatcher.py
Stage 48 = Autonomous Intent-to-Task Dispatcher (Natural Language -> Tool Execution).

Translates natural language user requests into verified operator workflows without
requiring the user to memorize rigid command-line arguments:
1. Intent Classifier:
   - SYSTEM_TELEMETRY: Hardware, RAM, CPU, disk, battery questions.
   - PROCESS_INSPECTION: Running tasks, process health (e.g. 'is ollama running?').
   - WORKSPACE_SEARCH: File searching and regex content grep across workspace.
   - CODE_SYNTHESIS_REQUEST: 'write a script to...', 'create a python tool that...'.
   - LORA_SLEEP_CYCLE: 'train personal lora', 'run sleep cycle'.
   - GENERAL_CONVERSATION: Forwarded cleanly to the multi-turn conversational core.
2. Safe Autonomous Execution:
   - Resolves workspace aliases ('tv', 'drift', 'keys') from Stage 44.
   - Routes telemetry and process queries directly to OperatorToolkit (Stage 47).
   - Routes code generation requests through CodeSynthesisPipeline (Stage 40) + TaskDaemon (Stage 38).
3. Ground Truth Verification:
   - Never hallucinates system state; returns physical hardware and disk facts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


STAGE = "48 autonomous intent dispatcher"


class IntentType:
    SYSTEM_TELEMETRY = "SYSTEM_TELEMETRY"
    PROCESS_INSPECTION = "PROCESS_INSPECTION"
    WORKSPACE_SEARCH = "WORKSPACE_SEARCH"
    CODE_SYNTHESIS_REQUEST = "CODE_SYNTHESIS_REQUEST"
    LORA_SLEEP_CYCLE = "LORA_SLEEP_CYCLE"
    PORT_PROBE = "PORT_PROBE"
    SANDBOX_CLEANUP = "SANDBOX_CLEANUP"
    IDENTITY_AND_CREATOR = "IDENTITY_AND_CREATOR"
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"


@dataclass
class IntentClassification:
    intent_type: str
    confidence: float
    extracted_target: str
    raw_text: str


class IntentDispatcher:
    """Classifies user intent and routes to verified operator subsystems."""

    def __init__(
        self,
        runtime: Any,
        profiler: Any = None,
        toolkit: Any = None,
    ) -> None:
        self.runtime = runtime
        self.profiler = profiler
        self.toolkit = toolkit
        self.dispatch_count = 0

    def classify_intent(self, text: str) -> IntentClassification:
        """Classifies natural language input into structured intent types."""
        raw = str(text or "").strip()
        lowered = raw.lower()

        # 1. Telemetry / Hardware metrics
        telem_patterns = [
            r"\b(how much (free )?(ram|memory|disk|space)|battery (percentage|level|status)|hardware status|system (info|telemetry)|cpu usage|memory load|disk usage)\b",
            r"\b(check (the )?(battery|ram|memory|disk|hardware|system))\b",
            r"\b(how much free space|how much free ram|how much free memory|how much free disk)\b",
            r"\b(ram and disk|memory and disk|cpu and ram)\b",
        ]
        for pat in telem_patterns:
            if re.search(pat, lowered):
                return IntentClassification(
                    intent_type=IntentType.SYSTEM_TELEMETRY,
                    confidence=0.95,
                    extracted_target="system_telemetry",
                    raw_text=raw,
                )

        # 2. Port & Network probing
        port_patterns = [
            r"\b(check (the )?ports|probe (the )?ports|are ports (open|listening)|network status|is port \d+ open)\b",
            r"\b(is ollama (online|running|listening)|is swarm (online|running))\b",
        ]
        for pat in port_patterns:
            if re.search(pat, lowered):
                return IntentClassification(
                    intent_type=IntentType.PORT_PROBE,
                    confidence=0.92,
                    extracted_target="ports",
                    raw_text=raw,
                )

        # 3. Process inspection
        proc_patterns = [
            r"\b(is process \w+ running|find process \w+|check tasklist|running processes|what processes are running)\b",
            r"\b(check if \w+(\.exe)? is running)\b",
        ]
        for pat in proc_patterns:
            m = re.search(pat, lowered)
            if m:
                # Extract target name if present
                words = lowered.split()
                target = words[-1] if len(words) > 1 else ""
                return IntentClassification(
                    intent_type=IntentType.PROCESS_INSPECTION,
                    confidence=0.90,
                    extracted_target=target,
                    raw_text=raw,
                )

        # 4. Workspace file search
        search_patterns = [
            r"\b(find file|search for file|where is file|search files|search workspace for|grep for)\s+([\w\s._-]+)",
            r"\b(where is (the )?([\w._-]+)\s+(folder|file|directory))\b",
        ]
        for pat in search_patterns:
            m = re.search(pat, lowered)
            if m:
                target = m.group(m.lastindex).strip() if m.lastindex else ""
                return IntentClassification(
                    intent_type=IntentType.WORKSPACE_SEARCH,
                    confidence=0.90,
                    extracted_target=target,
                    raw_text=raw,
                )

        # 5. Code synthesis request
        synth_patterns = [
            r"\b(write a (python )?(script|tool|program) (that|to)|create a (python )?(script|tool) (that|to)|generate code (that|to)|build a tool (that|to))\s+([^.!?\n]+)",
        ]
        for pat in synth_patterns:
            m = re.search(pat, lowered)
            if m:
                target = m.group(m.lastindex).strip() if m.lastindex else raw
                return IntentClassification(
                    intent_type=IntentType.CODE_SYNTHESIS_REQUEST,
                    confidence=0.95,
                    extracted_target=target,
                    raw_text=raw,
                )

        # 6. LoRA Sleep cycle request
        lora_patterns = [
            r"\b(train personal lora|run personal sleep cycle|trigger sleep cycle|update personal weights|adapt personal model)\b",
        ]
        for pat in lora_patterns:
            if re.search(pat, lowered):
                return IntentClassification(
                    intent_type=IntentType.LORA_SLEEP_CYCLE,
                    confidence=0.95,
                    extracted_target="personal_sleep_cycle",
                    raw_text=raw,
                )

        # 7. Sandbox cache cleanup
        clean_patterns = [
            r"\b(clean (sandbox|cache|temporary files|staging files)|clear staging|clean staging)\b",
        ]
        for pat in clean_patterns:
            if re.search(pat, lowered):
                return IntentClassification(
                    intent_type=IntentType.SANDBOX_CLEANUP,
                    confidence=0.95,
                    extracted_target="sandbox_cleanup",
                    raw_text=raw,
                )

        # 8. Sovereign Identity and Creator inquiries
        creator_patterns = [
            r"\b(who\s+(?:program+ed|made|created|built|designed|developed|coded)\s+you)\b",
            r"\b(who\s+is\s+your\s+(?:creator|programmer|maker|author|developer|designer))\b",
            r"\b(who\s+(?:are\s+you|r\s+u)\s*(?:lucy)?)\b",
        ]
        for pat in creator_patterns:
            if re.search(pat, lowered):
                return IntentClassification(
                    intent_type=IntentType.IDENTITY_AND_CREATOR,
                    confidence=0.99,
                    extracted_target="sovereign_identity",
                    raw_text=raw,
                )

        # Default fallback
        return IntentClassification(
            intent_type=IntentType.GENERAL_CONVERSATION,
            confidence=0.50,
            extracted_target="",
            raw_text=raw,
        )

    def dispatch(self, user_text: str) -> dict[str, Any] | None:
        """
        Executes autonomous actions if the intent matches an operator task.
        Returns dict with execution result, or None if it should fall through to conversation.
        """
        classification = self.classify_intent(user_text)
        itype = classification.intent_type
        self.dispatch_count += 1

        # 1. Telemetry
        if itype == IntentType.SYSTEM_TELEMETRY:
            if hasattr(self.runtime, "system_telemetry"):
                telem = self.runtime.system_telemetry()
                ram = telem.get("ram", {})
                disk = telem.get("disk", {})
                power = telem.get("power", {})
                msg = (
                    f"[Telemetry Check]\n"
                    f"• RAM: {ram.get('available_mb', 0)} MB free ({ram.get('memory_load_percent', 0)}% load)\n"
                    f"• Disk C: {disk.get('free_gb', 0)} GB free ({disk.get('percent_free', 0)}% free)\n"
                    f"• Power: {power.get('ac_line_status', 'Unknown')} ({power.get('battery_percent', 'N/A')})"
                )
                return {"handled": True, "intent": itype, "message": msg, "data": telem}

        # 2. Port & Network probe
        if itype == IntentType.PORT_PROBE:
            if hasattr(self.runtime, "probe_network_ports"):
                res = self.runtime.probe_network_ports()
                lines = [f"[Network Socket Probes] {res.get('active_services', 0)}/{res.get('total_probed', 0)} services online:"]
                for port, info in res.get("ports", {}).items():
                    lines.append(f"• Port {port} ({info.get('service')}): {info.get('status')}")
                return {"handled": True, "intent": itype, "message": "\n".join(lines), "data": res}

        # 3. Process inspection
        if itype == IntentType.PROCESS_INSPECTION:
            if hasattr(self.runtime, "inspect_processes"):
                target = classification.extracted_target or ""
                procs = self.runtime.inspect_processes(query=target, limit=10)
                if procs:
                    lines = [f"[Process Inspector] Found {len(procs)} matching process(es):"]
                    for p in procs:
                        lines.append(f"• [PID {p.get('pid')}] {p.get('name')} (Memory: {p.get('memory')})")
                    msg = "\n".join(lines)
                else:
                    msg = f"[Process Inspector] No active processes found matching '{target}'."
                return {"handled": True, "intent": itype, "message": msg, "data": procs}

        # 4. Workspace search
        if itype == IntentType.WORKSPACE_SEARCH:
            if hasattr(self.runtime, "search_workspace_files"):
                target = classification.extracted_target or ""
                # Check alias first
                if hasattr(self.runtime, "personal_profiler"):
                    target = self.runtime.personal_profiler.resolve_alias(target)
                matches = self.runtime.search_workspace_files(pattern=target, search_content=True, limit=10)
                if matches:
                    lines = [f"[Workspace Search] Found {len(matches)} match(es) for '{target}':"]
                    for m in matches:
                        lines.append(f"• {m.get('name')} ({m.get('size_bytes', 0)} bytes) -> {m.get('path')}")
                    msg = "\n".join(lines)
                else:
                    msg = f"[Workspace Search] No files found matching '{target}'."
                return {"handled": True, "intent": itype, "message": msg, "data": matches}

        # 5. Sandbox cleanup
        if itype == IntentType.SANDBOX_CLEANUP:
            if hasattr(self.runtime, "clean_sandbox_cache"):
                clean_res = self.runtime.clean_sandbox_cache(dry_run=False)
                msg = f"[Sandbox Cleanup] Freed {clean_res.get('bytes_freed', 0)} bytes across {clean_res.get('files_found', 0)} staging file(s)."
                return {"handled": True, "intent": itype, "message": msg, "data": clean_res}

        # 6. LoRA Sleep cycle
        if itype == IntentType.LORA_SLEEP_CYCLE:
            if hasattr(self.runtime, "trigger_personal_sleep_cycle"):
                res = self.runtime.trigger_personal_sleep_cycle()
                msg = f"[Personal LoRA Sleep Cycle] {res.get('badge', '')} - Adapter: {res.get('adapter_name', '')} (Records: {res.get('dataset_record_count', 0)})"
                return {"handled": True, "intent": itype, "message": msg, "data": res}

        # 7. Code synthesis request
        if itype == IntentType.CODE_SYNTHESIS_REQUEST:
            if hasattr(self.runtime, "submit_synthesis_task"):
                instruction = classification.extracted_target or user_text
                task_res = self.runtime.submit_synthesis_task(instruction)
                msg = f"[Code Synthesis Task Queued]\n• Task ID: {task_res.get('task_id')}\n• Instruction: {instruction}\n• Pipeline: AST parsing -> physical byte-compilation -> execution test."
                return {"handled": True, "intent": itype, "message": msg, "data": task_res}

        # General conversation / not directly handled by operator dispatch
        return None

    def status(self) -> dict[str, Any]:
        """Returns snapshot of intent dispatcher status."""
        return {
            "stage": STAGE,
            "intent_dispatcher": "active",
            "dispatch_count": self.dispatch_count,
            "supported_intents": [
                IntentType.SYSTEM_TELEMETRY,
                IntentType.PROCESS_INSPECTION,
                IntentType.WORKSPACE_SEARCH,
                IntentType.CODE_SYNTHESIS_REQUEST,
                IntentType.LORA_SLEEP_CYCLE,
                IntentType.PORT_PROBE,
                IntentType.SANDBOX_CLEANUP,
                IntentType.IDENTITY_AND_CREATOR,
                IntentType.GENERAL_CONVERSATION,
            ],
        }
