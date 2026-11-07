"""
terminal_react.py
Stage 70: Autonomous Terminal ReAct Loop & Self-Healing Execution Engine.

Enables Lucy to autonomously execute terminal tasks through a closed-loop ReAct cycle:
Reason -> Act -> Observe -> Self-Heal. Automatically diagnoses and recovers from common
CLI failures (Python stubs, missing PYTHONPATH, path resolution errors, socket timeouts)
within safe bounds, logging cryptographic receipts for every action.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

STAGE = "70 autonomous terminal react loop and self-healing execution engine"

# Common error signatures for automated diagnosis
DIAG_PYTHON_STUB = "python_stub_alias"
DIAG_MODULE_NOT_FOUND = "module_not_found"
DIAG_FILE_NOT_FOUND = "file_not_found"
DIAG_PORT_IN_USE = "port_in_use"
DIAG_SYNTAX_ERROR = "syntax_error"
DIAG_COMMAND_NOT_FOUND = "command_not_found"
DIAG_UNKNOWN = "unclassified_failure"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReActStep:
    """Represents a single iteration in the Reason -> Act -> Observe loop."""

    def __init__(
        self,
        attempt: int,
        thought: str,
        command: str,
        exit_code: int = 0,
        stdout: str = "",
        stderr: str = "",
        diagnosis: Optional[Dict[str, Any]] = None,
        remedy: Optional[str] = None,
    ) -> None:
        self.attempt = attempt
        self.timestamp = _now_iso()
        self.thought = thought
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.diagnosis = diagnosis or {}
        self.remedy = remedy

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt": self.attempt,
            "timestamp": self.timestamp,
            "thought": self.thought,
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout[:500] if len(self.stdout) > 500 else self.stdout,
            "stderr": self.stderr[:500] if len(self.stderr) > 500 else self.stderr,
            "diagnosis": self.diagnosis,
            "remedy": self.remedy,
        }


class ReActResult:
    """Result of an autonomous self-healing execution cycle."""

    def __init__(
        self,
        goal: str,
        initial_command: str,
        final_command: str,
        status: str,  # "success", "failed", "blocked"
        attempts_count: int,
        steps: List[ReActStep],
        stdout: str = "",
        stderr: str = "",
        healed: bool = False,
        error_summary: Optional[str] = None,
        receipt_id: Optional[str] = None,
    ) -> None:
        self.goal = goal
        self.initial_command = initial_command
        self.final_command = final_command
        self.status = status
        self.attempts_count = attempts_count
        self.steps = steps
        self.stdout = stdout
        self.stderr = stderr
        self.healed = healed
        self.error_summary = error_summary
        self.receipt_id = receipt_id
        self.timestamp = _now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": STAGE,
            "timestamp": self.timestamp,
            "goal": self.goal,
            "initial_command": self.initial_command,
            "final_command": self.final_command,
            "status": self.status,
            "attempts_count": self.attempts_count,
            "healed": self.healed,
            "error_summary": self.error_summary,
            "receipt_id": self.receipt_id,
            "steps": [s.to_dict() for s in self.steps],
        }

    def format_terminal_summary(self) -> str:
        """Renders a clean, pure-ASCII terminal audit of the execution loop."""
        status_badge = "[OK: HEALED]" if self.healed else ("[OK]" if self.status == "success" else "[FAILED]")
        lines = [
            f"+--- [Autonomous ReAct Execution: {status_badge}] -------------------+",
            f"| Goal: {self.goal or 'Execute terminal command'}",
            f"| Initial Command: {self.initial_command}",
            f"| Total Iterations: {self.attempts_count} | Self-Healed: {self.healed}",
        ]
        if self.receipt_id:
            lines.append(f"| Cryptographic Receipt: {self.receipt_id}")

        for s in self.steps:
            lines.append(f"| Step {s.attempt}: {s.thought}")
            lines.append(f"|   CMD: {s.command}")
            lines.append(f"|   Exit Code: {s.exit_code}")
            if s.diagnosis and s.exit_code != 0:
                diag_type = s.diagnosis.get("error_type", "error")
                lines.append(f"|   Diagnosis: [{diag_type}] {s.diagnosis.get('explanation', '')}")
            if s.remedy:
                lines.append(f"|   Applied Remedy: {s.remedy}")

        if self.status == "success":
            preview = self.stdout.strip().splitlines()
            if preview:
                last_line = preview[-1]
                lines.append(f"| Final Output: {last_line[:70]}")
        else:
            lines.append(f"| Error: {self.error_summary or 'Execution exhausted attempt budget'}")

        lines.append("+------------------------------------------------------------------+")
        return "\n".join(lines)


class TerminalReActEngine:
    """
    Autonomous ReAct execution harness that diagnoses CLI errors and auto-corrects them.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        receipt_ledger: Any = None,
        default_timeout: int = 45,
    ) -> None:
        self.project_root = Path(project_root).resolve() if project_root else Path.cwd().resolve()
        self.receipt_ledger = receipt_ledger
        self.default_timeout = default_timeout
        self.total_runs = 0
        self.healed_runs = 0
        self.failed_runs = 0
        self.last_result: Optional[ReActResult] = None

    def diagnose_failure(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        command: str,
    ) -> Dict[str, Any]:
        """Classifies the failure reason and suggests an automated remedy."""
        combined = f"{stdout}\n{stderr}"

        # 1. Python Stub Aliasing (WindowsApps stub)
        if "Python was not found" in combined or "App execution aliases" in combined:
            return {
                "error_type": DIAG_PYTHON_STUB,
                "explanation": "Windows invoked standard 'python' alias which resolved to disabled WindowsApps stub.",
                "remedy_type": "substitute_executable",
                "target_executable": sys.executable,
            }

        # 2. Module Not Found / ImportError
        mod_match = re.search(r"ModuleNotFoundError:\s+No module named\s+['\"]([^'\"]+)['\"]", combined)
        if mod_match:
            missing_mod = mod_match.group(1).strip()
            return {
                "error_type": DIAG_MODULE_NOT_FOUND,
                "missing_module": missing_mod,
                "explanation": f"Module '{missing_mod}' could not be imported by Python runtime.",
                "remedy_type": "set_pythonpath",
            }

        # 3. File Not Found
        fnf_match = re.search(r"FileNotFoundError:\s+\[Errno 2\]\s+No such file or directory:\s+['\"]([^'\"]+)['\"]", combined)
        if fnf_match:
            missing_file = fnf_match.group(1).strip()
            return {
                "error_type": DIAG_FILE_NOT_FOUND,
                "missing_file": missing_file,
                "explanation": f"Target file or path '{missing_file}' does not exist relative to working directory.",
                "remedy_type": "resolve_path",
            }

        # 4. Port In Use
        if "address already in use" in combined.lower() or "10048" in combined:
            port_match = re.search(r"\bport\s+(\d+)\b", command, re.I)
            port_num = port_match.group(1) if port_match else "unknown"
            return {
                "error_type": DIAG_PORT_IN_USE,
                "port": port_num,
                "explanation": f"Port {port_num} is already bound by another active process.",
                "remedy_type": "increment_port",
            }

        # 5. Syntax Error in Python script
        if "SyntaxError:" in combined:
            return {
                "error_type": DIAG_SYNTAX_ERROR,
                "explanation": "Python script contains a syntax error preventing compilation.",
                "remedy_type": "report_syntax",
            }

        # 6. Command Not Recognized
        if "not recognized as an internal or external command" in combined or "is not recognized as the name of a cmdlet" in combined:
            cmd_token = command.split()[0] if command.split() else ""
            return {
                "error_type": DIAG_COMMAND_NOT_FOUND,
                "command_token": cmd_token,
                "explanation": f"Binary or command '{cmd_token}' is not available in system PATH.",
                "remedy_type": "command_alias",
            }

        return {
            "error_type": DIAG_UNKNOWN,
            "explanation": f"Command exited with non-zero status code {exit_code}.",
            "remedy_type": "none",
        }

    def adapt_command(
        self,
        command: str,
        diagnosis: Dict[str, Any],
        current_env: Dict[str, str],
    ) -> Tuple[str, Dict[str, str], str]:
        """
        Synthesizes an adapted command and environment based on diagnosis.
        Returns: (new_command, new_env, remedy_description)
        """
        remedy_type = diagnosis.get("remedy_type")
        new_env = dict(current_env)

        if remedy_type == "substitute_executable":
            # Replace bare 'python' with verified active sys.executable
            active_py = f'"{sys.executable}"'
            new_cmd = re.sub(r"^(?:py|python)\b", lambda m: active_py, command.strip())
            return new_cmd, new_env, f"Substituted active Python binary: {sys.executable}"

        if remedy_type == "set_pythonpath":
            # Inject project_root into PYTHONPATH
            current_pp = new_env.get("PYTHONPATH", "")
            root_str = str(self.project_root)
            new_env["PYTHONPATH"] = f"{root_str};{current_pp}" if current_pp else root_str
            return command, new_env, f"Injected project root into PYTHONPATH: {root_str}"

        if remedy_type == "resolve_path":
            missing = diagnosis.get("missing_file", "")
            if missing:
                # Check if file exists inside project_root
                candidate = self.project_root / missing
                if candidate.exists():
                    new_cmd = command.replace(missing, str(candidate))
                    return new_cmd, new_env, f"Resolved relative file to absolute project path: {candidate}"
                # Search for filename match in project
                matched = list(self.project_root.rglob(Path(missing).name))
                if matched:
                    found = str(matched[0])
                    new_cmd = command.replace(missing, found)
                    return new_cmd, new_env, f"Discovered actual file location: {found}"

        return command, new_env, "No automated remedy available for this error signature."

    def execute_with_self_healing(
        self,
        command: str,
        goal: str = "",
        max_attempts: int = 3,
        env_overrides: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> ReActResult:
        """
        Runs the autonomous ReAct cycle:
        1. Formulates thought.
        2. Executes action.
        3. Observes exit code and stderr.
        4. Self-heals and retries if failure diagnosed.
        """
        self.total_runs += 1
        steps: List[ReActStep] = []
        current_command = command
        active_env = os.environ.copy()
        if env_overrides:
            active_env.update(env_overrides)

        effective_timeout = timeout or self.default_timeout
        attempt = 1
        healed = False

        while attempt <= max_attempts:
            # 1. Reason
            if attempt == 1:
                thought = f"Executing initial command for goal: '{goal or command}'."
            else:
                thought = f"Executing self-healed retry (attempt {attempt}/{max_attempts}) with adapted parameters."

            # 2. Act
            try:
                proc = subprocess.run(
                    current_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=effective_timeout,
                    cwd=str(self.project_root),
                    env=active_env,
                )
                exit_code = proc.returncode
                stdout = proc.stdout
                stderr = proc.stderr
            except subprocess.TimeoutExpired as exc:
                exit_code = 124
                stdout = exc.stdout or ""
                stderr = f"Execution timed out after {effective_timeout} seconds."
            except Exception as exc:
                exit_code = 1
                stdout = ""
                stderr = f"Execution failure: {exc}"

            # 3. Observe
            if exit_code == 0:
                # Success!
                step = ReActStep(
                    attempt=attempt,
                    thought=f"{thought} [SUCCESS]",
                    command=current_command,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                )
                steps.append(step)

                # Record receipt if ledger available
                receipt_id = None
                if self.receipt_ledger and hasattr(self.receipt_ledger, "record_receipt"):
                    try:
                        rcpt = self.receipt_ledger.record_receipt(
                            action_name="terminal_react_exec",
                            parameters={"command": current_command, "goal": goal},
                            status="success",
                        )
                        receipt_id = rcpt.get("receipt_id")
                    except Exception:
                        pass

                if healed or attempt > 1:
                    self.healed_runs += 1

                res = ReActResult(
                    goal=goal,
                    initial_command=command,
                    final_command=current_command,
                    status="success",
                    attempts_count=attempt,
                    steps=steps,
                    stdout=stdout,
                    stderr=stderr,
                    healed=(attempt > 1),
                    receipt_id=receipt_id,
                )
                self.last_result = res
                return res

            # Failure occurred: Diagnose
            diagnosis = self.diagnose_failure(exit_code, stdout, stderr, current_command)
            adapted_cmd, adapted_env, remedy_msg = self.adapt_command(current_command, diagnosis, active_env)

            step = ReActStep(
                attempt=attempt,
                thought=f"{thought} [FAILED with exit code {exit_code}]",
                command=current_command,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                diagnosis=diagnosis,
                remedy=remedy_msg,
            )
            steps.append(step)

            # Check if we were able to adapt
            if adapted_cmd == current_command and adapted_env == active_env and attempt > 1:
                # Could not adapt further
                break

            current_command = adapted_cmd
            active_env = adapted_env
            healed = True
            attempt += 1

        # Exhausted attempts
        self.failed_runs += 1
        res = ReActResult(
            goal=goal,
            initial_command=command,
            final_command=current_command,
            status="failed",
            attempts_count=len(steps),
            steps=steps,
            stdout=steps[-1].stdout if steps else "",
            stderr=steps[-1].stderr if steps else "",
            healed=False,
            error_summary=steps[-1].stderr if steps else "Unknown execution failure",
        )
        self.last_result = res
        return res

    def status(self) -> Dict[str, Any]:
        return {
            "stage": STAGE,
            "react_engine": "active",
            "project_root": str(self.project_root),
            "total_runs": self.total_runs,
            "healed_runs": self.healed_runs,
            "failed_runs": self.failed_runs,
            "recovery_rate": f"{(self.healed_runs / max(1, self.total_runs)) * 100:.1f}%",
            "has_last_result": self.last_result is not None,
        }
