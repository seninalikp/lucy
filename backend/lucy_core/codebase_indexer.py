"""
codebase_indexer.py
Stage 71: Local AST Codebase Indexer & High-Speed Symbol Graph.

Parses workspace Python code using native AST into an on-disk Symbol Graph, enabling
instant (<15ms) navigation of classes, functions, docstrings, and imports across the entire
repository without burning LLM context window tokens.
"""

from __future__ import annotations

import ast
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

STAGE = "71 local ast codebase indexer and high-speed symbol graph"

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "data",
    "dumps",
    "logs",
    "archive",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SymbolEntry:
    """Represents a code symbol extracted via AST."""

    def __init__(
        self,
        name: str,
        kind: str,  # "class", "function", "async_function", "constant", "import"
        file_path: str,
        line_start: int,
        line_end: int,
        docstring: Optional[str] = None,
        params: Optional[List[str]] = None,
        bases: Optional[List[str]] = None,
    ) -> None:
        self.name = name
        self.kind = kind
        self.file_path = file_path.replace("\\", "/")
        self.line_start = line_start
        self.line_end = line_end
        self.docstring = docstring.strip() if docstring else None
        self.params = params or []
        self.bases = bases or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "docstring": self.docstring,
            "params": self.params,
            "bases": self.bases,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SymbolEntry:
        return cls(
            name=data["name"],
            kind=data["kind"],
            file_path=data["file_path"],
            line_start=data["line_start"],
            line_end=data["line_end"],
            docstring=data.get("docstring"),
            params=data.get("params"),
            bases=data.get("bases"),
        )


