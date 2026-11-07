"""
multi_provider_pool.py
Stage 46 = Multi-Provider Key Rotation & Failover Pool.

Loads, categorizes, health-tracks, and automatically rotates the 25 API keys from
C:\\Users\\admin\\Desktop\\senin\\api keys.txt across:
- Groq (4 keys)
- SambaNova (4 keys)
- OpenRouter (4 keys)
- Gemini (4 keys)
- NVidia (4 keys)
- Hugging Face (4 keys)
- AI Horde (1 key)

Capabilities:
1. Robust parser for api keys.txt handling formatting variants and numbering.
2. Safe key fingerprint masking (never displays raw secrets in logs or terminal).
3. Automated in-provider round-robin rotation upon HTTP 429 / rate-limit detection.
4. Cross-provider fallback hierarchy: Groq -> SambaNova -> OpenRouter -> Gemini.
5. In-memory cooldown timer tracking to re-enable rate-limited keys after recovery.
6. Clean integration into LucyRuntime and SwarmDispatcher.
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from typing import Any


STAGE = "46 multi provider key rotation pool"
DEFAULT_KEYS_PATH = Path(r"C:\Users\admin\Desktop\senin\api keys.txt")
DEFAULT_COOLDOWN_SECONDS = 60.0

PROVIDER_HIERARCHY = ["groq", "sambanova", "openrouter", "gemini", "nvidia", "huggingface", "aihorde"]


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def mask_key(key: str) -> str:
    """Masks an API key for safe logging/display (e.g. gsk_Rkq...5Lwq)."""
    k = str(key or "").strip()
    if len(k) <= 8:
        return "[redacted-key]"
    return f"{k[:7]}...{k[-4:]}"


class KeyState:
    ACTIVE = "ACTIVE"
    COOLING_DOWN = "COOLING_DOWN"
    FAILED = "FAILED"
    DISABLED = "DISABLED"


class ManagedKey:
    """Represents a single managed provider key with health metrics."""

    def __init__(self, key: str, provider: str, index: int) -> None:
        self.raw_key = key.strip()
        self.provider = provider.lower()
        self.index = index
        self.state = KeyState.ACTIVE
        self.calls_count = 0
        self.errors_count = 0
        self.rate_limited_count = 0
        self.cooldown_until: float | None = None
        self.last_used_at: str | None = None

    @property
    def masked(self) -> str:
        return mask_key(self.raw_key)

    def is_available(self, current_time: float) -> bool:
        if self.state == KeyState.DISABLED:
            return False
        if self.state == KeyState.COOLING_DOWN:
            if self.cooldown_until and current_time >= self.cooldown_until:
                self.state = KeyState.ACTIVE
                self.cooldown_until = None
                return True
            return False
        return self.state == KeyState.ACTIVE

    def mark_used(self) -> None:
        self.calls_count += 1
        self.last_used_at = _now()

    def mark_rate_limited(self, current_time: float, cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS) -> None:
        self.rate_limited_count += 1
        self.state = KeyState.COOLING_DOWN
        self.cooldown_until = current_time + cooldown_seconds

    def mark_error(self) -> None:
        self.errors_count += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "masked_key": self.masked,
            "provider": self.provider,
            "state": self.state,
            "calls_count": self.calls_count,
            "errors_count": self.errors_count,
            "rate_limited_count": self.rate_limited_count,
            "last_used_at": self.last_used_at,
        }


class MultiProviderPool:
    """Manages multi-key provider rotation, health monitoring, and cross-provider failover."""

    def __init__(
        self,
        lucy_data: Path,
        keys_path: Path | None = None,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
    ) -> None:
        self.lucy_data = Path(lucy_data)
        self.lucy_data.mkdir(parents=True, exist_ok=True)
        self.keys_path = Path(keys_path) if keys_path else DEFAULT_KEYS_PATH
        self.cooldown_seconds = cooldown_seconds
        self.pool_status_file = self.lucy_data / "multi_provider_pool.json"

        # provider -> list[ManagedKey]
        self.pools: dict[str, list[ManagedKey]] = {p: [] for p in PROVIDER_HIERARCHY}
        self.active_indices: dict[str, int] = {p: 0 for p in PROVIDER_HIERARCHY}
        self.total_keys_loaded = 0

        self.load_keys()

    def parse_keys_file(self, content: str) -> dict[str, list[str]]:
        """Parses raw text from api keys.txt into clean provider -> key list mapping."""
        lines = content.splitlines()
        current_provider = "unknown"
        grouped: dict[str, list[str]] = {p: [] for p in PROVIDER_HIERARCHY}

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            low = line_clean.lower()
            # Provider header detection
            if low in ("gemini", "google"):
                current_provider = "gemini"
                continue
            elif low in ("openrouter", "open_router"):
                current_provider = "openrouter"
                continue
            elif low in ("groq",):
                current_provider = "groq"
                continue
            elif low in ("sambanova", "samba"):
                current_provider = "sambanova"
                continue
            elif low in ("nvidia", "n vidia", "nv"):
                current_provider = "nvidia"
                continue
            elif low in ("hugging-face", "huggingface", "hf"):
                current_provider = "huggingface"
                continue
            elif low in ("aihorde", "ai horde", "horde"):
                current_provider = "aihorde"
                continue

            # Strip leading numbers like "1.", "2. ", etc.
            key_candidate = re.sub(r"^\d+\.\s*", "", line_clean).strip()
            # Filter comments or instructions
            if key_candidate.startswith("#") or "i think api key" in key_candidate.lower():
                continue

            if len(key_candidate) > 10 and current_provider in grouped:
                grouped[current_provider].append(key_candidate)

        return grouped

    def load_keys(self) -> dict[str, Any]:
        """Loads and parses keys from disk into managed key pools."""
        self.pools = {p: [] for p in PROVIDER_HIERARCHY}
        self.active_indices = {p: 0 for p in PROVIDER_HIERARCHY}
        self.total_keys_loaded = 0

        if not self.keys_path.exists():
            return {
                "stage": STAGE,
                "loaded": False,
                "reason": f"File not found: {self.keys_path}",
                "total_keys": 0,
            }

        try:
            content = self.keys_path.read_text(encoding="utf-8")
            parsed = self.parse_keys_file(content)

            for provider, keys in parsed.items():
                for idx, k in enumerate(keys, start=1):
                    self.pools[provider].append(ManagedKey(key=k, provider=provider, index=idx))
                self.total_keys_loaded += len(keys)

            self._save_state()
            return {
                "stage": STAGE,
                "loaded": True,
                "keys_file": str(self.keys_path),
                "total_keys": self.total_keys_loaded,
                "provider_counts": {p: len(keys) for p, keys in self.pools.items()},
            }

        except Exception as e:
            return {
                "stage": STAGE,
                "loaded": False,
                "error": str(e),
                "total_keys": 0,
            }

    def _save_state(self) -> None:
        """Saves sanitized pool state to disk."""
        data = {
            "stage": STAGE,
            "updated_at": _now(),
            "keys_path": str(self.keys_path),
            "total_keys_loaded": self.total_keys_loaded,
            "providers": {},
        }
        for provider, keys in self.pools.items():
            data["providers"][provider] = {
                "active_index": self.active_indices.get(provider, 0),
                "total_keys": len(keys),
                "keys": [k.to_dict() for k in keys],
            }
        try:
            self.pool_status_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def get_active_key(self, provider: str = "groq") -> tuple[str | None, ManagedKey | None]:
        """
        Retrieves the currently active key for the given provider.
        If current key is cooling down or rate-limited, automatically rotates to the next available.
        """
        import time
        now = time.time()
        p = provider.lower()
        keys = self.pools.get(p, [])
        if not keys:
            return None, None

        idx = self.active_indices.get(p, 0)
        # Check current key
        if keys[idx].is_available(now):
            return keys[idx].raw_key, keys[idx]

        # Scan for next available key in round-robin fashion
        for step in range(1, len(keys)):
            next_idx = (idx + step) % len(keys)
            if keys[next_idx].is_available(now):
                self.active_indices[p] = next_idx
                self._save_state()
                return keys[next_idx].raw_key, keys[next_idx]

        # All keys in cooldown for this provider
        return None, None

    def rotate_key(self, provider: str = "groq", reason: str = "manual_rotation") -> dict[str, Any]:
        """Manually or automatically forces rotation to the next key in the pool."""
        p = provider.lower()
        keys = self.pools.get(p, [])
        if not keys:
            return {"rotated": False, "reason": f"No keys loaded for provider '{p}'."}

        current_idx = self.active_indices.get(p, 0)
        new_idx = (current_idx + 1) % len(keys)
        self.active_indices[p] = new_idx
        self._save_state()

        return {
            "rotated": True,
            "provider": p,
            "reason": reason,
            "previous_index": current_idx + 1,
            "new_index": new_idx + 1,
            "active_masked_key": keys[new_idx].masked,
        }

    def mark_rate_limited(self, provider: str = "groq") -> dict[str, Any]:
        """
        Marks current key as rate-limited, sets cooldown timer,
        and automatically rotates to next available key.
        """
        import time
        now = time.time()
        p = provider.lower()
        keys = self.pools.get(p, [])
        if not keys:
            return {"status": "error", "message": f"Provider '{p}' has no keys."}

        current_idx = self.active_indices.get(p, 0)
        target_key = keys[current_idx]
        target_key.mark_rate_limited(now, self.cooldown_seconds)

        # Attempt rotation
        next_raw, next_managed = self.get_active_key(p)
        self._save_state()

        if next_managed:
            return {
                "status": "rotated_on_rate_limit",
                "provider": p,
                "cooling_down_key": target_key.masked,
                "cooldown_seconds": self.cooldown_seconds,
                "new_active_key": next_managed.masked,
                "new_index": next_managed.index,
            }

        # All keys for this provider are cooling down -> trigger cross-provider failover
        failover_res = self.get_failover_provider(exclude={p})
        return {
            "status": "provider_exhausted_failover_recommended",
            "provider": p,
            "cooling_down_key": target_key.masked,
            "recommended_failover": failover_res,
        }

    def get_failover_provider(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """Finds the next healthy provider in the hierarchy."""
        import time
        now = time.time()
        ex = exclude or set()

        for prov in PROVIDER_HIERARCHY:
            if prov in ex:
                continue
            raw, managed = self.get_active_key(prov)
            if raw and managed:
                return {
                    "failover_available": True,
                    "provider": prov,
                    "active_index": managed.index,
                    "masked_key": managed.masked,
                }

        return {
            "failover_available": False,
            "reason": "All external cloud providers are exhausted or cooling down.",
        }

    def status(self) -> dict[str, Any]:
        """Returns comprehensive sanitized status of all key pools."""
        import time
        now = time.time()
        summary = {}

        for p, keys in self.pools.items():
            active_count = sum(1 for k in keys if k.is_available(now))
            cooldown_count = sum(1 for k in keys if k.state == KeyState.COOLING_DOWN and not k.is_available(now))
            curr_idx = self.active_indices.get(p, 0)
            curr_masked = keys[curr_idx].masked if keys else "None"

            summary[p] = {
                "total_keys": len(keys),
                "active_available": active_count,
                "cooling_down": cooldown_count,
                "current_active_key": curr_masked,
                "current_index": curr_idx + 1 if keys else 0,
            }

        return {
            "stage": STAGE,
            "multi_provider_pool": "active",
            "keys_file": str(self.keys_path),
            "total_keys_loaded": self.total_keys_loaded,
            "providers_count": len(self.pools),
            "providers_summary": summary,
            "cooldown_seconds": self.cooldown_seconds,
        }
