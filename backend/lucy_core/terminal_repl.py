"""
terminal_repl.py
Stage 50 = High-Performance Terminal REPL & Custom Command Palette.

Provides a fast, operator-grade terminal interface for Lucy:
1. ANSI Color & Operator Badge System:
   - Full ANSI 16-color & style support with automatic terminal detection.
   - Stylized status badges: [LUCY::SOVEREIGN] [RAM: XX% | KEYS: 25 | SENTINEL: OK].
   - Configurable prompts with timing and status indicators.
2. Persistent Command History Manager:
   - File-backed history storage in data/lucy/terminal_history.json.
   - Deduplication of consecutive identical commands.
   - Substring history search and chronological replay.
3. User Macro & Shortcut Engine:
   - Multi-step execution pipelines (e.g. 'macro health = sentinel alerts && telemetry').
   - File-backed storage in data/lucy/user_macros.json.
4. Command Palette & Autocomplete:
   - Fast prefix and substring autocomplete for slash commands and natural queries.
   - Categorized command directory: SYSTEM, PROVIDERS, SENTINEL, LORA, TASKS, REPL.
5. Interactive & Headless Stream REPL:
   - Stream-based runner supporting both interactive terminal input and headless I/O for tests.
   - Safe keyboard interrupt / EOF handling with clean shutdown.
"""

from __future__ import annotations

import datetime
import io
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


STAGE = "50 high-performance terminal repl"


# =====================================================================
# 1. ANSI COLOR & FORMATTING SYSTEM
# =====================================================================

