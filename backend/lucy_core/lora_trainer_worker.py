"""
lora_trainer_worker.py
Physical GPU LoRA Fine-Tuning Worker (Unsloth / HuggingFace PEFT + TRL).

Converts `data/lucy/learning/lora_dataset_alpaca.json` into a physical LoRA adapter
in `data/lucy/adapters/` when a CUDA GPU and Unsloth/PEFT are available.
"""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_HF_BASE_MODEL = "Qwen/Qwen2.5-3B-Instruct"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


class LoRATrainerWorker:
    """Executes real local LoRA weight training via Unsloth or HuggingFace PEFT."""

    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.adapters_dir = self.lucy_data / "adapters"
        self.learning_dir = self.lucy_data / "learning"
        self.dataset_file = self.learning_dir / "lora_dataset_alpaca.json"
        self.adapter_output_dir = self.adapters_dir / "lucy_personal_lora"
        self.gguf_adapter_path = self.adapters_dir / "lucy_personal_lora.gguf"
        self.safetensors_path = self.adapter_output_dir / "adapter_model.safetensors"
        self.training_log_file = self.adapters_dir / "lora_training_runs.jsonl"

        self.adapters_dir.mkdir(parents=True, exist_ok=True)
        self.learning_dir.mkdir(parents=True, exist_ok=True)

    def environment_capabilities(self) -> dict[str, Any]:
        has_torch = _has_module("torch")
        has_peft = _has_module("peft")
        has_trl = _has_module("trl")
        has_transformers = _has_module("transformers")
        has_unsloth = _has_module("unsloth")

        cuda_available = False
        device_name = "cpu"
        if has_torch:
            try:
                import torch
                cuda_available = bool(torch.cuda.is_available())
                if cuda_available:
                    device_name = str(torch.cuda.get_device_name(0))
            except Exception:
                cuda_available = False

        physical_adapter_exists = self.gguf_adapter_path.exists() or self.safetensors_path.exists()
        active_adapter_path = (
            str(self.gguf_adapter_path)
            if self.gguf_adapter_path.exists()
            else (str(self.adapter_output_dir) if self.safetensors_path.exists() else None)
        )

        return {
            "torch_installed": has_torch,
            "cuda_available": cuda_available,
            "gpu_device": device_name,
            "unsloth_installed": has_unsloth,
            "peft_trl_installed": bool(has_peft and has_trl and has_transformers),
            "can_run_gpu_lora": bool(cuda_available and (has_unsloth or (has_peft and has_trl and has_transformers))),
            "physical_adapter_exists": physical_adapter_exists,
            "active_adapter_path": active_adapter_path,
        }

    def train_adapter(
        self,
        base_model_id: str = DEFAULT_HF_BASE_MODEL,
        max_steps: int = 60,
        lora_rank: int = 16,
        lora_alpha: int = 32,
    ) -> dict[str, Any]:
        """
        Runs the physical LoRA training loop if CUDA + Unsloth/PEFT are present.
        Otherwise returns a structured readiness report so `lora_sleep_cycle.py`
        can still compile an Ollama Modelfile using native MESSAGE exemplars.
        """
        caps = self.environment_capabilities()
        if not self.dataset_file.exists():
            return {
                "trained": False,
                "mode": "missing_dataset",
                "reason": f"Dataset not found at {self.dataset_file}",
                "capabilities": caps,
            }

        try:
            records = json.loads(self.dataset_file.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"trained": False, "mode": "corrupt_dataset", "reason": str(exc), "capabilities": caps}

        if not isinstance(records, list) or len(records) == 0:
            return {
                "trained": False,
                "mode": "empty_dataset",
                "reason": "0 verified records in lora_dataset_alpaca.json. Interact or synthesize code first.",
                "capabilities": caps,
            }

        if not caps["can_run_gpu_lora"]:
            report = {
                "timestamp": _now_iso(),
                "trained": False,
                "mode": "ollama_message_exemplar_fallback",
                "dataset_records": len(records),
                "physical_adapter_path": caps["active_adapter_path"],
                "reason": (
                    "CUDA GPU or Unsloth/PEFT packages not active in current venv. "
                    "Falling back to Ollama Modelfile native MESSAGE exemplar baking."
                ),
                "install_hint": "pip install torch unsloth peft trl transformers datasets accelerate bitsandbytes",
                "capabilities": caps,
            }
            self._log_run(report)
            return report

        # Execute real PEFT / Unsloth SFT training on GPU
        try:
            import torch
            from datasets import Dataset
            from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
            from peft import LoraConfig, get_peft_model
            from trl import SFTTrainer

            formatted_texts = []
            for item in records:
                inst = str(item.get("instruction", "")).strip()
                inp = str(item.get("input", "")).strip()
                out = str(item.get("output", "")).strip()
                prompt = (
                    f"<|im_start|>system\nYou are LUCY, Senin's grounded personal operating assistant.<|im_end|>\n"
                    f"<|im_start|>user\n{inst}\n{inp}<|im_end|>\n"
                    f"<|im_start|>assistant\n{out}<|im_end|>"
                )
                formatted_texts.append({"text": prompt})

            hf_dataset = Dataset.from_list(formatted_texts)
            tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
            )

            peft_config = LoraConfig(
                r=lora_rank,
                lora_alpha=lora_alpha,
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM",
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            )
            model = get_peft_model(model, peft_config)

            self.adapter_output_dir.mkdir(parents=True, exist_ok=True)
            training_args = TrainingArguments(
                output_dir=str(self.adapter_output_dir),
                per_device_train_batch_size=1,
                gradient_accumulation_steps=4,
                warmup_steps=5,
                max_steps=max_steps,
                learning_rate=2e-4,
                fp16=True,
                logging_steps=10,
                save_strategy="no",
                report_to="none",
            )

            trainer = SFTTrainer(
                model=model,
                train_dataset=hf_dataset,
                dataset_text_field="text",
                max_seq_length=1024,
                tokenizer=tokenizer,
                args=training_args,
            )
            trainer.train()
            model.save_pretrained(str(self.adapter_output_dir))
            tokenizer.save_pretrained(str(self.adapter_output_dir))

            report = {
                "timestamp": _now_iso(),
                "trained": True,
                "mode": "gpu_peft_safetensors",
                "base_model": base_model_id,
                "dataset_records": len(records),
                "max_steps": max_steps,
                "lora_rank": lora_rank,
                "physical_adapter_path": str(self.adapter_output_dir),
                "capabilities": self.environment_capabilities(),
            }
            self._log_run(report)
            return report
        except Exception as exc:
            report = {
                "timestamp": _now_iso(),
                "trained": False,
                "mode": "gpu_training_error_fallback",
                "error": str(exc),
                "physical_adapter_path": caps["active_adapter_path"],
                "capabilities": caps,
            }
            self._log_run(report)
            return report

    def _log_run(self, report: dict[str, Any]) -> None:
        try:
            with open(self.training_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(report, ensure_ascii=False) + "\n")
        except Exception:
            pass
