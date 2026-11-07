"""
backend/lucy_core/web_reader.py
Stage 82: Grounded Web Page Extractor & Documentation Reader

Provides headless web page fetching, boilerplate/noise stripping, markdown and
code block extraction, PyPI metadata querying, and SSRF security guards for
Lucy's sovereign terminal CLI.
"""

from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

STAGE: int = 82

# SSRF Protection: forbid fetching localhost, private loopback, or private intranet ranges
BLOCKED_HOST_PATTERNS = [
    re.compile(r"""^(?:localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|::1|fe80::)""", re.I),
    re.compile(r"""^10\.\d+\.\d+\.\d+"""),
    re.compile(r"""^172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+"""),
    re.compile(r"""^192\.168\.\d+\.\d+"""),
]


@dataclass
class ExtractedWebPage:
    url: str
    title: str
    text_content: str
    code_blocks: List[str] = field(default_factory=list)
    elapsed_ms: float = 0.0
    from_cache: bool = False
    status_code: int = 200
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "text_content": self.text_content,
            "code_blocks": self.code_blocks,
            "elapsed_ms": self.elapsed_ms,
            "from_cache": self.from_cache,
            "status_code": self.status_code,
            "error": self.error,
        }

    def format_terminal_summary(self, max_chars: int = 2000) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| GROUNDED WEB PAGE EXTRACTOR (STAGE 82)                               |")
        lines.append("+----------------------------------------------------------------------+")
        title_str = self.title[:55]
        cache_str = " (CACHED)" if self.from_cache else ""
        lines.append(f"| Title: {title_str:<61} |")
        lines.append(f"| URL: {self.url[:50]:<50} | Time: {self.elapsed_ms:.1f}ms{cache_str:<7} |")
        lines.append(f"| Code Blocks Found: {len(self.code_blocks):<14} | Status: {self.status_code:<25} |")
        lines.append("+----------------------------------------------------------------------+")

        if self.error:
            lines.append(f"| Error: {self.error[:64]:<64} |")
            lines.append("+----------------------------------------------------------------------+")
            return "\n".join(lines)

        # Truncated body preview
        preview = self.text_content[:max_chars].strip()
        lines.append("| EXTRACTED CLEAN CONTENT:                                             |")
        lines.append("+----------------------------------------------------------------------+")
        for l in preview.splitlines()[:25]:
            if l.strip():
                lines.append(f"| {l[:68]:<68} |")
        if len(self.text_content) > max_chars or len(preview.splitlines()) > 25:
            lines.append(f"| ... [truncated, total {len(self.text_content)} characters]                      |")
        lines.append("+----------------------------------------------------------------------+")

        if self.code_blocks:
            lines.append("| EXTRACTED CODE BLOCKS:                                               |")
            lines.append("+----------------------------------------------------------------------+")
            for i, cb in enumerate(self.code_blocks[:3], start=1):
                first_line = cb.splitlines()[0] if cb.splitlines() else "code"
                lines.append(f"| Block [{i}] ({len(cb.splitlines())} lines): {first_line[:45]:<45} |")
            lines.append("+----------------------------------------------------------------------+")

        return "\n".join(lines)


