"""
backend/lucy_core/web_verifier.py
Stage 83: Web-Grounded Cross-Verification & Fact-Checking RAG

Provides multi-source cross-verification, anti-hallucination fact checking,
epistemic confidence calibration, and live evidence snippet extraction
for Lucy's sovereign terminal CLI.
"""

from __future__ import annotations

import ast
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.lucy_core.web_explorer import SovereignWebExplorer
from backend.lucy_core.web_reader import SovereignWebReader

STAGE: int = 83

# Stop words to ignore during lexical overlap calculation
STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "both", "through", "about", "for", "is", "of", "while", "during",
    "to", "from", "in", "out", "on", "off", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "can", "will", "just", "should",
    "now", "be", "been", "being", "have", "has", "had", "do", "does", "did"
}

NEGATION_TOKENS: Set[str] = {
    "not", "no", "never", "cannot", "n't", "false", "untrue", "neither",
    "nor", "disproven", "refuted", "unsupported", "debunked", "incorrect"
}

AFFIRMATION_TOKENS: Set[str] = {
    "is", "was", "are", "were", "confirmed", "verified", "true", "correct",
    "added", "removed", "supported", "released", "deprecated", "replaced"
}


@dataclass
class GroundedClaim:
    claim: str
    verification_status: str  # "SUPPORTED", "REFUTED", "AMBIGUOUS", "UNVERIFIED"
    confidence: float  # 0.0 to 1.0
    primary_sources: List[str] = field(default_factory=list)
    supporting_snippets: List[str] = field(default_factory=list)
    contradicting_snippets: List[str] = field(default_factory=list)
    reasoning: str = ""
    elapsed_ms: float = 0.0
    from_cache: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "verification_status": self.verification_status,
            "confidence": round(self.confidence, 4),
            "primary_sources": self.primary_sources,
            "supporting_snippets": self.supporting_snippets,
            "contradicting_snippets": self.contradicting_snippets,
            "reasoning": self.reasoning,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "from_cache": self.from_cache,
        }

    def format_terminal_summary(self) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| WEB-GROUNDED FACT CHECKER (STAGE 83)                                 |")
        lines.append("+----------------------------------------------------------------------+")
        claim_clean = self.claim[:60]
        lines.append(f"| Claim: {claim_clean:<61} |")
        status_str = f"[{self.verification_status}]"
        conf_pct = f"{self.confidence * 100.0:.1f}%"
        cache_tag = " (CACHED)" if self.from_cache else ""
        lines.append(f"| Status: {status_str:<20} | Confidence: {conf_pct:<10}{cache_tag:<14} |")
        time_str = f"{self.elapsed_ms:.1f}ms"
        src_cnt = f"{len(self.primary_sources)} source(s)"
        lines.append(f"| Sources Examined: {src_cnt:<14} | Time: {time_str:<27} |")
        lines.append("+----------------------------------------------------------------------+")

        if self.primary_sources:
            lines.append("| PRIMARY SOURCES:                                                     |")
            for src in self.primary_sources[:3]:
                lines.append(f"|  * {src[:65]:<65} |")
            lines.append("+----------------------------------------------------------------------+")

        if self.supporting_snippets:
            lines.append("| SUPPORTING EVIDENCE SNIPPETS:                                        |")
            for snip in self.supporting_snippets[:2]:
                wrapped = [snip[i : i + 65] for i in range(0, min(len(snip), 130), 65)]
                for w in wrapped:
                    lines.append(f"|  \"{w:<65}\" |")
            lines.append("+----------------------------------------------------------------------+")

        if self.contradicting_snippets:
            lines.append("| CONTRADICTING EVIDENCE SNIPPETS:                                     |")
            for snip in self.contradicting_snippets[:2]:
                wrapped = [snip[i : i + 65] for i in range(0, min(len(snip), 130), 65)]
                for w in wrapped:
                    lines.append(f"|  \"{w:<65}\" |")
            lines.append("+----------------------------------------------------------------------+")

        if self.reasoning:
            lines.append("| EPISTEMIC REASONING:                                                 |")
            reason_wrapped = [self.reasoning[i : i + 66] for i in range(0, min(len(self.reasoning), 198), 66)]
            for r in reason_wrapped:
                lines.append(f"|  {r:<66} |")
            lines.append("+----------------------------------------------------------------------+")

        return "\n".join(lines)


