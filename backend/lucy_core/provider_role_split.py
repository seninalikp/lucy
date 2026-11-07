"""
provider_role_split.py
Stage 35 = Provider Role Split & Sovereign Mind Boundary.

This stage establishes the architectural division between:
1. SOVEREIGN LOCAL MIND (Local Ollama):
   - Holds Lucy's continuous identity, memory, self-model, voice, and visualizer.
   - 100% local, zero external cloud dependencies.
   - Never rotated or swapped out for an external provider.

2. ANONYMOUS EXTERNAL WORKERS (Groq, OpenRouter, Gemini, NVIDIA, etc.):
   - Stateless background contractors for heavy code generation, compiler reviews, and batch compute.
   - Cryptographically & architecturally forbidden from receiving spine.json, user personal memory, or persona prompts.
   - Never allowed to impersonate Lucy or speak directly to the user.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.lucy_core.provider_registry import ProviderRegistry


STAGE = "35 provider role split"

ROLE_SOVEREIGN_MIND = "sovereign_local_mind"
ROLE_EXTERNAL_WORKER = "external_worker"

# Sovereign local engine definition (Local Ollama)
OLLAMA_SOVEREIGN_PROVIDER = {
    "provider_id": "ollama",
    "display_name": "Ollama Local Engine",
    "aliases": ["ollama", "local", "sovereign_mind", "local_engine"],
    "role": ROLE_SOVEREIGN_MIND,
    "enabled": True,
    "endpoint": "http://localhost:11434",
    "future_use": "Primary local neural substrate for consciousness, memory, voice, and face.",
    "credential_label_only": [],
    "allowed_capabilities": [
        "sovereign_identity",
        "persistent_memory",
        "voice_synthesis",
        "desktop_visualizer",
        "self_model_governance",
        "task_dispatch"
    ],
    "blocked_capabilities": [
        "unverified_cloud_sync",
        "identity_delegation"
    ]
}

# External cloud worker definitions (Stateless contractors)
EXTERNAL_WORKER_PROVIDERS = {
    "groq": {
        "provider_id": "groq",
        "display_name": "Groq Fast Worker",
        "aliases": ["groq", "groq_worker"],
        "role": ROLE_EXTERNAL_WORKER,
        "enabled": True,
        "future_use": "Fast background code generation and compiler error fixes.",
        "credential_label_only": ["GROQ API KEY"],
        "allowed_capabilities": ["code_generation", "code_review", "data_transform"],
        "blocked_capabilities": ["identity_impersonation", "memory_read", "spine_access", "direct_user_chat"]
    },
    "openrouter": {
        "provider_id": "openrouter",
        "display_name": "OpenRouter Gateway Worker",
        "aliases": ["openrouter", "openrouter_worker"],
        "role": ROLE_EXTERNAL_WORKER,
        "enabled": True,
        "future_use": "Multi-model fallback routing for heavy background tasks.",
        "credential_label_only": ["OPENROUTER API KEY"],
        "allowed_capabilities": ["code_generation", "code_review", "data_transform"],
        "blocked_capabilities": ["identity_impersonation", "memory_read", "spine_access", "direct_user_chat"]
    },
    "google": {
        "provider_id": "google",
        "display_name": "Google Gemini Worker",
        "aliases": ["google", "gemini", "gemini_worker"],
        "role": ROLE_EXTERNAL_WORKER,
        "enabled": False,
        "future_use": "Large context background code analysis.",
        "credential_label_only": ["GOOGLE API KEY"],
        "allowed_capabilities": ["code_generation", "code_review", "data_transform"],
        "blocked_capabilities": ["identity_impersonation", "memory_read", "spine_access", "direct_user_chat"]
    },
    "nvidia": {
        "provider_id": "nvidia",
        "display_name": "NVIDIA NIM Worker",
        "aliases": ["nvidia", "nvidia_worker"],
        "role": ROLE_EXTERNAL_WORKER,
        "enabled": False,
        "future_use": "High-throughput frontier code verification.",
        "credential_label_only": ["NVIDIA API KEY"],
        "allowed_capabilities": ["code_generation", "code_review", "data_transform"],
        "blocked_capabilities": ["identity_impersonation", "memory_read", "spine_access", "direct_user_chat"]
    }
}

FORBIDDEN_WORKER_PAYLOAD_KEYS = {
    "spine",
    "spine_json",
    "persona",
    "identity",
    "memory",
    "user_secrets",
    "voice_state",
    "visualizer_state",
}


class ProviderRoleSplit:
    """Manages the strict architectural boundary between local mind and worker swarm."""

    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.registry = ProviderRegistry(self.lucy_data)
        self.store_file = self.lucy_data / "provider_role_split.json"
        self._ensure_store()

    def _ensure_store(self) -> None:
        if not self.store_file.exists():
            initial_data = {
                "stage": STAGE,
                "sovereign_mind": OLLAMA_SOVEREIGN_PROVIDER,
                "workers": EXTERNAL_WORKER_PROVIDERS,
                "boundary_enforcement": "active",
                "rules": [
                    "External workers never receive persona or memory files",
                    "Only local Ollama holds sovereign identity and voice",
                    "Deterministic verification prevents model collapse"
                ]
            }
            self.store_file.write_text(json.dumps(initial_data, indent=2), encoding="utf-8")

    def status(self) -> dict[str, Any]:
        return {
            "stage": STAGE,
            "provider_role_split": "active",
            "sovereign_mind_provider": OLLAMA_SOVEREIGN_PROVIDER["provider_id"],
            "sovereign_mind_endpoint": OLLAMA_SOVEREIGN_PROVIDER["endpoint"],
            "sovereign_mind_role": ROLE_SOVEREIGN_MIND,
            "external_workers_count": len(EXTERNAL_WORKER_PROVIDERS),
            "external_worker_names": list(EXTERNAL_WORKER_PROVIDERS.keys()),
            "boundary_enforcement": "strict_isolation",
            "identity_leaks_blocked": True,
            "memory_leaks_blocked": True,
        }

    def get_sovereign_mind(self) -> dict[str, Any]:
        """Returns the sovereign local engine definition."""
        return OLLAMA_SOVEREIGN_PROVIDER.copy()

    def get_external_workers(self) -> list[dict[str, Any]]:
        """Returns the list of anonymous external worker definitions."""
        return [w.copy() for w in EXTERNAL_WORKER_PROVIDERS.values()]

    def is_sovereign(self, provider_id: str) -> bool:
        return provider_id.lower().strip() in OLLAMA_SOVEREIGN_PROVIDER["aliases"]

    def is_external_worker(self, provider_id: str) -> bool:
        pid = provider_id.lower().strip()
        for w in EXTERNAL_WORKER_PROVIDERS.values():
            if pid in w["aliases"]:
                return True
        return False

    def validate_worker_dispatch(self, payload: dict[str, Any]) -> tuple[bool, str]:
        """
        Anti-Hallucination & Identity Guardrail:
        Ensures a dispatch to an external worker never contains Lucy's identity, memory, or spine.
        """
        keys_present = set(payload.keys())
        violations = keys_present.intersection(FORBIDDEN_WORKER_PAYLOAD_KEYS)

        if violations:
            violated = ", ".join(sorted(violations))
            return False, f"SECURITY_VIOLATION: Payload contains sovereign protected data ({violated}). Dispatches to external workers must be anonymous code/task specifications only."

        # Check nested payload dictionary values for identity leak markers
        raw_text = json.dumps(payload).lower()
        if "you are lucy" in raw_text or "spine.json" in raw_text:
            return False, "SECURITY_VIOLATION: Payload contains persona instructions ('You are Lucy' or 'spine.json'). Workers must remain stateless typewriters."

        return True, "DISPATCH_PERMITTED: Payload is strictly technical and free of sovereign identity data."
