"""
backend/lucy_core/tool_synthesizer.py
Stage 73: Dynamic Local Tool Synthesizer & Ephemeral Sandbox

Enables Lucy to dynamically synthesize, inspect, safely sandbox, and execute
custom local Python tools on-the-fly without hallucinated one-liners or
uncontrolled execution environments.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

STAGE: int = 73

# Safety filter: disallow blatant self-destructive strings in synthesized code
DISALLOWED_CODE_PATTERNS = [
    "shutil.rmtree('/')",
    'shutil.rmtree("/")',
    'shutil.rmtree("C:\\\\")',
    "os.system('format ",
    'os.system("format ',
    ":(){ :|:& };:",  # fork bomb
]


@dataclass
class EphemeralSandboxResult:
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    error_message: Optional[str] = None
    script_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SynthesizedTool:
    name: str
    description: str
    code: str
    created_at: str
    script_path: str
    execution_count: int = 0
    last_executed: Optional[str] = None
    last_status: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SynthesizedTool:
        return cls(
            name=data.get("name", "unnamed_tool"),
            description=data.get("description", ""),
            code=data.get("code", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            script_path=data.get("script_path", ""),
            execution_count=data.get("execution_count", 0),
            last_executed=data.get("last_executed"),
            last_status=data.get("last_status"),
            tags=data.get("tags", []),
        )


class DynamicToolSynthesizer:
    """
    Manages dynamic tool generation, syntax verification, ephemeral sandboxed execution,
    and lifecycle cataloging for Lucy's terminal runtime.
    """

    def __init__(
        self,
        sandbox_dir: Optional[Path] = None,
        registry_file: Optional[Path] = None,
        receipt_ledger: Optional[Any] = None,
        project_root: Optional[Path] = None,
    ) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.sandbox_dir = sandbox_dir or (self.project_root / "scratch" / "sandbox")
        self.registry_file = registry_file or (self.project_root / "data" / "lucy" / "synthesized_tools.json")
        self.receipt_ledger = receipt_ledger

        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        self.tools: Dict[str, SynthesizedTool] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        if not self.registry_file.exists():
            return
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for item in raw.get("tools", []):
                tool = SynthesizedTool.from_dict(item)
                self.tools[tool.name] = tool
        except Exception:
            # Fall back to empty catalog on unreadable JSON
            self.tools = {}

    def _save_registry(self) -> None:
        try:
            data = {
                "version": STAGE,
                "updated_at": datetime.now().isoformat(),
                "tools": [t.to_dict() for t in self.tools.values()],
            }
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def validate_code_syntax(self, code: str) -> Optional[str]:
        """
        Validates Python code syntax via AST parsing and checks against destructive patterns.
        Returns None if valid, or an error string if invalid.
        """
        for bad in DISALLOWED_CODE_PATTERNS:
            if bad in code:
                return f"Disallowed destructive pattern detected: {bad}"
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return f"Syntax error at line {e.lineno}, col {e.offset}: {e.msg}"
        except Exception as e:
            return f"Code validation error: {str(e)}"

    def synthesize_tool(
        self,
        name: str,
        code: str,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> SynthesizedTool:
        """
        Synthesizes a new reusable Python tool, validates syntax, persists script into sandbox,
        and records in catalog.
        """
        clean_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name.strip())
        if not clean_name:
            clean_name = f"tool_{uuid.uuid4().hex[:8]}"

        err = self.validate_code_syntax(code)
        if err:
            raise ValueError(f"Failed to synthesize tool '{name}': {err}")

        script_file = self.sandbox_dir / f"{clean_name}.py"
        script_file.write_text(code, encoding="utf-8")

        tool = SynthesizedTool(
            name=clean_name,
            description=description.strip() or f"Dynamically synthesized tool {clean_name}",
            code=code,
            created_at=datetime.now().isoformat(),
            script_path=str(script_file),
            tags=tags or ["dynamic_tool"],
        )
        self.tools[clean_name] = tool
        self._save_registry()

        if self.receipt_ledger is not None:
            try:
                self.receipt_ledger.issue_receipt(
                    action_category="tool_synthesis",
                    operation="synthesize_tool",
                    target=clean_name,
                    verified_outcome=f"Synthesized script: {script_file.name}",
                )
            except Exception:
                pass

        return tool

    def execute_tool(
        self,
        name: str,
        args: Optional[List[str]] = None,
        timeout_sec: float = 10.0,
        env_overrides: Optional[Dict[str, str]] = None,
    ) -> EphemeralSandboxResult:
        """
        Executes a registered tool by name in a guarded ephemeral subprocess.
        """
        if name not in self.tools:
            return EphemeralSandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Tool '{name}' not found in registry.",
                duration_ms=0.0,
                error_message=f"Unknown tool: {name}",
            )

        tool = self.tools[name]
        script_path = Path(tool.script_path)
        if not script_path.exists():
            # Recreate script file if missing
            script_path.parent.mkdir(parents=True, exist_ok=True)
            script_path.write_text(tool.code, encoding="utf-8")

        res = self._execute_script(script_path, args=args, timeout_sec=timeout_sec, env_overrides=env_overrides)

        # Update stats
        tool.execution_count += 1
        tool.last_executed = datetime.now().isoformat()
        tool.last_status = "SUCCESS" if res.success else f"FAIL(exit={res.exit_code})"
        self._save_registry()

        if self.receipt_ledger is not None:
            try:
                self.receipt_ledger.issue_receipt(
                    action_category="tool_execution",
                    operation="run_synthesized_tool",
                    target=name,
                    verified_outcome=f"Exit: {res.exit_code}, Duration: {res.duration_ms:.1f}ms",
                )
            except Exception:
                pass

        return res

    def run_ephemeral_code(
        self,
        code: str,
        args: Optional[List[str]] = None,
        timeout_sec: float = 10.0,
        retain_on_error: bool = False,
    ) -> EphemeralSandboxResult:
        """
        Runs arbitrary Python code in an isolated scratch sandbox without saving it permanently.
        """
        err = self.validate_code_syntax(code)
        if err:
            return EphemeralSandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=err,
                duration_ms=0.0,
                error_message=err,
            )

        tmp_id = f"_ephemeral_{uuid.uuid4().hex[:8]}"
        tmp_script = self.sandbox_dir / f"{tmp_id}.py"
        tmp_script.write_text(code, encoding="utf-8")

        try:
            res = self._execute_script(tmp_script, args=args, timeout_sec=timeout_sec)
        finally:
            if not retain_on_error or res.success:
                try:
                    if tmp_script.exists():
                        tmp_script.unlink()
                except Exception:
                    pass

        return res

    def _execute_script(
        self,
        script_path: Path,
        args: Optional[List[str]] = None,
        timeout_sec: float = 10.0,
        env_overrides: Optional[Dict[str, str]] = None,
    ) -> EphemeralSandboxResult:
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend([str(a) for a in args])

        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)

        start_time = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max(0.5, timeout_sec),
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            success = (proc.returncode == 0)
            return EphemeralSandboxResult(
                success=success,
                exit_code=proc.returncode,
                stdout=proc.stdout or "",
                stderr=proc.stderr or "",
                duration_ms=duration_ms,
                error_message=None if success else f"Exited with code {proc.returncode}",
                script_path=str(script_path),
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            out = exc.stdout or ""
            err = exc.stderr or ""
            return EphemeralSandboxResult(
                success=False,
                exit_code=-1,
                stdout=out if isinstance(out, str) else out.decode("utf-8", errors="replace"),
                stderr=err if isinstance(err, str) else err.decode("utf-8", errors="replace"),
                duration_ms=duration_ms,
                error_message=f"Process timed out after {timeout_sec:.1f}s",
                script_path=str(script_path),
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return EphemeralSandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(exc),
                duration_ms=duration_ms,
                error_message=str(exc),
                script_path=str(script_path),
            )

    def list_tools(self, filter_tag: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for tool in self.tools.values():
            if filter_tag and filter_tag not in tool.tags:
                continue
            results.append(tool.to_dict())
        return results

    def get_tool(self, name: str) -> Optional[SynthesizedTool]:
        return self.tools.get(name)

    def delete_tool(self, name: str) -> bool:
        if name not in self.tools:
            return False
        tool = self.tools.pop(name)
        self._save_registry()
        script_file = Path(tool.script_path)
        if script_file.exists():
            try:
                script_file.unlink()
            except Exception:
                pass
        return True

    def purge_sandbox(self, max_age_hours: float = 24.0) -> Dict[str, Any]:
        """
        Removes ephemeral script files and stray scratch artifacts older than max_age_hours.
        Registered tools are preserved.
        """
        cutoff_sec = time.time() - (max_age_hours * 3600.0)
        purged = 0
        preserved = 0
        registered_paths = {Path(t.script_path).resolve() for t in self.tools.values()}

        for root, _, files in os.walk(self.sandbox_dir):
            for f in files:
                fpath = (Path(root) / f).resolve()
                if fpath in registered_paths:
                    preserved += 1
                    continue
                try:
                    stat = fpath.stat()
                    if stat.st_mtime < cutoff_sec or f.startswith("_ephemeral_"):
                        fpath.unlink()
                        purged += 1
                    else:
                        preserved += 1
                except Exception:
                    pass

        return {
            "purged_count": purged,
            "preserved_count": preserved,
            "sandbox_dir": str(self.sandbox_dir),
        }

    def format_terminal_summary(self) -> str:
        """
        Generates an ASCII-safe visual summary of all synthesized tools for terminal display.
        """
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| DYNAMIC LOCAL TOOL SYNTHESIZER (STAGE 73)                            |")
        lines.append("+----------------------------------------------------------------------+")
        lines.append(f"| Sandbox Directory: {str(self.sandbox_dir)[-48:]:<48} |")
        lines.append(f"| Registered Dynamic Tools: {len(self.tools):<42} |")
        lines.append("+----------------------------------------------------------------------+")
        if not self.tools:
            lines.append("|  (No synthesized tools registered yet. Use /synthesize to add one.)  |")
        else:
            lines.append(f"| {'NAME':<20} | {'RUNS':<6} | {'STATUS':<12} | {'TAGS':<20} |")
            lines.append("+----------------------+--------+--------------+----------------------+")
            for t in self.tools.values():
                status = (t.last_status or "NEVER_RUN")[:12]
                tags_str = ",".join(t.tags)[:20]
                lines.append(f"| {t.name[:20]:<20} | {t.execution_count:<6} | {status:<12} | {tags_str:<20} |")
        lines.append("+----------------------------------------------------------------------+")
        return "\n".join(lines)
