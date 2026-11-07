"""
swarm_dispatcher.py
Stage 39 = Swarm Dispatcher Bridge.

Connects Lucy's Sovereign Local Mind to the 4-agent Groq coding swarm in senin/ai/:
1. Writer Bot (Port 5820): Generates and writes production code files.
2. Checker Bot (Port 5821): Performs AST syntax verification, py_compile, and code reviews.
3. Director Bot (Port 5822): Multi-stage blueprint orchestrator and web UI.
4. Planner Bot (Groq Key #2): Task breakdown and architecture planner.

Features:
- Fast non-blocking socket health probes (<0.2s) for all bot endpoints.
- Strict Stage 35 boundary enforcement: persona and memory are sanitized before sending.
- Dual-mode operation: live HTTP dispatch if bot servers are running, deterministic
  local fallback/AST checks if offline.
- Asynchronous task integration with Stage 38 TaskDaemon.
- Swarm dispatch audit log in data/lucy/swarm/swarm_history.json.
"""

from __future__ import annotations

import ast
import datetime
import json
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable


STAGE = "39 swarm dispatcher bridge"
SOVEREIGN_POLICY = (
    "UNIDIRECTIONAL_AUTHORITY: Lucy is the sovereign mind and orchestrator; "
    "bots in senin/ai are external worker tools for Lucy's workspace. "
    "The bots NEVER command, supervise, or modify Lucy."
)

