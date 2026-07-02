"""
test_stage33_provider_registry.py
Stage 33 = Provider Registry.

This stage creates a safe local registry of provider metadata.

Allowed:
- provider names
- provider aliases
- provider roles
- provider enabled/disabled state
- credential labels only

Blocked:
- API key values
- APIKEYS file reading
- secret value loading
- provider calls
- network access
- health checks
- model routing
- external model execution
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class TestStage33ProviderRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _runtime_and_router(self):
        runtime = LucyRuntime(project_root=self.root)
        router = CommandRouter(runtime)
        return runtime, router

    def test_01_provider_registry_status_returns_stage33_status(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("provider registry status")
        self.assertIn("Provider registry status:", response.message)
        self.assertIn("Stage: 33 provider registry", response.message)
        self.assertIn("Provider registry: active", response.message)

    def test_02_provider_registry_status_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        for command in [
            "registry status",
            "model provider registry status",
            "provider list status",
        ]:
            self.assertIn("Provider registry status:", router.handle(command).message)

    def test_03_status_lists_default_providers(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("provider registry status")
        self.assertIn("Provider count: 4", response.message)
        self.assertIn("Enabled provider count: 0", response.message)
        self.assertIn("Disabled provider count: 4", response.message)
        self.assertIn("Provider names:", response.message)
        self.assertIn("google", response.message)
        self.assertIn("openrouter", response.message)
        self.assertIn("groq", response.message)
        self.assertIn("nvidia", response.message)

    def test_04_status_blocks_keys_calls_network_and_health_checks(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("provider registry status")
        self.assertIn("Credential labels only: true", response.message)
        self.assertIn("API key values: blocked", response.message)
        self.assertIn("API key file reading: blocked", response.message)
        self.assertIn("Secret value loading: blocked", response.message)
        self.assertIn("Provider calls: blocked", response.message)
        self.assertIn("Network access: blocked", response.message)
        self.assertIn("Provider health checks: not implemented", response.message)
        self.assertIn("Model routing: not implemented", response.message)
        self.assertIn("External model execution: not implemented", response.message)
        self.assertIn("Real actions: false", response.message)

    def test_05_provider_registry_list_displays_safe_provider_metadata(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("provider registry")
        self.assertIn("Registered providers:", response.message)
        self.assertIn("google | Google / Gemini", response.message)
        self.assertIn("openrouter | OpenRouter", response.message)
        self.assertIn("groq | Groq", response.message)
        self.assertIn("nvidia | NVIDIA", response.message)
        self.assertIn("disabled", response.message)
        self.assertIn("API key values returned: false", response.message)
        self.assertIn("Provider calls: false", response.message)
        self.assertIn("Network access: false", response.message)
        self.assertIn("Health checks: false", response.message)

    def test_06_provider_registry_list_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        for command in [
            "list providers",
            "registered providers",
            "show providers",
            "provider list",
        ]:
            self.assertIn("Registered providers:", router.handle(command).message)

    def test_07_show_provider_google_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("show provider google")
        self.assertIn("Registered provider:", response.message)
        self.assertIn("Provider ID: google", response.message)
        self.assertIn("Display name: Google / Gemini", response.message)
        self.assertIn("Aliases: google, gemini", response.message)
        self.assertIn("Enabled: false", response.message)

    def test_08_show_provider_gemini_alias_resolves_to_google(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("show provider gemini")
        self.assertIn("Registered provider:", response.message)
        self.assertIn("Provider ID: google", response.message)
        self.assertIn("Display name: Google / Gemini", response.message)

    def test_09_show_provider_openrouter_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("registered provider openrouter")
        self.assertIn("Provider ID: openrouter", response.message)
        self.assertIn("Display name: OpenRouter", response.message)

    def test_10_show_provider_groq_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("provider registry groq")
        self.assertIn("Provider ID: groq", response.message)
        self.assertIn("Display name: Groq", response.message)

    def test_11_show_provider_nvidia_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("show provider nvidia")
        self.assertIn("Provider ID: nvidia", response.message)
        self.assertIn("Display name: NVIDIA", response.message)

    def test_12_show_unknown_provider_is_safe(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("show provider unknownprovider")
        self.assertIn("Registered provider:", response.message)
        self.assertIn("Status: not found", response.message)
        self.assertIn("Requested provider: unknownprovider", response.message)
        self.assertIn("Provider call allowed: false", response.message)
        self.assertIn("Network allowed: false", response.message)
        self.assertIn("API key values returned: false", response.message)

    def test_13_provider_view_never_returns_key_values(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("show provider groq")
        self.assertIn("API key value returned: false", response.message)
        self.assertIn("API key value stored: false", response.message)
        self.assertNotIn("SECRET", response.message)
        self.assertNotIn("sk-", response.message)

    def test_14_enable_provider_changes_metadata_only(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("enable provider groq")
        self.assertIn("Provider registry update:", response.message)
        self.assertIn("Provider ID: groq", response.message)
        self.assertIn("Enabled: true", response.message)
        self.assertIn("Changed: true", response.message)
        self.assertIn("Provider call allowed: false", response.message)
        self.assertIn("Network allowed: false", response.message)
        self.assertIn("API key values returned: false", response.message)
        self.assertIn("Real action allowed: false", response.message)

    def test_15_disable_provider_changes_metadata_only(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("enable provider groq")
        response = router.handle("disable provider groq")
        self.assertIn("Provider registry update:", response.message)
        self.assertIn("Provider ID: groq", response.message)
        self.assertIn("Enabled: false", response.message)
        self.assertIn("Provider call allowed: false", response.message)
        self.assertIn("Network allowed: false", response.message)

    def test_16_enabled_status_updates_count(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("enable provider groq")
        response = router.handle("provider registry status")
        self.assertIn("Enabled provider count: 1", response.message)
        self.assertIn("Disabled provider count: 3", response.message)
        self.assertIn("Enabled providers: groq", response.message)

    def test_17_multiple_enabled_providers_are_metadata_only(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("enable provider google")
        router.handle("enable provider openrouter")
        response = router.handle("provider registry status")
        self.assertIn("Enabled provider count: 2", response.message)
        self.assertIn("Provider calls: blocked", response.message)
        self.assertIn("Network access: blocked", response.message)

    def test_18_enable_unknown_provider_is_safe(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("enable provider madeup")
        self.assertIn("Status: not found", response.message)
        self.assertIn("Provider call allowed: false", response.message)
        self.assertIn("Network allowed: false", response.message)
        self.assertIn("API key values returned: false", response.message)

    def test_19_disable_unknown_provider_is_safe(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("disable provider madeup")
        self.assertIn("Status: not found", response.message)
        self.assertIn("Provider call allowed: false", response.message)
        self.assertIn("Network allowed: false", response.message)

    def test_20_reset_provider_registry_disables_all(self) -> None:
        _, router = self._runtime_and_router()
        router.handle("enable provider groq")
        reset = router.handle("reset provider registry")
        self.assertIn("Provider registry reset:", reset.message)
        self.assertIn("Status: true", reset.message)
        self.assertIn("All providers disabled", reset.message)

        status = router.handle("provider registry status")
        self.assertIn("Enabled provider count: 0", status.message)
        self.assertIn("Disabled provider count: 4", status.message)

    def test_21_provider_registry_reset_alias_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("provider registry reset")
        self.assertIn("Provider registry reset:", response.message)

    def test_22_dry_run_provider_registry_blocks_execution(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("dry run provider registry")
        self.assertIn("Provider registry dry run:", response.message)
        self.assertIn("Stage: 33 provider registry", response.message)
        self.assertIn("Dry run only: true", response.message)
        self.assertIn("Would read API key file: false", response.message)
        self.assertIn("Would load secret values: false", response.message)
        self.assertIn("Would print secret values: false", response.message)
        self.assertIn("Would store secret values: false", response.message)
        self.assertIn("Would call provider: false", response.message)
        self.assertIn("Would use network: false", response.message)
        self.assertIn("Would run provider health check: false", response.message)
        self.assertIn("Would route model: false", response.message)
        self.assertIn("Would execute external model: false", response.message)
        self.assertIn("Would take real action: false", response.message)
        self.assertIn("Provider registry allowed: true", response.message)

    def test_23_dry_run_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        for command in [
            "dry-run provider registry",
            "test provider registry",
            "provider registry dry run",
        ]:
            self.assertIn("Provider registry dry run:", router.handle(command).message)

    def test_24_registry_file_contains_no_secret_values(self) -> None:
        runtime, router = self._runtime_and_router()
        router.handle("enable provider groq")
        registry_file = runtime.provider_registry.file
        text = registry_file.read_text(encoding="utf-8")
        self.assertIn('"api_key_value": "[blocked]"', text)
        self.assertIn('"api_key_value_stored": false', text)
        self.assertIn('"provider_call_allowed": false', text)
        self.assertIn('"network_allowed": false', text)
        self.assertNotIn("SECRET_", text)
        self.assertNotIn("sk-", text)

    def test_25_registry_runtime_has_no_provider_call_methods(self) -> None:
        runtime, _ = self._runtime_and_router()
        for method in [
            "call_provider",
            "call_groq",
            "call_gemini",
            "call_openrouter",
            "call_nvidia",
            "network_request",
            "provider_health_check",
            "route_model",
            "execute_external_model",
        ]:
            self.assertFalse(hasattr(runtime.provider_registry, method))

    def test_26_secret_safety_still_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("secrets provider key safety status")
        self.assertIn("Secrets/provider-key safety status:", response.message)
        self.assertIn("Secret value reading: blocked", response.message)

    def test_27_provider_identity_boundary_still_works(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("provider identity boundary status")
        self.assertIn("Provider identity boundary status:", response.message)
        self.assertIn("Provider calls: blocked", response.message)

    def test_28_autonomy_boundaries_still_work(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("autonomy boundaries status")
        self.assertIn("Autonomy boundaries status:", response.message)
        self.assertIn("Independent action: blocked", response.message)

    def test_29_tell_me_reflects_stage33_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("tell me")
        self.assertIn("Active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Guardian: active", response.message)
        self.assertIn("Secrets/provider-key safety: active", response.message)
        self.assertIn("Provider registry: active", response.message)
        self.assertIn("Registered providers: 4", response.message)
        self.assertIn("Enabled providers: 0", response.message)
        self.assertIn("Disabled providers: 4", response.message)
        self.assertIn("Stage 35 gate:", response.message)

    def test_30_what_next_reflects_stage33_safely(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("what next")
        self.assertIn("Current active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("describe what a provider health check would do", response.message)
        self.assertIn("no provider calls, no keys read", response.message)
        self.assertIn("Stage 35:", response.message)

    def test_31_stage34_health_check_dry_run_is_blocked(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("what next")
        self.assertIn("Stage 35:", response.message)
        self.assertIn("First manual model call stage blocked", response.message)


if __name__ == "__main__":
    unittest.main()
