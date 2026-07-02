import os
import sys
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.secrets import SessionSecretStore


class SessionSecretStoreTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("NVIDIA_API_KEY", None)

    def test_set_session_secret(self) -> None:
        store = SessionSecretStore()
        result = store.set_session_secret("NVIDIA", "NVIDIA_API_KEY", "test-key-value-123456")
        self.assertTrue(result["saved"])
        self.assertTrue(store.has("NVIDIA_API_KEY"))
        self.assertEqual(store.status("NVIDIA", "NVIDIA_API_KEY")["source"], "session")

    def test_refuses_empty_secret(self) -> None:
        store = SessionSecretStore()
        result = store.set_session_secret("NVIDIA", "NVIDIA_API_KEY", "")
        self.assertFalse(result["saved"])

    @unittest.skipUnless(sys.platform == "win32", "DPAPI permanent secret storage is Windows-only.")
    def test_set_persistent_secret(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SessionSecretStore(Path(temp_dir))
            result = store.set_persistent_secret("NVIDIA", "NVIDIA_API_KEY", "test-key-value-123456")
            self.assertTrue(result["saved"])
            self.assertTrue(Path(result["path"]).exists())

            os.environ.pop("NVIDIA_API_KEY", None)
            restored = SessionSecretStore(Path(temp_dir))
            self.assertEqual(restored.status("NVIDIA", "NVIDIA_API_KEY")["source"], "persistent_encrypted")
            self.assertEqual(restored.get("NVIDIA_API_KEY"), "test-key-value-123456")


if __name__ == "__main__":
    unittest.main()
