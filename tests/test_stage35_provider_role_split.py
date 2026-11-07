"""
test_stage35_provider_role_split.py
Stage 35 = Provider Role Split & Sovereign Mind Boundary.

Verifies:
1. Strict separation of Sovereign Mind (Ollama) vs External Workers (Groq, Gemini, OpenRouter, NVIDIA).
2. Anti-leak boundary: Dispatches to workers with persona or memory keys are blocked.
3. Router commands: "provider role split", "provider roles", "sovereign mind status".
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.provider_role_split import (
    ProviderRoleSplit,
    ROLE_SOVEREIGN_MIND,
    ROLE_EXTERNAL_WORKER,
    OLLAMA_SOVEREIGN_PROVIDER,
    EXTERNAL_WORKER_PROVIDERS
)


class TestStage35ProviderRoleSplit(unittest.TestCase):
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

    def test_01_status_reports_stage35(self) -> None:
        _, router = self._runtime_and_router()
        response = router.handle("provider role split")
        self.assertIn("Provider Role Split status:", response.message)
        self.assertIn("Stage: 35 provider role split", response.message)
        self.assertIn("Sovereign Mind: ollama", response.message)
        self.assertIn("Sovereign Role: sovereign_local_mind", response.message)

    def test_02_status_aliases_work(self) -> None:
        _, router = self._runtime_and_router()
        for cmd in ["provider roles", "role split status", "sovereign mind status"]:
            response = router.handle(cmd)
            self.assertIn("Provider Role Split status:", response.message)

    def test_03_sovereign_mind_definition(self) -> None:
        lucy_data = self.root / "data" / "lucy"
        role_split = ProviderRoleSplit(lucy_data)
        sov = role_split.get_sovereign_mind()
        self.assertEqual(sov["provider_id"], "ollama")
        self.assertEqual(sov["role"], ROLE_SOVEREIGN_MIND)
        self.assertEqual(sov["endpoint"], "http://localhost:11434")
        self.assertTrue(role_split.is_sovereign("ollama"))
        self.assertTrue(role_split.is_sovereign("sovereign_mind"))
        self.assertFalse(role_split.is_sovereign("groq"))

    def test_04_external_workers_definition(self) -> None:
        lucy_data = self.root / "data" / "lucy"
        role_split = ProviderRoleSplit(lucy_data)
        workers = role_split.get_external_workers()
        self.assertEqual(len(workers), 4)
        worker_ids = [w["provider_id"] for w in workers]
        self.assertIn("groq", worker_ids)
        self.assertIn("openrouter", worker_ids)
        self.assertIn("google", worker_ids)
        self.assertIn("nvidia", worker_ids)
        for w in workers:
            self.assertEqual(w["role"], ROLE_EXTERNAL_WORKER)

    def test_05_anti_leak_blocks_identity_payload_to_workers(self) -> None:
        lucy_data = self.root / "data" / "lucy"
        role_split = ProviderRoleSplit(lucy_data)

        # Attempt to send persona to a worker -> BLOCKED
        bad_payload = {"instruction": "Write code", "persona": "You are Lucy"}
        permitted, reason = role_split.validate_worker_dispatch(bad_payload)
        self.assertFalse(permitted)
        self.assertIn("SECURITY_VIOLATION", reason)

        # Attempt to send spine to a worker -> BLOCKED
        bad_payload_spine = {"instruction": "Write code", "spine_json": {"identity": "Lucy"}}
        permitted, reason = role_split.validate_worker_dispatch(bad_payload_spine)
        self.assertFalse(permitted)
        self.assertIn("SECURITY_VIOLATION", reason)

        # Clean technical instruction -> PERMITTED
        good_payload = {"instruction": "Write a python calculator class with add and subtract methods."}
        permitted, reason = role_split.validate_worker_dispatch(good_payload)
        self.assertTrue(permitted)
        self.assertIn("DISPATCH_PERMITTED", reason)


if __name__ == "__main__":
    unittest.main()
