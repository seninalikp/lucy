"""
fact_state_verifier.py
Stage 37 / Stage 61 Upgraded = Sentence-Scoped Deterministic Fact & Runtime State Verifier.

Fixes the whole-text false-positive bug:
1. Evaluates affirmative file creation/existence claims strictly sentence-by-sentence
   so a verb in paragraph 1 ("I saved your memory") never triggers a false positive
   on a filename mentioned in paragraph 3 ("You can check config.json").
2. Verifies physical existence on disk across project_root, promoted_tools/, and staging/.
3. Verifies security patterns (eval, exec, shell=True, hardcoded keys).
4. Verifies runtime state claims (task counts, memory nodes) against ground truth.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


STAGE = "37 fact state verifier"

AFFIRMATIVE_CLAIM_PATTERNS = [
    r"\b(?:created|wrote|written|saved|generated|updated|promoted|stored\s+in|file\s+at)\s+(?:the\s+file\s+|a\s+file\s+)?[`'\"]?([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z]{1,8})[`'\"]?",
    r"[`'\"]?([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z]{1,8})[`'\"]?\s+(?:was\s+created|has\s+been\s+saved|has\s+been\s+created|is\s+saved\s+on\s+disk|exists\s+on\s+disk|is\s+ready\s+at)",
]

VALID_FILE_EXTENSIONS = {
    "py", "json", "jsonl", "md", "txt", "sh", "bat", "ps1", "html", "css",
    "js", "ts", "yaml", "yml", "toml", "ini", "cfg", "csv", "sql", "xml", "log",
}

HYPOTHETICAL_MARKERS = (
    "for example",
    "e.g.",
    "such as",
    "you can create",
    "you could create",
    "if you create",
    "would be named",
    "imaginary",
    "is nonexistent",
    "are nonexistent",
    "is non-existent",
    "cannot claim",
    "do not exist",
    "does not exist",
)

DANGEROUS_PATTERNS = [
    (r"\beval\s*\(", "Dangerous dynamic code execution (eval)"),
    (r"\bexec\s*\(", "Dangerous arbitrary code execution (exec)"),
    (r"\bos\.system\s*\(", "Uncontrolled shell command execution (os.system)"),
    (r"subprocess\.Popen\([^)]*shell\s*=\s*True", "Shell injection risk (shell=True)"),
    (r"(?:password|api[_-]?key|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]", "Hardcoded plain-text credential detected"),
]


class FactStateVerifier:
    """Deterministic ground-truth verifier that validates agent assertions against disk state."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root).resolve()

    def extract_claimed_paths(self, text: str) -> list[str]:
        """
        Extracts file paths strictly from sentences that make an affirmative creation or
        existence claim, preventing cross-sentence false positives.
        """
        claimed: list[str] = []
        sentences = re.split(r"(?<=[.!?])\s+|\n+", str(text or ""))

        for sent in sentences:
            sent_lower = sent.lower().strip()
            if not sent_lower:
                continue
            if any(marker in sent_lower for marker in HYPOTHETICAL_MARKERS):
                continue

            for pattern in AFFIRMATIVE_CLAIM_PATTERNS:
                matches = re.findall(pattern, sent, re.IGNORECASE)
                for m in matches:
                    clean = m.strip().strip("`'\".,;:()")
                    ext = clean.rsplit(".", 1)[-1].lower() if "." in clean else ""
                    if (
                        "://" not in clean
                        and not clean.startswith(("http", "www.", "."))
                        and ext in VALID_FILE_EXTENSIONS
                        and len(clean) > 3
                    ):
                        if clean not in claimed:
                            claimed.append(clean)

        return claimed
    def verify_claim(self, claim_text: str, custom_root: Path | None = None) -> dict[str, Any]:
        root = Path(custom_root).resolve() if custom_root else self.project_root
        claimed_paths = self.extract_claimed_paths(claim_text)

        if not claimed_paths:
            return {
                "stage": STAGE,
                "verified": True,
                "claims_detected": 0,
                "verified_paths": [],
                "missing_paths": [],
                "hallucination_detected": False,
                "badge": "[ELIE: VERIFIED | No Unbacked Disk Claims]",
                "summary": "No unverified file creation or existence claims were made.",
            }

        verified_paths: list[str] = []
        missing_paths: list[str] = []

        for p_str in claimed_paths:
            normalized = p_str.replace("\\", "/")
            target = root / normalized
            promoted_target = root / "promoted_tools" / Path(normalized).name
            staging_target = root / "data" / "lucy" / "sandbox" / "staging" / Path(normalized).name

            if os.path.isabs(p_str) and os.path.exists(p_str):
                verified_paths.append(p_str)
            elif target.exists() or promoted_target.exists() or staging_target.exists():
                verified_paths.append(p_str)
            else:
                missing_paths.append(p_str)

        hallucination = len(missing_paths) > 0
        if hallucination:
            badge = f"[ELIE: HALLUCINATION_INTERCEPTED | Missing on disk: {', '.join(missing_paths)}]"
            summary = (
                f"Claim REJECTED. The following file(s) were claimed as created/existing "
                f"but do NOT exist on disk: {', '.join(missing_paths)}"
            )
        else:
            badge = f"[ELIE: VERIFIED | Disk State Matches Claim | Real Files: {len(verified_paths)}]"
            summary = f"Claim APPROVED. All {len(verified_paths)} claimed file(s) physically exist on disk."

        return {
            "stage": STAGE,
            "verified": not hallucination,
            "claims_detected": len(claimed_paths),
            "verified_paths": verified_paths,
            "missing_paths": missing_paths,
            "hallucination_detected": hallucination,
            "badge": badge,
            "summary": summary,
        }

    def verify_runtime_state_claims(self, text: str, runtime: Any = None) -> dict[str, Any]:
        """
        Verifies numerical claims about runtime state (e.g. task counts, memory counts)
        against ground truth runtime state to catch hallucinated metrics.
        """
        if not runtime:
            return {"verified": True, "claims": [], "discrepancies": []}

        discrepancies: list[str] = []
        claims: list[dict[str, Any]] = []

        # Check for open task count claims
        task_match = re.search(r"(\d+)\s+(?:open\s+tasks?|tasks?\s+(?:remaining|pending|open))", str(text or ""), re.IGNORECASE)
        if task_match and hasattr(runtime, "project_summary"):
            claimed_count = int(task_match.group(1))
            try:
                proj = runtime.project_summary()
                real_count = len(proj.get("open_tasks", []))
                claims.append({"type": "open_tasks", "claimed": claimed_count, "actual": real_count})
                if claimed_count != real_count:
                    discrepancies.append(f"Claimed {claimed_count} open tasks, but ground truth is {real_count}")
            except Exception:
                pass

        # Check for memory count claims
        mem_match = re.search(r"(\d+)\s+(?:memories|facts|memory\s+items)", str(text or ""), re.IGNORECASE)
        if mem_match and hasattr(runtime, "memory_graph"):
            claimed_mem = int(mem_match.group(1))
            try:
                st = runtime.memory_graph.status()
                real_mem = st.get("active_nodes", 0)
                claims.append({"type": "active_memories", "claimed": claimed_mem, "actual": real_mem})
                if claimed_mem != real_mem:
                    discrepancies.append(f"Claimed {claimed_mem} memories, but ground truth is {real_mem}")
            except Exception:
                pass

        return {
            "stage": STAGE,
            "verified": len(discrepancies) == 0,
            "claims": claims,
            "discrepancies": discrepancies,
            "hallucination_detected": len(discrepancies) > 0,
        }

    def guard_response(self, response_text: str, custom_root: Path | None = None, runtime: Any = None) -> dict[str, Any]:
        report = self.verify_claim(response_text, custom_root=custom_root)
        if runtime:
            state_report = self.verify_runtime_state_claims(response_text, runtime=runtime)
            report["runtime_state_verification"] = state_report
            if state_report.get("hallucination_detected"):
                report["hallucination_detected"] = True
                report["verified"] = False
                disc_str = "; ".join(state_report["discrepancies"])
                report["summary"] += f" State Claim Mismatch: {disc_str}."

        if report["hallucination_detected"]:
            corrected = (
                f"{response_text.strip()}\n\n"
                f"[WARN] {report['badge']}\n"
                f"Ground-Truth Correction: {report['summary']}"
            )
            report["guarded_text"] = corrected
        else:
            report["guarded_text"] = response_text
        return report

    def elie_security_review(self, code_text: str) -> dict[str, Any]:
        issues = []
        for pattern, desc in DANGEROUS_PATTERNS:
            if re.search(pattern, code_text, re.IGNORECASE):
                issues.append(desc)

        passed = len(issues) == 0
        return {
            "stage": STAGE,
            "security_review": "passed" if passed else "flagged",
            "safe": passed,
            "issues_count": len(issues),
            "issues": issues,
            "badge": "[ELIE: SECURITY_APPROVED]" if passed else f"[ELIE: SECURITY_FLAGGED | {len(issues)} issues]",
        }

    def status(self) -> dict[str, Any]:
        return {
            "stage": STAGE,
            "fact_state_verifier": "active",
            "root_path": str(self.project_root),
            "verification_mode": "physical_disk_state_only",
            "scope": "sentence_scoped_affirmative",
            "anti_hallucination_gate": "enforced",
            "lora_queue_protection": "active",
        }
