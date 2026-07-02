"""
safe_tools.py
Stage 5.1 read-only workspace awareness for Lucy.

All access is user-triggered, local, read-only, and restricted to enabled
approved folders.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.lucy_core.safe_storage import safe_read_json, safe_write_json
from backend.lucy_core.tool_policy import ToolActionPolicy, ToolActionRequest


SAFE_TOOLS_VERSION = "0.1.0"

ALLOWED_EXTENSIONS = {
    ".py",
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".css",
    ".js",
    ".csv",
    ".log",
}

BLOCKED_EXTENSIONS = {
    ".env",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".db",
    ".sqlite",
    ".wallet",
    ".kdbx",
    ".zip",
    ".exe",
    ".dll",
    ".bin",
    ".mp3",
    ".mp4",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".pdf",
}

SENSITIVE_PATTERNS = {
    "secret",
    "token",
    "api_key",
    "apikey",
    "password",
    "credential",
    "private",
    "wallet",
    "seed",
    "recovery",
    ".env",
    "key",
}

SKIP_DIR_NAMES = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "cache",
    ".cache",
    "secure",
}


@dataclass
class SafeToolResult:
    ok: bool
    action: str
    message: str
    data: Any = None
    blocked: bool = False
    reason: str = ""
    path: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return cleaned or "folder"


def _resolve(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


class ApprovedFolderRegistry:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.registry_file = lucy_data_dir / "approved_folders.json"
        self.lucy_data_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _default_data(self) -> dict:
        return {
            "version": SAFE_TOOLS_VERSION,
            "approved_folders": [],
            "blocked_paths": [],
            "last_updated": None,
        }

    def _ensure_file(self) -> None:
        if not self.registry_file.exists():
            safe_write_json(self.registry_file, self._default_data())

    def _read(self) -> dict:
        data = safe_read_json(self.registry_file, self._default_data())
        data.setdefault("version", SAFE_TOOLS_VERSION)
        data.setdefault("approved_folders", [])
        data.setdefault("blocked_paths", [])
        data.setdefault("last_updated", None)
        return data

    def _write(self, data: dict) -> None:
        data["last_updated"] = _now()
        safe_write_json(self.registry_file, data, backup=True)

    def list_approved_folders(self) -> SafeToolResult:
        data = self._read()
        return SafeToolResult(
            ok=True,
            action="list_approved_folders",
            message=f"{len(data['approved_folders'])} approved folder(s).",
            data=data["approved_folders"],
            blocked=False,
            path=str(self.registry_file),
        )

    def add_approved_folder(self, path: str | Path, name: str | None = None, notes: str = "") -> SafeToolResult:
        try:
            resolved = _resolve(path)
        except Exception as exc:
            return SafeToolResult(False, "add_approved_folder", "Folder not approved.", blocked=True, reason=str(exc), path=str(path))

        if not resolved.exists() or not resolved.is_dir():
            return SafeToolResult(
                ok=False,
                action="add_approved_folder",
                message="Folder not approved.",
                blocked=True,
                reason="Path must be an existing folder.",
                path=str(resolved),
            )

        data = self._read()
        folder_name = name or resolved.name or "Approved Folder"
        folder_id = _slug(folder_name)
        existing_ids = {item.get("id") for item in data["approved_folders"]}
        if folder_id in existing_ids:
            suffix = 2
            while f"{folder_id}_{suffix}" in existing_ids:
                suffix += 1
            folder_id = f"{folder_id}_{suffix}"

        for item in data["approved_folders"]:
            if _resolve(item.get("path", "")) == resolved:
                item["enabled"] = True
                item["access"] = "read_only"
                self._write(data)
                return SafeToolResult(
                    ok=True,
                    action="add_approved_folder",
                    message="Approved folder already existed and is enabled.",
                    data=item,
                    path=str(resolved),
                )

        record = {
            "id": folder_id,
            "name": folder_name,
            "path": str(resolved),
            "access": "read_only",
            "enabled": True,
            "added_at": _now(),
            "notes": notes,
        }
        data["approved_folders"].append(record)
        self._write(data)
        return SafeToolResult(
            ok=True,
            action="add_approved_folder",
            message="Approved folder added for read-only access.",
            data=record,
            path=str(resolved),
        )

    def remove_approved_folder(self, folder_id: str) -> SafeToolResult:
        data = self._read()
        before = len(data["approved_folders"])
        data["approved_folders"] = [item for item in data["approved_folders"] if item.get("id") != folder_id]
        if len(data["approved_folders"]) == before:
            return SafeToolResult(
                ok=False,
                action="remove_approved_folder",
                message="Approved folder not removed.",
                blocked=True,
                reason="Folder id was not found.",
            )
        self._write(data)
        return SafeToolResult(
            ok=True,
            action="remove_approved_folder",
            message=f"Approved folder removed: {folder_id}",
            data={"removed": folder_id},
        )

    def get_folder(self, folder_id: str) -> dict | None:
        for item in self._read()["approved_folders"]:
            if item.get("id") == folder_id:
                return item
        return None

    def enabled_folders(self) -> list[dict]:
        return [item for item in self._read()["approved_folders"] if item.get("enabled") and item.get("access") == "read_only"]

    def is_path_allowed(self, path: str | Path) -> SafeToolResult:
        try:
            candidate = _resolve(path)
        except Exception as exc:
            return SafeToolResult(False, "is_path_allowed", "Path is not allowed.", blocked=True, reason=str(exc), path=str(path))

        for folder in self.enabled_folders():
            root = _resolve(folder["path"])
            if candidate == root or root in candidate.parents:
                return SafeToolResult(
                    ok=True,
                    action="is_path_allowed",
                    message="Path is inside an enabled approved folder.",
                    data={"folder": folder},
                    path=str(candidate),
                )
        return SafeToolResult(
            ok=False,
            action="is_path_allowed",
            message="Path is outside approved folders.",
            blocked=True,
            reason="Lucy can only access enabled approved folders.",
            path=str(candidate),
        )


class SafeFileToolbox:
    def __init__(self, lucy_data_dir: Path) -> None:
        self.lucy_data_dir = lucy_data_dir
        self.registry = ApprovedFolderRegistry(lucy_data_dir)
        self.log_file = lucy_data_dir / "safe_tools_log.jsonl"
        self.audit_log_file = lucy_data_dir / "tool_audit_log.jsonl"
        self.policy = ToolActionPolicy()
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def list_approved_folders(self) -> SafeToolResult:
        result = self.registry.list_approved_folders()
        self._log(result)
        return result

    def add_approved_folder(self, path: str | Path, name: str | None = None, notes: str = "") -> SafeToolResult:
        result = self.registry.add_approved_folder(path, name=name, notes=notes)
        self._log(result)
        return result

    def remove_approved_folder(self, folder_id: str) -> SafeToolResult:
        result = self.registry.remove_approved_folder(folder_id)
        self._log(result, approved_folder_id=folder_id)
        return result

    def list_files(self, folder_id: str | None = None, max_depth: int = 3, max_items: int = 200) -> SafeToolResult:
        decision = self.policy.classify(
            ToolActionRequest("list_files", metadata={"max_depth": max_depth, "max_items": max_items})
        )
        if decision.requires_confirmation:
            result = self._confirmation_required("list_files", decision.reason, None, decision)
            self._log(result, approved_folder_id=folder_id)
            return result

        roots = self._selected_folders(folder_id)
        if isinstance(roots, SafeToolResult):
            self._log(roots, approved_folder_id=folder_id)
            return roots

        items: list[dict] = []
        skipped = 0
        for folder in roots:
            root = _resolve(folder["path"])
            for path in self._walk_files(root, max_depth=max_depth):
                if len(items) >= max_items:
                    break
                validation = self._validate_file_path(path)
                if not validation.ok:
                    skipped += 1
                    continue
                try:
                    stat = path.stat()
                    relative = str(path.relative_to(root)).replace("\\", "/")
                except OSError:
                    skipped += 1
                    continue
                items.append(
                    {
                        "folder_id": folder["id"],
                        "path": relative,
                        "size": stat.st_size,
                        "extension": path.suffix.lower(),
                    }
                )
        result = SafeToolResult(
            ok=True,
            action="list_files",
            message=f"Listed {len(items)} safe file(s).",
            data={"files": items, "skipped": skipped, "max_items": max_items},
        )
        self._log(result, approved_folder_id=folder_id)
        return result

    def read_text_file(self, path: str | Path, max_chars: int = 12000) -> SafeToolResult:
        candidate = self._resolve_requested_path(path)
        if isinstance(candidate, SafeToolResult):
            self._log(candidate)
            return candidate

        validation = self._validate_file_path(candidate)
        if not validation.ok:
            self._log(validation)
            return validation
        if not candidate.exists() or not candidate.is_file():
            result = self._blocked("read_text_file", "File does not exist.", candidate)
            self._log(result)
            return result
        try:
            stat = candidate.stat()
        except OSError as exc:
            result = self._blocked("read_text_file", f"Could not inspect file: {exc}", candidate)
            self._log(result)
            return result

        decision = self.policy.classify(
            ToolActionRequest(
                "read_text_file",
                target_path=str(candidate),
                metadata={"file_size": stat.st_size, "extension": candidate.suffix.lower()},
            )
        )
        if decision.requires_confirmation:
            result = self._confirmation_required("read_text_file", decision.reason, candidate, decision)
            self._log(result)
            return result

        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            result = self._blocked("read_text_file", f"Could not read file: {exc}", candidate)
            self._log(result)
            return result

        truncated = len(text) > max_chars
        result = SafeToolResult(
            ok=True,
            action="read_text_file",
            message="Safe text file read.",
            data={
                "text": text[:max_chars],
                "chars": min(len(text), max_chars),
                "truncated": truncated,
                "metadata": self._metadata(candidate),
            },
            path=str(candidate),
        )
        self._log(result)
        return result

    def search_text(
        self,
        query: str,
        folder_id: str | None = None,
        extensions: list[str] | None = None,
        max_results: int = 50,
    ) -> SafeToolResult:
        cleaned = query.strip()
        if not cleaned:
            result = self._blocked("search_text", "Search query was empty.", None)
            self._log(result, approved_folder_id=folder_id)
            return result
        decision = self.policy.classify(
            ToolActionRequest("search_text", metadata={"max_results": max_results})
        )
        if decision.requires_confirmation:
            result = self._confirmation_required("search_text", decision.reason, None, decision)
            self._log(result, approved_folder_id=folder_id)
            return result
        max_results = min(max_results, self.policy.MAX_SAFE_SEARCH_RESULTS)

        roots = self._selected_folders(folder_id)
        if isinstance(roots, SafeToolResult):
            self._log(roots, approved_folder_id=folder_id)
            return roots

        allowed_extensions = {ext.lower() for ext in extensions} if extensions else ALLOWED_EXTENSIONS
        allowed_extensions &= ALLOWED_EXTENSIONS
        matches: list[dict] = []
        lowered = cleaned.lower()
        skipped = 0
        for folder in roots:
            root = _resolve(folder["path"])
            for path in self._walk_files(root, max_depth=6):
                if len(matches) >= max_results:
                    break
                if path.suffix.lower() not in allowed_extensions:
                    continue
                validation = self._validate_file_path(path)
                if not validation.ok:
                    skipped += 1
                    continue
                try:
                    if path.stat().st_size > 750_000:
                        skipped += 1
                        continue
                    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                        if lowered in line.lower():
                            matches.append(
                                {
                                    "folder_id": folder["id"],
                                    "path": str(path.relative_to(root)).replace("\\", "/"),
                                    "line": line_number,
                                    "text": line.strip()[:220],
                                }
                            )
                            if len(matches) >= max_results:
                                break
                except OSError:
                    skipped += 1
        result = SafeToolResult(
            ok=True,
            action="search_text",
            message=f"Found {len(matches)} match(es).",
            data={"query": cleaned, "matches": matches, "skipped": skipped, "max_results": max_results},
        )
        self._log(result, approved_folder_id=folder_id)
        return result

    def summarize_tree(self, folder_id: str | None = None, max_depth: int = 3) -> SafeToolResult:
        listed = self.list_files(folder_id=folder_id, max_depth=max_depth, max_items=200)
        if not listed.ok:
            listed.action = "summarize_tree"
            return listed
        files = listed.data.get("files", []) if isinstance(listed.data, dict) else []
        by_extension: dict[str, int] = {}
        for item in files:
            extension = item.get("extension") or "(none)"
            by_extension[extension] = by_extension.get(extension, 0) + 1
        result = SafeToolResult(
            ok=True,
            action="summarize_tree",
            message=f"Summarized {len(files)} safe file(s).",
            data={"files": files, "by_extension": by_extension, "skipped": listed.data.get("skipped", 0)},
        )
        self._log(result, approved_folder_id=folder_id)
        return result

    def file_metadata(self, path: str | Path) -> SafeToolResult:
        candidate = self._resolve_requested_path(path)
        if isinstance(candidate, SafeToolResult):
            self._log(candidate)
            return candidate
        validation = self._validate_file_path(candidate)
        if not validation.ok:
            self._log(validation)
            return validation
        if not candidate.exists() or not candidate.is_file():
            result = self._blocked("file_metadata", "File does not exist.", candidate)
            self._log(result)
            return result
        result = SafeToolResult(
            ok=True,
            action="file_metadata",
            message="Safe file metadata returned.",
            data=self._metadata(candidate),
            path=str(candidate),
        )
        self._log(result)
        return result

    def status(self) -> SafeToolResult:
        folders = self.registry.enabled_folders()
        result = SafeToolResult(
            ok=True,
            action="status",
            message="Safe tools are available in read-only approved-folder mode.",
            data={
                "registry_file": str(self.registry.registry_file),
                "log_file": str(self.log_file),
                "audit_log_file": str(self.audit_log_file),
                "enabled_folders": len(folders),
                "approved_folder_count": len(folders),
                "allowed_extensions": sorted(ALLOWED_EXTENSIONS),
                "blocked_extensions": sorted(BLOCKED_EXTENSIONS),
                "sensitive_patterns": sorted(SENSITIVE_PATTERNS),
                "read_only": True,
                "safe_read_enabled": True,
                "write_enabled": False,
                "network_enabled": False,
                "execution_enabled": False,
                "confirmation_required_for_large_reads": True,
                "max_safe_read_bytes": self.policy.MAX_SAFE_READ_BYTES,
                "max_search_results": self.policy.MAX_SAFE_SEARCH_RESULTS,
            },
        )
        self._log(result)
        return result

    def _resolve_requested_path(self, path: str | Path) -> Path | SafeToolResult:
        raw = Path(path)
        if ".." in raw.parts:
            return self._blocked("path_validation", "Parent traversal is blocked.", raw)
        candidates = [raw] if raw.is_absolute() else [Path(folder["path"]) / raw for folder in self.registry.enabled_folders()]
        if not candidates:
            return self._blocked("path_validation", "No approved folders are enabled.", raw)
        for candidate in candidates:
            try:
                resolved = _resolve(candidate)
            except Exception:
                continue
            allowed = self.registry.is_path_allowed(resolved)
            if allowed.ok:
                return resolved
        return self._blocked("path_validation", "Path is outside approved folders.", raw)

    def _validate_file_path(self, path: Path) -> SafeToolResult:
        allowed = self.registry.is_path_allowed(path)
        if not allowed.ok:
            allowed.action = "file_validation"
            return allowed
        lowered_name = path.name.lower()
        lowered_full = str(path).replace("\\", "/").lower()
        if any(part.startswith(".") for part in path.parts if part not in {path.anchor, ""}):
            return self._blocked("file_validation", "Hidden paths are skipped by policy.", path)
        if any(name.lower() in SKIP_DIR_NAMES for name in path.parts):
            return self._blocked("file_validation", "System/cache/sensitive folders are skipped by policy.", path)
        if path.suffix.lower() in BLOCKED_EXTENSIONS:
            return self._blocked("file_validation", f"Blocked extension: {path.suffix.lower()}", path)
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            return self._blocked("file_validation", f"Extension is not allowed: {path.suffix.lower() or '(none)'}", path)
        if any(pattern in lowered_name or pattern in lowered_full for pattern in SENSITIVE_PATTERNS):
            return self._blocked("file_validation", "Sensitive filename pattern is blocked.", path)
        return SafeToolResult(True, "file_validation", "File path is safe.", path=str(path))

    def _selected_folders(self, folder_id: str | None) -> list[dict] | SafeToolResult:
        if folder_id:
            folder = self.registry.get_folder(folder_id)
            if not folder or not folder.get("enabled"):
                return SafeToolResult(False, "select_folder", "Folder not available.", blocked=True, reason="Approved folder id not found or disabled.")
            return [folder]
        folders = self.registry.enabled_folders()
        if not folders:
            return SafeToolResult(False, "select_folder", "No approved folders.", blocked=True, reason="Approve a folder first.")
        return folders

    def _walk_files(self, root: Path, max_depth: int):
        for current_root, dirs, names in os.walk(root):
            current = Path(current_root)
            try:
                relative_parts = current.relative_to(root).parts
            except ValueError:
                continue
            if len(relative_parts) >= max_depth:
                dirs[:] = []
            dirs[:] = [
                dirname for dirname in dirs
                if not dirname.startswith(".") and dirname not in SKIP_DIR_NAMES
            ]
            for name in names:
                yield current / name

    def _metadata(self, path: Path) -> dict:
        stat = path.stat()
        allowed = self.registry.is_path_allowed(path)
        folder = allowed.data.get("folder", {}) if isinstance(allowed.data, dict) else {}
        root = _resolve(folder["path"]) if folder else path.parent
        return {
            "folder_id": folder.get("id"),
            "name": path.name,
            "relative_path": str(path.relative_to(root)).replace("\\", "/") if root in path.parents or path == root else path.name,
            "size": stat.st_size,
            "extension": path.suffix.lower(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        }

    def _blocked(self, action: str, reason: str, path: str | Path | None) -> SafeToolResult:
        return SafeToolResult(
            ok=False,
            action=action,
            message="Safe file tool request refused.",
            blocked=True,
            reason=reason,
            path=str(path) if path is not None else None,
        )

    def _confirmation_required(
        self,
        action: str,
        reason: str,
        path: str | Path | None,
        decision,
    ) -> SafeToolResult:
        return SafeToolResult(
            ok=False,
            action=action,
            message="Safe file tool request requires manual confirmation.",
            data={
                "requires_confirmation": True,
                "policy_decision": decision.to_dict(),
                "summary": "No file contents were read or logged.",
            },
            blocked=False,
            reason=reason,
            path=str(path) if path is not None else None,
        )

    def _log(self, result: SafeToolResult, approved_folder_id: str | None = None) -> None:
        record = {
            "timestamp": _now(),
            "action": result.action,
            "requested_path": result.path,
            "approved_folder_id": approved_folder_id,
            "result": "ok" if result.ok else "refused",
            "blocked": result.blocked,
            "reason": result.reason,
        }
        try:
            with open(self.log_file, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass
        self._log_audit(result, approved_folder_id=approved_folder_id)

    def _log_audit(self, result: SafeToolResult, approved_folder_id: str | None = None) -> None:
        data = result.data if isinstance(result.data, dict) else {}
        policy = data.get("policy_decision") if isinstance(data.get("policy_decision"), dict) else {}
        record = {
            "timestamp": _now(),
            "session_count": None,
            "active_project": None,
            "action_name": result.action,
            "target_path": result.path,
            "approved_folder_id": approved_folder_id,
            "policy_category": policy.get("category"),
            "guardian_classification": data.get("guardian_classification"),
            "confirmation_id": data.get("confirmation_id"),
            "result": self._audit_result_label(result),
            "reason": result.reason,
        }
        try:
            with open(self.audit_log_file, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _audit_result_label(self, result: SafeToolResult) -> str:
        data = result.data if isinstance(result.data, dict) else {}
        if data.get("requires_confirmation"):
            return "requires_confirmation"
        if result.blocked:
            return "blocked"
        if result.ok:
            return "allowed"
        return "refused"
