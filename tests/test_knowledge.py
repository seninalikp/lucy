import json
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.knowledge import AICollectionsKnowledge
from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter


class KnowledgeTests(unittest.TestCase):
    def test_ingests_safe_text_and_redacts_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            data_dir = Path(temp) / "lucy_data"
            root = Path(temp) / "AI COLLECTIONS"
            root.mkdir()
            (root / "notes.md").write_text("# Project Map\nLucy should learn architecture notes.", encoding="utf-8")
            (root / "provider.py").write_text(
                "GROQ_API_KEY = 'gsk_test_secret_value'\n"
                "def call_groq():\n"
                "    return 'ok'\n",
                encoding="utf-8",
            )
            secure = root / "ELIE" / "api" / "secure"
            secure.mkdir(parents=True)
            (secure / "groq.key.enc").write_text("encrypted-value", encoding="utf-8")

            knowledge = AICollectionsKnowledge(data_dir)
            result = knowledge.ingest(str(root))

            self.assertTrue(result["ok"])
            self.assertEqual(result["counts"]["total_files"], 3)
            self.assertEqual(result["counts"]["indexed_text"], 2)
            self.assertEqual(result["counts"]["metadata_only"], 1)
            self.assertEqual(result["counts"]["redacted"], 1)

            index_text = knowledge.index_file.read_text(encoding="utf-8")
            self.assertNotIn("gsk_test_secret_value", index_text)
            self.assertIn("[redacted]", index_text)
            self.assertIn("groq.key.enc", index_text)

            search = knowledge.search("architecture")
            self.assertEqual(search["matches"][0]["path"], "notes.md")

    def test_router_eat_ai_collections_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project_root = Path(temp)
            root = project_root / "AI COLLECTIONS"
            root.mkdir()
            (root / "readme.md").write_text("AI collection readme.", encoding="utf-8")

            runtime = LucyRuntime(project_root=project_root)
            router = CommandRouter(runtime)
            response = router.handle(f"eat ai collections {root}")

            self.assertIn("AI Collections ingested", response.message)
            status = router.handle("ai collections status")
            self.assertIn("Files seen: 1", status.message)

            data = json.loads((project_root / "data" / "lucy" / "knowledge" / "ai_collections_index.json").read_text(encoding="utf-8"))
            self.assertEqual(data["counts"]["indexed_text"], 1)


if __name__ == "__main__":
    unittest.main()
