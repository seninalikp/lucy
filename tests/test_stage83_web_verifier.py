"""
tests/test_stage83_web_verifier.py
Unit tests for Stage 83: Web-Grounded Cross-Verification & Fact-Checking RAG
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.lucy_core.web_explorer import SearchResultItem, WebSearchResponse
from backend.lucy_core.web_reader import ExtractedWebPage
from backend.lucy_core.web_verifier import (
    GroundedClaim,
    WebFactChecker,
    STAGE,
)


class MockWebExplorer:
    def __init__(self, items=None):
        self.items = items or []

    def search(self, query: str, max_results: int = 5, bypass_cache: bool = False) -> WebSearchResponse:
        return WebSearchResponse(
            query=query,
            total_results=len(self.items),
            results=self.items,
            elapsed_ms=10.0,
            from_cache=False,
        )


class MockWebReader:
    def __init__(self, pages=None, pypi_data=None):
        self.pages = pages or {}
        self.pypi_data = pypi_data or {}

    def fetch_url(self, url: str, timeout_sec: float = 4.0, bypass_cache: bool = False) -> ExtractedWebPage:
        if url in self.pages:
            return self.pages[url]
        return ExtractedWebPage(
            url=url,
            title="Mock Title",
            text_content="Default mock text content with no relevant overlap.",
            code_blocks=[],
            status_code=200,
        )

    def fetch_pypi_package(self, package_name: str, timeout_sec: float = 3.5):
        if package_name in self.pypi_data:
            return self.pypi_data[package_name]
        return {"name": package_name, "version": "1.0.0", "summary": "A mock package."}


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


class TestStage83WebVerifier(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="lucy_stage83_test_"))
        self.cache_file = self.test_dir / "cache" / "fact_check_cache.json"
        self.mock_explorer = MockWebExplorer()
        self.mock_reader = MockWebReader()
        self.mock_ledger = MockReceiptLedger()

        self.checker = WebFactChecker(
            web_explorer=self.mock_explorer,
            web_reader=self.mock_reader,
            cache_file=self.cache_file,
            receipt_ledger=self.mock_ledger,
            max_sources=3,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_stage_constant(self):
        self.assertEqual(STAGE, 83)

    def test_02_empty_claim(self):
        res = self.checker.verify_claim("   ")
        self.assertEqual(res.verification_status, "UNVERIFIED")
        self.assertEqual(res.confidence, 0.0)
        self.assertIn("Empty claim", res.reasoning)

    def test_03_claim_tokenization(self):
        claim = "Is Python 3.12 dropping the distutils package in this release?"
        tokens = self.checker._tokenize_claim(claim)
        self.assertIn("python", tokens)
        self.assertIn("3.12", tokens)
        self.assertIn("distutils", tokens)
        self.assertNotIn("the", tokens)
        self.assertNotIn("this", tokens)

    def test_04_passage_extraction(self):
        text = "First long sentence about python architecture. Second long sentence about standard library removals. Third sentence!"
        passages = self.checker._extract_passages(text)
        self.assertGreaterEqual(len(passages), 2)
        self.assertIn("First long sentence about python architecture.", passages[0])

    def test_05_passage_scoring_and_negation(self):
        passage_affirm = "Python 3.12 completely removed distutils from standard library."
        score, has_neg = self.checker._score_passage(passage_affirm, ["python", "3.12", "distutils"])
        self.assertEqual(score, 1.0)
        self.assertFalse(has_neg)

        passage_neg = "Python 3.12 did not remove distutils, this claim is false."
        score_neg, has_neg_flag = self.checker._score_passage(passage_neg, ["python", "3.12", "distutils"])
        self.assertEqual(score_neg, 1.0)
        self.assertTrue(has_neg_flag)

    def test_06_verify_claim_supported(self):
        self.mock_explorer.items = [
            SearchResultItem(
                title="Python 3.12 Release Notes",
                url="https://docs.python.org/3/whatsnew/3.12.html",
                snippet="Python 3.12 removed the distutils module as deprecated in PEP 632.",
            )
        ]
        self.mock_reader.pages = {
            "https://docs.python.org/3/whatsnew/3.12.html": ExtractedWebPage(
                url="https://docs.python.org/3/whatsnew/3.12.html",
                title="Python 3.12 Release Notes",
                text_content="PEP 632: The distutils package has been removed from the standard library. Projects should use setuptools instead.",
            )
        }

        res = self.checker.verify_claim("Python 3.12 removed distutils")
        self.assertEqual(res.verification_status, "SUPPORTED")
        self.assertGreaterEqual(res.confidence, 0.70)
        self.assertGreaterEqual(len(res.supporting_snippets), 1)
        self.assertEqual(len(res.contradicting_snippets), 0)

    def test_07_verify_claim_refuted(self):
        self.mock_explorer.items = [
            SearchResultItem(
                title="Debunking Myths",
                url="https://example.com/debunk",
                snippet="It is completely false that Python 3.12 removed asyncio.",
            )
        ]
        self.mock_reader.pages = {
            "https://example.com/debunk": ExtractedWebPage(
                url="https://example.com/debunk",
                title="Debunking Myths",
                text_content="It is completely false and incorrect that Python 3.12 removed asyncio. Asyncio is actively maintained.",
            )
        }

        res = self.checker.verify_claim("Python 3.12 removed asyncio")
        self.assertEqual(res.verification_status, "REFUTED")
        self.assertGreaterEqual(res.confidence, 0.68)
        self.assertGreaterEqual(len(res.contradicting_snippets), 1)

    def test_08_verify_claim_ambiguous(self):
        self.mock_explorer.items = [
            SearchResultItem(
                title="Forum Discussion",
                url="https://example.com/thread",
                snippet="Conflicting opinions on this framework feature.",
            )
        ]
        self.mock_reader.pages = {
            "https://example.com/thread": ExtractedWebPage(
                url="https://example.com/thread",
                title="Forum Discussion",
                text_content="Some devs claim rust handles async safely. However other benchmarks showed rust async is not completely safe without care.",
            )
        }

        res = self.checker.verify_claim("rust async safely")
        self.assertEqual(res.verification_status, "AMBIGUOUS")
        self.assertEqual(res.confidence, 0.50)

    def test_09_caching_mechanism(self):
        self.checker.cache["test claim"] = {
            "cached_at": 2000000000.0,
            "data": {
                "claim": "test claim",
                "verification_status": "SUPPORTED",
                "confidence": 0.88,
                "primary_sources": ["https://cached.org"],
                "supporting_snippets": ["Cached supporting snippet."],
                "contradicting_snippets": [],
                "reasoning": "From cache.",
            },
        }
        self.checker._save_cache()

        res = self.checker.verify_claim("test claim")
        self.assertTrue(res.from_cache)
        self.assertEqual(res.verification_status, "SUPPORTED")
        self.assertEqual(res.confidence, 0.88)

    def test_10_terminal_summary_ascii_safe(self):
        claim = GroundedClaim(
            claim="PEP 544 added structural subtyping",
            verification_status="SUPPORTED",
            confidence=0.92,
            primary_sources=["https://peps.python.org/pep-0544/"],
            supporting_snippets=["PEP 544 introduces Protocols and static duck typing."],
            reasoning="Corroborated by official PEP repository.",
            elapsed_ms=145.2,
        )
        summary = claim.format_terminal_summary()
        summary.encode("ascii")  # Must not throw UnicodeEncodeError
        self.assertIn("WEB-GROUNDED FACT CHECKER", summary)
        self.assertIn("PEP 544", summary)
        self.assertIn("[SUPPORTED]", summary)
        self.assertIn("92.0%", summary)

    def test_11_code_snippet_verification_valid(self):
        code = """
