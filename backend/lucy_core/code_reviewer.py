"""
backend/lucy_core/code_reviewer.py
Stage 77: Autonomous Git Branch & Code Review Companion
(Local PR Diff & Semantic Changelog Engine)

Performs deterministic, local code review on workspace diffs, spots potential
regressions, detects credential leaks or debug artifacts, synthesizes conventional
commit messages, and produces clean semantic changelogs for sovereign terminal mode.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

STAGE: int = 77

# Sensitive pattern regexes
SECRET_PATTERNS = [
    re.compile(r"""(?i)(?:api_key|secret_key|auth_token|password|bearer|private_key)\s*[:=]\s*["'][a-zA-Z0-9_\-\.]{8,}["']"""),
    re.compile(r"""(?i)(?:AKIA[0-9A-Z]{16})"""),  # AWS access key format
    re.compile(r"""(?i)ghp_[a-zA-Z0-9]{36}"""),   # GitHub personal access token
]

DEBUG_PATTERNS = [
    re.compile(r"^\s*print\s*\(\s*['\"]DEBUG:?"),
    re.compile(r"^\s*console\.log\s*\("),
    re.compile(r"^\s*import pdb;?\s*pdb\.set_trace\(\)"),
    re.compile(r"^\s*breakpoint\(\)"),
]


@dataclass
class ReviewFinding:
    severity: str  # "HIGH", "MEDIUM", "LOW", "INFO"
    file_path: str
    line_number: Optional[int]
    message: str
    code_snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CodeReviewReport:
    timestamp: str
    files_reviewed: List[str]
    lines_added: int
    lines_removed: int
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    findings: List[ReviewFinding] = field(default_factory=list)
    proposed_commit: str = ""
    branch: str = "main"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def format_terminal_summary(self) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| AUTONOMOUS LOCAL CODE REVIEW REPORT (STAGE 77)                       |")
        lines.append("+----------------------------------------------------------------------+")
        lines.append(f"| Branch: {self.branch:<25} | Risk Assessment: {self.risk_level:<20} |")
        lines.append(f"| Files Changed: {len(self.files_reviewed):<18} | Lines Added: +{self.lines_added:<6} Lines Removed: -{self.lines_removed:<4} |")
        lines.append("+----------------------------------------------------------------------+")
        lines.append(f"| Proposed Commit: {self.proposed_commit[:50]:<51} |")
        lines.append("+----------------------------------------------------------------------+")

        if not self.findings:
            lines.append("|  (Clean diff. No security risks, regressions, or debug leaks found.) |")
            lines.append("+----------------------------------------------------------------------+")
        else:
            lines.append("| REVIEW FINDINGS & SUGGESTIONS:                                       |")
            lines.append("+----------+----------------------------------+------------------------+")
            lines.append(f"| {'SEVERITY':<8} | {'FILE':<32} | {'ISSUE':<22} |")
            lines.append("+----------+----------------------------------+------------------------+")
            for f in self.findings[:12]:
                sev = f.severity[:8]
                fpath = f.file_path[-32:]
                msg = f.message[:22]
                lines.append(f"| {sev:<8} | {fpath:<32} | {msg:<22} |")
            if len(self.findings) > 12:
                lines.append(f"| ... and {len(self.findings) - 12} more findings.                                       |")
            lines.append("+----------+----------------------------------+------------------------+")

        return "\n".join(lines)


