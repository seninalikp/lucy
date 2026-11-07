"""
test_stage46_multi_provider_pool.py
Stage 46 = Multi-Provider Key Rotation & Failover Pool.

Verifies:
1. Pool reports Stage 46 and active status.
2. Parsing of api keys.txt into structured provider groups.
3. Safe key masking (never leaks raw keys in logs or dicts).
4. In-provider round-robin key rotation.
5. Rate-limit marking, cooldown state, and automated rotation.
6. Cross-provider fallback hierarchy when primary provider is exhausted.
7. Cooldown expiration and key recovery.
8. LucyRuntime Stage 46 integration.
9. CommandRouter Stage 46 command routing and formatting.
"""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from backend.lucy_core.multi_provider_pool import (
    MultiProviderPool,
    KeyState,
    STAGE,
    mask_key,
)
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter

SAMPLE_KEYS_FILE_CONTENT = """gemini

1.mock-gemini-token-alpha
2.mock-gemini-token-beta

openrouter

1.mock-openrouter-token-alpha
2.mock-openrouter-token-beta

groq

1.mock-groq-token-alpha
2.mock-groq-token-beta
3.mock-groq-token-gamma

sambanova

1.mock-sambanova-token-alpha
2.mock-sambanova-token-beta
"""


class Stage46MultiProviderPoolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.lucy_data = self.root / "data" / "lucy"
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self.keys_file = self.root / "test_api_keys.txt"
        self.keys_file.write_text(SAMPLE_KEYS_FILE_CONTENT, encoding="utf-8")

        self.pool = MultiProviderPool(
            lucy_data=self.lucy_data,
            keys_path=self.keys_file,
            cooldown_seconds=1.0,  # Fast cooldown for unit tests
        )

    def tearDown(self) -> None:
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_01_initial_status(self) -> None:
        status = self.pool.status()
        self.assertEqual(status["stage"], STAGE)
        self.assertEqual(status["multi_provider_pool"], "active")
        self.assertEqual(status["total_keys_loaded"], 9)
        self.assertIn("groq", status["providers_summary"])
        self.assertEqual(status["providers_summary"]["groq"]["total_keys"], 3)
        self.assertEqual(status["providers_summary"]["openrouter"]["total_keys"], 2)

    def test_02_parse_keys_file(self) -> None:
        parsed = self.pool.parse_keys_file(SAMPLE_KEYS_FILE_CONTENT)
        self.assertEqual(len(parsed["gemini"]), 2)
        self.assertEqual(len(parsed["groq"]), 3)
        self.assertEqual(len(parsed["sambanova"]), 2)
        self.assertEqual(len(parsed["openrouter"]), 2)
        self.assertTrue(parsed["groq"][0].startswith("mock-groq"))

    def test_03_key_masking(self) -> None:
        raw = "mock-sample-key-token-for-mask-test-001"
        masked = mask_key(raw)
        self.assertNotIn("sample-key", masked)
        self.assertEqual(masked, "mock-sa...-001")

        # Verify to_dict never outputs raw_key
        key_obj = self.pool.pools["groq"][0]
        d = key_obj.to_dict()
        self.assertNotIn("raw_key", d)
        self.assertIn("masked_key", d)

    def test_04_round_robin_rotation(self) -> None:
        # Initial active key is #1
        raw1, managed1 = self.pool.get_active_key("groq")
        self.assertIsNotNone(raw1)
        self.assertEqual(managed1.index, 1)

        # Rotate to #2
        rot1 = self.pool.rotate_key("groq")
        self.assertTrue(rot1["rotated"])
        self.assertEqual(rot1["new_index"], 2)
        raw2, managed2 = self.pool.get_active_key("groq")
        self.assertEqual(managed2.index, 2)

        # Rotate to #3
        rot2 = self.pool.rotate_key("groq")
        self.assertEqual(rot2["new_index"], 3)

        # Rotate should loop back to #1
        rot3 = self.pool.rotate_key("groq")
        self.assertEqual(rot3["new_index"], 1)

    def test_05_rate_limit_cooldown_and_auto_rotation(self) -> None:
        # Mark key #1 rate-limited
        res = self.pool.mark_rate_limited("groq")
        self.assertEqual(res["status"], "rotated_on_rate_limit")
        self.assertEqual(res["new_index"], 2)

        # Active key should now be #2
        raw, managed = self.pool.get_active_key("groq")
        self.assertEqual(managed.index, 2)

    def test_06_cross_provider_failover(self) -> None:
        # Exhaust all 3 Groq keys
        self.pool.mark_rate_limited("groq")  # key 1 -> 2
        self.pool.mark_rate_limited("groq")  # key 2 -> 3
        res3 = self.pool.mark_rate_limited("groq")  # key 3 -> exhausted

        self.assertEqual(res3["status"], "provider_exhausted_failover_recommended")
        fo = res3["recommended_failover"]
        self.assertTrue(fo["failover_available"])
        self.assertEqual(fo["provider"], "sambanova")

    def test_07_cooldown_expiration(self) -> None:
        # Set short cooldown
        self.pool.cooldown_seconds = 0.1
        self.pool.mark_rate_limited("groq")
        time.sleep(0.15)

        # Key 1 should recover and be available again
        key1 = self.pool.pools["groq"][0]
        self.assertTrue(key1.is_available(time.time()))
        self.assertEqual(key1.state, KeyState.ACTIVE)


class Stage46RuntimeAndRouterIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "data" / "lucy").mkdir(parents=True, exist_ok=True)
        (self.root / "logs").mkdir(parents=True, exist_ok=True)
        self.runtime = LucyRuntime(project_root=self.root)
        self.router = CommandRouter(self.runtime)

    def tearDown(self) -> None:
        try:
            self.tmp.cleanup()
        except Exception:
            pass

    def test_08_runtime_methods(self) -> None:
        status = self.runtime.provider_pool_status()
        self.assertEqual(status["stage"], STAGE)
        self.assertIn("providers_summary", status)

        # Test rotation
        rot = self.runtime.rotate_provider_key("groq")
        self.assertTrue(rot["rotated"])

        # Test reload
        reload_res = self.runtime.reload_provider_keys()
        self.assertTrue(reload_res["loaded"])

    def test_09_router_commands(self) -> None:
        # Status command
        res1 = self.router.handle("provider pool status")
        self.assertIn("Multi-Provider Key Rotation Pool status:", res1.message)
        self.assertIn("Stage: 46 multi provider key rotation pool", res1.message)

        # Rotate key command
        res2 = self.router.handle("rotate key groq")
        self.assertIn("Provider Key Rotated:", res2.message)
        self.assertIn("Provider: groq", res2.message)

        # Reload keys command
        res3 = self.router.handle("reload api keys")
        self.assertIn("API Keys Reloaded Successfully", res3.message)


if __name__ == "__main__":
    unittest.main()
