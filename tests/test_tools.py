import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.tools import SafeToolbox


class SafeToolboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "README.md").write_text("Lucy operator tools are local.", encoding="utf-8")
        (self.root / ".env").write_text("SECRET=value", encoding="utf-8")
        self.tools = SafeToolbox(self.root)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_workspace_tree_lists_files(self) -> None:
        tree = self.tools.workspace_tree()
        paths = [item["path"] for item in tree["files"]]
        self.assertIn("README.md", paths)

    def test_find_files(self) -> None:
        result = self.tools.find_files("readme")
        self.assertIn("README.md", result["matches"])

    def test_search_text(self) -> None:
        result = self.tools.search_text("operator")
        self.assertEqual(result["matches"][0]["path"], "README.md")

    def test_read_text_file(self) -> None:
        result = self.tools.read_text_file("README.md")
        self.assertTrue(result["read"])
        self.assertIn("operator tools", result["text"])

    def test_refuses_outside_path(self) -> None:
        result = self.tools.read_text_file("../outside.txt")
        self.assertFalse(result["read"])

    def test_refuses_sensitive_name(self) -> None:
        result = self.tools.read_text_file(".env")
        self.assertFalse(result["read"])


if __name__ == "__main__":
    unittest.main()
