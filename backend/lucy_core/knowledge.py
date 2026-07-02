"""
knowledge.py
Safe AI Collections ingestion for Lucy.

This indexes the user's AI COLLECTIONS folder as knowledge, not as raw memory.
Secrets and key vault material are redacted or kept metadata-only.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


INDEX_VERSION = "0.1.0"
MAX_TEXT_BYTES = 750_000
MAX_READ_BYTES = 140_000
MAX_EXCERPT_CHARS = 4000

TEXT_SUFFIXES = {
    ".bat",
    ".cfg",
    ".css",
    ".csv",
    ".env",
    ".gd",
    ".gitattributes",
    ".gitignore",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}

SKIP_DIRS = {
    ".git",
    ".godot",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "site-packages",
    "venv",
    ".venv",
}

METADATA_ONLY_PATH_PARTS = {
    ".env",
    "api/secure",
    "local_unlock.py",
}

METADATA_ONLY_SUFFIXES = {
    ".enc",
    ".key",
    ".pem",
    ".pfx",
    ".p12",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".pyc",
    ".pyo",
    ".zip",
    ".7z",
    ".rar",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".wav",
    ".mp3",
    ".mp4",
    ".exe",
    ".dll",
}

SECRET_PATTERNS = [
    re.compile(r"gsk_[A-Za-z0-9_\-]+"),
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"AIza[A-Za-z0-9_\-]+"),
    re.compile(r"xai-[A-Za-z0-9_\-]+", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9_\.\-]+", re.IGNORECASE),
    re.compile(r"(?i)(api[_ -]?key\s*[:=]\s*)['\"]?[^'\"\s,}]+"),
    re.compile(r"(?i)(password\s*[:=]\s*)['\"]?[^'\"\s,}]+"),
    re.compile(r"(?i)(token\s*[:=]\s*)['\"]?[^'\"\s,}]+"),
    re.compile(r"(?i)(secret\s*[:=]\s*)['\"]?[^'\"\s,}]+"),
    re.compile(r"(?i)(master_password\s*=\s*)['\"][^'\"]+['\"]"),
    re.compile(r"-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----.*?-----END (RSA |OPENSSH |EC )?PRIVATE KEY-----", re.DOTALL),
]

SECRET_LINE = re.compile(
    r"(?i)\b(api[_-]?key|password|passwd|token|secret|credential|private[_-]?key|master_password)\b\s*[:=]"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def _tokens(text: str) -> set[str]:
    return {part for part in re.split(r"[^a-z0-9_]+", text.lower()) if len(part) > 2}


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _redact_text(text: str) -> tuple[str, bool]:
    changed = False
    lines: list[str] = []
    for line in text.splitlines():
        if SECRET_LINE.search(line):
            lines.append(re.sub(r"[:=].*$", "= [redacted]", line))
            changed = True
            continue
        cleaned = line
        for pattern in SECRET_PATTERNS:
            cleaned_new = pattern.sub("[redacted]", cleaned)
            if cleaned_new != cleaned:
                changed = True
            cleaned = cleaned_new
        lines.append(cleaned)
    return "\n".join(lines), changed


def _is_metadata_only_path(relative: str, suffix: str) -> tuple[bool, str]:
    lowered = relative.lower().replace("\\", "/")
    if suffix in METADATA_ONLY_SUFFIXES:
        return True, f"metadata only for {suffix or 'binary'} file"
    for part in METADATA_ONLY_PATH_PARTS:
        if part in lowered:
            return True, f"metadata only for sensitive path segment: {part}"
    return False, ""


def _summary_for_text(relative: str, text: str) -> dict:
    suffix = Path(relative).suffix.lower()
    non_empty = [line.strip() for line in text.splitlines() if line.strip()]
    summary: list[str] = []
    symbols: list[str] = []

    if suffix == ".py":
        for line in non_empty[:80]:
            if line.startswith("class ") or line.startswith("def "):
                symbols.append(line.split(":", 1)[0][:160])
            if line.startswith("import ") or line.startswith("from "):
                symbols.append(line[:160])
        doc_match = re.search(r'^\s*"""(.*?)"""', text, flags=re.DOTALL)
        if doc_match:
            first = re.sub(r"\s+", " ", doc_match.group(1)).strip()
            if first:
                summary.append(first[:240])

    if suffix in {".json", ".toml", ".yaml", ".yml"}:
        first_keys = []
        if suffix == ".json":
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    first_keys = list(data.keys())[:12]
            except Exception:
                first_keys = []
        if first_keys:
            summary.append("Top-level keys: " + ", ".join(str(key) for key in first_keys))

    for line in non_empty[:8]:
        if len(summary) >= 3:
            break
        if line.startswith("#") or line.startswith("##") or len(line) > 25:
            summary.append(line[:240])

    if not summary and non_empty:
        summary.append(non_empty[0][:240])

    return {
        "summary": " ".join(summary)[:600],
        "symbols": symbols[:20],
        "keywords": sorted(_tokens(relative + " " + " ".join(summary) + " ".join(symbols)))[:80],
    }


class AICollectionsKnowledge:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.knowledge_dir = data_dir / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.knowledge_dir / "ai_collections_index.json"

    def _default_roots(self) -> list[Path]:
        home = Path.home()
        configured = os.environ.get("LUCY_AI_COLLECTIONS_ROOT", "").strip()
        candidates = []
        if configured:
            candidates.append(Path(configured))
        candidates.extend(
            [
                home / "Downloads" / "AI COLLECTIONS",
                home / "Documents" / "AI COLLECTIONS",
            ]
        )
        return candidates

    def find_root(self, raw_root: str | None = None) -> Path | None:
        candidates = [Path(raw_root)] if raw_root else self._default_roots()
        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate.resolve()
        return None

    def ingest(self, raw_root: str | None = None, max_files: int | None = None) -> dict:
        root = self.find_root(raw_root)
        if root is None:
            return {
                "ok": False,
                "reason": "AI COLLECTIONS folder was not found.",
                "index_file": str(self.index_file),
            }

        records: list[dict] = []
        counts = {
            "total_files": 0,
            "indexed_text": 0,
            "metadata_only": 0,
            "too_large": 0,
            "errors": 0,
            "redacted": 0,
            "skipped_dirs": 0,
        }

        for current_root, dirs, names in os.walk(root):
            before = len(dirs)
            dirs[:] = [dirname for dirname in dirs if dirname.lower() not in SKIP_DIRS]
            counts["skipped_dirs"] += before - len(dirs)

            for name in names:
                path = Path(current_root) / name
                if max_files is not None and counts["total_files"] >= max_files:
                    break
                record = self._record_file(root, path)
                records.append(record)
                counts["total_files"] += 1
                counts[record["status"]] = counts.get(record["status"], 0) + 1
                if record.get("redacted"):
                    counts["redacted"] += 1
                if record["status"] == "error":
                    counts["errors"] += 1
            if max_files is not None and counts["total_files"] >= max_files:
                break

        data = {
            "version": INDEX_VERSION,
            "created_at": _now(),
            "updated_at": _now(),
            "root": str(root),
            "counts": counts,
            "records": records,
        }
        self.index_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return {
            "ok": True,
            "root": str(root),
            "index_file": str(self.index_file),
            "counts": counts,
        }

    def _record_file(self, root: Path, path: Path) -> dict:
        try:
            stat = path.stat()
            relative = _normalize_path(path.relative_to(root))
            suffix = path.suffix.lower()
            base = {
                "path": relative,
                "size": stat.st_size,
                "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "suffix": suffix,
            }

            metadata_only, reason = _is_metadata_only_path(relative, suffix)
            if metadata_only:
                return {**base, "status": "metadata_only", "reason": reason}

            if stat.st_size > MAX_TEXT_BYTES:
                return {**base, "status": "too_large", "reason": f"larger than {MAX_TEXT_BYTES} bytes"}

            if suffix not in TEXT_SUFFIXES:
                return {**base, "status": "metadata_only", "reason": "non-text suffix"}

            with path.open("rb") as handle:
                raw = handle.read(min(MAX_READ_BYTES, stat.st_size))
            text = raw.decode("utf-8", errors="replace")
            redacted, was_redacted = _redact_text(text)
            info = _summary_for_text(relative, redacted)
            return {
                **base,
                "status": "indexed_text",
                "sha256_sample": _sha256_bytes(raw),
                "redacted": was_redacted,
                "summary": info["summary"],
                "symbols": info["symbols"],
                "keywords": info["keywords"],
                "excerpt": redacted[:MAX_EXCERPT_CHARS],
                "truncated": stat.st_size > len(raw) or len(redacted) > MAX_EXCERPT_CHARS,
            }
        except Exception as exc:
            relative = _normalize_path(path.relative_to(root)) if root in path.parents else str(path)
            return {
                "path": relative,
                "status": "error",
                "reason": str(exc),
            }

    def status(self) -> dict:
        if not self.index_file.exists():
            return {
                "available": False,
                "index_file": str(self.index_file),
                "reason": "No AI Collections index exists yet.",
            }
        data = self._read()
        return {
            "available": True,
            "index_file": str(self.index_file),
            "root": data.get("root", ""),
            "updated_at": data.get("updated_at", ""),
            "counts": data.get("counts", {}),
        }

    def search(self, query: str, limit: int = 8) -> dict:
        cleaned = query.strip()
        if not cleaned:
            return {"query": query, "matches": [], "reason": "Search query was empty."}
        if not self.index_file.exists():
            return {"query": query, "matches": [], "reason": "AI Collections index does not exist yet."}

        query_tokens = _tokens(cleaned)
        lowered = cleaned.lower()
        matches: list[tuple[int, dict]] = []
        for record in self._read().get("records", []):
            haystack = " ".join(
                [
                    record.get("path", ""),
                    record.get("summary", ""),
                    " ".join(record.get("symbols", [])),
                    " ".join(record.get("keywords", [])),
                    record.get("excerpt", "")[:1000],
                ]
            )
            score = 0
            haystack_lower = haystack.lower()
            if lowered in haystack_lower:
                score += 10
            score += len(query_tokens & _tokens(haystack))
            if score:
                matches.append((score, record))

        matches.sort(key=lambda pair: pair[0], reverse=True)
        return {
            "query": query,
            "matches": [
                {
                    "path": item.get("path", ""),
                    "status": item.get("status", ""),
                    "summary": item.get("summary", item.get("reason", "")),
                    "redacted": item.get("redacted", False),
                    "symbols": item.get("symbols", [])[:8],
                }
                for _, item in matches[:limit]
            ],
            "limit": limit,
        }

    def _read(self) -> dict:
        try:
            return json.loads(self.index_file.read_text(encoding="utf-8"))
        except Exception:
            return {"records": [], "counts": {}}
