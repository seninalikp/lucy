import unittest
import base64
import hashlib
import json
import tempfile
from pathlib import Path

from backend.lucy_core.api_tools import ExternalToolRouter, NvidiaMemoryTool, ProviderKeySource


class ApiToolsTests(unittest.TestCase):
    def test_external_tool_status(self) -> None:
        router = ExternalToolRouter()
        status = router.status(nvidia_key_available=False)
        self.assertEqual(status["tools"][0]["name"], "nvidia_memory_fallback")
        self.assertFalse(status["tools"][0]["available"])

    def test_nvidia_tool_requires_key(self) -> None:
        tool = NvidiaMemoryTool()
        result = tool.memory_fallback("query", "context", api_key="")
        self.assertFalse(result["ok"])

    def test_elie_vault_unlocks_without_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            elie_root = Path(temp) / "ELIE"
            secure = elie_root / "api" / "secure"
            secure.mkdir(parents=True)
            (elie_root / "local_unlock.py").write_text(
                "UNLOCK_ALL = True\nMASTER_PASSWORD = 'pw123'\n",
                encoding="utf-8",
            )
            raw = b"ELIEKEY:test-groq-key-123456"
            pad = b""
            index = 0
            while len(pad) < len(raw):
                pad += hashlib.sha256(("pw123:" + str(index)).encode("utf-8")).digest()
                index += 1
            encrypted = bytes(raw[i] ^ pad[i] for i in range(len(raw)))
            (secure / "groq.key.enc").write_text(base64.b64encode(encrypted).decode("ascii"), encoding="utf-8")

            source = ProviderKeySource(elie_root=elie_root)

            lookup = source.get("groq")
            self.assertEqual(lookup.value, "test-groq-key-123456")
            self.assertEqual(lookup.source, "elie_vault:groq")

    def test_status_lists_elie_providers_without_key_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "data" / "lucy" / "secure").mkdir(parents=True)
            router = ExternalToolRouter(project_root=root, elie_root=root / "missing_elie")
            status = router.status(nvidia_key_available=False)

            encoded = json.dumps(status)
            self.assertIn("groq_chat", encoded)
            self.assertIn("openrouter_chat", encoded)
            self.assertNotIn("API_KEY", encoded)


if __name__ == "__main__":
    unittest.main()
