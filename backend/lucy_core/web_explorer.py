"""
backend/lucy_core/web_explorer.py
Stage 81: Sovereign Terminal Web Explorer & Headless Search Engine

Provides pure-terminal, headless web search capabilities (DuckDuckGo HTML / Lite)
with query privacy firewall, response caching, and structured ASCII results for Lucy.
No browser launch, no Web UI, 100% sovereign CLI execution.
"""

from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

STAGE: int = 81

# Privacy / Security Firewall: reject queries that accidentally expose local paths or credentials
BLOCKED_QUERY_PATTERNS = [
    re.compile(r"""[A-Za-z]:\\[\w\s\\.-]+"""),  # Windows absolute paths
    re.compile(r"""/(?:home|Users|etc|var|root)/[\w\s/.-]+"""),  # Unix absolute paths
    re.compile(r"""(?i)(?:api_key|secret_key|password|bearer|ghp_|AKIA)[=:]\S+"""),  # Secrets
]


@dataclass
class SearchResultItem:
    title: str
    url: str
    snippet: str
    source: str = "web"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SearchResultItem:
        return cls(
            title=data.get("title", ""),
            url=data.get("url", ""),
            snippet=data.get("snippet", ""),
            source=data.get("source", "web"),
        )


@dataclass
class WebSearchResponse:
    query: str
    total_results: int
    results: List[SearchResultItem] = field(default_factory=list)
    elapsed_ms: float = 0.0
    from_cache: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "total_results": self.total_results,
            "elapsed_ms": self.elapsed_ms,
            "from_cache": self.from_cache,
            "error": self.error,
            "results": [r.to_dict() for r in self.results],
        }

    def format_terminal_summary(self) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| SOVEREIGN WEB SEARCH RESULTS (STAGE 81)                              |")
        lines.append("+----------------------------------------------------------------------+")
        q_str = self.query[:45]
        cache_tag = " (CACHED)" if self.from_cache else ""
        lines.append(f"| Query: {q_str:<45} | Time: {self.elapsed_ms:.1f}ms{cache_tag:<8} |")
        lines.append(f"| Results Found: {self.total_results:<51} |")
        lines.append("+----------------------------------------------------------------------+")

        if self.error:
            lines.append(f"| Error: {self.error[:64]:<64} |")
            lines.append("+----------------------------------------------------------------------+")
            return "\n".join(lines)

        if not self.results:
            lines.append("|  (No matching search results returned from web endpoint.)          |")
            lines.append("+----------------------------------------------------------------------+")
            return "\n".join(lines)

        for i, item in enumerate(self.results[:5], start=1):
            t = item.title[:62]
            u = item.url[:62]
            s = item.snippet[:62]
            lines.append(f"| [{i}] {t:<64} |")
            lines.append(f"|     URL: {u:<60} |")
            lines.append(f"|     {s:<64} |")
            lines.append("+----------------------------------------------------------------------+")

        return "\n".join(lines)


