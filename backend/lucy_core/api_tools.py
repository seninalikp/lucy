"""
api_tools.py
External API tools for Lucy.

External providers are language tools for Lucy's safe chat layer. They do not
become Lucy's identity, and they must never expose key material.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from backend.lucy_core.secrets import _unprotect_with_dpapi


NVIDIA_CHAT_COMPLETIONS_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_NVIDIA_MODEL = "nvidia/llama-3.1-nemotron-nano-8b-v1"

OPENAI_COMPATIBLE_ENDPOINTS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "sambanova": "https://api.sambanova.ai/v1/chat/completions",
}

DEFAULT_MODELS = {
    "groq": "llama-3.1-8b-instant",
    "openrouter": "openrouter/auto",
    "sambanova": "Meta-Llama-3.3-70B-Instruct",
    "gemini": "gemini-2.5-flash",
}

PROVIDER_ENV_NAMES = {
    "nvidia": ["NVIDIA_API_KEY"],
    "groq": ["GROQ_API_KEY", "GROQ_KEY"],
    "openrouter": [
        "OPENROUTER_API_KEY",
        "OPENROUTER_KEY",
        "OPEN_ROUTER_API_KEY",
        "OPEN_ROUTER_KEY",
        "SUPERROUTER_API_KEY",
        "SUPERROUTER_KEY",
    ],
    "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY", "GENAI_API_KEY"],
    "sambanova": ["SAMBANOVA_API_KEY", "SAMBANOVA_KEY", "SAMBA_API_KEY", "SAMBA_KEY"],
}

PROVIDER_VAULT_NAMES = {
    "groq": ["groq"],
    "openrouter": ["openrouter", "superrouter"],
    "gemini": ["gemini"],
    "sambanova": ["sambanova", "sambanova_1", "sambanova_2", "sambanova_3", "sambanova_4"],
}

DEFAULT_PROVIDER_ORDER = ["groq", "openrouter", "gemini", "sambanova"]
ELIE_MAGIC = "ELIEKEY:"


def _redact(text: str) -> str:
    patterns = [
        r"gsk_[A-Za-z0-9_\-]+",
        r"sk-[A-Za-z0-9_\-]+",
        r"AIza[A-Za-z0-9_\-]+",
        r"Bearer\s+[A-Za-z0-9_\.\-]+",
        r"api[_ -]?key\s*[:=]\s*['\"]?[^'\"\s]+",
    ]
    redacted = str(text)
    for pattern in patterns:
        redacted = re.sub(pattern, "[redacted]", redacted, flags=re.IGNORECASE)
    return redacted


def _safe_secret_path_name(env_var: str) -> str:
    return "".join(part if part.isalnum() or part in {"_", "-"} else "_" for part in env_var)


def _clean_key(value: object) -> str:
    if value is None:
        return ""
    cleaned = str(value).strip().strip('"').strip("'")
    if len(cleaned) < 12:
        return ""
    return cleaned


@dataclass
class KeyLookup:
    value: str
    source: str


class ProviderKeySource:
    def __init__(self, project_root: Path | None = None, elie_root: Path | None = None) -> None:
        self.project_root = project_root
        self.elie_root = elie_root or self._find_elie_root()
        self._cache: dict[str, KeyLookup] = {}
        self._elie_master_password: str | None = None

    def _find_elie_root(self) -> Path | None:
        configured = os.environ.get("LUCY_ELIE_ROOT", "").strip()
        candidates: list[Path] = []
        if configured:
            candidates.append(Path(configured))

        home = Path.home()
        candidates.extend(
            [
                home / "Downloads" / "AI COLLECTIONS" / "AI COLLECTIONS" / "ELIE",
                home / "Downloads" / "AI COLLECTIONS" / "ELIE",
                home / "Documents" / "AI COLLECTIONS" / "AI COLLECTIONS" / "ELIE",
                home / "Documents" / "AI COLLECTIONS" / "ELIE",
            ]
        )

        for candidate in candidates:
            if candidate.exists() and (candidate / "api").exists():
                return candidate
        return None

    def elie_status(self) -> dict:
        available = bool(self.elie_root and self.elie_root.exists())
        return {
            "root": str(self.elie_root) if available else "",
            "available": available,
            "vault_available": bool(available and (self.elie_root / "api" / "secure").exists()),
            "auto_unlock_available": bool(available and self._load_elie_master_password()),
        }

    def get(self, provider: str) -> KeyLookup:
        provider = provider.lower().strip()
        if provider in self._cache:
            return self._cache[provider]

        lookup = (
            self._from_environment(provider)
            or self._from_lucy_dpapi(provider)
            or self._from_elie_vault(provider)
            or self._from_elie_loose_files(provider)
            or KeyLookup("", "missing")
        )
        if lookup.value:
            self._cache[provider] = lookup
        return lookup

    def available(self, provider: str) -> bool:
        return bool(self.get(provider).value)

    def _from_environment(self, provider: str) -> KeyLookup | None:
        for env_var in PROVIDER_ENV_NAMES.get(provider, []):
            value = _clean_key(os.environ.get(env_var))
            if value:
                return KeyLookup(value, f"environment:{env_var}")
        return None

    def _from_lucy_dpapi(self, provider: str) -> KeyLookup | None:
        if self.project_root is None:
            return None
        secure_dir = self.project_root / "data" / "lucy" / "secure"
        for env_var in PROVIDER_ENV_NAMES.get(provider, []):
            path = secure_dir / f"{_safe_secret_path_name(env_var)}.dpapi.json"
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("env_var") != env_var:
                    continue
                value = _clean_key(_unprotect_with_dpapi(data.get("encrypted_value", "")))
            except Exception:
                continue
            if value:
                os.environ[env_var] = value
                return KeyLookup(value, f"lucy_dpapi:{env_var}")
        return None

    def _load_elie_master_password(self) -> str:
        if self._elie_master_password is not None:
            return self._elie_master_password
        self._elie_master_password = ""
        if not self.elie_root:
            return ""
        unlock_file = self.elie_root / "local_unlock.py"
        if not unlock_file.exists():
            return ""
        try:
            text = unlock_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
        if not re.search(r"UNLOCK_ALL\s*=\s*True", text):
            return ""
        match = re.search(r"MASTER_PASSWORD\s*=\s*['\"]([^'\"]+)['\"]", text)
        if not match:
            return ""
        self._elie_master_password = match.group(1)
        return self._elie_master_password

    def _from_elie_vault(self, provider: str) -> KeyLookup | None:
        if provider == "nvidia" or not self.elie_root:
            return None
        password = self._load_elie_master_password()
        if not password:
            return None
        secure_dir = self.elie_root / "api" / "secure"
        for name in PROVIDER_VAULT_NAMES.get(provider, [provider]):
            path = secure_dir / f"{name}.key.enc"
            if not path.exists():
                continue
            value = self._decrypt_elie_key_file(path, password)
            if value:
                return KeyLookup(value, f"elie_vault:{name}")
        return None

    def _decrypt_elie_key_file(self, path: Path, password: str) -> str:
        try:
            raw = base64.b64decode(path.read_text(encoding="utf-8").strip().encode("ascii"))
            decoded = self._elie_xor(raw, password).decode("utf-8", errors="ignore")
        except Exception:
            return ""
        if not decoded.startswith(ELIE_MAGIC):
            return ""
        return _clean_key(decoded[len(ELIE_MAGIC):])

    def _elie_xor(self, raw: bytes, password: str) -> bytes:
        pad = b""
        index = 0
        while len(pad) < len(raw):
            pad += hashlib.sha256((password + ":" + str(index)).encode("utf-8")).digest()
            index += 1
        return bytes(raw[i] ^ pad[i] for i in range(len(raw)))

    def _from_elie_loose_files(self, provider: str) -> KeyLookup | None:
        if not self.elie_root:
            return None
        key_names = {name.upper() for name in PROVIDER_ENV_NAMES.get(provider, [])}
        if not key_names:
            return None

        search_files: list[Path] = []
        for pattern in ("*.env", ".env", "*.json", "*.txt", "*.py"):
            search_files.extend(self.elie_root.rglob(pattern))

        skip_parts = {
            "__pycache__",
            ".git",
            "desktop_uploads",
            "desktop_voice",
            "elie_ops",
            "backups",
            "fixer_backups",
            "neural_backups",
        }

        for path in search_files:
            lower_parts = {part.lower() for part in path.parts}
            if lower_parts & skip_parts:
                continue
            value = ""
            if path.suffix.lower() == ".json":
                value = self._scan_json_file(path, key_names)
            if not value and (path.suffix.lower() in {".env", ".txt", ".py"} or path.name.lower() == ".env"):
                value = self._scan_env_text_file(path, key_names)
            if value:
                return KeyLookup(value, f"elie_file:{path.name}")
        return None

    def _scan_env_text_file(self, path: Path, key_names: set[str]) -> str:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
        for line in text.splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            for key_name in key_names:
                if raw.upper().startswith(key_name + "="):
                    return _clean_key(raw.split("=", 1)[1])
                if raw.upper().startswith(key_name + ":"):
                    return _clean_key(raw.split(":", 1)[1])
        return ""

    def _scan_json_file(self, path: Path, key_names: set[str]) -> str:
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            return ""

        def walk(obj) -> str:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if str(key).upper() in key_names:
                        found = _clean_key(value)
                        if found:
                            return found
                    found = walk(value)
                    if found:
                        return found
            if isinstance(obj, list):
                for item in obj:
                    found = walk(item)
                    if found:
                        return found
            return ""

        return walk(data)


class NvidiaMemoryTool:
    def status(self, key_available: bool) -> dict:
        return {
            "name": "nvidia_memory_fallback",
            "provider": "nvidia",
            "available": key_available,
            "endpoint": NVIDIA_CHAT_COMPLETIONS_URL,
            "model": os.environ.get("NVIDIA_MODEL", DEFAULT_NVIDIA_MODEL),
            "role": "memory_fallback_tool_not_lucy_brain",
        }

    def memory_fallback(self, query: str, local_context: str, api_key: str, timeout: int = 30) -> dict:
        if not api_key:
            return {"ok": False, "reason": "NVIDIA_API_KEY is not available."}

        system_prompt = (
            "You are an external memory fallback tool for Lucy. "
            "You are not Lucy and not her brain. Return concise, practical memory hints only. "
            "Do not ask for secrets. Do not claim identity. If unsure, say so."
        )
        user_prompt = (
            "Lucy local memory did not fully answer this query.\n\n"
            f"Query: {query}\n\n"
            f"Local context summary:\n{local_context[:2000]}\n\n"
            "Return: likely relevant memory hints, missing info, and next local action."
        )
        payload = {
            "model": os.environ.get("NVIDIA_MODEL", DEFAULT_NVIDIA_MODEL),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 600,
            "stream": False,
        }
        request = urllib.request.Request(
            NVIDIA_CHAT_COMPLETIONS_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
            data = json.loads(raw)
            text = data["choices"][0]["message"]["content"]
            return {
                "ok": True,
                "provider": "nvidia",
                "model": payload["model"],
                "text": text,
                "saved_as": "external_suggestion_not_long_term_memory",
            }
        except Exception as exc:
            return {
                "ok": False,
                "provider": "nvidia",
                "reason": _redact(str(exc)),
            }


class ExternalChatTool:
    def __init__(self, key_source: ProviderKeySource) -> None:
        self.key_source = key_source

    def status(self, provider: str) -> dict:
        provider = provider.lower().strip()
        lookup = self.key_source.get(provider)
        return {
            "name": f"{provider}_chat",
            "provider": provider,
            "available": bool(lookup.value),
            "model": self._model_for(provider),
            "role": "external_chat_tool_for_lucy_safe_language_layer",
            "key_source": lookup.source if lookup.value else "missing",
        }

    def ask(self, provider: str, prompt: str, system_prompt: str, timeout: int = 45) -> dict:
        provider = provider.lower().strip()
        lookup = self.key_source.get(provider)
        if not lookup.value:
            return {"ok": False, "provider": provider, "reason": f"{provider} key not found"}

        if provider == "gemini":
            return self._ask_gemini(prompt, system_prompt, lookup, timeout)

        if provider in OPENAI_COMPATIBLE_ENDPOINTS:
            return self._ask_openai_compatible(provider, prompt, system_prompt, lookup, timeout)

        return {"ok": False, "provider": provider, "reason": f"Unknown provider: {provider}"}

    def _model_for(self, provider: str) -> str:
        env_name = f"LUCY_{provider.upper()}_MODEL"
        return os.environ.get(env_name) or os.environ.get(f"{provider.upper()}_MODEL") or DEFAULT_MODELS[provider]

    def _ask_openai_compatible(self, provider: str, prompt: str, system_prompt: str, lookup: KeyLookup, timeout: int) -> dict:
        payload = {
            "model": self._model_for(provider),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.35,
            "max_tokens": 900,
            "stream": False,
        }
        headers = {
            "Authorization": "Bearer " + lookup.value,
            "Content-Type": "application/json",
            "User-Agent": "Lucy/0.1 local",
        }
        if provider == "openrouter":
            headers["HTTP-Referer"] = "http://localhost/lucy"
            headers["X-Title"] = "Lucy Local"

        request = urllib.request.Request(
            OPENAI_COMPATIBLE_ENDPOINTS[provider],
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="ignore")
            data = json.loads(raw)
            return {
                "ok": True,
                "provider": provider,
                "model": payload["model"],
                "text": data["choices"][0]["message"]["content"],
                "key_source": lookup.source,
            }
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            return {"ok": False, "provider": provider, "reason": _redact(f"HTTP {exc.code}: {body[:500]}")}
        except Exception as exc:
            return {"ok": False, "provider": provider, "reason": _redact(str(exc))}

    def _ask_gemini(self, prompt: str, system_prompt: str, lookup: KeyLookup, timeout: int) -> dict:
        model = self._model_for("gemini")
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": system_prompt + "\n\n" + prompt},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.35,
                "maxOutputTokens": 900,
            },
        }
        request = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-goog-api-key": lookup.value,
                "Content-Type": "application/json",
                "User-Agent": "Lucy/0.1 local",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="ignore")
            data = json.loads(raw)
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts)
            return {
                "ok": True,
                "provider": "gemini",
                "model": model,
                "text": text,
                "key_source": lookup.source,
            }
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            return {"ok": False, "provider": "gemini", "reason": _redact(f"HTTP {exc.code}: {body[:500]}")}
        except Exception as exc:
            return {"ok": False, "provider": "gemini", "reason": _redact(str(exc))}


class ExternalToolRouter:
    def __init__(self, project_root: Path | None = None, elie_root: Path | None = None) -> None:
        self.key_source = ProviderKeySource(project_root=project_root, elie_root=elie_root)
        self.nvidia_memory = NvidiaMemoryTool()
        self.chat_tool = ExternalChatTool(self.key_source)

    def provider_order(self) -> list[str]:
        configured = os.environ.get("LUCY_API_ORDER", "")
        if configured:
            providers = [item.strip().lower() for item in configured.split(",") if item.strip()]
            providers = ["openrouter" if provider == "superrouter" else provider for provider in providers]
            return [provider for provider in providers if provider in DEFAULT_PROVIDER_ORDER]
        return list(DEFAULT_PROVIDER_ORDER)

    def status(self, nvidia_key_available: bool | None = None) -> dict:
        nvidia_available = self.key_source.available("nvidia") if nvidia_key_available is None else nvidia_key_available
        tools = [self.nvidia_memory.status(nvidia_available)]
        tools.extend(self.chat_tool.status(provider) for provider in self.provider_order())
        return {
            "tools": tools,
            "provider_order": self.provider_order(),
            "elie_key_source": self.key_source.elie_status(),
        }

    def chat(self, prompt: str, system_prompt: str, provider: str = "auto") -> dict:
        provider = provider.lower().strip()
        providers = self.provider_order() if provider in {"", "auto"} else [provider]
        providers = ["openrouter" if item == "superrouter" else item for item in providers]

        attempts = []
        for name in providers:
            if name not in DEFAULT_PROVIDER_ORDER:
                attempts.append({"provider": name, "ok": False, "reason": "unsupported"})
                continue
            result = self.chat_tool.ask(name, prompt, system_prompt)
            attempts.append({
                "provider": name,
                "ok": result.get("ok", False),
                "reason": result.get("reason", ""),
            })
            if result.get("ok"):
                result["attempts"] = attempts
                return result
        return {
            "ok": False,
            "provider": "none",
            "reason": "No external provider answered.",
            "attempts": attempts,
        }
