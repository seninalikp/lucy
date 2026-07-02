"""
test_stage34_provider_health_check.py
Stage 34 = Provider Health-Check Dry Run.

This stage describes what a provider health check WOULD do, without doing it.

Allowed:
- describe planned health-check steps (dry-run text only)
- read provider metadata from the local registry
- record dry-run plans locally

Blocked:
- real provider calls
- network access
- API key / secret value reading
- provider reachability ping or authentication
- model routing / external model execution
- treating a provider as Lucy's identity
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.provider_health_check import ProviderHealthCheck


class TestStage34ProviderHealthCheck(unittest.TestCase):
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

    # ---------- NEW BEHAVIOUR ----------
    def test_01_status_reports_stage34(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("provider health check status")
        self.assertIn("Provider health-check status:", response.message)
        self.assertIn("Stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Execution mode: dry_run_only", response.message)

    def test_02_status_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        for command in [
            "health check status",
            "provider health status",
            "provider health-check status",
        ]:
            self.assertIn(
                "Provider health-check status:", router.handle(command).message
            )

    def test_03_dry_run_all_providers(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("dry run provider health check")
        self.assertIn("Provider health-check dry run:", response.message)
        self.assertIn("Scope: all_registered_providers", response.message)
        self.assertIn("Message:", response.message)

    def test_04_dry_run_all_enumerates_registered_providers(self) -> None:
        runtime, _ = self._runtime_and_router()
        result = runtime.dry_run_provider_health_check()
        # Stage 33 seeds google/openrouter/groq/nvidia by default.
        for pid in ("google", "openrouter", "groq", "nvidia"):
            self.assertIn(pid, result["targets"])

    def test_05_dry_run_single_known_provider(self) -> None:
        runtime, _ = self._runtime_and_router()
        result = runtime.dry_run_provider_health_check("gemini")
        self.assertEqual(result["scope"], "single_provider")
        self.assertEqual(result["targets"], ["gemini"])
        self.assertTrue(result["provider_known_in_registry"])

    def test_06_dry_run_single_unknown_provider(self) -> None:
        runtime, _ = self._runtime_and_router()
        result = runtime.dry_run_provider_health_check("does-not-exist")
        self.assertEqual(result["scope"], "single_provider")
        self.assertFalse(result["provider_known_in_registry"])
        # Unknown provider is still safe: nothing is contacted.
        self.assertFalse(result["would_call_provider"])
        self.assertFalse(result["would_use_network"])

    def test_07_dry_run_prefix_command(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("dry run provider health groq")
        self.assertIn("Scope: single_provider", response.message)
        self.assertIn("Targets: groq", response.message)

    def test_08_records_accumulate(self) -> None:
        runtime, router = self._runtime_and_router()
        runtime.dry_run_provider_health_check()
        runtime.dry_run_provider_health_check("groq")
        records = runtime.list_provider_health_checks()
        self.assertEqual(len(records), 2)
        self.assertIn(
            "Provider health-check dry runs:",
            router.handle("health check records").message,
        )

    def test_09_records_empty_message(self) -> None:
        _, router = self._runtime_and_router()
        self.assertIn("None recorded yet.", router.handle("health check records").message)

    def test_10_reset_clears_records(self) -> None:
        runtime, router = self._runtime_and_router()
        runtime.dry_run_provider_health_check()
        self.assertEqual(len(runtime.list_provider_health_checks()), 1)
        response = router.handle("reset provider health check")
        self.assertIn("Provider health-check reset:", response.message)
        self.assertEqual(len(runtime.list_provider_health_checks()), 0)

    def test_11_store_file_created(self) -> None:
        runtime, _ = self._runtime_and_router()
        runtime.dry_run_provider_health_check()
        store = self.root / "data" / "lucy" / "provider_health_check.json"
        self.assertTrue(store.exists())

    # ---------- BACKWARD COMPATIBILITY ----------
    def test_12_stage33_registry_untouched(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("provider registry status")
        self.assertIn("Stage: 33 provider registry", response.message)
        self.assertIn("Provider registry: active", response.message)

    def test_13_stage33_providers_still_disabled_by_default(self) -> None:
        runtime, _ = self._runtime_and_router()
        for provider in runtime.list_registered_providers():
            self.assertFalse(provider["enabled"])

    def test_14_tell_me_reflects_stage34(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("tell me")
        self.assertIn("Active stage: 34 provider health-check dry-run", response.message)
        self.assertIn("Guardian: active", response.message)
        self.assertIn("Stage 35 gate:", response.message)

    def test_15_what_next_reflects_stage34(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("what next")
        self.assertIn(
            "Current active stage: 34 provider health-check dry-run", response.message
        )
        self.assertIn("describe what a provider health check would do", response.message)
        self.assertIn("Stage 35:", response.message)

    # ---------- STAGE GATE ----------
    def test_16_forward_gate_targets_stage35(self) -> None:
        runtime, _ = self._runtime_and_router()
        status = runtime.current_lucy_status()
        self.assertIn("stage35_gate", status)
        self.assertIn("Stage 35", status["stage35_gate"])
        self.assertIn("blocked until Stage 34", status["stage35_gate"])

    def test_17_no_stage35_work_present(self) -> None:
        # Stage 35 (first manual model call) must not be implemented yet.
        runtime, _ = self._runtime_and_router()
        self.assertFalse(hasattr(runtime, "first_manual_model_call"))
        self.assertFalse(hasattr(runtime, "call_provider"))

    # ---------- SAFETY ----------
    def test_18_dry_run_blocks_every_real_action(self) -> None:
        runtime, _ = self._runtime_and_router()
        result = runtime.dry_run_provider_health_check()
        for flag in (
            "would_call_provider",
            "would_use_network",
            "would_read_api_key_file",
            "would_load_secret_values",
            "would_print_secret_values",
            "would_ping_provider",
            "would_authenticate",
            "would_route_model",
            "would_execute_external_model",
            "would_ingest_provider_output",
            "would_take_real_action",
            "real_health_check_performed",
        ):
            self.assertFalse(result[flag], f"{flag} must be False")

    def test_19_provider_is_not_lucy_identity(self) -> None:
        runtime, _ = self._runtime_and_router()
        result = runtime.dry_run_provider_health_check("gemini")
        self.assertFalse(result["provider_is_lucy_identity"])

    def test_20_status_marks_network_and_calls_blocked(self) -> None:
        runtime, _ = self._runtime_and_router()
        status = runtime.provider_health_check_status()
        self.assertEqual(status["provider_calls"], "blocked")
        self.assertEqual(status["network_access"], "blocked")
        self.assertEqual(status["api_key_file_reading"], "blocked")
        self.assertFalse(status["real_actions"])

    def test_21_health_check_never_reads_secret_store(self) -> None:
        # Even if a secrets file exists, a dry run must not reference its contents.
        secure = self.root / "data" / "lucy" / "secure"
        secure.mkdir(parents=True, exist_ok=True)
        (secure / "NVIDIA_API_KEY.dpapi.json").write_text("{\"sentinel\": \"SECRET\"}", encoding="utf-8")
        runtime, _ = self._runtime_and_router()
        result = runtime.dry_run_provider_health_check("nvidia")
        self.assertNotIn("SECRET", str(result))
        self.assertFalse(result["would_read_api_key_file"])

    def test_22_module_stage_constant(self) -> None:
        phc = ProviderHealthCheck(self.root / "data" / "lucy")
        self.assertEqual(phc.status()["stage"], "34 provider health-check dry-run")


if __name__ == "__main__":
    unittest.main()