class SovereignWebExplorer:
    """
    Executes fast, headless web searches, enforces outbound privacy guards,
    and caches responses locally to eliminate redundant network overhead.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        cache_file: Optional[Path] = None,
        receipt_ledger: Optional[Any] = None,
        cache_ttl_sec: float = 7200.0,
    ) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.cache_file = cache_file or (self.project_root / "data" / "lucy" / "cache" / "web_search_cache.json")
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

    def check_query_safety(self, query: str) -> Optional[str]:
        """
        Validates that outbound search queries do not leak sensitive local paths or credentials.
        """
        for pat in BLOCKED_QUERY_PATTERNS:
            if pat.search(query):
                return "Blocked: query contains sensitive local file path or credential pattern."
        return None

    def search(
        self,
        query: str,
        max_results: int = 5,
        timeout_sec: float = 3.5,
        bypass_cache: bool = False,
    ) -> WebSearchResponse:
        """
        Searches the web via headless DuckDuckGo HTML / Lite endpoints.
        """
        cleaned_query = query.strip()
        if not cleaned_query:
            return WebSearchResponse(query="", total_results=0, error="Empty query.")

        # 1. Privacy guard check
        guard_err = self.check_query_safety(cleaned_query)
        if guard_err:
            return WebSearchResponse(query=cleaned_query, total_results=0, error=guard_err)

        # 2. Check local cache
        cache_key = cleaned_query.lower()
        now = time.time()
        if not bypass_cache and cache_key in self.cache:
            entry = self.cache[cache_key]
            if (now - entry.get("cached_at", 0)) < self.cache_ttl_sec:
                raw_items = entry.get("results", [])
                items = [SearchResultItem.from_dict(it) for it in raw_items[:max_results]]
                return WebSearchResponse(
                    query=cleaned_query,
                    total_results=len(items),
                    results=items,
                    elapsed_ms=0.5,
                    from_cache=True,
                )

        # 3. Headless network query
        start_time = time.perf_counter()
        results, err = self._fetch_duckduckgo(cleaned_query, max_results=max_results, timeout_sec=timeout_sec)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if not err and results:
            self.cache[cache_key] = {
                "cached_at": now,
                "results": [r.to_dict() for r in results],
            }
            self._save_cache()

            if self.receipt_ledger is not None:
                try:
                    self.receipt_ledger.issue_receipt(
                        action_category="web_search",
                        operation="search",
                        target=cleaned_query[:40],
                        verified_outcome=f"Retrieved {len(results)} search results in {elapsed_ms:.1f}ms",
                    )
                except Exception:
                    pass

        return WebSearchResponse(
            query=cleaned_query,
            total_results=len(results),
            results=results,
            elapsed_ms=elapsed_ms,
            from_cache=False,
            error=err,
        )

    def _fetch_duckduckgo(
        self,
        query: str,
        max_results: int = 5,
        timeout_sec: float = 3.5,
    ) -> Tuple[List[SearchResultItem], Optional[str]]:
        """
        Headless query to DuckDuckGo HTML endpoint using POST.
        """
        data = urllib.parse.urlencode({"q": query}).encode("utf-8")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            req = urllib.request.Request("https://html.duckduckgo.com/html/", data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                body = resp.read().decode("utf-8", errors="replace")

            results = self._parse_html_results(body, max_results=max_results)
            return results, None
        except urllib.error.URLError as exc:
            return [], f"Network error connecting to search provider: {exc.reason}"
        except Exception as exc:
            return [], f"Search failed: {str(exc)}"

    def _parse_html_results(self, body: str, max_results: int = 5) -> List[SearchResultItem]:
        """
        Parses title, link, and snippets from DuckDuckGo HTML structure.
        """
        items: List[SearchResultItem] = []
        # Pattern for title links: <a class="result__a" href="...">Title</a>
        title_links = list(re.finditer(r"""<a[^>]*class=['"]result__a['"][^>]*href=['"]([^'"]+)['"][^>]*>(.*?)</a>""", body, re.S | re.I))
        # Pattern for snippets: <a class="result__snippet" ...>Snippet</a>
        snippets = list(re.finditer(r"""<a[^>]*class=['"]result__snippet['"][^>]*>(.*?)</a>""", body, re.S | re.I))

        # Fallback to lite structure if result__a not present
        if not title_links:
            title_links = list(re.finditer(r"""class=['"]result-link['"][^>]*href=['"]([^'"]+)['"][^>]*>([^<]+)</a>""", body, re.I))
            snippets = list(re.finditer(r"""class=['"]result-snippet['"][^>]*>([^<]+)</td>""", body, re.I))

        for i in range(min(len(title_links), max_results)):
            raw_url = title_links[i].group(1).strip()
            # Clean DDG redirect URL if present
            if "uddg=" in raw_url:
                try:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                    raw_url = parsed.get("uddg", [raw_url])[0]
                except Exception:
                    pass

            raw_title = html.unescape(re.sub(r"<[^<]+?>", "", title_links[i].group(2)).strip())
            snippet_text = ""
            if i < len(snippets):
                snippet_text = html.unescape(re.sub(r"<[^<]+?>", "", snippets[i].group(1)).strip())

            items.append(
                SearchResultItem(
                    title=raw_title,
                    url=raw_url,
                    snippet=snippet_text,
                    source="duckduckgo",
                )
            )

        return items

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
            "cached_queries": len(self.cache),
            "cache_file": str(self.cache_file),
            "ttl_seconds": self.cache_ttl_sec,
        }
