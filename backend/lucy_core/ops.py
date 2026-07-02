"""
ops.py
Safe local operations inspired by ELIE safe_ops.

Lucy can scan and back up her own project folder. She cannot silently rewrite
files through this module.
"""

from __future__ import annotations

import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path


SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "venv", ".venv"}
SENSITIVE_PARTS = {".env", "secure", "secret", "password", "credential", "private_key", "wallet", "seed"}
RISKY_CODE_MARKERS = ["shutil.rmtree(", "os.remove(", "os.system(", "shell=True", "eval(", "exec(", "subprocess"]


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


class SafeOps:
    def __init__(self, project_root: Path, lucy_data_dir: Path) -> None:
        self.project_root = project_root.resolve()
        self.ops_dir = lucy_data_dir / "ops"
        self.backups_dir = self.ops_dir / "backups"
        self.reports_dir = self.ops_dir / "reports"
        self.proposals_dir = self.ops_dir / "proposals"
        for folder in [self.ops_dir, self.backups_dir, self.reports_dir, self.proposals_dir]:
            folder.mkdir(parents=True, exist_ok=True)

    def _relative(self, path: Path) -> str:
        return str(path.relative_to(self.project_root)).replace("\\", "/")

    def _is_sensitive(self, path: Path) -> bool:
        lowered = self._relative(path).lower() if self.project_root in path.resolve().parents else str(path).lower()
        return any(part in lowered for part in SENSITIVE_PARTS)

    def _iter_project_files(self) -> list[Path]:
        files: list[Path] = []
        for root, dirs, names in os.walk(self.project_root):
            dirs[:] = [dirname for dirname in dirs if dirname not in SKIP_DIRS]
            root_path = Path(root)
            for name in names:
                path = root_path / name
                if self._is_sensitive(path):
                    continue
                files.append(path)
        return files

    def backup_project(self) -> dict:
        out = self.backups_dir / f"lucy_backup_{_stamp()}.zip"
        count = 0
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in self._iter_project_files():
                relative = self._relative(path)
                if relative.startswith("data/lucy/ops/backups/"):
                    continue
                archive.write(path, relative)
                count += 1
        return {"created": True, "path": str(out), "files": count}

    def scan_project(self) -> dict:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "root": str(self.project_root),
            "checks": [],
            "suggestions": [],
        }
        for required in ["run_lucy_core.py", "backend/lucy_core/lucy_runtime.py", "backend/lucy_core/router.py"]:
            path = self.project_root / required
            report["checks"].append({"name": required, "exists": path.exists()})

        for path in self._iter_project_files():
            if path.suffix.lower() != ".py":
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for marker in RISKY_CODE_MARKERS:
                if marker in text:
                    report["suggestions"].append(
                        {
                            "file": self._relative(path),
                            "marker": marker,
                            "note": "Review before allowing automation or self-modification.",
                        }
                    )

        out = self.reports_dir / f"lucy_scan_{_stamp()}.json"
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        report["report_path"] = str(out)
        return report
