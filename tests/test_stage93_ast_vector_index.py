"""
tests/test_stage93_ast_vector_index.py
Stage 93 = Semantic AST Vector Code Indexer

Verifies:
1. STAGE constant is 93.
2. SymbolExtractor extracts classes, methods, functions, and module constants.
3. Tokenizer splits CamelCase and snake_case symbols into searchable sub-tokens.
4. Repository indexing scans Python source files and builds inverted symbol index.
5. Search ranks exact name matches and semantic signature matches.
6. Search result formatting produces CP1252-safe ASCII table.
7. Symbol tree produces hierarchical indented representation.
8. Index persistence and reload from disk (ast_index.json).
9. Execution receipt ledger logging for indexing.
10. Status reporting dictionary.
"""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.ast_vector_index import (
    STAGE,
    ASTVectorCodeIndexer,
    CodeSymbol,
    IndexSummary,
    SearchResultMatch,
    SymbolExtractor,
    SymbolKind,
)


class MockReceiptLedger:
    def __init__(self) -> None:
        self.issued_receipts = []

    def issue_receipt(
        self,
        action_category: str,
        operation: str,
        target: str,
        verified_outcome: str = "",
        details: dict | None = None,
    ) -> dict:
        receipt = {
            "action_category": action_category,
            "operation": operation,
            "target": target,
            "verified_outcome": verified_outcome,
        }
        self.issued_receipts.append(receipt)
        return receipt