class ANSIColor:
    """ANSI terminal styling system with auto-detection and safe fallbacks."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    _ANSI_REGEX = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

    @classmethod
    def supports_color(cls) -> bool:
        """Determines if current environment supports ANSI colors."""
        if os.environ.get("NO_COLOR"):
            return False
        if os.environ.get("FORCE_COLOR") == "1":
            return True
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    @classmethod
    def style(cls, text: str, *styles: str, enabled: bool = True) -> str:
        """Applies styles to text if enabled; returns bare text otherwise."""
        if not enabled or not styles:
            return text
        prefix = "".join(styles)
        return f"{prefix}{text}{cls.RESET}"

    @classmethod
    def strip(cls, text: str) -> str:
        """Strips all ANSI escape sequences from text."""
        return cls._ANSI_REGEX.sub("", text)


# =====================================================================
# 2. PERSISTENT COMMAND HISTORY MANAGER
# =====================================================================

class TerminalHistoryManager:
    """Persistent, file-backed command history with deduping and search."""

    def __init__(self, history_file: Optional[Path] = None, max_entries: int = 500) -> None:
        self.history_file = history_file or (
            Path(r"C:\Users\admin\Desktop\senin\LUCY\lucy\data\lucy\terminal_history.json")
        )
        self.max_entries = max_entries
        self._history: List[Dict[str, str]] = []
        self._load()

    def _load(self) -> None:
        if self.history_file.exists():
            try:
                data = json.loads(self.history_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self._history = data[-self.max_entries:]
            except Exception:
                self._history = []

    def _save(self) -> None:
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            self.history_file.write_text(
                json.dumps(self._history, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    def add(self, command: str) -> bool:
        """Adds command to history if non-empty and not duplicate of previous."""
        cmd = command.strip()
        if not cmd:
            return False

        if self._history and self._history[-1].get("command") == cmd:
            return False

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._history.append({"command": cmd, "timestamp": now})
        if len(self._history) > self.max_entries:
            self._history = self._history[-self.max_entries:]

        self._save()
        return True

    def get_history(self, limit: int = 50) -> List[str]:
        """Returns recent commands in chronological order."""
        return [entry["command"] for entry in self._history[-limit:]]

    def search_history(self, query: str, limit: int = 10) -> List[str]:
        """Returns commands matching query (case-insensitive)."""
        q = query.lower().strip()
        if not q:
            return self.get_history(limit)
        matches = [entry["command"] for entry in self._history if q in entry["command"].lower()]
        return matches[-limit:]

    def clear(self) -> None:
        """Clears all history in-memory and on disk."""
        self._history = []
        self._save()

    def count(self) -> int:
        return len(self._history)


# =====================================================================
# 3. USER MACRO & SHORTCUT ENGINE
# =====================================================================

class MacroEngine:
    """User-defined shortcut and multi-step pipeline engine."""

    DEFAULT_MACROS = {
        "quickcheck": "sentinel alerts && telemetry",
        "health": "provider status && sentinel status",
        "sync": "scan workspace && train personal lora",
    }

    def __init__(self, macro_file: Optional[Path] = None) -> None:
        self.macro_file = macro_file or (
            Path(r"C:\Users\admin\Desktop\senin\LUCY\lucy\data\lucy\user_macros.json")
        )
        self._macros: Dict[str, str] = dict(self.DEFAULT_MACROS)
        self._load()

    def _load(self) -> None:
        if self.macro_file.exists():
            try:
                data = json.loads(self.macro_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._macros.update(data)
            except Exception:
                pass

    def _save(self) -> None:
        try:
            self.macro_file.parent.mkdir(parents=True, exist_ok=True)
            self.macro_file.write_text(
                json.dumps(self._macros, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    def register_macro(self, name: str, pipeline: str) -> Dict[str, Any]:
        """Registers or updates a user shortcut."""
        clean_name = name.strip().lower().lstrip("/")
        clean_pipe = pipeline.strip()
        if not clean_name or not clean_pipe:
            return {"ok": False, "error": "Name and pipeline cannot be empty."}

        self._macros[clean_name] = clean_pipe
        self._save()
        return {"ok": True, "name": clean_name, "pipeline": clean_pipe}

    def delete_macro(self, name: str) -> bool:
        """Deletes a custom macro."""
        clean_name = name.strip().lower().lstrip("/")
        if clean_name in self._macros:
            del self._macros[clean_name]
            self._save()
            return True
        return False

    def list_macros(self) -> Dict[str, str]:
        """Returns all registered macros."""
        return dict(self._macros)

    def resolve_macro(self, command: str) -> Optional[List[str]]:
        """If command matches a macro, returns list of sub-commands to run."""
        clean = command.strip().lower().lstrip("/")
        if clean in self._macros:
            pipeline = self._macros[clean]
            steps = [s.strip() for s in pipeline.split("&&") if s.strip()]
            return steps
        return None


# =====================================================================
# 4. COMMAND PALETTE & AUTOCOMPLETE
# =====================================================================

class CommandPalette:
    """Registry of known Lucy commands and intelligent autocomplete provider."""

    COMMANDS: Dict[str, Dict[str, Any]] = {
        # System
        "/status": {"desc": "Show overall Lucy status & sovereign mind health", "cat": "SYSTEM"},
        "/telemetry": {"desc": "Show live Windows hardware, RAM, CPU, disk & battery", "cat": "SYSTEM"},
        "/recap": {"desc": "Show multi-turn cross-session conversation summary", "cat": "SYSTEM"},
        "/clear": {"desc": "Clear terminal screen", "cat": "SYSTEM"},
        "/exit": {"desc": "Cleanly shutdown operator session", "cat": "SYSTEM"},
        # Providers & Keys
        "/keys": {"desc": "Show multi-provider pool status & masked keys", "cat": "PROVIDERS"},
        "/providers": {"desc": "List registered cloud providers & health metrics", "cat": "PROVIDERS"},
        "rotate keys": {"desc": "Rotate to next healthy provider key in the pool", "cat": "PROVIDERS"},
        "provider status": {"desc": "Detailed status of all 25 API keys and failover", "cat": "PROVIDERS"},
        # Sentinel
        "/sentinel": {"desc": "Workspace sentinel status and active background watcher", "cat": "SENTINEL"},
        "sentinel alerts": {"desc": "Check pending AST syntax errors & file modifications", "cat": "SENTINEL"},
        "scan workspace": {"desc": "Run a fast proactive scan of workspace directory", "cat": "SENTINEL"},
        "start sentinel": {"desc": "Start background workspace watchdog thread", "cat": "SENTINEL"},
        "stop sentinel": {"desc": "Stop background workspace watchdog thread", "cat": "SENTINEL"},
        # LoRA
        "/lora": {"desc": "Personal LoRA sleep cycle alignment & gate evaluation", "cat": "LORA"},
        "train personal lora": {"desc": "Synthesize Alpaca dataset and generate Modelfile", "cat": "LORA"},
        "evaluate lora": {"desc": "Run 10-Question Alignment Gate verification", "cat": "LORA"},
        # Tasks & Tools
        "/goal": {"desc": "Execute multi-step autonomous Goal DAG: /goal <instruction>", "cat": "TASKS"},
        "/goals": {"desc": "List history of executed multi-step goals", "cat": "TASKS"},
        "/tasks": {"desc": "Show background task daemon queue and active workers", "cat": "TASKS"},
        "clean cache": {"desc": "Clean ephemeral sandbox and cache directory", "cat": "TASKS"},
        "list processes": {"desc": "List running Windows processes and RAM footprint", "cat": "TASKS"},
        # REPL & Config
        "/palette": {"desc": "Show full interactive command palette directory", "cat": "REPL"},
        "/help": {"desc": "Show help guide and command usage syntax", "cat": "REPL"},
        "/history": {"desc": "Show recent command history [optional: limit]", "cat": "REPL"},
        "/macro": {"desc": "Manage shortcuts: /macro list | add <name>=<cmd> | del <name>", "cat": "REPL"},
    }

    def __init__(self, macro_engine: Optional[MacroEngine] = None) -> None:
        self.macros = macro_engine or MacroEngine()

    def autocomplete(self, prefix: str) -> List[str]:
        """Returns sorted matching commands based on prefix and substring match."""
        p = prefix.strip().lower()
        if not p:
            return sorted(self.COMMANDS.keys())

        exact_prefix: List[str] = []
        substring_match: List[str] = []

        all_candidates = list(self.COMMANDS.keys())
        for m in self.macros.list_macros().keys():
            all_candidates.append(f"/{m}")
            all_candidates.append(m)

        for cand in all_candidates:
            cand_lower = cand.lower()
            if cand_lower.startswith(p):
                exact_prefix.append(cand)
            elif p in cand_lower:
                substring_match.append(cand)

        return sorted(list(set(exact_prefix))) + [
            c for c in sorted(list(set(substring_match))) if c not in exact_prefix
        ]

    def render_help(self, category: Optional[str] = None) -> str:
        """Renders categorized help guide."""
        cat_filter = category.upper() if category else None
        by_cat: Dict[str, List[tuple[str, str]]] = {}

        for cmd, info in self.COMMANDS.items():
            cat = info["cat"]
            if cat_filter and cat != cat_filter:
                continue
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append((cmd, info["desc"]))

        lines = [
            "================================================================================",
            " LUCY COMMAND PALETTE & OPERATOR REFERENCE",
            "================================================================================",
        ]
        for cat, items in sorted(by_cat.items()):
            lines.append(f"\n[{cat}]")
            for cmd, desc in sorted(items, key=lambda x: x[0]):
                lines.append(f"  {cmd:<24} - {desc}")

        macro_dict = self.macros.list_macros()
        if macro_dict and (cat_filter is None or cat_filter == "MACROS"):
            lines.append("\n[USER MACROS & SHORTCUTS]")
            for m_name, m_pipe in sorted(macro_dict.items()):
                lines.append(f"  /{m_name:<23} -> {m_pipe}")

        lines.append("\n================================================================================")
        return "\n".join(lines)


# =====================================================================
# 5. TERMINAL REPL (INTERACTIVE & HEADLESS)
# =====================================================================

class TerminalREPL:
    """High-performance terminal operator loop and dispatcher."""

    def __init__(
        self,
        runtime: Any = None,
        router: Any = None,
        lucy_data: Optional[Path] = None,
        enable_color: bool = True,
    ) -> None:
        self.runtime = runtime
        self.router = router
        self.enable_color = enable_color and ANSIColor.supports_color()

        base_data = lucy_data or Path(r"C:\Users\admin\Desktop\senin\LUCY\lucy\data\lucy")
        self.history = TerminalHistoryManager(history_file=base_data / "terminal_history.json")
        self.macros = MacroEngine(macro_file=base_data / "user_macros.json")
        self.palette = CommandPalette(macro_engine=self.macros)

    def render_banner(self) -> str:
        """Returns stylized terminal operator startup banner."""
        c = ANSIColor
        title = "LUCY :: SOVEREIGN TERMINAL OPERATOR (v3.1.0-alpha / STAGE 50)"
        sub1 = "Local Sovereign Mind: Ollama (qwen2.5:3b) | Multi-Provider Pool (25 Keys)"
        sub2 = "Proactive Sentinel: Active | LoRA Sleep Cycle: Ready | Palette: /help"

        if self.enable_color:
            bar = c.style("=" * 80, c.CYAN)
            t_str = c.style(f"  {title}", c.BOLD, c.BRIGHT_WHITE)
            s1_str = c.style(f"  {sub1}", c.GREEN)
            s2_str = c.style(f"  {sub2}", c.YELLOW)
            return f"\n{bar}\n{t_str}\n{s1_str}\n{s2_str}\n{bar}\n"
        else:
            bar = "=" * 80
            return f"\n{bar}\n  {title}\n  {sub1}\n  {sub2}\n{bar}\n"

    def render_status_badge(self) -> str:
        """Generates a compact, one-line status badge."""
        c = ANSIColor
        badge_parts = ["[LUCY::SOVEREIGN]"]

        # Hardware summary if runtime has telemetry
        if self.runtime and hasattr(self.runtime, "system_telemetry"):
            try:
                telem = self.runtime.system_telemetry()
                ram_load = telem.get("ram", {}).get("memory_load_percent", "?")
                badge_parts.append(f"RAM: {ram_load}%")
            except Exception:
                pass

        # Sentinel status
        if self.runtime and hasattr(self.runtime, "sentinel_status"):
            try:
                s_stat = self.runtime.sentinel_status()
                watch = "ACTIVE" if s_stat.get("background_watcher", {}).get("running") else "IDLE"
                badge_parts.append(f"SENTINEL: {watch}")
            except Exception:
                pass

        # Provider pool
        if self.runtime and hasattr(self.runtime, "provider_pool_status"):
            try:
                p_stat = self.runtime.provider_pool_status()
                badge_parts.append(f"KEYS: {p_stat.get('total_keys', 25)}")
            except Exception:
                pass

        joined = " | ".join(badge_parts)
        if self.enable_color:
            return c.style(f"[{joined}]", c.DIM, c.CYAN)
        return f"[{joined}]"

    def render_prompt(self) -> str:
        """Returns stylized terminal input prompt."""
        c = ANSIColor
        if self.enable_color:
            p_prefix = c.style("lucy", c.BOLD, c.BRIGHT_GREEN)
            p_sep = c.style("::", c.DIM, c.WHITE)
            p_role = c.style("operator", c.CYAN)
            p_arrow = c.style(" > ", c.BOLD, c.YELLOW)
            return f"{p_prefix}{p_sep}{p_role}{p_arrow}"
        return "lucy::operator > "

    def execute_one(self, command: str) -> Dict[str, Any]:
        """Executes a single command line, handling macros, palette, and dispatch."""
        cmd = command.strip()
        t0 = time.perf_counter()

        if not cmd:
            return {
                "ok": True,
                "command": "",
                "output": "",
                "should_exit": False,
                "elapsed_ms": 0.0,
                "stage": STAGE,
            }

        # 1. Add to persistent history
        self.history.add(cmd)

        # 2. Check user macros
        macro_steps = self.macros.resolve_macro(cmd)
        if macro_steps is not None:
            results = []
            for step in macro_steps:
                sub_res = self.execute_one(step)
                results.append(f"[{step}]\n{sub_res['output']}")
                if sub_res.get("should_exit"):
                    elapsed = (time.perf_counter() - t0) * 1000
                    return {
                        "ok": True,
                        "command": cmd,
                        "output": "\n\n".join(results),
                        "should_exit": True,
                        "elapsed_ms": round(elapsed, 2),
                        "stage": STAGE,
                    }
            elapsed = (time.perf_counter() - t0) * 1000
            return {
                "ok": True,
                "command": cmd,
                "output": "\n\n".join(results),
                "should_exit": False,
                "elapsed_ms": round(elapsed, 2),
                "stage": STAGE,
            }

        lowered = cmd.lower()

        # 3. Handle REPL Palette commands
        if lowered in {"/exit", "/quit", "exit", "quit"}:
            elapsed = (time.perf_counter() - t0) * 1000
            return {
                "ok": True,
                "command": cmd,
                "output": "Lucy operator session closed cleanly.",
                "should_exit": True,
                "elapsed_ms": round(elapsed, 2),
                "stage": STAGE,
            }

        if lowered in {"/clear", "clear", "cls"}:
            elapsed = (time.perf_counter() - t0) * 1000
            return {
                "ok": True,
                "command": cmd,
                "output": "\033[2J\033[H",
                "should_exit": False,
                "elapsed_ms": round(elapsed, 2),
                "stage": STAGE,
            }

        if lowered in {"/help", "/h", "help"}:
            elapsed = (time.perf_counter() - t0) * 1000
            return {
                "ok": True,
                "command": cmd,
                "output": self.palette.render_help(),
                "should_exit": False,
                "elapsed_ms": round(elapsed, 2),
                "stage": STAGE,
            }

        if lowered in {"/palette", "/commands", "palette"}:
            elapsed = (time.perf_counter() - t0) * 1000
            return {
                "ok": True,
                "command": cmd,
                "output": self.palette.render_help(),
                "should_exit": False,
                "elapsed_ms": round(elapsed, 2),
                "stage": STAGE,
            }

        if lowered.startswith("/history"):
            parts = cmd.split()
            limit = 20
            if len(parts) > 1 and parts[1].isdigit():
                limit = int(parts[1])
            hist = self.history.get_history(limit)
            out_lines = [f"Recent Command History ({len(hist)} entries):"]
            for i, h_cmd in enumerate(hist, 1):
                out_lines.append(f"  {i:>2}. {h_cmd}")
            elapsed = (time.perf_counter() - t0) * 1000
            return {
                "ok": True,
                "command": cmd,
                "output": "\n".join(out_lines),
                "should_exit": False,
                "elapsed_ms": round(elapsed, 2),
                "stage": STAGE,
            }

        if lowered.startswith("/macro"):
            parts = cmd.split(maxsplit=2)
            if len(parts) == 1 or parts[1].lower() == "list":
                macros = self.macros.list_macros()
                out_lines = ["Registered User Macros:"]
                for name, pipe in macros.items():
                    out_lines.append(f"  {name} = {pipe}")
                output = "\n".join(out_lines)
            elif parts[1].lower() == "del" and len(parts) > 2:
                success = self.macros.delete_macro(parts[2])
                output = f"Macro '{parts[2]}' deleted." if success else f"Macro '{parts[2]}' not found."
            elif "=" in cmd:
                # /macro add name = cmd OR /macro name = cmd
                body = cmd[len("/macro"):].strip()
                if body.lower().startswith("add"):
                    body = body[3:].strip()
                name, pipeline = body.split("=", 1)
                res = self.macros.register_macro(name.strip(), pipeline.strip())
                output = f"Macro registered: {res['name']} = {res['pipeline']}"
            else:
                output = "Usage: /macro list | /macro add <name> = <pipeline> | /macro del <name>"

            elapsed = (time.perf_counter() - t0) * 1000
            return {
                "ok": True,
                "command": cmd,
                "output": output,
                "should_exit": False,
                "elapsed_ms": round(elapsed, 2),
                "stage": STAGE,
            }

        # 4. Route to Lucy Router or LucyRuntime
        output_msg = ""
        should_exit = False

        # Preserve leading slash for Stage 68-90 cognitive/operator commands; strip only for legacy status commands
        legacy_slash = {"/status", "/telemetry", "/recap", "/keys", "/providers", "/lora"}
        route_cmd = cmd.lstrip("/") if lowered in legacy_slash else cmd

        if self.router is not None:
            resp = self.router.handle(route_cmd)
            output_msg = resp.message or ""
            should_exit = bool(resp.should_exit)
        elif self.runtime is not None:
            if hasattr(self.runtime, "respond"):
                output_msg = str(self.runtime.respond(route_cmd))
            else:
                output_msg = f"Runtime received command: {route_cmd}"
        else:
            output_msg = f"[Standalone REPL Mock Response] Command: {cmd}"

        elapsed = (time.perf_counter() - t0) * 1000
        return {
            "ok": True,
            "command": cmd,
            "output": output_msg,
            "should_exit": should_exit,
            "elapsed_ms": round(elapsed, 2),
            "stage": STAGE,
        }

    def run_batch(self, commands: List[str]) -> List[Dict[str, Any]]:
        """Executes a list of commands sequentially."""
        results = []
        for cmd in commands:
            res = self.execute_one(cmd)
            results.append(res)
            if res.get("should_exit"):
                break
        return results

    def run_interactive(
        self,
        input_stream: Optional[io.TextIOBase] = None,
        output_stream: Optional[io.TextIOBase] = None,
        max_turns: Optional[int] = None,
    ) -> None:
        """Stream-based interactive operator loop."""
        in_s = input_stream or sys.stdin
        out_s = output_stream or sys.stdout

        # Print banner
        out_s.write(self.render_banner())
        out_s.flush()

        turn = 0
        while True:
            if max_turns is not None and turn >= max_turns:
                break
            turn += 1

            # Prompt
            prompt = self.render_prompt()
            out_s.write(prompt)
            out_s.flush()

            try:
                line = in_s.readline()
                if not line:  # EOF
                    out_s.write("\nLucy operator session closed (EOF).\n")
                    break
                line = line.rstrip("\r\n")
            except (KeyboardInterrupt, EOFError):
                out_s.write("\nLucy operator session closed cleanly.\n")
                break

            result = self.execute_one(line)
            if result.get("output"):
                out_s.write(f"{result['output']}\n")
                out_s.flush()

            if result.get("should_exit"):
                break

    def status(self) -> Dict[str, Any]:
        """Reports Stage 50 REPL status."""
        return {
            "stage": STAGE,
            "color_enabled": self.enable_color,
            "history_count": self.history.count(),
            "macros_registered": len(self.macros.list_macros()),
            "palette_commands_count": len(self.palette.COMMANDS),
            "status": "ready",
        }