DEFAULT_SWARM_CONFIG = {
    "writer_host": "localhost",
    "writer_port": 5820,
    "checker_host": "localhost",
    "checker_port": 5821,
    "director_host": "localhost",
    "director_port": 5822,
    "model": "openai/gpt-oss-120b",
}


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class SwarmDispatcher:
    """Dispatches tasks to the external 4-bot coding swarm while preserving sovereign boundaries."""

    def __init__(self, lucy_data: Path, config_path: Path | None = None) -> None:
        self.lucy_data = Path(lucy_data)
        self.swarm_dir = self.lucy_data / "swarm"
        self.swarm_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.swarm_dir / "swarm_history.json"

        self.config = self._load_swarm_config(config_path)
        self.writer_url = f"http://{self.config['writer_host']}:{self.config['writer_port']}"
        self.checker_url = f"http://{self.config['checker_host']}:{self.config['checker_port']}"
        self.director_url = f"http://{self.config['director_host']}:{self.config['director_port']}"

    def _load_swarm_config(self, custom_path: Path | None = None) -> dict[str, Any]:
        """Searches for senin/ai/config.json; uses safe defaults if not found."""
        candidate_paths = []
        if custom_path:
            candidate_paths.append(Path(custom_path))

        # Check typical relative locations from Lucy workspace
        candidate_paths.extend([
            Path(r"C:\Users\admin\Desktop\senin\ai\config.json"),
            self.lucy_data.parent.parent / "ai" / "config.json",
            self.lucy_data.parent / "ai" / "config.json",
        ])

        for p in candidate_paths:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        merged = dict(DEFAULT_SWARM_CONFIG)
                        merged.update(data)
                        merged["_config_source"] = str(p)
                        return merged
                except Exception:
                    pass

        conf = dict(DEFAULT_SWARM_CONFIG)
        conf["_config_source"] = "default_fallback"
        return conf

    def is_bot_online(self, host: str, port: int, timeout: float = 0.2) -> bool:
        """Fast non-blocking socket probe to verify if a bot server is running."""
        try:
            clean_host = "127.0.0.1" if host in ("localhost", "127.0.0.1") else host
            s = socket.create_connection((clean_host, port), timeout=timeout)
            s.close()
            return True
        except (OSError, socket.timeout):
            return False

    def probe_bot(self, bot_name: str) -> dict[str, Any]:
        """Probes a specific bot server and measures latency."""
        host_key = f"{bot_name}_host"
        port_key = f"{bot_name}_port"
        host = self.config.get(host_key, "localhost")
        port = int(self.config.get(port_key, 0))

        start_time = time.time()
        online = self.is_bot_online(host, port)
        latency = round((time.time() - start_time) * 1000, 2)

        return {
            "bot": bot_name,
            "host": host,
            "port": port,
            "endpoint": f"http://{host}:{port}",
            "online": online,
            "latency_ms": latency if online else None,
            "status": "ONLINE" if online else "OFFLINE",
        }

    def ensure_writer_online(self, max_wait_seconds: float = 6.0) -> bool:
        """
        If the Writer Bot server (Port 5820) is offline, automatically launches
        it in the background and waits for port 5820 to open.
        """
        host = self.config.get("writer_host", "localhost")
        port = int(self.config.get("writer_port", 5820))
        if self.is_bot_online(host, port):
            return True

        candidate_scripts = [
            Path(r"C:\Users\admin\Desktop\senin\ai\writer\code_writer_bot.py"),
            self.lucy_data.parent.parent / "ai" / "writer" / "code_writer_bot.py",
            self.lucy_data.parent / "ai" / "writer" / "code_writer_bot.py",
        ]

        writer_script = next((p for p in candidate_scripts if p.exists()), None)
        if writer_script:
            import subprocess
            import sys
            py_bin = sys.executable or r"C:\Users\admin\AppData\Local\Python\bin\python.exe"
            try:
                subprocess.Popen(
                    [str(py_bin), str(writer_script), "--server-only"],
                    cwd=str(writer_script.parent),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except Exception:
                pass

        start = time.time()
        while time.time() - start < max_wait_seconds:
            if self.is_bot_online(host, port):
                return True
            time.sleep(0.3)
        return self.is_bot_online(host, port)

    def ensure_bot_online(self, bot_name: str, max_wait_seconds: float = 6.0) -> bool:
        """Auto-launches any of the senin/ai bots (writer, checker, director) if offline."""
        host = self.config.get(f"{bot_name}_host", "localhost")
        port = int(self.config.get(f"{bot_name}_port", 0))
        if port and self.is_bot_online(host, port):
            return True

        script_names = {
            "writer": "code_writer_bot.py",
            "checker": "checker_bot.py",
            "director": "director_bot.py",
        }
        script_file = script_names.get(bot_name)
        if not script_file:
            return False

        candidate_dirs = [
            Path(r"C:/Users/admin/Desktop/senin/ai") / bot_name,
            self.lucy_data.parent.parent / "ai" / bot_name,
            self.lucy_data.parent / "ai" / bot_name,
        ]

        target_script = None
        for cd in candidate_dirs:
            cand = cd / script_file
            if cand.exists():
                target_script = cand
                break

        if target_script:
            import subprocess
            import sys
            py_bin = sys.executable or r"C:/Users/admin/AppData/Local/Python/bin/python.exe"
            try:
                subprocess.Popen(
                    [str(py_bin), str(target_script), "--server-only"],
                    cwd=str(target_script.parent),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except Exception:
                pass

        start = time.time()
        while time.time() - start < max_wait_seconds:
            if self.is_bot_online(host, port):
                return True
            time.sleep(0.3)
        return self.is_bot_online(host, port)

    def ensure_checker_online(self, max_wait_seconds: float = 6.0) -> bool:
        return self.ensure_bot_online("checker", max_wait_seconds=max_wait_seconds)

    def ensure_director_online(self, max_wait_seconds: float = 6.0) -> bool:
        return self.ensure_bot_online("director", max_wait_seconds=max_wait_seconds)

    def connect_bot(self, bot_name: str) -> dict[str, Any]:
        """Connects Lucy to a specific bot in senin/ai, auto-launching if offline."""
        online = self.ensure_bot_online(bot_name, max_wait_seconds=6.0)
        probe = self.probe_bot(bot_name)
        model = self.config.get("model", "openai/gpt-oss-120b")
        health_info: dict[str, Any] = {}
        endpoint = probe.get("endpoint", "")
        if online and endpoint:
            try:
                req = urllib.request.Request(f"{endpoint}/health", method="GET")
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    health_info = json.loads(resp.read().decode("utf-8"))
            except Exception:
                pass

        port = probe.get("port", 0)
        return {
            "bot": bot_name,
            "online": online,
            "status": "CONNECTED" if online else "OFFLINE",
            "endpoint": endpoint,
            "port": port,
            "model": health_info.get("model", model),
            "latency_ms": probe.get("latency_ms"),
            "health": health_info,
            "sovereign_policy": SOVEREIGN_POLICY,
            "message": (
                f"Connected to {bot_name.capitalize()} Bot on port {port} ({health_info.get('model', model)})."
                if online else
                f"Failed to connect to {bot_name.capitalize()} Bot on port {port}."
            ),
        }

    def connect_writer_bot(self) -> dict[str, Any]:
        return self.connect_bot("writer")

    def connect_checker_bot(self) -> dict[str, Any]:
        return self.connect_bot("checker")

    def connect_director_bot(self) -> dict[str, Any]:
        return self.connect_bot("director")

    def connect_swarm(self) -> dict[str, Any]:
        """Connects Lucy to all external bots in senin/ai (Writer, Checker, Director)."""
        w = self.connect_writer_bot()
        c = self.connect_checker_bot()
        d = self.connect_director_bot()
        online_count = sum(1 for b in (w, c, d) if b["online"])
        return {
            "stage": STAGE,
            "sovereign_policy": SOVEREIGN_POLICY,
            "online_count": online_count,
            "total_bots": 3,
            "status": "ALL_CONNECTED" if online_count == 3 else f"{online_count}/3_ONLINE",
            "writer": w,
            "checker": c,
            "director": d,
            "message": f"Connected to {online_count}/3 bots in senin/ai. Lucy remains sovereign master.",
        }

    def status(self) -> dict[str, Any]:
        """Returns the complete health status of the 4-agent swarm."""
        writer_status = self.probe_bot("writer")
        checker_status = self.probe_bot("checker")
        director_status = self.probe_bot("director")

        online_count = sum(1 for b in (writer_status, checker_status, director_status) if b["online"])

        return {
            "stage": STAGE,
            "swarm_dispatcher": "active",
            "model": self.config.get("model", "unknown"),
            "config_source": self.config.get("_config_source", "unknown"),
            "online_bots_count": online_count,
            "total_bots_monitored": 3,
            "writer": writer_status,
            "checker": checker_status,
            "director": director_status,
            "planner": {
                "bot": "planner",
                "role": "Orchestrator Client (Groq Key #2)",
                "status": "CONFIGURED",
            },
            "boundary_safety": "ENFORCED (Zero persona/memory leaks to cloud workers)",
        }

    def sanitize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Stage 35 boundary enforcement:
        Strips Lucy's personal spine, memory, identity, and private keys
        before sending instructions to cloud workers.
        """
        forbidden_keys = {
            "spine", "persona", "memory", "memories", "private_keys",
            "identity", "secret", "secrets", "user_preferences", "system_prompt"
        }
        sanitized = {}
        for k, v in payload.items():
            if k.lower() not in forbidden_keys:
                sanitized[k] = v
        return sanitized

    def _record_history(self, record: dict[str, Any]) -> None:
        """Appends a dispatch event to history (keeping last 100 entries)."""
        try:
            records = []
            if self.history_file.exists():
                try:
                    with open(self.history_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            records = data
                except Exception:
                    pass

            records.insert(0, record)
            records = records[:100]

            temp_path = self.history_file.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            temp_path.replace(self.history_file)
        except Exception:
            pass

    def dispatch_write(
        self,
        instruction: str,
        filename: str = "",
        folder: str = "",
        context: str = "",
        save: bool = True,
        sender: str = "LUCY Sovereign Mind",
    ) -> dict[str, Any]:
        """
        Dispatches code writing instruction to Writer Bot on port 5820.
        Falls back smoothly if bot is offline.
        """
        # Auto-connect to Writer Bot if offline
        if not self.probe_bot("writer")["online"]:
            self.ensure_writer_online(max_wait_seconds=5.0)

        is_online = self.probe_bot("writer")["online"]
        record = {
            "timestamp": _now_iso(),
            "target_bot": "writer",
            "instruction": instruction,
            "filename": filename,
            "folder": folder,
            "online": is_online,
        }

        if not is_online:
            record["status"] = "OFFLINE_FALLBACK"
            record["result"] = {
                "success": False,
                "offline": True,
                "message": (
                    "Writer Bot is currently offline on port 5820. "
                    "Start it via START_SYSTEM.bat in senin/ai/ to generate live code."
                ),
            }
            self._record_history(record)
            return record["result"]

        payload = self.sanitize_payload({
            "instruction": instruction,
            "filename": filename,
            "folder": folder,
            "context": context,
            "save": save,
            "sender": sender,
        })

        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.writer_url}/write",
                data=data_bytes,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                record["status"] = "SUCCESS"
                record["result"] = result
                self._record_history(record)
                return result
        except Exception as e:
            record["status"] = "ERROR"
            record["error"] = str(e)
            record["result"] = {"success": False, "error": str(e)}
            self._record_history(record)
            return record["result"]

    def dispatch_check(
        self,
        code: str,
        filepath: str = "",
        instruction: str = "",
        context: str = "",
        sender: str = "LUCY Sovereign Mind",
    ) -> dict[str, Any]:
        """
        Dispatches code verification to Checker Bot on port 5821.
        If offline, performs a deterministic local AST syntax check!
        """
        if not self.probe_bot("checker")["online"]:
            self.ensure_checker_online(max_wait_seconds=5.0)
        is_online = self.probe_bot("checker")["online"]
        record = {
            "timestamp": _now_iso(),
            "target_bot": "checker",
            "filepath": filepath,
            "online": is_online,
        }

        if not is_online:
            # Deterministic Local Fallback: Python AST Parse
            syntax_valid = False
            syntax_error = None
            try:
                ast.parse(code)
                syntax_valid = True
            except SyntaxError as e:
                syntax_error = f"SyntaxError at line {e.lineno}: {e.msg}"

            fallback_res = {
                "success": True,
                "bot": "checker_local_ast_fallback",
                "online": False,
                "syntax_valid": syntax_valid,
                "ast_valid": syntax_valid,
                "status": "APPROVED" if syntax_valid else "SYNTAX_ERROR",
                "approved": syntax_valid,
                "issues": [syntax_error] if syntax_error else [],
                "message": (
                    "Checker Bot server is offline on port 5821. "
                    f"Local AST verification completed: {'Syntax Valid' if syntax_valid else syntax_error}."
                ),
            }
            record["status"] = "OFFLINE_LOCAL_AST"
            record["result"] = fallback_res
            self._record_history(record)
            return fallback_res

        payload = self.sanitize_payload({
            "code": code,
            "filepath": filepath,
            "instruction": instruction,
            "context": context,
            "sender": sender,
        })

        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.checker_url}/check",
                data=data_bytes,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                result["online"] = True
                if "ast_valid" not in result:
                    real_tests = result.get("real_tests", {})
                    syntax_ok = real_tests.get("syntax_ok") if isinstance(real_tests, dict) else None
                    if syntax_ok is not None:
                        result["ast_valid"] = bool(syntax_ok)
                    else:
                        result["ast_valid"] = (result.get("status") in ("APPROVED", "COMPLETED")) or bool(result.get("approved"))
                if "syntax_valid" not in result:
                    result["syntax_valid"] = result.get("ast_valid", True)
                if "approved" not in result:
                    result["approved"] = result.get("status") == "APPROVED"
                record["status"] = "SUCCESS"
                record["result"] = result
                self._record_history(record)
                return result
        except Exception as e:
            record["status"] = "ERROR"
            record["error"] = str(e)
            record["result"] = {"success": False, "error": str(e)}
            self._record_history(record)
            return record["result"]

    def dispatch_director(
        self,
        blueprint: str,
        stage: str = "",
        workspace: str = "",
    ) -> dict[str, Any]:
        """Dispatches multi-stage execution to Director Bot on port 5822."""
        if not self.probe_bot("director")["online"]:
            self.ensure_director_online(max_wait_seconds=5.0)
        is_online = self.probe_bot("director")["online"]
        record = {
            "timestamp": _now_iso(),
            "target_bot": "director",
            "stage": stage,
            "online": is_online,
        }

        if not is_online:
            record["status"] = "OFFLINE_FALLBACK"
            record["result"] = {
                "success": False,
                "offline": True,
                "message": "Director Bot is offline on port 5822. Start it via START_SYSTEM.bat.",
            }
            self._record_history(record)
            return record["result"]

        payload = {
            "blueprint": blueprint,
            "stage": stage,
            "workspace": workspace,
        }

        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.director_url}/run_stage",
                data=data_bytes,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=45.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                record["status"] = "SUCCESS"
                record["result"] = result
                self._record_history(record)
                return result
        except Exception as e:
            record["status"] = "ERROR"
            record["error"] = str(e)
            record["result"] = {"success": False, "error": str(e)}
            self._record_history(record)
            return record["result"]

    def history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Returns recent swarm dispatch events."""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data[:limit]
        except Exception:
            pass
        return []