import os
import requests
from pathlib import Path

def fetch_data():
    return requests.get("https://example.com")
"""
        report = self.checker.verify_code_snippet(code)
        self.assertTrue(report["valid_syntax"])
        self.assertIn("requests", report["imported_modules"])
        self.assertIn("os", report["imported_modules"])
        self.assertIn("requests", report["packages_checked"])

        summary = self.checker.format_code_verification_summary(report)
        summary.encode("ascii")
        self.assertIn("CODE SNIPPET VERIFICATION REPORT", summary)
        self.assertIn("VALID [OK]", summary)

    def test_12_code_snippet_verification_syntax_error(self):
        bad_code = "def broken_func(:\n    return 42"
        report = self.checker.verify_code_snippet(bad_code)
        self.assertFalse(report["valid_syntax"])
        self.assertIn("SyntaxError", report["error"])

    def test_13_receipt_ledger_integration(self):
        res = self.checker.verify_claim("Python GIL removal is in 3.13")
        self.assertEqual(len(self.mock_ledger.receipts), 1)
        self.assertEqual(self.mock_ledger.receipts[0]["category"], "fact_check")
        self.assertEqual(self.mock_ledger.receipts[0]["operation"], "verify_claim")

    def test_14_cache_clear_and_status(self):
        self.checker.cache["key1"] = {"cached_at": 1.0}
        self.checker._save_cache()
        st = self.checker.status()
        self.assertEqual(st["cached_claims"], 1)

        cleared = self.checker.clear_cache()
        self.assertEqual(cleared, 1)
        self.assertEqual(len(self.checker.cache), 0)


if __name__ == "__main__":
    unittest.main()