class TestStage93ASTVectorIndex(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.index_dir = self.root / "data" / "lucy" / "code_index"
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.ledger = MockReceiptLedger()
        self.indexer = ASTVectorCodeIndexer(
            project_root=self.root,
            receipt_ledger=self.ledger,
            index_dir=self.index_dir,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_01_stage_constant(self) -> None:
        self.assertEqual(STAGE, 93)

    def test_02_symbol_extractor_classes_and_methods(self) -> None:
        code = (
            "GLOBAL_LIMIT = 500\n\n"
            "class MathEngine:\n"
            '    """Performs neural math computation."""\n'
            "    def add_numbers(self, a: int, b: int) -> int:\n"
            "        return a + b\n\n"
            "def calculate_total(items):\n"
            "    return sum(items)\n"
        )
        lines = code.splitlines()
        extractor = SymbolExtractor("math.py", lines)
        extractor.visit(ast.parse(code))

        names = {s.name: s for s in extractor.symbols}
        self.assertIn("GLOBAL_LIMIT", names)
        self.assertEqual(names["GLOBAL_LIMIT"].kind, SymbolKind.CONSTANT)

        self.assertIn("MathEngine", names)
        self.assertEqual(names["MathEngine"].kind, SymbolKind.CLASS)
        self.assertIn("neural", names["MathEngine"].docstring)

        self.assertIn("add_numbers", names)
        self.assertEqual(names["add_numbers"].kind, SymbolKind.METHOD)
        self.assertEqual(names["add_numbers"].parent_symbol, "MathEngine")

        self.assertIn("calculate_total", names)
        self.assertEqual(names["calculate_total"].kind, SymbolKind.FUNCTION)

    def test_03_subtokenization_camel_and_snake(self) -> None:
        extractor = SymbolExtractor("test.py", [])
        tokens = extractor._tokenize("CommandRouter execute_one_turn")
        self.assertIn("command", tokens)
        self.assertIn("router", tokens)
        self.assertIn("execute", tokens)
        self.assertIn("turn", tokens)

    def test_04_index_repository_and_receipt(self) -> None:
        # Create sample source files
        mod_dir = self.root / "backend"
        mod_dir.mkdir(parents=True, exist_ok=True)
        (mod_dir / "service.py").write_text(
            "class AuthenticationService:\n"
            "    def authenticate_user(self, username, password):\n"
            "        return True\n",
            encoding="utf-8",
        )
        (mod_dir / "router.py").write_text(
            "class CommandRouter:\n"
            "    def handle(self, command):\n"
            "        return 'OK'\n",
            encoding="utf-8",
        )

        summary = self.indexer.index_repository(target_dir=mod_dir)
        self.assertIsInstance(summary, IndexSummary)
        self.assertEqual(summary.total_files, 2)
        self.assertEqual(summary.total_classes, 2)
        self.assertEqual(summary.total_methods, 2)
        self.assertGreater(summary.total_symbols, 0)

        # Verify receipt
        receipts = [r for r in self.ledger.issued_receipts if r["operation"] == "index_repository"]
        self.assertEqual(len(receipts), 1)

    def test_05_search_ranking_and_boosting(self) -> None:
        mod_dir = self.root / "src"
        mod_dir.mkdir(parents=True, exist_ok=True)
        (mod_dir / "auth.py").write_text(
            "class AuthService:\n"
            '    """Handles user authentication and login tokens."""\n'
            "    def verify_token(self, token):\n"
            "        return True\n",
            encoding="utf-8",
        )
        (mod_dir / "data.py").write_text(
            "class DataStore:\n"
            "    def get_user(self, user_id):\n"
            "        return None\n",
            encoding="utf-8",
        )
        self.indexer.index_repository(target_dir=mod_dir)

        # Query "auth"
        matches = self.indexer.search("auth", top_k=3)
        self.assertGreater(len(matches), 0)
        top_match = matches[0]
        self.assertEqual(top_match.symbol.name, "AuthService")
        self.assertGreater(top_match.score, 0.0)

    def test_06_format_search_results_ascii_safe(self) -> None:
        mod_dir = self.root / "src"
        mod_dir.mkdir(parents=True, exist_ok=True)
        (mod_dir / "worker.py").write_text(
            "class TaskWorker:\n"
            '    """Background task processor."""\n'
            "    def process_task(self, task_id):\n"
            "        pass\n",
            encoding="utf-8",
        )
        self.indexer.index_repository(target_dir=mod_dir)
        matches = self.indexer.search("worker")

        res_str = self.indexer.format_search_results("worker", matches)
        self.assertIn("AST CODE SEARCH RESULTS (STAGE 93)", res_str)
        self.assertIn("TaskWorker", res_str)
        self.assertIn("+----------------------------------------------------------------------+", res_str)
        res_str.encode("cp1252")

    def test_07_symbol_tree_navigation(self) -> None:
        mod_dir = self.root / "src"
        mod_dir.mkdir(parents=True, exist_ok=True)
        test_file = mod_dir / "pipeline.py"
        test_file.write_text(
            "DEFAULT_TIMEOUT = 30\n\n"
            "class DataPipeline:\n"
            "    def extract(self): pass\n"
            "    def transform(self): pass\n\n"
            "def run_pipeline(): pass\n",
            encoding="utf-8",
        )
        self.indexer.index_repository(target_dir=mod_dir)

        tree = self.indexer.get_symbol_tree("pipeline.py")
        self.assertIn("AST HIERARCHICAL SYMBOL TREE", tree)
        self.assertIn("class DataPipeline", tree)
        self.assertIn("def extract()", tree)
        self.assertIn("def transform()", tree)
        self.assertIn("def run_pipeline()", tree)
        self.assertIn("const DEFAULT_TIMEOUT", tree)
        tree.encode("cp1252")

    def test_08_index_persistence_and_reload(self) -> None:
        mod_dir = self.root / "src"
        mod_dir.mkdir(parents=True, exist_ok=True)
        (mod_dir / "test_mod.py").write_text("class TestClass:\n    pass\n", encoding="utf-8")
        self.indexer.index_repository(target_dir=mod_dir)

        # Reload into second instance
        indexer2 = ASTVectorCodeIndexer(
            project_root=self.root,
            index_dir=self.index_dir,
        )
        self.assertGreater(len(indexer2.symbols), 0)
        self.assertIn("src/test_mod.py:TestClass", indexer2.symbols)
        self.assertIsNotNone(indexer2.latest_summary)

    def test_09_status_dict(self) -> None:
        st = self.indexer.status()
        self.assertEqual(st["stage"], 93)
        self.assertEqual(st["status"], "active")
        self.assertIn("index_directory", st)
        self.assertIn("total_symbols", st)


if __name__ == "__main__":
    unittest.main()
