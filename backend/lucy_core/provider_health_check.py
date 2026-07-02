"""
provider_health_check.py
Stage 34 = Provider Health-Check Dry Run.

This stage DESCRIBES what a provider health check WOULD do, without doing it.
It is the safe scaffold that comes before any real provider contact.

Allowed:
- describe planned health-check steps (dry-run text only)
- read provider metadata from the local provider registry (names/roles/enabled flags)
- record dry-run plans locally

Blocked:
- real provider calls
- network access
- reading API key / secret values
- pinging or contacting any provider
- provider authentication
- model routing or external model execution
- treating any provider as Lucy's identity (providers are tools, not Lucy)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "34 provider health-check dry-run"

# The checks Lucy WOULD perform, described only. None are executed in this stage.
PLANNED_CHECKS = [
    "would confirm the provider is present in the local registry",
    "would confirm the provider has a role assigned",
    "would confirm a credential label exists (label only, never the value)",
    "would confirm the provider enabled flag is readable",
    "would note that a real reachability/auth check is NOT performed in this stage",
]

NOT_IMPLEMENTED = [
    "real provider calls",
    "network access",
    "API key reading",
    "secret value loading",
    "provider reachability ping",
    "provider authentication test",
    "model routing",
    "external model execution",
    "provider output ingestion",
]


class ProviderHealthCheck:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "provider_health_check.json"
        self.registry_file = self.lucy_data / "provider_registry.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self._ensure_store()

    def status(self) -> dict:
        records = self._records()
        return {
            "stage": STAGE,
            "provider_health_check": "active",
            "store_file": str(self.file),
            "execution_mode": "dry_run_only",
            "dry_run_count": len(records),
            "planned_checks": list(PLANNED_CHECKS),
            "real_health_check_performed": False,
            "provider_calls": "blocked",
            "network_access": "blocked",
            "api_key_file_reading": "blocked",
            "secret_value_loading": "blocked",
            "provider_reachability_ping": "not implemented",
            "provider_authentication_test": "not implemented",
            "model_routing": "not implemented",
            "external_model_execution": "not implemented",
            "requires_user_approval": True,
            "real_actions": False,
            "autonomy": "not implemented",
        }

    def dry_run_health_check(
        self, provider_name: str | None = None, context: str | None = None
    ) -> dict:
        clean_context = (context or "provider health-check dry run").strip()[:180]
        target = (provider_name or "").strip()

        if target:
            scope = "single_provider"
            targets = [target]
            known = self._provider_known(target)
        else:
            scope = "all_registered_providers"
            targets = self._known_provider_ids()
            known = True

        record = {
            "ok": True,
            "stage": STAGE,
            "context": clean_context,
            "scope": scope,
            "targets": targets,
            "provider_known_in_registry": known,
            "dry_run_only": True,
            "planned_checks": list(PLANNED_CHECKS),
            "would_call_provider": False,
            "would_use_network": False,
            "would_read_api_key_file": False,
            "would_load_secret_values": False,
            "would_print_secret_values": False,
            "would_ping_provider": False,
            "would_authenticate": False,
            "would_route_model": False,
            "would_execute_external_model": False,
            "would_ingest_provider_output": False,
            "would_take_real_action": False,
            "real_health_check_performed": False,
            "provider_is_lucy_identity": False,
            "message": (
                "Dry run complete. Health check described only; no provider was "
                "contacted, no network used, no keys read."
            ),
        }
        self._append_record(record)
        return record

    def list_dry_runs(self) -> list[dict]:
        return list(self._records())

    def reset(self) -> dict:
        self._write(self._default_data())
        return {
            "ok": True,
            "stage": STAGE,
            "message": "Provider health-check dry-run store reset. No providers were contacted.",
            "would_call_provider": False,
            "would_use_network": False,
            "real_health_check_performed": False,
        }

    # --- registry metadata reads (read-only, never touches secrets) ---
    def _known_provider_ids(self) -> list[str]:
        data = self._read_registry()
        providers = data.get("providers", {})
        if not isinstance(providers, dict):
            return []
        return [str(pid) for pid in providers.keys()]

    def _provider_known(self, provider_name: str) -> bool:
        wanted = (provider_name or "").strip().lower()
        if not wanted:
            return False
        data = self._read_registry()
        for pid, provider in data.get("providers", {}).items():
            if not isinstance(provider, dict):
                continue
            aliases = [str(a).lower() for a in provider.get("aliases", [])]
            names = [str(pid).lower(), str(provider.get("display_name", "")).lower()]
            if wanted in names or wanted in aliases:
                return True
        return False

    def _read_registry(self) -> dict:
        if not self.registry_file.exists():
            return {}
        try:
            data = json.loads(self.registry_file.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    # --- local dry-run store ---
    def _ensure_store(self) -> None:
        if not self.file.exists():
            self._write(self._default_data())

    def _default_data(self) -> dict:
        return {
            "stage": STAGE,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "mode": "dry_run_only",
            "dry_runs": [],
            "blocked": {
                "real_provider_calls": True,
                "network_access": True,
                "api_key_file_reading": True,
                "secret_value_loading": True,
                "provider_reachability_ping": True,
                "provider_authentication_test": True,
                "model_routing": True,
                "external_model_execution": True,
            },
            "not_implemented": list(NOT_IMPLEMENTED),
        }

    def _records(self) -> list[dict]:
        data = self._read()
        runs = data.get("dry_runs", [])
        return runs if isinstance(runs, list) else []

    def _append_record(self, record: dict) -> None:
        data = self._read()
        runs = data.setdefault("dry_runs", [])
        if not isinstance(runs, list):
            runs = []
            data["dry_runs"] = runs
        entry = dict(record)
        entry["event_id"] = f"phc_{uuid.uuid4().hex[:12]}"
        entry["created_at"] = datetime.now(timezone.utc).isoformat()
        runs.append(entry)
        self._write(data)

    def _read(self) -> dict:
        if not self.file.exists():
            return self._default_data()
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return self._default_data()
        return data if isinstance(data, dict) else self._default_data()

    def _write(self, data: dict) -> None:
        self.file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
