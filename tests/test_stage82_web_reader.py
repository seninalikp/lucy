"""
tests/test_stage82_web_reader.py
Unit tests for Stage 82: Grounded Web Page Extractor & Documentation Reader
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.web_reader import (
    ExtractedWebPage,
    SovereignWebReader,
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


class TestStage82WebReader(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage82_test_"))
        self.cache_file = self.test_dir / "cache" / "pages_cache.json"
        self.ledger = MockReceiptLedger()
        self.reader = SovereignWebReader(
            project_root=self.test_dir,
            cache_file=self.cache_file,
            receipt_ledger=self.ledger,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 82)

    def test_02_ssrf_blocks_localhost(self):
        err1 = self.reader.validate_url_safety("http://127.0.0.1:11434/api/tags")
        self.assertIsNotNone(err1)
        self.assertIn("Blocked SSRF", err1)

        err2 = self.reader.validate_url_safety("http://localhost:8000/admin")
        self.assertIsNotNone(err2)
        self.assertIn("Blocked SSRF", err2)

        err3 = self.reader.validate_url_safety("http://0.0.0.0:5000")
        self.assertIsNotNone(err3)
        self.assertIn("Blocked SSRF", err3)

    def test_03_ssrf_blocks_private_networks(self):
        err_192 = self.reader.validate_url_safety("http://192.168.1.100/router")
        self.assertIsNotNone(err_192)
        self.assertIn("Blocked SSRF", err_192)

        err_10 = self.reader.validate_url_safety("http://10.0.0.1/internal")
        self.assertIsNotNone(err_10)
        self.assertIn("Blocked SSRF", err_10)

        # Public domain is allowed
        err_public = self.reader.validate_url_safety("https://docs.python.org/3/")
        self.assertIsNone(err_public)

    def test_04_ssrf_blocks_invalid_schemes(self):
        err_file = self.reader.validate_url_safety("file:///C:/Users/admin/passwords.txt")
        self.assertIsNotNone(err_file)
        self.assertIn("not allowed", err_file)

        err_ftp = self.reader.validate_url_safety("ftp://example.com/file")
        self.assertIsNotNone(err_ftp)
        self.assertIn("not allowed", err_ftp)

    def test_05_clean_content_and_code_extraction(self):
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Python Asyncio Guide</title><style>body { font: 12px; }</style></head>
        <body>
            <nav><a href="/home">Home</a></nav>
            <h1>Asyncio Basics</h1>
            <p>Here is an example coroutine:</p>
            <pre><code>import asyncio
async def main():
    print("Hello from async")
asyncio.run(main())</code></pre>
            <footer>Copyright 2026</footer>
            <script>console.log("analytics");</script>
        </body>
        </html>
        """
        title, text, code_blocks = self.reader._extract_clean_content(sample_html)
        self.assertEqual(title, "Python Asyncio Guide")
        self.assertIn("# Asyncio Basics", text)
        self.assertIn("Here is an example coroutine:", text)
        # Nav and script stripped
        self.assertNotIn("console.log", text)
        self.assertNotIn("Copyright", text)

        # Code block extracted
        self.assertEqual(len(code_blocks), 1)
        self.assertIn("async def main():", code_blocks[0])

    def test_06_empty_url_handling(self):
        res = self.reader.fetch_url("")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Empty URL", res.error)

    def test_07_caching_mechanism(self):
        url = "https://example.com/cached_doc"
        self.reader.cache[url] = {
            "cached_at": 2000000000.0,
            "title": "Cached Example Doc",
            "text_content": "Clean cached content",
            "code_blocks": ["x = 1\ny = 2"],
            "status_code": 200,
        }
        self.reader._save_cache()

        res = self.reader.fetch_url(url)
        self.assertTrue(res.from_cache)
        self.assertEqual(res.title, "Cached Example Doc")
        self.assertEqual(len(res.code_blocks), 1)

    def test_08_pypi_error_handling(self):
        # Empty package
        res = self.reader.fetch_pypi_package("")
        self.assertIn("error", res)

    def test_09_terminal_summary_ascii_safe(self):
        page = ExtractedWebPage(
            url="https://peps.python.org/pep-0008/",
            title="PEP 8 - Style Guide for Python Code",
            text_content="# Introduction\nThis document gives coding conventions for the Python code.",
            code_blocks=["def function():\n    return 42"],
            elapsed_ms=120.5,
            from_cache=False,
        )
        summary = page.format_terminal_summary()
        summary.encode("ascii")
        self.assertIn("GROUNDED WEB PAGE EXTRACTOR", summary)
        self.assertIn("PEP 8", summary)
        self.assertIn("+", summary)
        self.assertIn("-", summary)
        self.assertIn("|", summary)

    def test_10_clear_cache_and_status(self):
        self.reader.cache["test"] = {"cached_at": 1.0}
        self.reader._save_cache()
        st = self.reader.status()
        self.assertEqual(st["cached_pages"], 1)

        cleared = self.reader.clear_cache()
        self.assertEqual(cleared, 1)
        self.assertEqual(len(self.reader.cache), 0)

    def test_11_format_pypi_summary(self):
        sample_info = {
            "name": "fastapi",
            "version": "0.110.0",
            "summary": "FastAPI framework, high performance, easy to learn.",
            "author": "Tiangolo",
            "license": "MIT",
            "requires_python": ">=3.8",
            "home_page": "https://fastapi.tiangolo.com",
            "requires_dist": ["starlette", "pydantic"],
        }
        summary = SovereignWebReader.format_pypi_summary(sample_info)
        summary.encode("ascii")
        self.assertIn("PYPI PACKAGE METADATA", summary)
        self.assertIn("fastapi", summary)
        self.assertIn("0.110.0", summary)
        self.assertIn("starlette", summary)

        err_summary = SovereignWebReader.format_pypi_summary({"error": "Package not found"})
        self.assertIn("Package not found", err_summary)

    def test_12_format_code_blocks_summary(self):
        blocks = ["x = 1\ny = 2\nprint(x + y)", "def foo():\n    return 42"]
        summary = SovereignWebReader.format_code_blocks_summary("https://docs.python.org", blocks)
        summary.encode("ascii")
        self.assertIn("EXTRACTED CODE BLOCKS", summary)
        self.assertIn("https://docs.python.org", summary)
        self.assertIn("print(x + y)", summary)

        empty_summary = SovereignWebReader.format_code_blocks_summary("https://empty.org", [])
        self.assertIn("No formatted code blocks found", empty_summary)

    def test_13_receipt_ledger_integration(self):
        # Verify receipt ledger logs upon successful fetch or mock receipt
        self.reader.receipt_ledger.issue_receipt(
            action_category="web_fetch",
            operation="fetch_url",
            target="https://example.com/docs",
            verified_outcome="Extracted 120 chars, 1 code blocks",
        )
        self.assertEqual(len(self.ledger.receipts), 1)
        self.assertEqual(self.ledger.receipts[0]["category"], "web_fetch")
        self.assertEqual(self.ledger.receipts[0]["operation"], "fetch_url")

    def test_14_pypi_error_formatting(self):
        err_info = {"error": "PyPI Package 'nonexistent_foo_123' not found (HTTP 404)"}
        summary = SovereignWebReader.format_pypi_summary(err_info)
        summary.encode("ascii")
        self.assertIn("PYPI PACKAGE METADATA", summary)
        self.assertIn("Error:", summary)
        self.assertIn("404", summary)


if __name__ == "__main__":
    unittest.main()