class AutonomousCodeReviewer:
    """
    Analyzes local uncommitted git changes (or filesystem deltas), reviews AST
    and patterns for security and regression risks, generates conventional commits,
    and produces changelogs.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        receipt_ledger: Optional[Any] = None,
    ) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.receipt_ledger = receipt_ledger

    def get_git_diff(self, cached: bool = False) -> str:
        """Retrieves unified git diff safely with timeout."""
        cmd = ["git", "diff"]
        if cached:
            cmd.append("--cached")
        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            return res.stdout or ""
        except Exception:
            return ""

    def get_git_branch(self) -> str:
        try:
            res = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            return res.stdout.strip() or "local"
        except Exception:
            return "local"

    def review_diff(self, diff_text: Optional[str] = None) -> CodeReviewReport:
        if diff_text is None:
            diff_text = self.get_git_diff()

        branch = self.get_git_branch()
        files_reviewed: List[str] = []
        findings: List[ReviewFinding] = []
        lines_added = 0
        lines_removed = 0

        current_file = ""
        current_line_no = 0

        for line in diff_text.splitlines():
            if line.startswith("diff --git"):
                parts = line.split(" ")
                if len(parts) >= 4:
                    raw_b = parts[3]
                    current_file = raw_b.replace("b/", "")
                    if current_file not in files_reviewed:
                        files_reviewed.append(current_file)
                continue

            if line.startswith("@@"):
                m = re.search(r"\+(\d+)", line)
                if m:
                    current_line_no = int(m.group(1)) - 1
                continue

            if line.startswith("+") and not line.startswith("+++"):
                lines_added += 1
                current_line_no += 1
                added_code = line[1:]

                # 1. Check for secret leaks
                for sec_pat in SECRET_PATTERNS:
                    if sec_pat.search(added_code):
                        findings.append(
                            ReviewFinding(
                                severity="HIGH",
                                file_path=current_file or "unknown",
                                line_number=current_line_no,
                                message="Potential hardcoded secret or token detected",
                                code_snippet=added_code.strip()[:60],
                            )
                        )
                        break

                # 2. Check for leftover debug statements
                for dbg_pat in DEBUG_PATTERNS:
                    if dbg_pat.search(added_code):
                        findings.append(
                            ReviewFinding(
                                severity="LOW",
                                file_path=current_file or "unknown",
                                line_number=current_line_no,
                                message="Leftover debug statement",
                                code_snippet=added_code.strip()[:60],
                            )
                        )
                        break

            elif line.startswith("-") and not line.startswith("---"):
                lines_removed += 1
                removed_code = line[1:]
                # Check if public API or important class removed
                if re.match(r"^\s*def\s+[a-zA-Z0-9_]+\s*\(", removed_code) or re.match(r"^\s*class\s+[a-zA-Z0-9_]+", removed_code):
                    findings.append(
                        ReviewFinding(
                            severity="MEDIUM",
                            file_path=current_file or "unknown",
                            line_number=current_line_no,
                            message=f"Removed public symbol: {removed_code.strip()[:40]}",
                            code_snippet=removed_code.strip(),
                        )
                    )

        # Compute risk level
        highs = sum(1 for f in findings if f.severity == "HIGH")
        mediums = sum(1 for f in findings if f.severity == "MEDIUM")
        if highs > 0:
            risk = "HIGH"
        elif mediums > 2 or lines_added + lines_removed > 400:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        proposed_commit = self.generate_commit_message(files_reviewed, lines_added, lines_removed, findings)

        report = CodeReviewReport(
            timestamp=datetime.now().isoformat(),
            files_reviewed=files_reviewed,
            lines_added=lines_added,
            lines_removed=lines_removed,
            risk_level=risk,
            findings=findings,
            proposed_commit=proposed_commit,
            branch=branch,
        )

        if self.receipt_ledger is not None:
            try:
                self.receipt_ledger.issue_receipt(
                    action_category="code_review",
                    operation="review_diff",
                    target=branch,
                    verified_outcome=f"Reviewed {len(files_reviewed)} files: +{lines_added}/-{lines_removed}, Risk: {risk}",
                )
            except Exception:
                pass

        return report

    def generate_commit_message(
        self,
        files: List[str],
        lines_added: int,
        lines_removed: int,
        findings: List[ReviewFinding],
    ) -> str:
        """
        Synthesizes a clean conventional commit based on the modified files and operations.
        """
        if not files:
            return "chore: no files modified"

        # Determine scope from main file
        primary_file = files[0]
        scope = Path(primary_file).stem.replace("test_", "")

        # Determine type
        if all("test" in f.lower() for f in files):
            c_type = "test"
            desc = f"add test coverage for {scope}"
        elif any("fix" in f.lower() or "bug" in f.lower() for f in files):
            c_type = "fix"
            desc = f"resolve issues in {scope}"
        elif any("config" in f.lower() or "spec" in f.lower() for f in files):
            c_type = "config"
            desc = f"update configuration for {scope}"
        elif any("docs" in f.lower() or f.endswith(".md") for f in files):
            c_type = "docs"
            desc = f"document updates in {scope}"
        elif lines_added > lines_removed * 2:
            c_type = "feat"
            desc = f"implement enhancements in {scope}"
        elif lines_removed > 0 and lines_added > 0:
            c_type = "refactor"
            desc = f"refactor {scope} workflow"
        else:
            c_type = "chore"
            desc = f"update {scope}"

        return f"{c_type}({scope}): {desc}"

    def generate_changelog(self, recent_commits_limit: int = 5) -> str:
        """
        Generates a semantic changelog from recent git log.
        """
        try:
            res = subprocess.run(
                ["git", "log", f"-n{recent_commits_limit}", "--pretty=format:%h|%an|%s"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            raw_lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
        except Exception:
            raw_lines = []

        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| SEMANTIC CHANGELOG (STAGE 77)                                        |")
        lines.append("+----------------------------------------------------------------------+")
        if not raw_lines:
            lines.append("|  (No recent git commits found in local repository.)                  |")
        else:
            for l in raw_lines:
                parts = l.split("|", 2)
                h = parts[0] if len(parts) > 0 else "hash"
                s = parts[2] if len(parts) > 2 else ""
                lines.append(f"| [{h[:7]}] {s[:56]:<58} |")
        lines.append("+----------------------------------------------------------------------+")
        return "\n".join(lines)
