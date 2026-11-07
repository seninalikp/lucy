"""
ollama_connector.py
Stage 36 / Stage 66 Upgraded = Native Multi-Turn Message Arrays & Sovereign Ollama Connector.

Supports native message arrays `messages: [{"role": "system/user/assistant"}, ...]`
instead of flattened prompt strings, allowing local models to maintain deep conversational context.
"""

from __future__ import annotations

import json
import socket
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any


STAGE = "36 local ollama sovereign connector"
STAGE_66 = "66 native multi-turn message arrays and coreference resolver"
DEFAULT_OLLAMA_ENDPOINT = "http://localhost:11434"
DEFAULT_SOVEREIGN_MODEL = "lucy:personal"


class OllamaConnector:
    """Sovereign local LLM connector supporting native multi-turn message arrays."""

    def __init__(self, lucy_data: Path, endpoint: str = DEFAULT_OLLAMA_ENDPOINT) -> None:
        self.lucy_data = Path(lucy_data)
        self.endpoint = endpoint.rstrip("/")
        self.adapters_dir = self.lucy_data / "adapters"
        self.adapters_dir.mkdir(parents=True, exist_ok=True)
        self.store_file = self.lucy_data / "ollama_connector_status.json"

    def _http_endpoint(self) -> str:
        """Returns the HTTP endpoint, mapping localhost -> 127.0.0.1 for fast Windows IPv4 dispatch."""
        if "://localhost" in self.endpoint:
            return self.endpoint.replace("://localhost", "://127.0.0.1")
        return self.endpoint

    def is_online(self) -> bool:
        """Fast non-blocking check if local Ollama daemon is listening on port 11434."""
        try:
            host = "127.0.0.1"
            port = 11434
            if "://" in self.endpoint:
                clean = self.endpoint.split("://")[1]
                parts = clean.split(":")
                host = parts[0]
                if host in ("localhost", "127.0.0.1"):
                    host = "127.0.0.1"
                if len(parts) > 1:
                    port = int(parts[1].split("/")[0])
            s = socket.create_connection((host, port), timeout=0.3)
            s.close()
            return True
        except (OSError, socket.timeout):
            return False

    def ensure_online(self, max_wait_seconds: float = 3.0) -> bool:
        """If Ollama is offline, automatically launches 'ollama serve' in background and waits for port to open."""
        if self.is_online():
            return True
        import shutil
        import subprocess
        ollama_bin = shutil.which("ollama") or r"C:\Users\admin\AppData\Local\Programs\Ollama\ollama.exe"
        if Path(ollama_bin).exists():
            try:
                subprocess.Popen(
                    [str(ollama_bin), "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except Exception:
                pass
        import time
        start = time.time()
        while time.time() - start < max_wait_seconds:
            if self.is_online():
                return True
            time.sleep(0.3)
        return self.is_online()

    def list_local_models(self) -> list[str]:
        if not self.is_online():
            return []
        try:
            req = urllib.request.Request(f"{self._http_endpoint()}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except Exception:
            return []

    def detect_active_adapters(self) -> list[str]:
        """Scans data/lucy/adapters/ for LoRA adapter files (.safetensors, .bin, .gguf)."""
        if not self.adapters_dir.exists():
            return []
        adapters = [
            f.name for f in self.adapters_dir.iterdir()
            if f.is_file() and f.suffix.lower() in (".safetensors", ".bin", ".gguf")
        ]
        return sorted(adapters)

    def list_models(self) -> list[dict[str, Any]]:
        """Returns list of {"name": model_name} dicts for compatibility with Stage 42/45."""
        return [{"name": m} for m in self.list_local_models()]

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
    ) -> dict[str, Any]:
        """Compatibility wrapper around chat_messages for CodeSynthesisPipeline and SanityGate."""
        target_model = model or DEFAULT_SOVEREIGN_MODEL
        msgs: list[dict[str, str]] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.append({"role": "user", "content": prompt})
        res = self.chat_messages(msgs, model=target_model)
        return {
            "ok": bool(res.get("ok")),
            "online": bool(res.get("online")),
            "model": res.get("model", target_model),
            "response": res.get("message", ""),
            "message": res.get("message", ""),
        }

    def has_model(self, model_name: str | None = None) -> bool:
        target = (model_name or DEFAULT_SOVEREIGN_MODEL).lower()
        models = [m.lower() for m in self.list_local_models()]
        return any(target in m for m in models)

    def chat_messages(self, messages: list[dict[str, str]], model: str = DEFAULT_SOVEREIGN_MODEL) -> dict[str, Any]:
        """Sends a native message array to Ollama's /api/chat endpoint."""
        if not self.is_online():
            return {
                "ok": False,
                "online": False,
                "source": "deterministic_spine",
                "model": "deterministic_fallback",
                "message": "My local neural core is asleep or Ollama is offline. Operating safely in deterministic spine mode.",
                "reason": "Ollama offline",
            }

        target_model = model or DEFAULT_SOVEREIGN_MODEL
        if not self.has_model(target_model):
            return {
                "ok": False,
                "online": True,
                "source": "deterministic_spine",
                "model": "deterministic_fallback",
                "message": f"Model '{target_model}' not yet pulled in Ollama. Operating safely in deterministic spine mode.",
                "reason": "Model not installed",
            }

        try:
            payload = json.dumps({
                "model": target_model,
                "messages": messages,
                "stream": False,
                "keep_alive": "30m",
                "options": {
                    "temperature": 0.5,
                    "num_ctx": 2048,
                    "num_predict": 512
                }
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self._http_endpoint()}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=20.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                msg = result.get("message", {}).get("content", "").strip()
                return {
                    "ok": True,
                    "online": True,
                    "model": target_model,
                    "source": "local_ollama",
                    "message": msg,
                }
        except Exception as e:
            return {
                "ok": False,
                "online": False,
                "source": "deterministic_spine",
                "model": "deterministic_fallback",
                "message": f"Local inference error: {e}. Reverted to deterministic spine.",
                "reason": str(e),
            }

    # Alias for chat_messages
    def chat(self, messages: list[dict[str, str]], model: str = DEFAULT_SOVEREIGN_MODEL) -> dict[str, Any]:
        return self.chat_messages(messages, model=model)

    def chat_or_fallback(
        self,
        prompt: str,
        system_prompt: str = "",
        history: list[dict[str, str]] | None = None,
        messages: list[dict[str, str]] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Builds a native message array from history, system prompt, and current prompt,
        dispatching to Ollama /api/chat. Falls back to deterministic spine if offline.
        """
        target_model = model if (model and self.has_model(model)) else DEFAULT_SOVEREIGN_MODEL
        if not self.is_online() or not self.has_model(target_model):
            return {
                "source": "deterministic_spine",
                "online": False,
                "model": "deterministic_fallback",
                "message": "My local neural core is asleep or Ollama is offline. Operating safely in deterministic spine mode.",
            }

        if messages:
            msg_list = list(messages)
        else:
            msg_list: list[dict[str, str]] = []
            if system_prompt:
                msg_list.append({"role": "system", "content": system_prompt})

            if history:
                for turn in history:
                    u = turn.get("input", "").strip()
                    r = turn.get("reply", "").strip()
                    if u:
                        msg_list.append({"role": "user", "content": u})
                    if r:
                        msg_list.append({"role": "assistant", "content": r})

            msg_list.append({"role": "user", "content": prompt})

        res = self.chat_messages(msg_list, model=target_model)
        if res.get("ok") and res.get("message"):
            return {
                "source": "local_ollama",
                "online": True,
                "model": DEFAULT_SOVEREIGN_MODEL,
                "message": res["message"],
            }

        return {
            "source": "deterministic_spine",
            "online": False,
            "model": "deterministic_fallback",
            "message": "Local inference fallback: Operating safely in deterministic spine mode.",
        }

    def status(self) -> dict[str, Any]:
        online = self.is_online()
        models = self.list_local_models() if online else []
        adapters = self.detect_active_adapters()
        return {
            "stage": STAGE,
            "stage_66": STAGE_66,
            "ollama_connector": "active",
            "endpoint": self.endpoint,
            "online": online,
            "status_description": "CONNECTED (Sovereign local engine online)" if online else "OFFLINE (Deterministic fallback mode)",
            "multiturn_chat_supported": True,
            "installed_models_count": len(models),
            "installed_models": models,
            "active_adapters_count": len(adapters),
            "active_adapters": adapters,
            "default_model": DEFAULT_SOVEREIGN_MODEL,
            "fallback_mode": "deterministic_spine_active" if not online else "neural_sovereign_active",
        }
