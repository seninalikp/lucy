"""
test_stage71_codebase_indexer.py
Stage 71: Local AST Codebase Indexer & High-Speed Symbol Graph Unit Tests.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.codebase_indexer import (
    CodebaseIndexer,
    PythonSymbolVisitor,
    SymbolEntry,
    STAGE as STAGE_71,
)
from backend.lucy_core.lucy_runtime import LucyRuntime


class TestStage71CodebaseIndexer(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.data_dir = self.root / "data"

        # Create a mock python package
        self.src_dir = self.root / "pkg"
        self.src_dir.mkdir(parents=True, exist_ok=True)

        self.file1 = self.src_dir / "service.py"
        self.file1.write_text(
            '"""Service module docstring."""\n\n'
            "import os\n"
            "from math import sqrt\n\n"
            "class BaseService:\n"
            '    """Base class for services."""\n'
            "    def ping(self) -> str:\n"
            '        """Ping health check."""\n'
            '        return "pong"\n\n'
            "class AudioService(BaseService):\n"
            "    def __init__(self, port: int = 8000) -> None:\n"
            "        self.port = port\n\n"
            "    async def stream_audio(self, buffer_size: int = 1024) -> None:\n"
            '        """Stream audio async."""\n'
            "        pass\n",
            encoding="utf-8",
        )

        self.indexer = CodebaseIndexer(project_root=self.root, data_dir=self.data_dir)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_01_ast_symbol_visitor_extracts_classes_and_functions(self) -> None:
        res = self.indexer.index_workspace(force=True)
        self.assertEqual(res.get("stage"), STAGE_71)
        self.assertGreater(res.get("total_symbols", 0), 0)

        # Look up AudioService
        syms = self.indexer.find_symbol("AudioService", exact=True)
        self.assertEqual(len(syms), 1)
        audio_cls = syms[0]
        self.assertEqual(audio_cls["kind"], "class")
        self.assertEqual(audio_cls["bases"], ["BaseService"])

    def test_02_async_function_support(self) -> None:
        self.indexer.index_workspace(force=True)
        syms = self.indexer.find_symbol("stream_audio", exact=True)
        self.assertEqual(len(syms), 1)
        func = syms[0]
        self.assertEqual(func["kind"], "async_function")
        self.assertIn("buffer_size", func["params"])
        self.assertEqual(func["docstring"], "Stream audio async.")

    def test_03_index_workspace_and_cache(self) -> None:
        res = self.indexer.index_workspace(force=True)
        self.assertTrue(self.indexer.cache_file.exists())
        self.assertEqual(res["total_files"], 1)
        self.assertEqual(res["parsed_files"], 1)

    def test_04_incremental_indexing(self) -> None:
        self.indexer.index_workspace(force=True)
        # Second run should skip already cached file
        res2 = self.indexer.index_workspace(force=False)
        self.assertEqual(res2["cached_files"], 1)
        self.assertEqual(res2["parsed_files"], 0)

    def test_05_find_symbol_exact_and_fuzzy(self) -> None:
        self.indexer.index_workspace(force=True)

        # Exact match
        exact = self.indexer.find_symbol("BaseService", exact=True)
        self.assertEqual(len(exact), 1)

        # Fuzzy substring match
        fuzzy = self.indexer.find_symbol("service", exact=False)
        self.assertGreaterEqual(len(fuzzy), 2)  # BaseService, AudioService

    def test_06_file_outline(self) -> None:
        self.indexer.index_workspace(force=True)
        outline = self.indexer.get_file_outline("pkg/service.py")
        self.assertGreaterEqual(len(outline), 4)

        names = [s["name"] for s in outline]
        self.assertIn("BaseService", names)
        self.assertIn("ping", names)
        self.assertIn("AudioService", names)
        self.assertIn("stream_audio", names)

    def test_07_find_importers(self) -> None:
        # Create file2 that imports service
        file2 = self.src_dir / "consumer.py"
        file2.write_text("from pkg.service import AudioService\n", encoding="utf-8")

        self.indexer.index_workspace(force=True)
        importers = self.indexer.find_importers("AudioService")
        self.assertIn("pkg/consumer.py", importers)

    def test_08_format_symbol_lookup(self) -> None:
        self.indexer.index_workspace(force=True)
        text = self.indexer.format_symbol_lookup("AudioService")
        self.assertIn("[Symbol Lookup: 'AudioService'", text)
        self.assertIn("CLASS AudioService", text)
        self.assertIn("pkg/service.py", text)

    def test_09_runtime_codebase_commands(self) -> None:
        runtime = LucyRuntime()
        status = runtime.codebase_index_status()
        self.assertEqual(status.get("stage"), STAGE_71)
        self.assertEqual(status.get("codebase_indexer"), "active")

        # Test /where on actual codebase symbol
        res = runtime.lucy_respond("/where PersonaGovernor")
        self.assertIn("[Symbol Lookup:", res)
        self.assertIn("PersonaGovernor", res)

    def test_10_index_live_lucy_codebase(self) -> None:
        runtime = LucyRuntime()
        res = runtime.codebase_indexer.index_workspace(force=False)
        self.assertGreater(res.get("total_symbols", 0), 50)
        self.assertGreater(res.get("total_files", 0), 20)


if __name__ == "__main__":
    unittest.main()
