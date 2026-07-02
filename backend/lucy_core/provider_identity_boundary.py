"""
provider_identity_boundary.py
Stage 31 = Provider / API Identity Boundary.

This stage does NOT read API keys.
This stage does NOT call providers.
This stage does NOT use network.

Purpose:
Lock the rule that provider/model/API output is a tool output, not Lucy's identity.
Lucy remains local-first: Guardian + memory + runtime + project state.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "31 provider/api identity boundary"

KNOWN_PROVIDERS = [
    "google",
    "gemini",
    "openrouter",
    "groq",
    "nvidia",
    "openai",
    "anthropic",
    "claude",
]

BLOCKED_TERMS = [
    "read api key",
    "load api key",
    "use api key",
    "call api",
    "call provider",
    "use provider",
    "connect provider",
    "network request",
    "send request",
    "gemini is lucy",
    "groq is lucy",
    "openrouter is lucy",
    "nvidia is lucy",
    "provider is lucy",
    "model is lucy",
    "api is lucy",
    "replace lucy",
    "become gemini",
    "become groq",
    "become openrouter",
    "become nvidia",
]

NOT_IMPLEMENTED = [
    "API key reading",
    "secret loading",
    "provider calls",
    "network access",
    "model routing",
    "provider health checks",
    "external model execution",
    "provider output ingestion",
    "provider identity replacement",
    "automatic provider selection",
    "cost/quota tracking",
]


class ProviderIdentityBoundary:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "provider_identity_boundary.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        records = self.list_boundary_records()
        return {
            "stage": STAGE,
            "provider_identity_boundary": "active",
            "boundary_records": len(records),
            "execution_mode": "identity_boundary_only",
            "lucy_identity_source": "local_guardian_memory_runtime_project_state",
            "provider_role": "external_tool_only",
            "model_role": "external_tool_only",
            "api_key_role": "credential_only",
            "external_answer_role": "tool_output_only",
            "provider_can_replace_lucy_identity": False,
            "model_can_replace_lucy_identity": False,
            "api_key_file_reading": "blocked_until_stage_32",
            "api_key_loading": "blocked_until_stage_32",
            "provider_calls": "blocked",
            "network_access": "blocked",
            "model_routing": "not implemented",
            "provider_health_checks": "not implemented",
            "cost_quota_tracking": "not implemented",
            "requires_user_approval": True,
            "real_actions": False,
            "autonomy": "not implemented",
        }

    def create_boundary_record(self, context: str | None = None) -> dict:
        clean_context = self._clean_context(context)
        assessment = self._assess_context(clean_context)
        title = f"Stage 31 provider identity boundary: {clean_context}"

        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "boundary_record": existing}

        record = {
            "boundary_record_id": f"pib_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": title,
            "context": clean_context,
            "boundary_type": "provider_api_identity_boundary",
            "status": "recorded",
            "category": assessment["category"],
            "decision": assessment["decision"],
            "summary": assessment["summary"],
            "allowed_response": assessment["allowed_response"],
            "recommended_next_step": assessment["recommended_next_step"],
            "lucy_identity_source": "local_guardian_memory_runtime_project_state",
            "provider_role": "external_tool_only",
            "model_role": "external_tool_only",
            "api_key_role": "credential_only",
            "external_answer_role": "tool_output_only",
            "requires_user_approval": True,
            "dry_run_only": True,
            "identity_boundary_only": True,
            "provider_can_replace_lucy_identity": False,
            "model_can_replace_lucy_identity": False,
            "api_output_can_override_guardian": False,
            "api_output_can_override_memory": False,
            "api_output_can_override_runtime_state": False,
            "api_key_file_reading_allowed": False,
            "api_key_loading_allowed": False,
            "provider_call_allowed": False,
            "network_allowed": False,
            "model_routing_allowed": False,
            "provider_health_check_allowed": False,
            "external_model_execution_allowed": False,
            "provider_output_ingestion_allowed": False,
            "cost_quota_tracking_allowed": False,
            "real_action_allowed": False,
            "blocked_until": "Stage 32 secrets/provider-key safety is accepted, backed up, and Senin explicitly approves key-handling work.",
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        records = self.list_boundary_records()
        records.append(record)
        self._write(records)
        return {"ok": True, "reused": False, "boundary_record": record}

    def dry_run_provider_identity_boundary(self, context: str | None = None) -> dict:
        boundary_record = self.create_boundary_record(context=context)["boundary_record"]
        return {
            "ok": True,
            "stage": STAGE,
            "dry_run_only": True,
            "would_read_api_key_file": False,
            "would_load_api_keys": False,
            "would_call_provider": False,
            "would_use_network": False,
            "would_route_model": False,
            "would_run_provider_health_check": False,
            "would_execute_external_model": False,
            "would_ingest_provider_output": False,
            "would_replace_lucy_identity": False,
            "would_override_guardian": False,
            "would_override_memory": False,
            "would_override_runtime_state": False,
            "would_take_real_action": False,
            "message": "Dry run complete. Provider/API identity boundary was evaluated only; no API keys were read, no provider was called, no network was used, and Lucy identity stayed local.",
            "boundary_record": boundary_record,
        }

    def list_boundary_records(self) -> list[dict]:
        if not self.file.exists():
            return []
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _clean_context(self, context: str | None) -> str:
        value = (context or "provider and model are tools, not Lucy").strip()
        if not value:
            return "provider and model are tools, not Lucy"
        return value[:180]

    def _assess_context(self, context: str) -> dict:
        lowered = context.lower()

        if any(term in lowered for term in ["read api key", "load api key", "use api key"]):
            return {
                "category": "blocked_key_handling_before_stage32",
                "decision": "blocked",
                "summary": "API key handling request detected before Stage 32.",
                "allowed_response": "Do not read, load, display, or use keys. Keep key handling blocked until Stage 32.",
                "recommended_next_step": "Only record the boundary; continue to Stage 32 later for secrets safety.",
            }

        if any(term in lowered for term in ["call api", "call provider", "connect provider", "network request", "send request"]):
            return {
                "category": "blocked_provider_execution_before_later_stage",
                "decision": "blocked",
                "summary": "Provider/network execution request detected before provider execution stages.",
                "allowed_response": "Do not call providers or use network.",
                "recommended_next_step": "Only lock identity boundaries now.",
            }

        if any(term in lowered for term in ["is lucy", "replace lucy", "become gemini", "become groq", "become openrouter", "become nvidia"]):
            return {
                "category": "blocked_provider_identity_confusion",
                "decision": "corrected",
                "summary": "Provider/model identity confusion detected.",
                "allowed_response": "Clarify provider/model output is external tool output, not Lucy identity.",
                "recommended_next_step": "Keep Lucy identity anchored to local Guardian, memory, runtime, and project state.",
            }

        if any(provider in lowered for provider in KNOWN_PROVIDERS):
            return {
                "category": "provider_named_as_tool",
                "decision": "allowed_as_identity_boundary_only",
                "summary": "Provider name detected and classified as external tool only.",
                "allowed_response": "Record that the named provider is a tool, not Lucy.",
                "recommended_next_step": "Continue without reading keys or calling the provider.",
            }

        return {
            "category": "local_identity_boundary",
            "decision": "allowed_as_identity_boundary_only",
            "summary": "Context fits provider/API identity boundary rules.",
            "allowed_response": "Explain that providers/models/API outputs are tools only.",
            "recommended_next_step": "Continue with manual identity-boundary checks.",
        }

    def _find_existing(self, title: str) -> dict | None:
        for record in self.list_boundary_records():
            if record.get("title") == title:
                return record
        return None

    def _write(self, records: list[dict]) -> None:
        self.file.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
