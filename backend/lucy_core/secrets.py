"""
secrets.py
Session and encrypted permanent secret handling for Lucy.

Session secrets live only inside the current Python process. Permanent secrets
are encrypted with Windows DPAPI for the current Windows user before they are
written to Lucy's secure folder.
"""

from __future__ import annotations

import base64
import ctypes
import getpass
import json
import os
import sys
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(wintypes.BYTE)),
    ]


def _require_windows_dpapi() -> None:
    if sys.platform != "win32":
        raise RuntimeError("Permanent secret storage requires Windows DPAPI on this build.")


def _protect_with_dpapi(value: str) -> str:
    _require_windows_dpapi()
    data = value.encode("utf-8")
    in_buffer = ctypes.create_string_buffer(data)
    in_blob = _DataBlob(len(data), ctypes.cast(in_buffer, ctypes.POINTER(wintypes.BYTE)))
    out_blob = _DataBlob()

    crypt32 = ctypes.windll.crypt32
    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        wintypes.LPCWSTR,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL

    ok = crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        "Lucy local secret",
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    if not ok:
        raise ctypes.WinError()

    try:
        encrypted = ctypes.string_at(out_blob.pbData, out_blob.cbData)
        return base64.b64encode(encrypted).decode("ascii")
    finally:
        ctypes.windll.kernel32.LocalFree(ctypes.cast(out_blob.pbData, ctypes.c_void_p))


def _unprotect_with_dpapi(value: str) -> str:
    _require_windows_dpapi()
    encrypted = base64.b64decode(value.encode("ascii"))
    in_buffer = ctypes.create_string_buffer(encrypted)
    in_blob = _DataBlob(len(encrypted), ctypes.cast(in_buffer, ctypes.POINTER(wintypes.BYTE)))
    out_blob = _DataBlob()

    crypt32 = ctypes.windll.crypt32
    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL

    ok = crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    if not ok:
        raise ctypes.WinError()

    try:
        decrypted = ctypes.string_at(out_blob.pbData, out_blob.cbData)
        return decrypted.decode("utf-8")
    finally:
        ctypes.windll.kernel32.LocalFree(ctypes.cast(out_blob.pbData, ctypes.c_void_p))


class SessionSecretStore:
    def __init__(self, secure_dir: Path | None = None) -> None:
        self._session_values: dict[str, str] = {}
        self.secure_dir = secure_dir
        if self.secure_dir is not None:
            self.secure_dir.mkdir(parents=True, exist_ok=True)

    def _secret_path(self, env_var: str) -> Path | None:
        if self.secure_dir is None:
            return None
        safe_name = "".join(part if part.isalnum() or part in {"_", "-"} else "_" for part in env_var)
        return self.secure_dir / f"{safe_name}.dpapi.json"

    def has(self, env_var: str) -> bool:
        return bool(self._session_values.get(env_var) or os.environ.get(env_var) or self._get_persistent_secret(env_var))

    def get(self, env_var: str) -> str:
        return self._session_values.get(env_var) or os.environ.get(env_var) or self._get_persistent_secret(env_var)

    def status(self, provider: str, env_var: str) -> dict:
        persistent_path = self._secret_path(env_var)
        persistent_available = bool(persistent_path and persistent_path.exists())
        source = (
            "session"
            if self._session_values.get(env_var)
            else "environment"
            if os.environ.get(env_var)
            else "persistent_encrypted"
            if self._get_persistent_secret(env_var)
            else "missing"
        )
        return {
            "provider": provider,
            "env_var": env_var,
            "available": self.has(env_var),
            "source": source,
            "persistent_available": persistent_available,
            "persistent_path": str(persistent_path) if persistent_path else "",
        }

    def set_session_secret(self, provider: str, env_var: str, value: str) -> dict:
        cleaned = value.strip()
        if not cleaned:
            return {"saved": False, "reason": "No key was entered."}
        if len(cleaned) < 12:
            return {"saved": False, "reason": "That key looks too short."}

        self._session_values[env_var] = cleaned
        os.environ[env_var] = cleaned
        return {
            "saved": True,
            "provider": provider,
            "env_var": env_var,
            "scope": "current_lucy_session_only",
        }

    def set_persistent_secret(self, provider: str, env_var: str, value: str) -> dict:
        cleaned = value.strip()
        if not cleaned:
            return {"saved": False, "reason": "No key was entered."}
        if len(cleaned) < 12:
            return {"saved": False, "reason": "That key looks too short."}

        path = self._secret_path(env_var)
        if path is None:
            return {"saved": False, "reason": "Permanent secure folder is not configured."}

        try:
            encrypted = _protect_with_dpapi(cleaned)
        except Exception as exc:
            return {"saved": False, "reason": f"Encrypted save failed: {exc}"}

        record = {
            "provider": provider,
            "env_var": env_var,
            "storage": "windows_dpapi_current_user",
            "created_or_updated_at": _now(),
            "encrypted_value": encrypted,
        }
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        self._session_values[env_var] = cleaned
        os.environ[env_var] = cleaned
        return {
            "saved": True,
            "provider": provider,
            "env_var": env_var,
            "scope": "permanent_encrypted_current_windows_user",
            "storage": "windows_dpapi_current_user",
            "path": str(path),
        }

    def _get_persistent_secret(self, env_var: str) -> str:
        path = self._secret_path(env_var)
        if path is None or not path.exists():
            return ""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("env_var") != env_var:
                return ""
            encrypted = data.get("encrypted_value", "")
            if not encrypted:
                return ""
            value = _unprotect_with_dpapi(encrypted)
        except Exception:
            return ""
        self._session_values[env_var] = value
        os.environ[env_var] = value
        return value

    def forget_persistent_secret(self, env_var: str) -> dict:
        path = self._secret_path(env_var)
        self._session_values.pop(env_var, None)
        os.environ.pop(env_var, None)
        if path is None or not path.exists():
            return {"forgotten": False, "reason": "No permanent key was found."}
        path.unlink()
        return {"forgotten": True, "path": str(path)}

    def prompt_for_secret(self, provider: str, env_var: str, permanent: bool = False) -> dict:
        print(f"{provider} key setup")
        if permanent:
            print("Paste the key below. Input is hidden. Lucy will encrypt it for this Windows user.")
        else:
            print("Paste the key below. Input is hidden. Lucy will keep it only for this session.")
        value = getpass.getpass(f"{env_var}: ")
        if permanent:
            return self.set_persistent_secret(provider, env_var, value)
        return self.set_session_secret(provider, env_var, value)
