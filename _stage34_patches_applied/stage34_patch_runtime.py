"""
stage34_patch_runtime.py
Surgical, idempotent patch of backend/lucy_core/lucy_runtime.py for Stage 34.
Run from the project root:  python stage34_patch_runtime.py
Safe to run more than once.
"""

from pathlib import Path
import sys

PATH = Path("backend/lucy_core/lucy_runtime.py")


def insert_after(text, anchor, addition, sentinel, label):
    """Insert `addition` immediately after `anchor`. Skip if `sentinel` present."""
    if sentinel in text:
        print(f"  [skip] {label} (already applied)")
        return text
    if text.count(anchor) != 1:
        print(f"  [FAIL] anchor for '{label}' found {text.count(anchor)} time(s), expected 1")
        sys.exit(1)
    print(f"  [ok]   {label}")
    return text.replace(anchor, anchor + addition, 1)


def replace_exact(text, old, new, label):
    """Replace `old` with `new`. Idempotent: skip when already done."""
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

    text = insert_after(
        text,
        "from backend.lucy_core.provider_registry import ProviderRegistry\n",
        "from backend.lucy_core.provider_health_check import ProviderHealthCheck\n",
        "from backend.lucy_core.provider_health_check import ProviderHealthCheck",
        "import ProviderHealthCheck",
    )

    gate_line = (
        'STAGE34_GATE = "Provider health-check dry-run stage blocked until Stage 33 '
        "is accepted, backed up locally, uploaded to Drive, and Senin explicitly "
        'approves Stage 34 health-check dry-run work"\n'
    )
    new_consts = (
        'STAGE34_SAFE_NEXT_ACTION = "Finish Stage 34 provider health-check dry-run '
        'checks, run tests, and back up after acceptance."\n'
        'STAGE34_OPERATIONAL_NEXT_ACTION = "describe what a provider health check '
        "would do, dry-run only, no network, no provider calls, no keys read, run "
        'tests, manual checks, then backup after acceptance"\n'
        'STAGE34_STAGE_LABEL = "34 provider health-check dry-run"\n'
        'STAGE35_GATE = "First manual model call stage blocked until Stage 34 is '
        "accepted, backed up locally, uploaded to Drive, and Senin explicitly "
        'approves Stage 35 work"\n'
    )
    text = insert_after(text, gate_line, new_consts, "STAGE34_STAGE_LABEL =", "Stage 34/35 constants")

    text = insert_after(
        text,
        "        self.provider_registry = ProviderRegistry(lucy_data)\n",
        "        self.provider_health_check = ProviderHealthCheck(lucy_data)\n",
        "self.provider_health_check = ProviderHealthCheck(lucy_data)",
        "instantiate ProviderHealthCheck",
    )

    anchor = (
        "    def dry_run_provider_registry(self, context: str | None = None) -> dict:\n"
        "        return self.provider_registry.dry_run_provider_registry(context=context)\n"
    )
    methods = (
        "\n"
        "    def provider_health_check_status(self) -> dict:\n"
        "        return self.provider_health_check.status()\n"
        "\n"
        "    def dry_run_provider_health_check(self, provider_name: str | None = None, context: str | None = None) -> dict:\n"
        "        return self.provider_health_check.dry_run_health_check(provider_name=provider_name, context=context)\n"
        "\n"
        "    def list_provider_health_checks(self) -> list[dict]:\n"
        "        return self.provider_health_check.list_dry_runs()\n"
        "\n"
        "    def reset_provider_health_check(self) -> dict:\n"
        "        return self.provider_health_check.reset()\n"
    )
    text = insert_after(text, anchor, methods, "def provider_health_check_status(self)", "runtime wiring methods")

    text = replace_exact(text, '"active_stage": STAGE33_STAGE_LABEL,', '"active_stage": STAGE34_STAGE_LABEL,', "active_stage -> Stage 34")
    text = replace_exact(text, '"next_safe_action": STAGE33_SAFE_NEXT_ACTION,', '"next_safe_action": STAGE34_SAFE_NEXT_ACTION,', "status next_safe_action -> Stage 34")
    text = replace_exact(text, '"next_safe_action": STAGE33_OPERATIONAL_NEXT_ACTION,', '"next_safe_action": STAGE34_OPERATIONAL_NEXT_ACTION,', "next_action operational -> Stage 34")
    text = replace_exact(text, '"stage34_gate": STAGE34_GATE,', '"stage35_gate": STAGE35_GATE,', "forward gate key -> stage35_gate")
    text = replace_exact(
        text,
        "        if any(marker in lowered for marker in STALE_NEXT_ACTION_MARKERS):\n            return STAGE33_SAFE_NEXT_ACTION\n",
        "        if any(marker in lowered for marker in STALE_NEXT_ACTION_MARKERS):\n            return STAGE34_SAFE_NEXT_ACTION\n",
        "stale-marker fallback -> Stage 34",
    )
    text = replace_exact(
        text,
        "        except Exception:\n            pass\n        return STAGE33_SAFE_NEXT_ACTION\n",
        "        except Exception:\n            pass\n        return STAGE34_SAFE_NEXT_ACTION\n",
        "next-action fallback -> Stage 34",
    )

    text = replace_exact(text, 'f"Current active stage: {STAGE33_STAGE_LABEL}. "', 'f"Current active stage: {STAGE34_STAGE_LABEL}. "', "what-next inline: active stage")
    text = replace_exact(text, 'f"Next safe action: {STAGE33_OPERATIONAL_NEXT_ACTION}. "', 'f"Next safe action: {STAGE34_OPERATIONAL_NEXT_ACTION}. "', "what-next inline: next action")
    text = replace_exact(text, 'f"Stage 34 gate is {STAGE34_GATE}."', 'f"Stage 35 gate is {STAGE35_GATE}."', "what-next inline: forward gate")

    PATH.write_text(text, encoding="utf-8")
    print("[done] lucy_runtime.py patched.")


if __name__ == "__main__":
    main()