class PythonSymbolVisitor(ast.NodeVisitor):
    """Traverses Python AST to extract classes, functions, and symbols."""

    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.symbols: List[SymbolEntry] = []
        self.imports: List[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        doc = ast.get_docstring(node)
        bases: List[str] = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(f"{ast.unparse(b.value)}.{b.attr}")

        entry = SymbolEntry(
            name=node.name,
            kind="class",
            file_path=self.rel_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=doc,
            bases=bases,
        )
        self.symbols.append(entry)

        # Visit class body to collect methods
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_function(node, "function")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_function(node, "async_function")

    def _record_function(self, node: Any, kind: str) -> None:
        doc = ast.get_docstring(node)
        params: List[str] = []
        for arg in node.args.args:
            params.append(arg.arg)

        entry = SymbolEntry(
            name=node.name,
            kind=kind,
            file_path=self.rel_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=doc,
            params=params,
        )
        self.symbols.append(entry)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = node.module or ""
        for alias in node.names:
            self.imports.append(f"{mod}.{alias.name}" if mod else alias.name)


class CodebaseIndexer:
    """
    Builds and manages the local AST symbol graph.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        data_dir: Optional[Path] = None,
    ) -> None:
        self.project_root = Path(project_root).resolve() if project_root else Path.cwd().resolve()
        self.data_dir = Path(data_dir).resolve() if data_dir else (self.project_root / "data" / "lucy")
        self.cache_file = self.data_dir / "symbol_graph.json"

        self._symbols_by_name: Dict[str, List[SymbolEntry]] = {}
        self._symbols_by_file: Dict[str, List[SymbolEntry]] = {}
        self._file_mtimes: Dict[str, float] = {}
        self._file_imports: Dict[str, List[str]] = {}
        self.last_indexed_at: Optional[str] = None

        self.load_cache()

    def load_cache(self) -> None:
        """Loads cached symbol graph from disk if present."""
        if not self.cache_file.exists():
            return
        try:
            data = json.loads(self.cache_file.read_text(encoding="utf-8"))
            self._file_mtimes = data.get("file_mtimes", {})
            self._file_imports = data.get("file_imports", {})
            self.last_indexed_at = data.get("last_indexed_at")

            raw_symbols = data.get("symbols", [])
            for sym_dict in raw_symbols:
                entry = SymbolEntry.from_dict(sym_dict)
                self._symbols_by_name.setdefault(entry.name.lower(), []).append(entry)
                self._symbols_by_file.setdefault(entry.file_path, []).append(entry)
        except Exception:
            pass

    def save_cache(self) -> None:
        """Persists symbol graph to disk."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            all_symbols = []
            for entries in self._symbols_by_file.values():
                for e in entries:
                    all_symbols.append(e.to_dict())

            payload = {
                "stage": STAGE,
                "last_indexed_at": self.last_indexed_at,
                "file_mtimes": self._file_mtimes,
                "file_imports": self._file_imports,
                "total_symbols": len(all_symbols),
                "symbols": all_symbols,
            }
            self.cache_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def index_workspace(self, force: bool = False) -> Dict[str, Any]:
        """
        Scans workspace for Python files and parses AST incrementally.
        """
        start_time = time.time()
        parsed_files = 0
        skipped_files = 0
        failed_files = 0

        # Scan eligible python files
        py_files: List[Path] = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if f.endswith(".py"):
                    py_files.append(Path(root) / f)

        for py_path in py_files:
            try:
                rel_str = str(py_path.relative_to(self.project_root)).replace("\\", "/")
                mtime = py_path.stat().st_mtime

                if not force and self._file_mtimes.get(rel_str) == mtime and rel_str in self._symbols_by_file:
                    skipped_files += 1
                    continue

                source_code = py_path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(source_code, filename=rel_str)

                visitor = PythonSymbolVisitor(rel_str)
                visitor.visit(tree)

                # Clear old file entries
                if rel_str in self._symbols_by_file:
                    old_entries = self._symbols_by_file[rel_str]
                    for oe in old_entries:
                        name_key = oe.name.lower()
                        if name_key in self._symbols_by_name:
                            self._symbols_by_name[name_key] = [
                                x for x in self._symbols_by_name[name_key] if x.file_path != rel_str
                            ]

                # Store new entries
                self._symbols_by_file[rel_str] = visitor.symbols
                for sym in visitor.symbols:
                    self._symbols_by_name.setdefault(sym.name.lower(), []).append(sym)

                self._file_imports[rel_str] = visitor.imports
                self._file_mtimes[rel_str] = mtime
                parsed_files += 1
            except Exception:
                failed_files += 1

        elapsed = time.time() - start_time
        self.last_indexed_at = _now_iso()
        self.save_cache()

        total_syms = sum(len(v) for v in self._symbols_by_file.values())
        return {
            "stage": STAGE,
            "total_files": len(py_files),
            "parsed_files": parsed_files,
            "cached_files": skipped_files,
            "failed_files": failed_files,
            "total_symbols": total_syms,
            "elapsed_ms": round(elapsed * 1000, 2),
        }

    def find_symbol(self, name: str, exact: bool = False) -> List[Dict[str, Any]]:
        """Searches for a symbol by name."""
        if not self._symbols_by_name:
            self.index_workspace(force=False)
        q = name.strip().lower()
        if not q:
            return []

        results: List[SymbolEntry] = []
        if exact:
            results = self._symbols_by_name.get(q, [])
        else:
            for k, entries in self._symbols_by_name.items():
                if q in k:
                    results.extend(entries)

        return [r.to_dict() for r in results]

    def get_file_outline(self, rel_path: str) -> List[Dict[str, Any]]:
        """Returns all classes and functions in a specific file."""
        if not self._symbols_by_file:
            self.index_workspace(force=False)
        norm = rel_path.replace("\\", "/").strip().lstrip("/")
        entries = self._symbols_by_file.get(norm, [])
        return [e.to_dict() for e in entries]

    def find_importers(self, symbol_or_mod: str) -> List[str]:
        """Finds all files in the workspace that import a given module or symbol."""
        target = symbol_or_mod.strip().lower()
        importers: List[str] = []
        for file_path, imports in self._file_imports.items():
            for imp in imports:
                if target in imp.lower():
                    importers.append(file_path)
                    break
        return sorted(importers)

    def format_symbol_lookup(self, name: str) -> str:
        """Renders clean ASCII terminal representation of symbol search results."""
        matches = self.find_symbol(name, exact=False)
        if not matches:
            return f"No code symbol matching '{name}' found in workspace."

        lines = [
            f"+--- [Symbol Lookup: '{name}' ({len(matches)} matches)] -------------------+",
        ]
        for idx, m in enumerate(matches[:8], start=1):
            kind = m.get("kind", "symbol").upper()
            sym_name = m.get("name")
            f_path = m.get("file_path")
            lines_range = f"L{m.get('line_start')}-L{m.get('line_end')}"
            lines.append(f"| [{idx}] {kind} {sym_name} @ {f_path}:{lines_range}")

            params = m.get("params")
            if params:
                lines.append(f"|     Args: ({', '.join(params)})")
            doc = m.get("docstring")
            if doc:
                doc_first = doc.splitlines()[0][:60]
                lines.append(f"|     Doc: {doc_first}")

        if len(matches) > 8:
            lines.append(f"| ... and {len(matches) - 8} more matches.")
        lines.append("+------------------------------------------------------------------+")
        return "\n".join(lines)

    def format_file_outline(self, rel_path: str) -> str:
        """Renders clean ASCII outline of a file's symbols."""
        norm = rel_path.replace("\\", "/").strip().lstrip("/")
        outline = self.get_file_outline(norm)
        if not outline:
            return f"No symbols found or file '{norm}' is not indexed."

        lines = [
            f"+--- [File Outline: {norm} ({len(outline)} symbols)] -------------------+",
        ]
        for sym in outline:
            kind = sym.get("kind", "").upper()
            sname = sym.get("name")
            start = sym.get("line_start")
            end = sym.get("line_end")
            lines.append(f"|   [{kind:<14}] {sname:<30} (L{start}-L{end})")
        lines.append("+------------------------------------------------------------------+")
        return "\n".join(lines)

    def status(self) -> Dict[str, Any]:
        total_syms = sum(len(v) for v in self._symbols_by_file.values())
        return {
            "stage": STAGE,
            "codebase_indexer": "active",
            "indexed_files": len(self._symbols_by_file),
            "total_symbols": total_syms,
            "last_indexed_at": self.last_indexed_at,
            "cache_file": str(self.cache_file),
        }
