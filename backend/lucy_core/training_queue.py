"""
training_queue.py
Stage 36 = Verified LoRA Training Queue & Anti-Model-Collapse Gatekeeper.

Collects only 100% verified, hallucination-free interactions (compiler-tested code
from Stage 40 and ELIE/Receipt-verified turns from Stages 37 & 55) into
data/lucy/learning/verified_training_queue.jsonl for LoRA sleep cycles.

Features:
1. Admits interactions into verified_training_queue.jsonl only if:
   - Non-empty instruction and response.
   - Zero hallucination intercept badges ([ELIE: HALLUCINATION_INTERCEPTED, [STAGE 55 RECEIPT INTERCEPT).
   - Sensitive credentials automatically redacted into safe placeholder tokens.
   - Deduplication via SHA-256 turn hashing.
2. Formats training data into standard Alpaca format for Unsloth / HuggingFace PEFT SFTTrainer.
3. Generates Ollama Modelfile with ADAPTER directive for local hot-swapping.
4. Top exemplars extractor for few-shot prompt baking and two-speed alignment.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.lucy_core.learning import _redact


STAGE = "36 verified lora training queue"

SENSITIVE_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{20,}",
    r"gsk_[A-Za-z0-9_-]{20,}",
    r"nvapi-[A-Za-z0-9_-]{20,}",
    r"AIza[A-Za-z0-9_-]{20,}",
    r"(?i)(api[_-]?key|password|token|secret|private[_-]?key)\s*[:=]\s*\S+",
]

REJECT_MARKERS = (
    "[ELIE: HALLUCINATION_INTERCEPTED",
    "[STAGE 55 RECEIPT INTERCEPT",
    "[Guardian Blocked]",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _contains_raw_secrets(text: str) -> bool:
    for pat in SENSITIVE_PATTERNS:
        if re.search(pat, str(text or "")):
            return True
    return False


class VerifiedTrainingQueue:
    """Gatekeeper for data/lucy/learning/verified_training_queue.jsonl."""

    def __init__(self, lucy_data: Path) -> None:
        self.lucy_data = Path(lucy_data)
        self.learning_dir = self.lucy_data / "learning"
        self.learning_dir.mkdir(parents=True, exist_ok=True)
        self.queue_file = self.learning_dir / "verified_training_queue.jsonl"
        self.lessons_file = self.learning_dir / "local_lessons.json"
        self.adapters_dir = self.lucy_data / "adapters"
        self.adapters_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_files()

    def _ensure_files(self) -> None:
        if not self.queue_file.exists():
            self.queue_file.touch()
        if not self.lessons_file.exists():
            self.lessons_file.write_text("[]", encoding="utf-8")

    def count(self) -> int:
        if not self.queue_file.exists():
            return 0
        try:
            with open(self.queue_file, "r", encoding="utf-8") as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0

    def record_verified_interaction(
        self,
        instruction: str,
        response: str,
        verification_source: str = "elie_and_receipt_verified",
        input_context: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Admits an interaction into the permanent LoRA training queue ONLY if:
        1. Both instruction and response meet minimum length requirements.
        2. Neither contains hallucination intercept badges ([ELIE, [STAGE 55, [Guardian).
        3. Credentials are automatically redacted to ensure clean training.
        4. No duplicate instruction+response hash already exists.
        """
        clean_inst, red_inst = _redact(str(instruction or "").strip())
        if "[redacted" in clean_inst:
            red_inst = True

        clean_resp, red_resp = _redact(str(response or "").strip())
        if "[redacted" in clean_resp:
            red_resp = True

        clean_inp, red_inp = _redact(str(input_context or "").strip())
        if "[redacted" in clean_inp:
            red_inp = True

        had_redactions = red_inst or red_resp or red_inp

        if len(clean_inst) < 4 or len(clean_resp) < 6:
            return {
                "admitted": False,
                "recorded": False,
                "reason": "Interaction too short for LoRA training.",
            }

        combined = f"{clean_inst}\n{clean_inp}\n{clean_resp}"
        if any(marker in combined for marker in REJECT_MARKERS):
            return {
                "admitted": False,
                "recorded": False,
                "reason": "Hallucination or blocked marker detected; barred from LoRA queue.",
            }

        if _contains_raw_secrets(combined):
            return {
                "admitted": False,
                "recorded": False,
                "reason": "Unredacted credential pattern detected; barred from LoRA queue.",
            }

        digest = hashlib.sha256(f"{clean_inst.lower()}||{clean_resp.lower()}".encode("utf-8")).hexdigest()[:16]
        existing = self.load_all()
        for item in existing:
            if item.get("hash") == digest:
                return {
                    "admitted": False,
                    "recorded": False,
                    "duplicate": True,
                    "hash": digest,
                }

        record = {
            "id": f"vtq_{len(existing) + 1:04d}",
            "hash": digest,
            "timestamp": _now_iso(),
            "instruction": clean_inst,
            "input": clean_inp,
            "response": clean_resp,
            "output": clean_resp,
            "verification_source": verification_source,
            "had_redactions": had_redactions,
            "metadata": metadata or {},
        }

        try:
            with open(self.queue_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            return {
                "admitted": True,
                "recorded": True,
                "total_queue_count": self.count(),
                "had_redactions": had_redactions,
                "record": record,
            }
        except Exception as exc:
            return {"admitted": False, "recorded": False, "reason": str(exc)}

    def load_all(self, limit: int | None = None) -> list[dict[str, Any]]:
        if not self.queue_file.exists():
            return []
        items: list[dict[str, Any]] = []
        try:
            for line in self.queue_file.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict) and obj.get("instruction") and (obj.get("response") or obj.get("output")):
                        items.append(obj)
                except Exception:
                    continue
        except Exception:
            return []
        if limit is not None and limit > 0:
            return items[-limit:]
        return items

    def top_exemplars(self, limit: int = 5) -> list[dict[str, str]]:
        """Returns the most recent high-signal verified pairs for few-shot or Modelfile baking."""
        records = self.load_all(limit=limit * 2)
        exemplars: list[dict[str, str]] = []
        for r in reversed(records):
            inst = str(r.get("instruction", "")).strip()
            resp = str(r.get("response") or r.get("output", "")).strip()
            if inst and resp and len(resp) <= 1200:
                exemplars.append({"instruction": inst, "response": resp})
            if len(exemplars) >= limit:
                break
        exemplars.reverse()
        return exemplars

    def record_user_preference_rule(self, rule_text: str, category: str = "coding_style") -> dict[str, Any]:
        """Records a permanent rule from user feedback to auto-inject into background worker prompts."""
        clean_rule, _ = _redact(rule_text.strip())
        try:
            current_lessons = json.loads(self.lessons_file.read_text(encoding="utf-8"))
        except Exception:
            current_lessons = []

        new_entry = {
            "timestamp": _now_iso(),
            "category": category,
            "rule": clean_rule,
            "enforce_on_workers": True,
        }
        current_lessons.append(new_entry)
        self.lessons_file.write_text(json.dumps(current_lessons, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"recorded": True, "total_rules": len(current_lessons), "rule": clean_rule}

    def get_worker_preference_headers(self) -> str:
        """Generates the preference header to prepend to background Writer Bot prompts."""
        try:
            lessons = json.loads(self.lessons_file.read_text(encoding="utf-8"))
            active_rules = [l["rule"] for l in lessons if l.get("enforce_on_workers")]
            if not active_rules:
                return ""
            header_lines = ["USER ACCUMULATED PREFERENCES (Enforced by Lucy):"]
            for r in active_rules[-8:]:
                header_lines.append(f"- {r}")
            return "\n".join(header_lines) + "\n\n"
        except Exception:
            return ""

    def export_alpaca_dataset(self, output_path: Path | None = None) -> Path:
        """
        Converts the verified queue into standard Alpaca format for LoRA fine-tuning:
        [{"instruction": "...", "input": "", "output": "..."}]
        """
        out_file = output_path or (self.learning_dir / "lora_dataset_alpaca.json")
        dataset = []

        if self.queue_file.exists():
            with open(self.queue_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        dataset.append({
                            "instruction": record.get("instruction", ""),
                            "input": record.get("input", ""),
                            "output": record.get("response") or record.get("output", ""),
                        })
                    except Exception:
                        continue

        out_file.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")
        return out_file

    def generate_modelfile_for_adapter(self, adapter_name: str, base_model: str = "qwen2.5:7b") -> str:
        """Generates an Ollama Modelfile ready to hot-swap the new LoRA adapter."""
        modelfile_content = f"""# LUCY Autonomous Modelfile - Auto-Generated after LoRA Sleep Cycle
FROM {base_model}

# Attach sovereign neural memory adapter
ADAPTER ./adapters/{adapter_name}

# Set temperature & context
PARAMETER temperature 0.3
PARAMETER num_ctx 8192

# Invariant Core Persona
SYSTEM \"\"\"You are LUCY, an autonomous localized AI operating system created and programmed solely by Senin as a sovereign local AI desktop operating assistant.
You hold continuous personal memory, deterministic safety boundaries, and manage background coding workers.
You never hallucinate; if you lack facts or a file does not exist on disk, you state it plainly.\"\"\"
"""
        modelfile_path = self.lucy_data / "Modelfile"
        modelfile_path.write_text(modelfile_content, encoding="utf-8")
        return modelfile_content

    def status(self) -> dict[str, Any]:
        records = self.load_all()
        return {
            "stage": STAGE,
            "training_queue": "active",
            "queue_file": str(self.queue_file),
            "verified_samples_count": len(records),
            "verified_records_count": len(records),
            "ready_for_sleep_cycle": len(records) >= 1,
            "lessons_file": str(self.lessons_file),
            "anti_hallucination_gate": "active (unverified samples blocked)",
        }


# Backward-compatible alias
TrainingQueue = VerifiedTrainingQueue
