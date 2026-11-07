"""
backend/lucy_core/test_triage.py
Stage 79: Local Test Suite Auto-Discoverer & Regression Triage Engine

Dynamically maps modified source modules to their test suites via AST import analysis,
runs targeted affected test subsets in sub-seconds, extracts failure tracebacks,
and diagnoses root causes for Lucy's sovereign CLI runtime.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

STAGE: int = 79


@dataclass
class TriageFailure:
    test_name: str
    test_file: str
    error_type: str
    error_message: str
    failing_line: Optional[str] = None
    diagnosis: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TriageRunResult:
    success: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    elapsed_sec: float
    executed_test_files: List[str] = field(default_factory=list)
    failures: List[TriageFailure] = field(default_factory=list)
    raw_output: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "elapsed_sec": self.elapsed_sec,
            "executed_test_files": self.executed_test_files,
            "failures": [f.to_dict() for f in self.failures],
            "raw_output": self.raw_output,
        }

    def format_terminal_summary(self) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| REGRESSION TEST TRIAGE REPORT (STAGE 79)                             |")
        lines.append("+----------------------------------------------------------------------+")
        status_str = "ALL PASSED" if self.success else f"FAILED ({self.failed_tests} failures)"
        lines.append(f"| Outcome: {status_str:<25} | Duration: {self.elapsed_sec:.2f}s{'':<18} |")
        lines.append(f"| Tests Ran: {self.total_tests:<23} | Passed: {self.passed_tests:<7} Failed: {self.failed_tests:<6} |")
        lines.append(f"| Target Test Suites: {len(self.executed_test_files):<46} |")
        lines.append("+----------------------------------------------------------------------+")

        if self.executed_test_files:
            lines.append("| EXECUTED TEST MODULES:                                               |")
            for tf in self.executed_test_files[:6]:
                lines.append(f"|  * {tf[-60:]:<64} |")
            if len(self.executed_test_files) > 6:
                lines.append(f"|  * ... and {len(self.executed_test_files) - 6} more suites                          |")
            lines.append("+----------------------------------------------------------------------+")

        if self.success:
            lines.append("|  (Targeted tests passed cleanly. Workspace is verified.)            |")
            lines.append("+----------------------------------------------------------------------+")
        else:
            lines.append("| DIAGNOSED FAILURES & SUGGESTED FIXES:                                |")
            lines.append("+----------------------+------------------+----------------------------+")
            lines.append(f"| {'TEST':<20} | {'ERROR TYPE':<16} | {'DIAGNOSIS / FIX':<26} |")
            lines.append("+----------------------+------------------+----------------------------+")
            for f in self.failures[:8]:
                t_str = f.test_name[:20]
                e_str = f.error_type[:16]
                d_str = f.diagnosis[:26]
                lines.append(f"| {t_str:<20} | {e_str:<16} | {d_str:<26} |")
            lines.append("+----------------------+------------------+----------------------------+")

        return "\n".join(lines)


class TestTriageEngine:
    """
    Analyzes codebase dependency graphs, discovers tests exercising touched code,
    executes targeted test suites, and diagnoses failure root causes.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        codebase_indexer: Optional[Any] = None,
        receipt_ledger: Optional[Any] = None,
    ) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.tests_dir = self.project_root / "tests"
        self.codebase_indexer = codebase_indexer
        self.receipt_ledger = receipt_ledger

        # Cache of module_name -> set of test file paths importing it
        self._import_map: Dict[str, Set[Path]] = {}
        self._last_map_build: float = 0.0

    def build_test_import_map(self, force: bool = False) -> Dict[str, Set[Path]]:
        """
        Scans all files in `tests/` using AST and builds a reverse map:
        module_name -> set of test files importing it.
        """
        now = time.time()
        if not force and self._import_map and (now - self._last_map_build) < 60.0:
            return self._import_map

        new_map: Dict[str, Set[Path]] = {}
        if not self.tests_dir.exists():
            return new_map

        for tf in self.tests_dir.glob("test_*.py"):
            try:
                content = tf.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=str(tf))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            mod = alias.name.split(".")[-1]
                            new_map.setdefault(mod, set()).add(tf)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        mod = node.module.split(".")[-1]
                        new_map.setdefault(mod, set()).add(tf)
            except Exception:
                pass

        self._import_map = new_map
        self._last_map_build = now
        return self._import_map

    def find_affected_tests(self, modified_files: List[str]) -> List[Path]:
        """
        Given a list of modified file paths, determines which test files in tests/
        need to be executed.
        """
        import_map = self.build_test_import_map()
        affected: Set[Path] = set()

        for mf in modified_files:
            p = Path(mf)
            stem = p.stem

            # 1. If modified file is already a test file
            if "test_" in stem:
                test_candidate = self.tests_dir / p.name
                if test_candidate.exists():
                    affected.add(test_candidate)
                continue

            # 2. Check AST import map
            if stem in import_map:
                affected.update(import_map[stem])

            # 3. Direct name heuristic: test_<stem>.py or test_stage*_<stem>.py
            for tf in self.tests_dir.glob("test_*.py"):
                tf_name = tf.stem
                if stem in tf_name or (stem.replace("_", "") in tf_name.replace("_", "")):
                    affected.add(tf)

        return sorted(list(affected), key=lambda p: p.name)

    def run_tests(
        self,
        test_paths: List[Path | str],
        timeout_sec: float = 45.0,
    ) -> TriageRunResult:
        """
        Executes a targeted list of test files via `unittest` runner.
        """
        if not test_paths:
            return TriageRunResult(
                success=True,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                elapsed_sec=0.0,
                executed_test_files=[],
                failures=[],
                raw_output="No matching test files found.",
            )

        str_paths = [str(Path(p).resolve()) for p in test_paths]
        # Format for unittest discovery: pass relative module paths or file paths
        cmd = [sys.executable, "-m", "unittest"]
        for sp in str_paths:
            try:
                rel = os.path.relpath(sp, str(self.project_root))
                cmd.append(rel)
            except Exception:
                cmd.append(sp)

        start_time = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max(5.0, timeout_sec),
            )
            elapsed = time.perf_counter() - start_time
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            combined = stdout + "\n" + stderr

            total, passed, failed, failures = self._parse_unittest_output(combined)
            success = (proc.returncode == 0) and (failed == 0)

            res = TriageRunResult(
                success=success,
                total_tests=total,
                passed_tests=passed,
                failed_tests=failed,
                elapsed_sec=elapsed,
                executed_test_files=[Path(p).name for p in test_paths],
                failures=failures,
                raw_output=combined,
            )

            if self.receipt_ledger is not None:
                try:
                    self.receipt_ledger.issue_receipt(
                        action_category="test_triage",
                        operation="run_targeted_tests",
                        target=",".join(res.executed_test_files[:3]),
                        verified_outcome=f"Ran {total} tests in {elapsed:.2f}s: {passed} passed, {failed} failed",
                    )
                except Exception:
                    pass

            return res

        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - start_time
            return TriageRunResult(
                success=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                elapsed_sec=elapsed,
                executed_test_files=[Path(p).name for p in test_paths],
                failures=[
                    TriageFailure(
                        test_name="TestSuiteTimeout",
                        test_file="all",
                        error_type="TimeoutExpired",
                        error_message=f"Tests timed out after {timeout_sec:.1f}s",
                        diagnosis="Possible infinite loop or hanging subprocess call.",
                    )
                ],
                raw_output=f"Execution timed out after {timeout_sec}s",
            )
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            return TriageRunResult(
                success=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                elapsed_sec=elapsed,
                executed_test_files=[Path(p).name for p in test_paths],
                failures=[
                    TriageFailure(
                        test_name="RunnerException",
                        test_file="all",
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                        diagnosis=f"Failed to launch test runner: {exc}",
                    )
                ],
                raw_output=str(exc),
            )

    def _parse_unittest_output(self, output: str) -> Tuple[int, int, int, List[TriageFailure]]:
        total = 0
        failed = 0
        passed = 0
        failures: List[TriageFailure] = []

        m_ran = re.search(r"Ran (\d+) tests? in", output)
        if m_ran:
            total = int(m_ran.group(1))

        m_failed = re.search(r"FAILED \((?:failures=(\d+))?(?:, )?(?:errors=(\d+))?\)", output)
        if m_failed:
            f_count = int(m_failed.group(1) or 0)
            e_count = int(m_failed.group(2) or 0)
            failed = f_count + e_count
        elif "OK" in output:
            failed = 0

        passed = max(0, total - failed)

        # Parse individual failure blocks: FAIL: ... or ERROR: ...
        fail_blocks = re.split(r"={70,}", output)
        for block in fail_blocks:
            m_header = re.search(r"(?:FAIL|ERROR): ([a-zA-Z0-9_]+) \(([^)]+)\)", block)
            if m_header:
                test_name = m_header.group(1)
                test_file = m_header.group(2)

                # Find the exception line: skip summary lines at the bottom of the block
                lines = [l.strip() for l in block.splitlines() if l.strip()]
                exc_line = "Failure"
                for l in reversed(lines):
                    if l.startswith(("Ran ", "FAILED", "OK", "-")):
                        continue
                    if ":" in l or "Error" in l or "Exception" in l:
                        exc_line = l
                        break

                err_type = exc_line.split(":")[0].strip() if ":" in exc_line else "Failure"
                diag = self._diagnose_error(exc_line, block)

                failures.append(
                    TriageFailure(
                        test_name=test_name,
                        test_file=test_file,
                        error_type=err_type,
                        error_message=exc_line,
                        diagnosis=diag,
                    )
                )

        return total, passed, failed, failures

    def _diagnose_error(self, err_msg: str, block: str) -> str:
        if "AssertionError" in err_msg:
            return "Value mismatch: verify expected vs actual outputs."
        elif "AttributeError" in err_msg:
            return "Missing attribute: verify method/variable was initialized or spelled correctly."
        elif "TypeError" in err_msg:
            return "Type or argument count mismatch: check function signature."
        elif "ModuleNotFoundError" in err_msg or "ImportError" in err_msg:
            return "Import failure: verify module path in PYTHONPATH."
        elif "FileNotFoundError" in err_msg:
            return "Path error: ensure test file or resource exists on disk."
        return "Review traceback for error origin."

    def triage_uncommitted(self) -> TriageRunResult:
        """
        Detects uncommitted files via git diff (or workspace deltas) and runs affected tests.
        """
        modified: List[str] = []
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=1.5,
            )
            for line in res.stdout.splitlines():
                if line.strip():
                    parts = line.strip().split(" ", 1)
                    if len(parts) > 1:
                        modified.append(parts[1].strip())
        except Exception:
            pass

        if not modified:
            # Fall back to testing Stage 78/77 recent tests
            recent_tests = list(self.tests_dir.glob("test_stage7*.py"))
            return self.run_tests(recent_tests)

        affected = self.find_affected_tests(modified)
        if not affected:
            # If no specific tests affected, test recent stage
            affected = list(self.tests_dir.glob("test_stage7*.py"))
        return self.run_tests(affected)