class SovereignWebReader:
    """
    Safely fetches public web documentation, extracts boilerplate-free content,
    queries PyPI package metadata, and enforces SSRF boundaries.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        cache_file: Optional[Path] = None,
        receipt_ledger: Optional[Any] = None,
        cache_ttl_sec: float = 86400.0,  # 24 hours
    ) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.cache_file = cache_file or (self.project_root / "data" / "lucy" / "cache" / "web_pages_cache.json")
        self.receipt_ledger = receipt_ledger
        self.cache_ttl_sec = cache_ttl_sec

        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if not self.cache_file.exists():
            return
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self.cache = json.load(f)
        except Exception:
            self.cache = {}

    def _save_cache(self) -> None:
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except Exception:
            pass

    def validate_url_safety(self, url: str) -> Optional[str]:
        """
        SSRF check: disallows non-http/https schemes and private intranet IP targets.
        """
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return f"Blocked: scheme '{parsed.scheme}' not allowed (http/https only)."

            hostname = parsed.hostname or ""
            for pat in BLOCKED_HOST_PATTERNS:
                if pat.search(hostname):
                    return f"Blocked SSRF target: hostname '{hostname}' is a private or loopback address."
            return None
        except Exception as e:
            return f"Invalid URL: {str(e)}"

    def fetch_url(
        self,
        url: str,
        timeout_sec: float = 4.0,
        bypass_cache: bool = False,
    ) -> ExtractedWebPage:
        """
        Fetches a web page and returns cleanly extracted text and code blocks.
        """
        clean_url = url.strip()
        if not clean_url:
            return ExtractedWebPage(url="", title="", text_content="", error="Empty URL provided.")

        if not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url

        # SSRF check
        ssrf_err = self.validate_url_safety(clean_url)
        if ssrf_err:
            return ExtractedWebPage(url=clean_url, title="", text_content="", error=ssrf_err, status_code=403)

        # Cache check
        now = time.time()
        if not bypass_cache and clean_url in self.cache:
            entry = self.cache[clean_url]
            if (now - entry.get("cached_at", 0)) < self.cache_ttl_sec:
                return ExtractedWebPage(
                    url=clean_url,
                    title=entry.get("title", ""),
                    text_content=entry.get("text_content", ""),
                    code_blocks=entry.get("code_blocks", []),
                    elapsed_ms=0.5,
                    from_cache=True,
                    status_code=entry.get("status_code", 200),
                )

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,text/plain,*/*",
        }

        start_time = time.perf_counter()
        try:
            req = urllib.request.Request(clean_url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                status_code = resp.status
                raw_bytes = resp.read()
                charset = resp.headers.get_content_charset() or "utf-8"
                html_body = raw_bytes.decode(charset, errors="replace")

            title, clean_text, code_blocks = self._extract_clean_content(html_body)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            page = ExtractedWebPage(
                url=clean_url,
                title=title or clean_url,
                text_content=clean_text,
                code_blocks=code_blocks,
                elapsed_ms=elapsed_ms,
                from_cache=False,
                status_code=status_code,
            )

            # Save to cache
            self.cache[clean_url] = {
                "cached_at": now,
                "title": page.title,
                "text_content": page.text_content,
                "code_blocks": page.code_blocks,
                "status_code": status_code,
            }
            self._save_cache()

            if self.receipt_ledger is not None:
                try:
                    self.receipt_ledger.issue_receipt(
                        action_category="web_fetch",
                        operation="fetch_url",
                        target=clean_url[:40],
                        verified_outcome=f"Extracted {len(clean_text)} chars, {len(code_blocks)} code blocks in {elapsed_ms:.1f}ms",
                    )
                except Exception:
                    pass

            return page

        except urllib.error.HTTPError as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ExtractedWebPage(url=clean_url, title="", text_content="", error=f"HTTP {exc.code}: {exc.reason}", status_code=exc.code, elapsed_ms=elapsed_ms)
        except urllib.error.URLError as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ExtractedWebPage(url=clean_url, title="", text_content="", error=f"Network error: {exc.reason}", elapsed_ms=elapsed_ms)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ExtractedWebPage(url=clean_url, title="", text_content="", error=str(exc), elapsed_ms=elapsed_ms)

    def _extract_clean_content(self, html_text: str) -> Tuple[str, str, List[str]]:
        """
        Strips script, style, navigation boilerplate and extracts clean text and code blocks.
        """
        # 1. Extract Title
        m_title = re.search(r"<title[^>]*>(.*?)</title>", html_text, re.I | re.S)
        title = html.unescape(m_title.group(1).strip()) if m_title else ""

        # 2. Extract Code Blocks (<pre><code>...</code></pre> or <pre>...</pre>)
        code_blocks: List[str] = []
        for m in re.finditer(r"<pre[^>]*>(?:<code[^>]*>)?(.*?)(?:</code>)?</pre>", html_text, re.I | re.S):
            raw_code = html.unescape(re.sub(r"<[^<]+?>", "", m.group(1)).strip())
            if raw_code and len(raw_code.splitlines()) >= 2:
                code_blocks.append(raw_code)

        # 3. Strip non-content tags
        cleaned = re.sub(r"<(script|style|nav|footer|header|noscript|svg|iframe)[^>]*>.*?</\1>", " ", html_text, flags=re.I | re.S)
        # Convert header tags to markdown
        cleaned = re.sub(r"<h1[^>]*>(.*?)</h1>", r"\n# \1\n", cleaned, flags=re.I | re.S)
        cleaned = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n## \1\n", cleaned, flags=re.I | re.S)
        cleaned = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n### \1\n", cleaned, flags=re.I | re.S)
        cleaned = re.sub(r"<li[^>]*>(.*?)</li>", r"\n* \1", cleaned, flags=re.I | re.S)
        cleaned = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\1\n", cleaned, flags=re.I | re.S)
        cleaned = re.sub(r"<br\s*/?>", "\n", cleaned, flags=re.I)

        # Strip remaining tags
        cleaned = re.sub(r"<[^<]+?>", " ", cleaned)
        cleaned = html.unescape(cleaned)

        # Collapse whitespace while preserving single blank lines
        lines = [re.sub(r"[ \t]+", " ", l).strip() for l in cleaned.splitlines()]
        compact_lines: List[str] = []
        last_empty = False
        for l in lines:
            if not l:
                if not last_empty:
                    compact_lines.append("")
                last_empty = True
            else:
                compact_lines.append(l)
                last_empty = False

        final_text = "\n".join(compact_lines).strip()
        return title, final_text, code_blocks

    def fetch_pypi_package(self, package_name: str, timeout_sec: float = 3.5) -> Dict[str, Any]:
        """
        Queries official PyPI JSON API for package versions, summary, and dependencies.
        """
        pkg = package_name.strip().lower()
        if not pkg:
            return {"error": "Empty package name."}

        url = f"https://pypi.org/pypi/{pkg}/json"
        headers = {"User-Agent": "LucyWebReader/82.0"}

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            info = data.get("info", {})
            return {
                "name": info.get("name", pkg),
                "version": info.get("version", "unknown"),
                "summary": info.get("summary", ""),
                "home_page": info.get("home_page") or info.get("project_url", ""),
                "author": info.get("author", ""),
                "license": info.get("license", ""),
                "requires_python": info.get("requires_python", ""),
                "requires_dist": (info.get("requires_dist") or [])[:8],
            }
        except urllib.error.HTTPError as exc:
            return {"error": f"PyPI Package '{pkg}' not found (HTTP {exc.code})"}
        except Exception as exc:
            return {"error": f"PyPI lookup error: {str(exc)}"}

    def clear_cache(self) -> int:
        count = len(self.cache)
        self.cache.clear()
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except Exception:
                pass
        return count

    def status(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "cached_pages": len(self.cache),
            "cache_file": str(self.cache_file),
            "ttl_seconds": self.cache_ttl_sec,
        }

    @staticmethod
    def format_pypi_summary(info: Dict[str, Any]) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| PYPI PACKAGE METADATA (STAGE 82)                                     |")
        lines.append("+----------------------------------------------------------------------+")
        if "error" in info:
            lines.append(f"| Error: {info['error'][:64]:<64} |")
            lines.append("+----------------------------------------------------------------------+")
            return "\n".join(lines)
        pkg = str(info.get("name", "unknown"))[:25]
        ver = str(info.get("version", "unknown"))[:25]
        lines.append(f"| Package: {pkg:<25} | Version: {ver:<27} |")
        summary = str(info.get("summary", ""))[:60]
        lines.append(f"| Summary: {summary:<60} |")
        author = str(info.get("author", ""))[:25]
        license_str = str(info.get("license", ""))[:25]
        lines.append(f"| Author:  {author:<25} | License: {license_str:<27} |")
        py_req = str(info.get("requires_python", ""))[:60]
        if py_req:
            lines.append(f"| Python:  {py_req:<60} |")
        hp = str(info.get("home_page", ""))[:60]
        if hp:
            lines.append(f"| Homepage:{hp:<60} |")
        reqs = info.get("requires_dist", [])
        if reqs:
            lines.append("+----------------------------------------------------------------------+")
            lines.append("| Dependencies:                                                        |")
            for r in reqs[:6]:
                clean_r = str(r)[:65]
                lines.append(f"|  * {clean_r:<65} |")
        lines.append("+----------------------------------------------------------------------+")
        return "\n".join(lines)

    @staticmethod
    def format_code_blocks_summary(url: str, code_blocks: List[str]) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| EXTRACTED CODE BLOCKS (STAGE 82)                                     |")
        lines.append(f"| Source: {url[:60]:<60} |")
        lines.append("+----------------------------------------------------------------------+")
        if not code_blocks:
            lines.append("| No formatted code blocks found on this page.                         |")
            lines.append("+----------------------------------------------------------------------+")
            return "\n".join(lines)

        for i, block in enumerate(code_blocks[:5], start=1):
            bl_lines = block.splitlines()
            count_str = f"{len(bl_lines)} lines"
            lines.append(f"| [Block {i}] ({count_str:<12}):                                        |")
            for bl in bl_lines[:15]:
                clean_bl = bl[:66]
                lines.append(f"|   {clean_bl:<66} |")
            if len(bl_lines) > 15:
                lines.append(f"|   ... [{len(bl_lines) - 15} more lines]                                       |")
            lines.append("+ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -+")
        lines[-1] = "+----------------------------------------------------------------------+"
        return "\n".join(lines)

