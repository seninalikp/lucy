"""
stage34_patch_router.py
Surgical, idempotent patch of backend/lucy_core/router.py for Stage 34.
Run from the project root:  python stage34_patch_router.py
Safe to run more than once.
"""

from pathlib import Path
import sys

PATH = Path("backend/lucy_core/router.py")


def insert_after(text, anchor, addition, sentinel, label):
    if sentinel in text:
        print(f"  [skip] {label} (already applied)")
        return text
    if text.count(anchor) != 1:
        print(f"  [FAIL] anchor for '{label}' found {text.count(anchor)} time(s), expected 1")
        sys.exit(1)
    print(f"  [ok]   {label}")
    return text.replace(anchor, anchor + addition, 1)


def insert_before(text, anchor, addition, sentinel, label):
    if sentinel in text:
        print(f"  [skip] {label} (already applied)")
        return text
    if text.count(anchor) != 1:
        print(f"  [FAIL] anchor for '{label}' found {text.count(anchor)} time(s), expected 1")
        sys.exit(1)
    print(f"  [ok]   {label}")
    return text.replace(anchor, addition + anchor, 1)


def replace_exact(text, old, new, label):
    if new in text and old not in text:
        print(f"  [skip] {label} (already applied)")
        return text
    count = text.count(old)
    if count == 0:
        print(f"  [FAIL] anchor not found: {label}")
        sys.exit(1)
    print(f"  [ok]   {label} ({count} occurrence(s))")
    return text.replace(old, new)


