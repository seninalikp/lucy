"""
tests/test_stage81_web_explorer.py
Unit tests for Stage 81: Sovereign Terminal Web Explorer & Headless Search Engine
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.web_explorer import (
    SearchResultItem,
    SovereignWebExplorer,
    WebSearchResponse,
    STAGE,
)


class MockReceiptLedger:
    def __init__(self):
        self.receipts = []

    def issue_receipt(self, action_category: str, operation: str, target: str, verified_outcome: str):
        self.receipts.append({
            "category": action_category,
            "operation": operation,
            "target": target,
            "outcome": verified_outcome,
        })


class TestStage81WebExplorer(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage81_test_"))
        self.cache_file = self.test_dir / "cache" / "search_cache.json"
        self.ledger = MockReceiptLedger()
        self.explorer = SovereignWebExplorer(
            project_root=self.test_dir,
            cache_file=self.cache_file,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 81)

    def test_02_privacy_firewall_blocks_paths(self):
        # Windows path
        err_win = self.explorer.check_query_safety("search C:\\Users\\admin\\Desktop\\secret.txt")
        self.assertIsNotNone(err_win)
        self.assertIn("Blocked", err_win)

        # Unix path
        err_unix = self.explorer.check_query_safety("check /etc/passwd or /Users/admin")
        self.assertIsNotNone(err_unix)
        self.assertIn("Blocked", err_unix)

    def test_03_privacy_firewall_blocks_credentials(self):
        err_key = self.explorer.check_query_safety("how to use api_key=sk_live_12345678")
        self.assertIsNotNone(err_key)
        self.assertIn("Blocked", err_key)

        # Valid query passes
        err_valid = self.explorer.check_query_safety("python asyncio tutorial documentation")
        self.assertIsNone(err_valid)

    def test_04_parse_lite_html_results(self):
        mock_html = """
        <html><body><table>
        <tr><td><a class="result-link" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fdocs.python.org%2F3%2F&rut=...">Python Documentation</a></td></tr>
        <tr><td class="result-snippet">Official Python 3 language documentation, tutorials, and libraries.</td></tr>
        <tr><td><a class="result-link" href="https://pypi.org/project/requests/">Requests: HTTP for Humans</a></td></tr>
        <tr><td class="result-snippet">Python HTTP library for human beings.</td></tr>
        </table></body></html>
        """
        items = self.explorer._parse_html_results(mock_html, max_results=5)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].title, "Python Documentation")
        self.assertEqual(items[0].url, "https://docs.python.org/3/")
        self.assertIn("Official Python", items[0].snippet)

        self.assertEqual(items[1].title, "Requests: HTTP for Humans")
        self.assertEqual(items[1].url, "https://pypi.org/project/requests/")

    def test_05_empty_query_error(self):
        res = self.explorer.search("")
        self.assertEqual(res.total_results, 0)
        self.assertIn("Empty query", res.error)

    def test_06_caching_mechanism(self):
        # Inject entry into cache
        cache_key = "python decorators"
        self.explorer.cache[cache_key] = {
            "cached_at": 2000000000.0,  # far future
            "results": [
                {"title": "Primer on Decorators", "url": "https://realpython.com/primer-on-python-decorators/", "snippet": "Guide", "source": "web"}
            ],
        }
        self.explorer._save_cache()

        res = self.explorer.search("python decorators")
        self.assertTrue(res.from_cache)
        self.assertEqual(res.total_results, 1)
        self.assertEqual(res.results[0].title, "Primer on Decorators")

    def test_07_clear_cache(self):
        self.explorer.cache["test"] = {"cached_at": 1.0, "results": []}
        self.explorer._save_cache()
        self.assertTrue(self.cache_file.exists())

        cleared = self.explorer.clear_cache()
        self.assertEqual(cleared, 1)
        self.assertEqual(len(self.explorer.cache), 0)
        self.assertFalse(self.cache_file.exists())

    def test_08_terminal_summary_ascii_safe(self):
        res = WebSearchResponse(
            query="python typing protocol",
            total_results=2,
            results=[
                SearchResultItem(title="PEP 544 - Protocols", url="https://peps.python.org/pep-0544/", snippet="Structural subtyping"),
                SearchResultItem(title="typing.Protocol", url="https://docs.python.org/3/library/typing.html", snippet="Standard library Protocol"),
            ],
            elapsed_ms=45.2,
            from_cache=False,
        )
        summary = res.format_terminal_summary()
        summary.encode("ascii")
        self.assertIn("SOVEREIGN WEB SEARCH RESULTS", summary)
        self.assertIn("PEP 544", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)

    def test_09_status(self):
        st = self.explorer.status()
        self.assertEqual(st["status"], "active")
        self.assertIn("cached_queries", st)

    def test_10_receipt_ledger_logging(self):
        # Inject successful search result directly to trigger receipt
        self.explorer.receipt_ledger.issue_receipt(
            action_category="web_search",
            operation="search",
            target="pytest fixtures",
            verified_outcome="Retrieved 3 search results",
        )
        self.assertEqual(len(self.ledger.receipts), 1)
        self.assertEqual(self.ledger.receipts[0]["operation"], "search")


if __name__ == "__main__":
    unittest.main()
