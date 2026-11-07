"""
backend/lucy_core/lora_compiler.py
Stage 85: Local Model Adapter Compiler & Ollama Hot-Swap Engine

Dynamically compiles Ollama Modelfiles with baked high-signal exemplars,
binds physical GGUF LoRA adapters, executes atomic zero-downtime hot-swaps,
and maintains adapter versioning with automated rollback capability.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.lucy_core.lora_harvester import HighSignalLoRAHarvester

STAGE: int = 85
DEFAULT_BASE_MODEL = "lucy:personal"
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"


@dataclass
class CompiledAdapterManifest:
    tag: str
    base_model: str
    modelfile_path: str
    gguf_adapter_path: Optional[str]
    exemplar_count: int
    compiled_at: float = field(default_factory=time.time)
    status: str = "READY"  # "READY", "ACTIVE", "ROLLBACK", "FAILED"
    health_checked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag": self.tag,
            "base_model": self.base_model,
            "modelfile_path": self.modelfile_path,
            "gguf_adapter_path": self.gguf_adapter_path,
            "exemplar_count": self.exemplar_count,
            "compiled_at": self.compiled_at,
            "status": self.status,
            "health_checked": self.health_checked,
        }


class LocalModelAdapterCompiler:
    """
    Sovereign Modelfile Compiler and Ollama Hot-Swap Manager.
    Bakes verified high-signal interaction exemplars into local model variants,
    executes atomic model switching, and protects runtime continuity with rollback.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        harvester: Optional[HighSignalLoRAHarvester] = None,
        receipt_ledger: Optional[Any] = None,
        active_model: str = DEFAULT_BASE_MODEL,
        ollama_host: str = DEFAULT_OLLAMA_HOST,
        adapters_dir: Optional[Path] = None,
    ) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.adapters_dir = adapters_dir or (self.project_root / "data" / "lucy" / "lora" / "adapters")
        self.adapters_dir.mkdir(parents=True, exist_ok=True)

        self.modelfiles_dir = self.adapters_dir / "modelfiles"
        self.modelfiles_dir.mkdir(parents=True, exist_ok=True)

        self.harvester = harvester or HighSignalLoRAHarvester(project_root=self.project_root)
        self.receipt_ledger = receipt_ledger
        self.ollama_host = ollama_host.rstrip("/")

        self.active_model: str = active_model
        self.previous_model: str = DEFAULT_BASE_MODEL

        self.registry_file = self.adapters_dir / "adapter_registry.json"
        self.manifests: List[CompiledAdapterManifest] = []
        self._load_registry()

    def _load_registry(self) -> None:
        if not self.registry_file.exists():
            return
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.active_model = data.get("active_model", self.active_model)
                self.previous_model = data.get("previous_model", self.previous_model)
                for item in data.get("manifests", []):
                    self.manifests.append(
                        CompiledAdapterManifest(
                            tag=item["tag"],
                            base_model=item["base_model"],
                            modelfile_path=item["modelfile_path"],
                            gguf_adapter_path=item.get("gguf_adapter_path"),
                            exemplar_count=item.get("exemplar_count", 0),
                            compiled_at=item.get("compiled_at", time.time()),
                            status=item.get("status", "READY"),
                            health_checked=item.get("health_checked", False),
                        )
                    )
        except Exception:
            pass

    def _save_registry(self) -> None:
        try:
            payload = {
                "active_model": self.active_model,
                "previous_model": self.previous_model,
                "last_updated": datetime.now().isoformat(),
                "manifests": [m.to_dict() for m in self.manifests],
            }
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass

    def check_ollama_daemon(self, timeout_sec: float = 2.0) -> Tuple[bool, List[str]]:
        """
        Queries local Ollama tags API to confirm daemon is responding and list installed models.
        """
        url = f"{self.ollama_host}/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LucyAdapterCompiler/85.0"})
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                return True, models
        except Exception:
            return False, []

    def build_modelfile(
        self,
        base_model: str = DEFAULT_BASE_MODEL,
        custom_tag: Optional[str] = None,
        max_exemplars: int = 6,
        adapter_path: Optional[str] = None,
    ) -> Tuple[str, Path]:
        """
        Generates an Ollama Modelfile incorporating:
        - Base model directive
        - GGUF adapter binding (if present)
        - Deterministic low-hallucination inference parameters
        - First-person peer system prompt
        - Baked high-signal exemplars from the interaction harvester
        """
        tag = custom_tag or f"lucy:personal-v85.{len(self.manifests) + 1}"
        file_name = f"Modelfile.{tag.replace(':', '_')}"
        out_path = self.modelfiles_dir / file_name

        # Resolve GGUF adapter
        gguf_directive = ""
        resolved_gguf = None
        if adapter_path and Path(adapter_path).exists():
            resolved_gguf = str(Path(adapter_path).resolve())
            gguf_directive = f"ADAPTER {resolved_gguf}\n"
        else:
            # Check if any .gguf files exist in adapters dir
            gguf_candidates = list(self.adapters_dir.glob("*.gguf"))
            if gguf_candidates:
                resolved_gguf = str(gguf_candidates[0].resolve())
                gguf_directive = f"ADAPTER {resolved_gguf}\n"

        # System prompt enforcing authentic first-person peer tone & anti-sycophancy
        system_prompt = (
            "You are LUCY, a local sovereign AI systems companion and software engineer. "
            "You speak strictly in the first person ('I', 'my', 'we', 'let's'). "
            "Never refer to yourself in the third person as 'Lucy'. "
            "Do not output sycophantic filler, apologies, or disclaimers. "
            "Provide direct, concise, technically rigorous answers. Ground facts in verified reality. "
            "Challenge incorrect premises constructively. Verify code syntax before presenting it."
        )

        lines = [
            f"FROM {base_model}",
            gguf_directive.strip() if gguf_directive else "# No GGUF adapter specified; using exemplar fine-tuning",
            "PARAMETER temperature 0.2",
            "PARAMETER top_p 0.85",
            "PARAMETER repeat_penalty 1.15",
            "PARAMETER num_ctx 8192",
            f'SYSTEM """{system_prompt}"""',
        ]

        # Bake top high-signal exemplars from harvester
        exemplars = []
        if self.harvester and hasattr(self.harvester, "curated_interactions"):
            # Sort by signal score descending
            sorted_items = sorted(
                self.harvester.curated_interactions,
                key=lambda x: x.signal_score,
                reverse=True,
            )
            exemplars = sorted_items[:max_exemplars]

        for ex in exemplars:
            u_text = ex.instruction.replace('"""', "'''").strip()
            a_text = ex.response.replace('"""', "'''").strip()
            if u_text and a_text:
                lines.append(f'MESSAGE user """{u_text}"""')
                lines.append(f'MESSAGE assistant """{a_text}"""')

        content = "\n".join(lines) + "\n"
        out_path.write_text(content, encoding="utf-8")
        return content, out_path

    def health_check_model(self, tag: str, timeout_sec: float = 10.0) -> bool:
        """
        Sends a test inference ping to verify the compiled model responds cleanly.
        """
        url = f"{self.ollama_host}/api/generate"
        payload = json.dumps({"model": tag, "prompt": "health_check", "stream": False}).encode("utf-8")
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "LucyAdapterCompiler/85.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                return resp.status == 200
        except Exception:
            return False

    def compile_model(
        self,
        base_model: str = DEFAULT_BASE_MODEL,
        custom_tag: Optional[str] = None,
        max_exemplars: int = 6,
        adapter_path: Optional[str] = None,
        auto_swap: bool = True,
        mock_cli_run: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Builds Modelfile and runs `ollama create <tag> -f <modelfile_path>`.
        Verifies health and optionally hot-swaps active runtime pointer.
        """
        tag = custom_tag or f"lucy:personal-v85.{len(self.manifests) + 1}"
        content, modelfile_path = self.build_modelfile(
            base_model=base_model,
            custom_tag=tag,
            max_exemplars=max_exemplars,
            adapter_path=adapter_path,
        )

        ollama_bin = shutil.which("ollama")
        if not ollama_bin and mock_cli_run is None:
            manifest = CompiledAdapterManifest(
                tag=tag,
                base_model=base_model,
                modelfile_path=str(modelfile_path),
                gguf_adapter_path=adapter_path,
                exemplar_count=max_exemplars,
                status="PREPARED_ON_DISK",
                health_checked=False,
            )
            self.manifests.append(manifest)
            self._save_registry()
            return {
                "compiled": False,
                "reason": "Ollama CLI not found on PATH; Modelfile generated on disk.",
                "tag": tag,
                "modelfile_path": str(modelfile_path),
            }

        # Execute ollama create
        start_time = time.perf_counter()
        if mock_cli_run is True or (ollama_bin and mock_cli_run is None):
            try:
                cmd = [ollama_bin or "ollama", "create", tag, "-f", str(modelfile_path)]
                if mock_cli_run is True:
                    # In test mock mode, simulate successful process
                    returncode = 0
                    stdout = "transferring model data\nsuccess"
                    stderr = ""
                else:
                    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    returncode = proc.returncode
                    stdout = proc.stdout.strip()
                    stderr = proc.stderr.strip()

                compile_ok = returncode == 0
            except Exception as e:
                compile_ok = False
                returncode = -1
                stdout = ""
                stderr = str(e)
        else:
            compile_ok = False
            returncode = -1
            stdout = ""
            stderr = "Execution skipped"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if not compile_ok:
            manifest = CompiledAdapterManifest(
                tag=tag,
                base_model=base_model,
                modelfile_path=str(modelfile_path),
                gguf_adapter_path=adapter_path,
                exemplar_count=max_exemplars,
                status="FAILED",
                health_checked=False,
            )
            self.manifests.append(manifest)
            self._save_registry()
            return {
                "compiled": False,
                "reason": f"Ollama compile failed (code {returncode}): {stderr}",
                "tag": tag,
                "modelfile_path": str(modelfile_path),
            }

        # Perform health check
        health_ok = True
        if mock_cli_run is not True:
            health_ok = self.health_check_model(tag)

        manifest = CompiledAdapterManifest(
            tag=tag,
            base_model=base_model,
            modelfile_path=str(modelfile_path),
            gguf_adapter_path=adapter_path,
            exemplar_count=max_exemplars,
            status="READY",
            health_checked=health_ok,
        )
        self.manifests.append(manifest)

        # Auto-swap if requested
        swapped = False
        if auto_swap and (health_ok or mock_cli_run is True):
            swap_res = self.hot_swap(tag, skip_health_check=True)
            swapped = swap_res.get("success", False)

        self._save_registry()

        if self.receipt_ledger is not None:
            try:
                self.receipt_ledger.issue_receipt(
                    action_category="lora_compiler",
                    operation="compile_model",
                    target=tag,
                    verified_outcome=f"Compiled in {elapsed_ms:.1f}ms, health: {health_ok}, swapped: {swapped}",
                )
            except Exception:
                pass

        return {
            "compiled": True,
            "tag": tag,
            "elapsed_ms": round(elapsed_ms, 2),
            "modelfile_path": str(modelfile_path),
            "health_checked": health_ok,
            "swapped_active": swapped,
            "active_model": self.active_model,
        }

    def hot_swap(self, target_model: str, skip_health_check: bool = False) -> Dict[str, Any]:
        """
        Atomically switches active model pointer with rollback preservation.
        """
        clean_tag = target_model.strip()
        if not clean_tag:
            return {"success": False, "reason": "Empty model tag provided."}

        # Health check before swapping
        if not skip_health_check:
            daemon_ok, models = self.check_ollama_daemon()
            if daemon_ok and clean_tag not in models:
                # If daemon is running and model isn't in tags, fail safely
                return {
                    "success": False,
                    "reason": f"Target model '{clean_tag}' is not registered in local Ollama daemon.",
                    "active_model": self.active_model,
                }

        old_model = self.active_model
        self.previous_model = old_model
        self.active_model = clean_tag

        # Update manifest statuses
        for m in self.manifests:
            if m.tag == clean_tag:
                m.status = "ACTIVE"
            elif m.tag == old_model:
                m.status = "READY"

        self._save_registry()

        if self.receipt_ledger is not None:
            try:
                self.receipt_ledger.issue_receipt(
                    action_category="lora_compiler",
                    operation="hot_swap",
                    target=clean_tag,
                    verified_outcome=f"Swapped from {old_model} to {clean_tag}",
                )
            except Exception:
                pass

        return {
            "success": True,
            "swapped_from": old_model,
            "active_model": self.active_model,
            "previous_model": self.previous_model,
        }

    def rollback(self) -> Dict[str, Any]:
        """
        Reverts active model to previous model or baseline DEFAULT_BASE_MODEL.
        """
        target = self.previous_model or DEFAULT_BASE_MODEL
        res = self.hot_swap(target, skip_health_check=True)
        if res.get("success"):
            for m in self.manifests:
                if m.tag == res.get("swapped_from"):
                    m.status = "ROLLBACK"
            self._save_registry()

            if self.receipt_ledger is not None:
                try:
                    self.receipt_ledger.issue_receipt(
                        action_category="lora_compiler",
                        operation="rollback",
                        target=target,
                        verified_outcome=f"Rolled back to {target}",
                    )
                except Exception:
                    pass

        return res

    def format_terminal_summary(self) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| LOCAL MODEL ADAPTER COMPILER & HOT-SWAP ENGINE (STAGE 85)            |")
        lines.append("+----------------------------------------------------------------------+")
        active_str = self.active_model[:30]
        prev_str = self.previous_model[:30]
        lines.append(f"| Active Model:   {active_str:<25} | Prev Model: {prev_str:<18} |")

        daemon_ok, models = self.check_ollama_daemon()
        daemon_str = f"ONLINE ({len(models)} models)" if daemon_ok else "OFFLINE / UNREACHABLE"
        lines.append(f"| Ollama Daemon:  {daemon_str:<51} |")
        lines.append(f"| Modelfiles Dir: {self.modelfiles_dir.name:<51} |")
        lines.append("+----------------------------------------------------------------------+")

        if self.manifests:
            lines.append("| COMPILED ADAPTER VERSIONS:                                           |")
            for m in self.manifests[-4:]:
                stat_tag = f"[{m.status}]"
                hc_tag = "OK" if m.health_checked else "-"
                info_line = f"{m.tag:<28} {stat_tag:<10} Ex: {m.exemplar_count}  Health: {hc_tag}"
                lines.append(f"|  * {info_line:<65} |")
            lines.append("+----------------------------------------------------------------------+")

        return "\n".join(lines)

    def status(self) -> Dict[str, Any]:
        daemon_ok, models = self.check_ollama_daemon()
        return {
            "status": "active",
            "active_model": self.active_model,
            "previous_model": self.previous_model,
            "compiled_adapters_count": len(self.manifests),
            "ollama_daemon_online": daemon_ok,
            "ollama_installed_models": models,
            "adapters_directory": str(self.adapters_dir),
        }
