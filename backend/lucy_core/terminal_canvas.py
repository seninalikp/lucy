"""
backend/lucy_core/terminal_canvas.py
Stage 75: Terminal ANSI Canvas & Syntax-Highlighted Visual Stream

Provides high-speed, pure-terminal syntax highlighting (Python, JSON, Markdown, Diff),
ASCII-safe tree rendering, metric bars, and canvas framing for sovereign terminal interaction.
No web UI, no desktop UI, 100% cp1252-safe ASCII boundaries.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

STAGE: int = 75

# ANSI Escape Codes
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_RED = "\033[31m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_BLUE = "\033[34m"
C_MAGENTA = "\033[35m"
C_CYAN = "\033[36m"
C_WHITE = "\033[37m"
C_GRAY = "\033[90m"

ANSI_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Removes all ANSI escape sequences from a string."""
    return ANSI_REGEX.sub("", text)


class TerminalSyntaxHighlighter:
    """
    Regex-based terminal syntax colorizer for Python, JSON, Markdown, and unified Diffs.
    Gracefully falls back to plain text when colors are disabled.
    """

    PYTHON_KEYWORDS = {
        "def", "class", "import", "from", "return", "if", "elif", "else",
        "while", "for", "in", "try", "except", "finally", "with", "as",
        "lambda", "yield", "raise", "pass", "break", "continue", "async", "await",
    }
    PYTHON_BUILTINS = {
        "True", "False", "None", "self", "str", "int", "float", "dict",
        "list", "set", "tuple", "bool", "print", "len", "range", "open",
    }

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled and not bool(os.environ.get("NO_COLOR"))

    def colorize(self, text: str, color_code: str) -> str:
        if not self.enabled:
            return text
        return f"{color_code}{text}{C_RESET}"

    def highlight_python_line(self, line: str) -> str:
        if not self.enabled:
            return line

        # Comments
        comment_idx = line.find("#")
        code_part = line if comment_idx == -1 else line[:comment_idx]
        comment_part = "" if comment_idx == -1 else line[comment_idx:]

        # String literals in code part
        def replace_string(m: re.Match) -> str:
            return f"{C_GREEN}{m.group(0)}{C_RESET}"

        # Handle single and double quoted strings
        code_part = re.sub(r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', replace_string, code_part)

        # Highlight keywords and builtins
        def replace_ident(m: re.Match) -> str:
            token = m.group(0)
            if token in self.PYTHON_KEYWORDS:
                return f"{C_BOLD}{C_CYAN}{token}{C_RESET}"
            elif token in self.PYTHON_BUILTINS:
                return f"{C_YELLOW}{token}{C_RESET}"
            return token

        # Only replace identifiers not inside ANSI sequences
        parts = ANSI_REGEX.split(code_part)
        delims = ANSI_REGEX.findall(code_part)
        new_parts = []
        for p in parts:
            p_hl = re.sub(r"\b[A-Za-z_][A-Za-z0-9_]*\b", replace_ident, p)
            # Numbers
            p_hl = re.sub(r"\b\d+(?:\.\d+)?\b", lambda m: f"{C_MAGENTA}{m.group(0)}{C_RESET}", p_hl)
            new_parts.append(p_hl)

        reconstructed_code = ""
        for i in range(len(new_parts)):
            reconstructed_code += new_parts[i]
            if i < len(delims):
                reconstructed_code += delims[i]

        hl_comment = f"{C_GRAY}{comment_part}{C_RESET}" if comment_part else ""
        return reconstructed_code + hl_comment

    def highlight_python(self, code: str, line_numbers: bool = True, start_line: int = 1) -> str:
        lines = code.splitlines()
        digits = max(3, len(str(start_line + len(lines))))
        out = []
        for i, line in enumerate(lines, start=start_line):
            hl = self.highlight_python_line(line)
            if line_numbers:
                num_str = f"{i:>{digits}} | "
                if self.enabled:
                    num_str = f"{C_DIM}{num_str}{C_RESET}"
                out.append(f"{num_str}{hl}")
            else:
                out.append(hl)
        return "\n".join(out)

    def highlight_diff(self, diff_text: str) -> str:
        if not self.enabled:
            return diff_text
        out = []
        for line in diff_text.splitlines():
            if line.startswith("+++") or line.startswith("---"):
                out.append(f"{C_BOLD}{C_YELLOW}{line}{C_RESET}")
            elif line.startswith("+"):
                out.append(f"{C_GREEN}{line}{C_RESET}")
            elif line.startswith("-"):
                out.append(f"{C_RED}{line}{C_RESET}")
            elif line.startswith("@@"):
                out.append(f"{C_CYAN}{line}{C_RESET}")
            elif line.startswith("diff ") or line.startswith("index "):
                out.append(f"{C_BOLD}{C_GRAY}{line}{C_RESET}")
            else:
                out.append(line)
        return "\n".join(out)

    def highlight_json(self, json_text: str) -> str:
        if not self.enabled:
            return json_text
        out = []
        for line in json_text.splitlines():
            # Highlight JSON keys: "key":
            line = re.sub(r'("[^"]+")\s*:', lambda m: f"{C_CYAN}{m.group(1)}{C_RESET}:", line)
            # Highlight string values: : "value"
            line = re.sub(r':\s*("[^"]*")', lambda m: f": {C_GREEN}{m.group(1)}{C_RESET}", line)
            # Highlight numeric/boolean values
            line = re.sub(r'\b(true|false|null)\b', lambda m: f"{C_YELLOW}{m.group(1)}{C_RESET}", line)
            line = re.sub(r':\s*(-?\d+(?:\.\d+)?)\b', lambda m: f": {C_MAGENTA}{m.group(1)}{C_RESET}", line)
            out.append(line)
        return "\n".join(out)

    def highlight_markdown(self, md_text: str) -> str:
        if not self.enabled:
            return md_text
        out = []
        in_code_block = False
        for line in md_text.splitlines():
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                out.append(f"{C_CYAN}{line}{C_RESET}")
                continue
            if in_code_block:
                out.append(f"{C_GREEN}{line}{C_RESET}")
                continue
            if line.startswith("#"):
                out.append(f"{C_BOLD}{C_YELLOW}{line}{C_RESET}")
            elif line.strip().startswith(("* ", "- ", "1. ", "2. ", "3. ")):
                out.append(f"{C_MAGENTA}{line[:4]}{C_RESET}{line[4:]}")
            else:
                out.append(line)
        return "\n".join(out)


class TerminalCanvas:
    """
    ASCII-safe layout framing and visual streaming for sovereign terminal mode.
    Guarantees no Unicode box characters (uses '+', '-', '|' exclusively).
    """

    def __init__(self, colors_enabled: bool = True) -> None:
        self.highlighter = TerminalSyntaxHighlighter(enabled=colors_enabled)

    def render_box(self, title: str, lines: List[str], width: int = 72) -> str:
        w = max(width, len(title) + 6)
        border = "+" + "-" * (w - 2) + "+"
        title_str = f"| {title.upper()[:w-4]} "
        title_line = title_str + " " * (w - len(title_str) - 1) + "|"

        out = [border, title_line, border]
        for l in lines:
            # Calculate visible length ignoring ANSI
            raw_l = strip_ansi(l)
            if len(raw_l) > w - 4:
                # Wrap long line
                l_str = f"| {l[:w-4]} |"
            else:
                padding = " " * (w - 4 - len(raw_l))
                l_str = f"| {l}{padding} |"
            out.append(l_str)
        out.append(border)
        return "\n".join(out)

    def render_progress_bar(self, current: int, total: int, width: int = 20, label: str = "") -> str:
        total = max(1, total)
        fraction = max(0.0, min(1.0, current / total))
        fill_len = int(fraction * width)
        if fill_len == width:
            bar = "=" * width
        elif fill_len > 0:
            bar = "=" * (fill_len - 1) + ">" + " " * (width - fill_len)
        else:
            bar = " " * width

        pct = int(fraction * 100.0)
        lbl = f" {label}" if label else ""
        return f"[{bar}] {pct:3d}% ({current}/{total}){lbl}"

    def render_tree(self, root_dir: Path, max_depth: int = 2, max_entries: int = 40) -> str:
        """
        Renders an ASCII directory tree without Unicode characters.
        """
        lines = [f"{root_dir.name}/"]
        ignore_dirs = {".git", "__pycache__", ".pytest_cache", "venv", ".venv", "archive", "dumps", "node_modules"}

        count = 0

        def _walk(path: Path, prefix: str, depth: int):
            nonlocal count
            if depth > max_depth or count >= max_entries:
                return
            try:
                entries = sorted(list(path.iterdir()), key=lambda e: (e.is_file(), e.name.lower()))
            except Exception:
                return

            filtered = [e for e in entries if e.name not in ignore_dirs and not e.name.endswith(".pyc")]
            for idx, entry in enumerate(filtered):
                if count >= max_entries:
                    lines.append(f"{prefix}+-- ... (truncated)")
                    return
                count += 1
                is_last = (idx == len(filtered) - 1)
                node_marker = "+-- "
                sub_prefix = "|   " if not is_last else "    "

                if entry.is_dir():
                    lines.append(f"{prefix}{node_marker}{entry.name}/")
                    _walk(entry, prefix + sub_prefix, depth + 1)
                else:
                    sz = entry.stat().st_size if entry.exists() else 0
                    lines.append(f"{prefix}{node_marker}{entry.name} ({sz}B)")

        _walk(root_dir, "", 1)
        return "\n".join(lines)

    def view_file(self, file_path: Path, max_lines: int = 80, start_line: int = 1) -> str:
        """
        Reads a local file and presents it formatted with syntax highlighting and line numbers.
        """
        if not file_path.exists():
            return f"Error: File not found: {file_path}"
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"Error reading file: {e}"

        lines = content.splitlines()
        slice_lines = lines[start_line - 1 : start_line - 1 + max_lines]
        sliced_code = "\n".join(slice_lines)

        ext = file_path.suffix.lower()
        if ext == ".py":
            hl_code = self.highlighter.highlight_python(sliced_code, line_numbers=True, start_line=start_line)
        elif ext == ".json":
            hl_code = self.highlighter.highlight_json(sliced_code)
        elif ext in (".diff", ".patch"):
            hl_code = self.highlighter.highlight_diff(sliced_code)
        elif ext in (".md", ".markdown"):
            hl_code = self.highlighter.highlight_markdown(sliced_code)
        else:
            hl_code = sliced_code

        header = f"FILE: {file_path.name} ({len(lines)} lines, viewing {start_line}-{min(len(lines), start_line + max_lines - 1)})"
        return f"+{'-' * 70}+\n| {header:<68} |\n+{'-' * 70}+\n{hl_code}\n+{'-' * 70}+"