def main():
    if not PATH.exists():
        print(f"[FAIL] {PATH} not found. Run from the project root.")
        sys.exit(1)

    text = PATH.read_text(encoding="utf-8")

    registry_tail = (
        '        if lowered.startswith("provider registry "):\n'
        '            provider_name = lowered.replace("provider registry ", "", 1).strip()\n'
        "            return RouterResponse(self._format_provider_registry_provider_result(self.runtime.get_registered_provider(provider_name)))\n"
    )
    dispatch = (
        "\n"
        '        if lowered in {"provider health check status", "health check status", "provider health status", "provider health-check status"}:\n'
        "            return RouterResponse(self._format_provider_health_check_status(self.runtime.provider_health_check_status()))\n"
        "\n"
        '        if lowered in {"provider health check records", "health check records", "list provider health checks", "provider health check dry runs"}:\n'
        "            return RouterResponse(self._format_provider_health_check_records(self.runtime.list_provider_health_checks()))\n"
        "\n"
        '        if lowered in {"reset provider health check", "provider health check reset"}:\n'
        "            return RouterResponse(self._format_provider_health_check_reset(self.runtime.reset_provider_health_check()))\n"
        "\n"
        '        if lowered in {"dry run provider health check", "dry-run provider health check", "provider health check dry run", "test provider health check"}:\n'
        "            return RouterResponse(self._format_provider_health_check_dry_run(self.runtime.dry_run_provider_health_check()))\n"
        "\n"
        '        if lowered.startswith("dry run provider health "):\n'
        '            provider_name = lowered.replace("dry run provider health ", "", 1).strip()\n'
        "            return RouterResponse(self._format_provider_health_check_dry_run(self.runtime.dry_run_provider_health_check(provider_name)))\n"
    )
    text = insert_after(
        text, registry_tail, dispatch,
        "self._format_provider_health_check_status(self.runtime.provider_health_check_status())",
        "health-check dispatch branches",
    )

    helper_anchor = "    def _provider_registry_provider_lines(self, provider: dict) -> list[str]:\n"
    formatters = (
        "    def _format_provider_health_check_status(self, result: dict) -> str:\n"
        '        return "\\n".join(\n'
        "            [\n"
        '                "Provider health-check status:",\n'
        "                f\"Stage: {result.get('stage', '34 provider health-check dry-run')}\",\n"
        "                f\"Health check: {result.get('provider_health_check', 'active')}\",\n"
        "                f\"Execution mode: {result.get('execution_mode', 'dry_run_only')}\",\n"
        "                f\"Dry runs recorded: {result.get('dry_run_count', 0)}\",\n"
        "                f\"Real health check performed: {str(result.get('real_health_check_performed', False)).lower()}\",\n"
        "                f\"Provider calls: {result.get('provider_calls', 'blocked')}\",\n"
        "                f\"Network access: {result.get('network_access', 'blocked')}\",\n"
        "                f\"API key file reading: {result.get('api_key_file_reading', 'blocked')}\",\n"
        "                f\"Secret value loading: {result.get('secret_value_loading', 'blocked')}\",\n"
        "                f\"Provider reachability ping: {result.get('provider_reachability_ping', 'not implemented')}\",\n"
        "                f\"Provider authentication test: {result.get('provider_authentication_test', 'not implemented')}\",\n"
        "                f\"Model routing: {result.get('model_routing', 'not implemented')}\",\n"
        "                f\"External model execution: {result.get('external_model_execution', 'not implemented')}\",\n"
        "                f\"Real actions: {str(result.get('real_actions', False)).lower()}\",\n"
        "            ]\n"
        "        )\n"
        "\n"
        "    def _format_provider_health_check_dry_run(self, result: dict) -> str:\n"
        '        targets = ", ".join(result.get("targets", [])) or "none"\n'
        '        return "\\n".join(\n'
        "            [\n"
        '                "Provider health-check dry run:",\n'
        "                f\"Stage: {result.get('stage', '34 provider health-check dry-run')}\",\n"
        "                f\"Context: {result.get('context', '')}\",\n"
        "                f\"Scope: {result.get('scope', '')}\",\n"
        '                f"Targets: {targets}",\n'
        "                f\"Provider known in registry: {str(result.get('provider_known_in_registry', False)).lower()}\",\n"
        "                f\"Dry run only: {str(result.get('dry_run_only', True)).lower()}\",\n"
        "                f\"Would call provider: {str(result.get('would_call_provider', False)).lower()}\",\n"
        "                f\"Would use network: {str(result.get('would_use_network', False)).lower()}\",\n"
        "                f\"Would read API key file: {str(result.get('would_read_api_key_file', False)).lower()}\",\n"
        "                f\"Would load secret values: {str(result.get('would_load_secret_values', False)).lower()}\",\n"
        "                f\"Would ping provider: {str(result.get('would_ping_provider', False)).lower()}\",\n"
        "                f\"Would authenticate: {str(result.get('would_authenticate', False)).lower()}\",\n"
        "                f\"Would route model: {str(result.get('would_route_model', False)).lower()}\",\n"
        "                f\"Would execute external model: {str(result.get('would_execute_external_model', False)).lower()}\",\n"
        "                f\"Would take real action: {str(result.get('would_take_real_action', False)).lower()}\",\n"
        "                f\"Real health check performed: {str(result.get('real_health_check_performed', False)).lower()}\",\n"
        "                f\"Provider is Lucy identity: {str(result.get('provider_is_lucy_identity', False)).lower()}\",\n"
        "                f\"Message: {result.get('message', '')}\",\n"
        "            ]\n"
        "        )\n"
        "\n"
        "    def _format_provider_health_check_records(self, records: list) -> str:\n"
        "        if not records:\n"
        '            return "Provider health-check dry runs:\\nNone recorded yet."\n'
        '        lines = ["Provider health-check dry runs:"]\n'
        "        for rec in records:\n"
        '            targets = ", ".join(rec.get("targets", [])) or "none"\n'
        "            lines.append(\n"
        "                f\"- {rec.get('created_at', '')} | scope={rec.get('scope', '')} | \"\n"
        '                f"targets={targets} | "\n'
        "                f\"real_health_check_performed={str(rec.get('real_health_check_performed', False)).lower()}\"\n"
        "            )\n"
        '        return "\\n".join(lines)\n'
        "\n"
        "    def _format_provider_health_check_reset(self, result: dict) -> str:\n"
        '        return "\\n".join(\n'
        "            [\n"
        '                "Provider health-check reset:",\n'
        "                f\"Stage: {result.get('stage', '34 provider health-check dry-run')}\",\n"
        "                f\"Real health check performed: {str(result.get('real_health_check_performed', False)).lower()}\",\n"
        "                f\"Message: {result.get('message', '')}\",\n"
        "            ]\n"
        "        )\n"
        "\n"
    )
    text = insert_before(
        text, helper_anchor, formatters,
        "def _format_provider_health_check_status",
        "health-check formatters",
    )

    text = replace_exact(
        text,
        "f\"  Stage 34 gate: {status.get('stage34_gate')}\",",
        "f\"  Stage 35 gate: {status.get('stage35_gate')}\",",
        "status formatter forward gate",
    )
    text = replace_exact(
        text,
        "f\"  Stage 34: {result.get('stage34_gate')}\",",
        "f\"  Stage 35: {result.get('stage35_gate')}\",",
        "next-action formatter forward gate",
    )

    PATH.write_text(text, encoding="utf-8")
    print("[done] router.py patched.")


if __name__ == "__main__":
    main()