class WebFactChecker:
    """
    Sovereign Fact-Checking RAG engine that cross-references claims across
    multiple independent web sources to prevent LLM hallucinations.
    """

    def __init__(
        self,
        web_explorer: Optional[SovereignWebExplorer] = None,
        web_reader: Optional[SovereignWebReader] = None,
        cache_file: Optional[Path] = None,
        receipt_ledger: Optional[Any] = None,
        cache_ttl_sec: float = 86400.0,
        max_sources: int = 3,
    ) -> None:
        self.web_explorer = web_explorer or SovereignWebExplorer()
        self.web_reader = web_reader or SovereignWebReader()
        self.receipt_ledger = receipt_ledger
        self.cache_ttl_sec = cache_ttl_sec
        self.max_sources = max(1, min(5, max_sources))

        project_root = Path(__file__).resolve().parent.parent.parent
        self.cache_file = cache_file or (project_root / "data" / "lucy" / "cache" / "fact_check_cache.json")
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

    def _tokenize_claim(self, claim: str) -> List[str]:
        words = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", claim.lower())
        return [w for w in words if w not in STOP_WORDS]

    def _extract_passages(self, text: str) -> List[str]:
        # Split on sentence boundaries and newlines
        raw_passages = re.split(r"(?<=[.!?])\s+|\n+", text)
        clean = []
        for p in raw_passages:
            cleaned = re.sub(r"\s+", " ", p).strip()
            if len(cleaned) >= 25 and not cleaned.startswith(("#", "*", "|", "+")):
                clean.append(cleaned)
        return clean

    def _score_passage(self, passage: str, claim_tokens: List[str]) -> Tuple[float, bool]:
        """
        Computes relevance score and determines whether passage expresses negation.
        """
        if not claim_tokens:
            return 0.0, False

        p_lower = passage.lower()
        matched_tokens = sum(1 for token in claim_tokens if token in p_lower)
        coverage = matched_tokens / len(claim_tokens)

        # Check for negation words
        has_negation = any(re.search(rf"\b{re.escape(neg)}\b", p_lower) for neg in NEGATION_TOKENS)

        return coverage, has_negation

    def verify_claim(
        self,
        claim: str,
        bypass_cache: bool = False,
        timeout_per_source: float = 3.5,
    ) -> GroundedClaim:
        """
        Searches web, reads multiple candidate pages, and grounds the claim with evidence.
        """
        clean_claim = claim.strip()
        if not clean_claim:
            return GroundedClaim(
                claim="",
                verification_status="UNVERIFIED",
                confidence=0.0,
                reasoning="Empty claim provided.",
            )

        # 1. Check Cache
        cache_key = clean_claim.lower()
        now = time.time()
        if not bypass_cache and cache_key in self.cache:
            entry = self.cache[cache_key]
            if (now - entry.get("cached_at", 0)) < self.cache_ttl_sec:
                data = entry.get("data", {})
                return GroundedClaim(
                    claim=data.get("claim", clean_claim),
                    verification_status=data.get("verification_status", "UNVERIFIED"),
                    confidence=data.get("confidence", 0.0),
                    primary_sources=data.get("primary_sources", []),
                    supporting_snippets=data.get("supporting_snippets", []),
                    contradicting_snippets=data.get("contradicting_snippets", []),
                    reasoning=data.get("reasoning", ""),
                    elapsed_ms=0.5,
                    from_cache=True,
                )

        start_time = time.perf_counter()
        claim_tokens = self._tokenize_claim(clean_claim)

        # 2. Search Web
        search_resp = self.web_explorer.search(clean_claim, max_results=self.max_sources)
        search_items = getattr(search_resp, "results", getattr(search_resp, "items", []))
        urls_to_examine = [item.url for item in search_items if item.url.startswith(("http://", "https://"))]

        primary_sources: List[str] = []
        supporting_snippets: List[str] = []
        contradicting_snippets: List[str] = []

        # 3. Read Pages and Extract Evidence Passages
        for url in urls_to_examine[: self.max_sources]:
            page = self.web_reader.fetch_url(url, timeout_sec=timeout_per_source)
            if page.error or not page.text_content:
                continue

            primary_sources.append(url)
            passages = self._extract_passages(page.text_content)

            for p in passages:
                score, has_neg = self._score_passage(p, claim_tokens)
                if score >= 0.50:
                    if has_neg:
                        if p not in contradicting_snippets:
                            contradicting_snippets.append(p)
                    else:
                        if p not in supporting_snippets:
                            supporting_snippets.append(p)

        # 4. If no supporting snippets from page bodies, check search snippets as fallback
        if not supporting_snippets and not contradicting_snippets:
            for item in search_items:
                if item.snippet:
                    score, has_neg = self._score_passage(item.snippet, claim_tokens)
                    if score >= 0.40:
                        if item.url not in primary_sources:
                            primary_sources.append(item.url)
                        if has_neg:
                            contradicting_snippets.append(item.snippet)
                        else:
                            supporting_snippets.append(item.snippet)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # 5. Determine Verification Status & Calibrate Confidence
        if supporting_snippets and not contradicting_snippets:
            status = "SUPPORTED"
            base_conf = 0.70
            bonus = min(0.25, len(primary_sources) * 0.08 + len(supporting_snippets) * 0.04)
            confidence = min(0.96, base_conf + bonus)
            reasoning = f"Corroborated by {len(primary_sources)} source(s) with {len(supporting_snippets)} supporting passage(s)."
        elif contradicting_snippets and not supporting_snippets:
            status = "REFUTED"
            base_conf = 0.68
            bonus = min(0.24, len(primary_sources) * 0.08 + len(contradicting_snippets) * 0.04)
            confidence = min(0.94, base_conf + bonus)
            reasoning = f"Contradicted by {len(contradicting_snippets)} passage(s) across {len(primary_sources)} source(s)."
        elif supporting_snippets and contradicting_snippets:
            status = "AMBIGUOUS"
            confidence = 0.50
            reasoning = f"Found conflicting evidence: {len(supporting_snippets)} supporting vs {len(contradicting_snippets)} contradicting passage(s)."
        else:
            status = "UNVERIFIED"
            confidence = 0.15
            reasoning = "Insufficient public evidence found in searched documents to verify claim."

        result = GroundedClaim(
            claim=clean_claim,
            verification_status=status,
            confidence=confidence,
            primary_sources=primary_sources,
            supporting_snippets=supporting_snippets[:4],
            contradicting_snippets=contradicting_snippets[:4],
            reasoning=reasoning,
            elapsed_ms=elapsed_ms,
            from_cache=False,
        )

        # 6. Save to cache
        self.cache[cache_key] = {
            "cached_at": now,
            "data": result.to_dict(),
        }
        self._save_cache()

        # 7. Issue Execution Receipt
        if self.receipt_ledger is not None:
            try:
                self.receipt_ledger.issue_receipt(
                    action_category="fact_check",
                    operation="verify_claim",
                    target=clean_claim[:40],
                    verified_outcome=f"Status: {status} (conf: {confidence:.2f}, {len(primary_sources)} sources)",
                )
            except Exception:
                pass

        return result

    def verify_code_snippet(self, code: str) -> Dict[str, Any]:
        """
        Validates code syntax using AST, discovers imported external packages,
        and checks external libraries against PyPI metadata.
        """
        clean_code = code.strip()
        if not clean_code:
            return {"valid_syntax": False, "error": "Empty code snippet provided."}

        # 1. AST Syntax Check
        try:
            tree = ast.parse(clean_code)
            syntax_valid = True
            syntax_error = None
        except SyntaxError as e:
            return {
                "valid_syntax": False,
                "error": f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}",
                "packages_checked": {},
            }

        # 2. Extract Imports
        imported_modules: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module.split(".")[0])

        # Filter standard library modules to focus on third-party packages
        stdlib_sample = {
            "sys", "os", "re", "json", "time", "math", "random", "pathlib",
            "datetime", "urllib", "typing", "collections", "itertools",
            "functools", "shutil", "tempfile", "unittest", "dataclasses",
            "ast", "sqlite3", "csv", "hashlib", "subprocess", "logging"
        }
        external_pkgs = [m for m in imported_modules if m not in stdlib_sample]

        # 3. Check third-party packages on PyPI
        checked_packages = {}
        for pkg in external_pkgs[:4]:
            pypi_info = self.web_reader.fetch_pypi_package(pkg)
            checked_packages[pkg] = {
                "exists": "error" not in pypi_info,
                "latest_version": pypi_info.get("version", "unknown"),
                "summary": pypi_info.get("summary", ""),
                "requires_python": pypi_info.get("requires_python", ""),
            }

        return {
            "valid_syntax": syntax_valid,
            "error": syntax_error,
            "imported_modules": sorted(list(imported_modules)),
            "packages_checked": checked_packages,
        }

    def format_code_verification_summary(self, verification_res: Dict[str, Any]) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| CODE SNIPPET VERIFICATION REPORT (STAGE 83)                          |")
        lines.append("+----------------------------------------------------------------------+")
        syn_ok = verification_res.get("valid_syntax", False)
        syn_status = "VALID [OK]" if syn_ok else "INVALID [SYNTAX ERROR]"
        lines.append(f"| AST Syntax: {syn_status:<55} |")

        err = verification_res.get("error")
        if err:
            lines.append(f"| Error: {err[:63]:<63} |")

        mods = verification_res.get("imported_modules", [])
        mods_str = ", ".join(mods) if mods else "None"
        lines.append(f"| Imported Modules: {mods_str[:49]:<49} |")
        lines.append("+----------------------------------------------------------------------+")

        pkgs = verification_res.get("packages_checked", {})
        if pkgs:
            lines.append("| PYPI PACKAGE GROUNDING:                                              |")
            for pkg, info in pkgs.items():
                ex_str = "[PyPI OK]" if info.get("exists") else "[PyPI Missing]"
                ver_str = f"v{info.get('latest_version', '?')}"
                lines.append(f"|  * {pkg:<15} {ex_str:<15} {ver_str:<32} |")
            lines.append("+----------------------------------------------------------------------+")

        return "\n".join(lines)

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
            "cached_claims": len(self.cache),
            "max_sources": self.max_sources,
            "cache_file": str(self.cache_file),
            "ttl_seconds": self.cache_ttl_sec,
        }
