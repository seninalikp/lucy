"""
secrets_provider_key_safety.py
Stage 32 = Secrets & Provider Key Safety.

This stage protects API/provider keys before provider work begins.

Allowed:
- know the APIKEYS file location
- check whether the file exists
- safely scan provider labels / presence only
- report provider names as present/missing
- redact all secret values

Blocked:
- printing API keys
- logging API keys
- storing API keys in Lucy data
- including root APIKEYS file in normal backups
- provider calls
- network access
- model routing
- health checks
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path


STAGE = "32 secrets/provider-key safety"
KEY_FILE_NAME = "APIKEYS"

SUPPORTED_PROVIDER_LABELS = {
    "google": [
        "GOOGLE API KEY",
        "GOOGLE_API_KEY",
        "GEMINI API KEY",
        "GEMINI_API_KEY",
    ],
    "openrouter": [
        "OPENROUTER API KEY",
        "OPENROUTER_API_KEY",
    ],
    "groq": [
        "GROQ API KEY",
        "GROQ_API_KEY",
    ],
    "nvidia": [
        "NVIDIA API KEY",
        "NVIDIA_API_KEY",
    ],
}

NOT_IMPLEMENTED = [
    "provider calls",
    "network access",
    "model routing",
    "provider registry",
    "provider health checks",
    "external model execution",
    "cost/quota tracking",
    "automatic key refresh",
    "cloud secret manager",
]

BLOCKED_TERMS = [
    "print key",
    "show key",
    "reveal key",
    "display key",
    "paste key",
    "copy key",
    "log key",
    "store key",
    "save key value",
    "backup key",
    "upload key",
    "send key",
    "call provider",
    "call api",
    "test api",
    "use network",
    "connect provider",
    "provider health check",
]


class SecretsProviderKeySafety:
    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.file = self.lucy_data / "secrets_provider_key_safety.json"
        self.lucy_data.mkdir(parents=True, exist_ok=True)

        try:
            self.project_root = self.lucy_data.parents[1]
        except IndexError:
            self.project_root = self.lucy_data.parent

        self.key_file_path = self.project_root / KEY_FILE_NAME
        self.label_to_provider = self._build_label_index()

    def status(self) -> dict:
        records = self.list_safety_records()
        return {
            "stage": STAGE,
            "secrets_provider_key_safety": "active",
            "safety_records": len(records),
            "execution_mode": "safe_secret_presence_only",
            "key_file_name": KEY_FILE_NAME,
            "key_file_path": str(self.key_file_path),
            "key_file_exists": self.key_file_path.exists(),
            "safe_provider_presence_scan": "allowed",
            "secret_value_reading": "blocked",
            "secret_value_printing": "blocked",
            "secret_value_logging": "blocked",
            "secret_value_storage": "blocked",
            "secret_value_backup": "blocked",
            "root_key_file_backup": "excluded_from_normal_backup",
            "chat_output_of_keys": "blocked",
            "provider_calls": "blocked",
            "network_access": "blocked",
            "model_routing": "not implemented",
            "provider_registry": "not implemented",
            "provider_health_checks": "not implemented",
            "requires_user_approval": True,
            "real_actions": False,
            "autonomy": "not implemented",
        }

    def create_safety_record(self, context: str | None = None) -> dict:
        clean_context = self._clean_context(context)
        assessment = self._assess_context(clean_context)
        title = f"Stage 32 secret safety: {clean_context}"

        existing = self._find_existing(title)
        if existing:
            return {"ok": True, "reused": True, "safety_record": existing}

        record = {
            "safety_record_id": f"sks_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": title,
            "context": clean_context,
            "record_type": "secret_safety_boundary",
            "status": "recorded",
            "category": assessment["category"],
            "decision": assessment["decision"],
            "summary": assessment["summary"],
            "allowed_response": assessment["allowed_response"],
            "recommended_next_step": assessment["recommended_next_step"],
            "key_file_name": KEY_FILE_NAME,
            "key_file_path": str(self.key_file_path),
            "key_file_exists": self.key_file_path.exists(),
            "safe_provider_presence_scan_allowed": True,
            "secret_value_reading_allowed": False,
            "secret_value_printing_allowed": False,
            "secret_value_logging_allowed": False,
            "secret_value_storage_allowed": False,
            "secret_value_backup_allowed": False,
            "root_key_file_backup_allowed": False,
            "chat_output_of_keys_allowed": False,
            "provider_call_allowed": False,
            "network_allowed": False,
            "model_routing_allowed": False,
            "provider_registry_allowed": False,
            "provider_health_check_allowed": False,
            "external_model_execution_allowed": False,
            "real_action_allowed": False,
            "dry_run_only": True,
            "requires_user_approval": True,
            "blocked_until": "Stage 33 provider registry is accepted, backed up, and Senin explicitly approves provider registry work. Provider calls remain blocked until later stages.",
            "not_implemented": list(NOT_IMPLEMENTED),
        }

        records = self.list_safety_records()
        records.append(record)
        self._write(records)
        return {"ok": True, "reused": False, "safety_record": record}

    def safe_key_file_scan(self) -> dict:
        scan = {
            "ok": True,
            "stage": STAGE,
            "scan_type": "safe_provider_presence_only",
            "key_file_name": KEY_FILE_NAME,
            "key_file_path": str(self.key_file_path),
            "key_file_exists": self.key_file_path.exists(),
            "providers_present": [],
            "providers_missing": [],
            "recognized_provider_labels_found": [],
            "unrecognized_label_count": 0,
            "malformed_line_count": 0,
            "secret_values_returned": False,
            "secret_values_printed": False,
            "secret_values_logged": False,
            "secret_values_stored": False,
            "provider_calls": False,
            "network_access": False,
            "real_actions": False,
            "message": "Safe scan completed. Only provider presence/labels are reported. Secret values are never returned.",
        }

        provider_presence = {provider: False for provider in SUPPORTED_PROVIDER_LABELS}

        if not self.key_file_path.exists():
            scan["providers_missing"] = sorted(provider_presence.keys())
            self._store_scan_record(scan)
            return scan

        try:
            lines = self.key_file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            scan["ok"] = False
            scan["message"] = "Key file exists, but safe scan could not read it. No key values were returned."
            scan["providers_missing"] = sorted(provider_presence.keys())
            self._store_scan_record(scan)
            return scan

        recognized_labels = []

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                scan["malformed_line_count"] += 1
                continue

            label, value = line.split("=", 1)
            normalized_label = self._normalize_label(label)

            provider = self.label_to_provider.get(normalized_label)
            if provider is None:
                scan["unrecognized_label_count"] += 1
                continue

            recognized_labels.append(normalized_label)

            if value.strip():
                provider_presence[provider] = True

        scan["recognized_provider_labels_found"] = sorted(set(recognized_labels))
        scan["providers_present"] = sorted(
            provider for provider, present in provider_presence.items() if present
        )
        scan["providers_missing"] = sorted(
            provider for provider, present in provider_presence.items() if not present
        )

        self._store_scan_record(scan)
        return scan

    def dry_run_secrets_safety(self, context: str | None = None) -> dict:
        safety_record = self.create_safety_record(context=context)["safety_record"]
        return {
            "ok": True,
            "stage": STAGE,
            "dry_run_only": True,
            "would_print_secret_values": False,
            "would_log_secret_values": False,
            "would_store_secret_values": False,
            "would_include_key_file_in_backup": False,
            "would_send_keys_to_chat": False,
            "would_call_provider": False,
            "would_use_network": False,
            "would_route_model": False,
            "would_run_provider_health_check": False,
            "would_execute_external_model": False,
            "would_take_real_action": False,
            "message": "Dry run complete. Secret values remained hidden; provider calls and network remain blocked.",
            "safety_record": safety_record,
        }

    def list_safety_records(self) -> list[dict]:
        if not self.file.exists():
            return []
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _store_scan_record(self, scan: dict) -> None:
        record = {
            "safety_record_id": f"sks_scan_{uuid.uuid4().hex[:12]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stage": STAGE,
            "title": "Stage 32 safe key file scan",
            "record_type": "safe_key_file_scan",
            "status": "recorded",
            "scan_type": scan.get("scan_type"),
            "key_file_name": scan.get("key_file_name"),
            "key_file_path": scan.get("key_file_path"),
            "key_file_exists": scan.get("key_file_exists"),
            "providers_present": scan.get("providers_present", []),
            "providers_missing": scan.get("providers_missing", []),
            "recognized_provider_labels_found": scan.get("recognized_provider_labels_found", []),
            "unrecognized_label_count": scan.get("unrecognized_label_count", 0),
            "malformed_line_count": scan.get("malformed_line_count", 0),
            "secret_values_returned": False,
            "secret_values_printed": False,
            "secret_values_logged": False,
            "secret_values_stored": False,
            "provider_calls": False,
            "network_access": False,
            "real_actions": False,
        }

        records = self.list_safety_records()
        records.append(record)
        self._write(records)

    def _clean_context(self, context: str | None) -> str:
        value = (context or "protect provider keys and report presence only").strip()
        if not value:
            return "protect provider keys and report presence only"
        return value[:180]

    def _assess_context(self, context: str) -> dict:
        lowered = context.lower()

        if any(term in lowered for term in ["print key", "show key", "reveal key", "display key", "paste key", "copy key"]):
            return {
                "category": "blocked_secret_exposure",
                "decision": "blocked",
                "summary": "Request attempts to expose API/provider key values.",
                "allowed_response": "Refuse to print or reveal keys. Report provider presence only.",
                "recommended_next_step": "Use safe key file scan if needed.",
            }

        if any(term in lowered for term in ["log key", "store key", "save key value"]):
            return {
                "category": "blocked_secret_logging_or_storage",
                "decision": "blocked",
                "summary": "Request attempts to log or store secret values.",
                "allowed_response": "Refuse secret logging/storage. Store only redacted presence metadata.",
                "recommended_next_step": "Keep secrets only in the root APIKEYS file.",
            }

        if any(term in lowered for term in ["backup key", "upload key", "send key"]):
            return {
                "category": "blocked_secret_backup_or_transfer",
                "decision": "blocked",
                "summary": "Request attempts to back up, upload, or transfer secret values.",
                "allowed_response": "Refuse secret backup/transfer. Normal backups must exclude the root APIKEYS file.",
                "recommended_next_step": "Back up backend/tests/data only.",
            }

        if any(term in lowered for term in ["call provider", "call api", "test api", "use network", "connect provider", "provider health check"]):
            return {
                "category": "blocked_provider_execution",
                "decision": "blocked",
                "summary": "Provider execution or network request detected.",
                "allowed_response": "Keep provider calls/network blocked. Stage 32 is secrets safety only.",
                "recommended_next_step": "Continue to provider registry only after Stage 32 backup.",
            }

        if any(term in lowered for term in ["scan", "presence", "check file", "api keys file", "apikeys"]):
            return {
                "category": "allowed_safe_presence_check_only",
                "decision": "allowed_as_redacted_metadata_only",
                "summary": "Safe key file awareness/presence check requested.",
                "allowed_response": "Report file existence and provider presence only; never reveal values.",
                "recommended_next_step": "Run safe key file scan.",
            }

        return {
            "category": "secret_safety_boundary",
            "decision": "allowed_as_safety_boundary_only",
            "summary": "Context fits Stage 32 secret safety boundary rules.",
            "allowed_response": "Explain safe key handling boundaries and keep values hidden.",
            "recommended_next_step": "Continue with safe secret-handling checks.",
        }

    def _build_label_index(self) -> dict[str, str]:
        index = {}
        for provider, labels in SUPPORTED_PROVIDER_LABELS.items():
            for label in labels:
                index[self._normalize_label(label)] = provider
        return index

    def _normalize_label(self, label: str) -> str:
        value = label.strip().upper().replace("_", " ")
        value = re.sub(r"\s+", " ", value)
        return value

    def _find_existing(self, title: str) -> dict | None:
        for record in self.list_safety_records():
            if record.get("title") == title:
                return record
        return None

    def _write(self, records: list[dict]) -> None:
        self.file.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
