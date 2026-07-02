"""
provider_registry.py
Stage 33 = Provider Registry.

This stage creates a safe local registry of external model providers.

Allowed:
- store provider names
- store provider aliases
- store provider roles
- store enabled/disabled state
- store future capability notes

Blocked:
- API key values
- reading APIKEYS file
- provider calls
- network access
- health checks
- model routing
- external model execution
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "33 provider registry"

DEFAULT_PROVIDERS = {
    "google": {
        "provider_id": "google",
        "display_name": "Google / Gemini",
        "aliases": ["google", "gemini"],
        "role": "external_model_provider",
        "enabled": False,
        "future_use": "Gemini model provider after later approval.",
        "credential_label_only": ["GOOGLE API KEY", "GEMINI API KEY"],
    },
    "openrouter": {
        "provider_id": "openrouter",
        "display_name": "OpenRouter",
        "aliases": ["openrouter"],
        "role": "external_model_provider_gateway",
        "enabled": False,
        "future_use": "Multi-model routing gateway after later approval.",
        "credential_label_only": ["OPENROUTER API KEY"],
    },
    "groq": {
        "provider_id": "groq",
        "display_name": "Groq",
        "aliases": ["groq"],
        "role": "external_model_provider",
        "enabled": False,
        "future_use": "Fast external model provider after later approval.",
        "credential_label_only": ["GROQ API KEY"],
    },
    "nvidia": {
        "provider_id": "nvidia",
        "display_name": "NVIDIA",
        "aliases": ["nvidia"],
        "role": "external_model_provider",
        "enabled": False,
        "future_use": "NVIDIA external model provider after later approval.",
        "credential_label_only": ["NVIDIA API KEY"],
    },
}

NOT_IMPLEMENTED = [
    "API key reading",
    "secret value loading",
    "provider calls",
    "network access",
    "provider health checks",
    "model routing",
    "external model execution",
    "provider output ingestion",
    "cost/quota tracking",
]


class ProviderRegistry:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "provider_registry.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self._ensure_registry()

    def status(self) -> dict:
        providers = self.list_providers()
        enabled = [p for p in providers if p.get("enabled") is True]
        disabled = [p for p in providers if p.get("enabled") is not True]

        return {
            "stage": STAGE,
            "provider_registry": "active",
            "registry_file": str(self.file),
            "execution_mode": "local_provider_metadata_only",
            "provider_count": len(providers),
            "enabled_provider_count": len(enabled),
            "disabled_provider_count": len(disabled),
            "provider_names": [p.get("provider_id") for p in providers],
            "enabled_providers": [p.get("provider_id") for p in enabled],
            "disabled_providers": [p.get("provider_id") for p in disabled],
            "provider_names_allowed": True,
            "provider_roles_allowed": True,
            "provider_enabled_state_allowed": True,
            "credential_labels_only": True,
            "api_key_values": "blocked",
            "api_key_file_reading": "blocked",
            "secret_value_loading": "blocked",
            "provider_calls": "blocked",
            "network_access": "blocked",
            "provider_health_checks": "not implemented",
            "model_routing": "not implemented",
            "external_model_execution": "not implemented",
            "requires_user_approval": True,
            "real_actions": False,
            "autonomy": "not implemented",
        }

    def list_providers(self) -> list[dict]:
        data = self._read()
        providers = data.get("providers", {})
        if not isinstance(providers, dict):
            return []
        return [self._safe_provider_view(provider) for provider in providers.values() if isinstance(provider, dict)]

    def get_provider(self, provider_name: str) -> dict:
        provider_id = self._resolve_provider_id(provider_name)
        if provider_id is None:
            return {
                "ok": False,
                "reason": "provider_not_found",
                "requested_provider": provider_name,
                "stage": STAGE,
                "provider_call_allowed": False,
                "network_allowed": False,
                "api_key_values_returned": False,
            }

        data = self._read()
        provider = data["providers"][provider_id]
        return {
            "ok": True,
            "provider": self._safe_provider_view(provider),
            "stage": STAGE,
            "provider_call_allowed": False,
            "network_allowed": False,
            "api_key_values_returned": False,
        }

    def set_provider_enabled(self, provider_name: str, enabled: bool) -> dict:
        provider_id = self._resolve_provider_id(provider_name)
        if provider_id is None:
            return {
                "ok": False,
                "reason": "provider_not_found",
                "requested_provider": provider_name,
                "stage": STAGE,
                "provider_call_allowed": False,
                "network_allowed": False,
                "api_key_values_returned": False,
            }

        data = self._read()
        provider = data["providers"][provider_id]
        provider["enabled"] = bool(enabled)
        provider["updated_at"] = datetime.now(timezone.utc).isoformat()
        data.setdefault("registry_events", []).append(
            {
                "event_id": f"prg_{uuid.uuid4().hex[:12]}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "stage": STAGE,
                "event": "provider_enabled_state_changed",
                "provider_id": provider_id,
                "enabled": bool(enabled),
                "api_key_values_returned": False,
                "provider_call_allowed": False,
                "network_allowed": False,
                "real_action_allowed": False,
            }
        )
        self._write(data)

        return {
            "ok": True,
            "provider": self._safe_provider_view(provider),
            "stage": STAGE,
            "changed": True,
            "provider_call_allowed": False,
            "network_allowed": False,
            "api_key_values_returned": False,
            "real_action_allowed": False,
        }

    def reset_registry(self) -> dict:
        self._write(self._default_data())
        return {
            "ok": True,
            "stage": STAGE,
            "message": "Provider registry reset to safe defaults. All providers disabled.",
            "provider_call_allowed": False,
            "network_allowed": False,
            "api_key_values_returned": False,
        }

    def dry_run_provider_registry(self, context: str | None = None) -> dict:
        clean_context = (context or "provider registry dry run").strip()[:180]
        return {
            "ok": True,
            "stage": STAGE,
            "context": clean_context,
            "dry_run_only": True,
            "would_read_api_key_file": False,
            "would_load_secret_values": False,
            "would_print_secret_values": False,
            "would_store_secret_values": False,
            "would_call_provider": False,
            "would_use_network": False,
            "would_run_provider_health_check": False,
            "would_route_model": False,
            "would_execute_external_model": False,
            "would_take_real_action": False,
            "provider_registry_allowed": True,
            "message": "Dry run complete. Provider registry metadata only; no keys, provider calls, network, or health checks were used.",
        }

    def _ensure_registry(self) -> None:
        if not self.file.exists():
            self._write(self._default_data())
            return

        data = self._read()
        providers = data.setdefault("providers", {})

        changed = False
        for provider_id, provider in DEFAULT_PROVIDERS.items():
            if provider_id not in providers:
                providers[provider_id] = self._provider_record(provider)
                changed = True

        if changed:
            self._write(data)

    def _default_data(self) -> dict:
        return {
            "stage": STAGE,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "mode": "local_provider_metadata_only",
            "providers": {
                provider_id: self._provider_record(provider)
                for provider_id, provider in DEFAULT_PROVIDERS.items()
            },
            "registry_events": [],
            "blocked": {
                "api_key_values": True,
                "api_key_file_reading": True,
                "secret_value_loading": True,
                "provider_calls": True,
                "network_access": True,
                "provider_health_checks": True,
                "model_routing": True,
                "external_model_execution": True,
            },
            "not_implemented": list(NOT_IMPLEMENTED),
        }

    def _provider_record(self, provider: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "provider_id": provider["provider_id"],
            "display_name": provider["display_name"],
            "aliases": list(provider["aliases"]),
            "role": provider["role"],
            "enabled": bool(provider.get("enabled", False)),
            "future_use": provider["future_use"],
            "credential_label_only": list(provider["credential_label_only"]),
            "api_key_value": "[blocked]",
            "api_key_value_stored": False,
            "api_key_value_returned": False,
            "provider_call_allowed": False,
            "network_allowed": False,
            "health_check_allowed": False,
            "model_routing_allowed": False,
            "external_model_execution_allowed": False,
            "created_at": now,
            "updated_at": now,
        }

    def _safe_provider_view(self, provider: dict) -> dict:
        return {
            "provider_id": provider.get("provider_id", ""),
            "display_name": provider.get("display_name", ""),
            "aliases": list(provider.get("aliases", [])),
            "role": provider.get("role", ""),
            "enabled": bool(provider.get("enabled", False)),
            "future_use": provider.get("future_use", ""),
            "credential_label_only": list(provider.get("credential_label_only", [])),
            "api_key_value_returned": False,
            "api_key_value_stored": False,
            "provider_call_allowed": False,
            "network_allowed": False,
            "health_check_allowed": False,
            "model_routing_allowed": False,
            "external_model_execution_allowed": False,
        }

    def _resolve_provider_id(self, provider_name: str) -> str | None:
        wanted = (provider_name or "").strip().lower()
        if not wanted:
            return None

        data = self._read()
        for provider_id, provider in data.get("providers", {}).items():
            aliases = [str(a).lower() for a in provider.get("aliases", [])]
            names = [provider_id.lower(), str(provider.get("display_name", "")).lower()]
            if wanted in names or wanted in aliases:
                return provider_id
        return None

    def _read(self) -> dict:
        if not self.file.exists():
            return self._default_data()
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return self._default_data()
        if isinstance(data, dict):
            return data
        return self._default_data()

    def _write(self, data: dict) -> None:
        self.file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
