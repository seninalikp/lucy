"""
backend/lucy_core/lora_harvester.py
Stage 84: High-Signal LoRA Interaction Harvester & Preference Dataset Curator

Extracts, filters, and curates gold-standard interaction pairs and DPO preference
triplets from Lucy's live conversations, enforcing strict anti-sycophancy,
anti-hallucination grounding, and pure first-person peer voice.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

STAGE: int = 84

# Boilerplate sycophantic / bot tropes that penalize response score or define 'rejected' pairs
SYCOPHANTIC_PATTERNS = [
    re.compile(r"\b(?:as an ai(?: language model)?|certainly!|i would be happy to|i am here to assist)\b", re.I),
    re.compile(r"\b(?:i apologize for the confusion|please feel free to|let me know if you need anything else)\b", re.I),
    re.compile(r"\b(?:great question!|absolutely!|you are completely right, my apologies)\b", re.I),
]

# Third-person self-references (strictly prohibited in 'chosen' responses)
THIRD_PERSON_PATTERNS = [
    re.compile(r"\bLucy thinks\b", re.I),
    re.compile(r"\bLucy will\b", re.I),
    re.compile(r"\bLucy is\b", re.I),
    re.compile(r"\bLucy can\b", re.I),
    re.compile(r"\bLucy has\b", re.I),
    re.compile(r"\bLucy recommends\b", re.I),
    re.compile(r"\bLucy suggests\b", re.I),
    re.compile(r"\bLucy's\b", re.I),
]


@dataclass
class CuratedInteraction:
    interaction_id: str
    instruction: str
    response: str
    category: str  # "coding", "reasoning", "fact_grounding", "anti_sycophancy", "system_ops"
    signal_score: float  # 0.0 to 1.0
    epistemic_grounding: bool
    pushback_detected: bool
    first_person_pure: bool
    created_at: float = field(default_factory=time.time)

    def to_alpaca(self) -> Dict[str, str]:
        return {
            "instruction": self.instruction,
            "input": "",
            "output": self.response,
        }

    def to_sharegpt(self) -> Dict[str, Any]:
        return {
            "id": self.interaction_id,
            "conversations": [
                {"from": "human", "value": self.instruction},
                {"from": "gpt", "value": self.response},
            ],
        }


@dataclass
class DPOPreferencePair:
    pair_id: str
    prompt: str
    chosen: str
    rejected: str
    category: str
    margin_score: float  # Difference in quality between chosen and rejected (0.1 to 1.0)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair_id": self.pair_id,
            "prompt": self.prompt,
            "chosen": self.chosen,
            "rejected": self.rejected,
            "category": self.category,
            "margin_score": round(self.margin_score, 3),
            "created_at": self.created_at,
        }


class HighSignalLoRAHarvester:
    """
    Scans runtime interaction history, evaluates cognitive signal quality,
    enforces first-person peer voice, and maintains high-signal LoRA and DPO datasets.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        data_dir: Optional[Path] = None,
        receipt_ledger: Optional[Any] = None,
        min_signal_threshold: float = 0.70,
    ) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.data_dir = data_dir or (self.project_root / "data" / "lucy" / "lora")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.receipt_ledger = receipt_ledger
        self.min_signal_threshold = min_signal_threshold

        self.golden_file = self.data_dir / "golden_interactions_alpaca.json"
        self.dpo_file = self.data_dir / "preference_pairs_dpo.jsonl"
        self.manifest_file = self.data_dir / "harvester_manifest.json"

        self.curated_interactions: List[CuratedInteraction] = []
        self.preference_pairs: List[DPOPreferencePair] = []
        self._load_datasets()

    def _load_datasets(self) -> None:
        # Load golden alpaca items
        if self.golden_file.exists():
            try:
                with open(self.golden_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        self.curated_interactions.append(
                            CuratedInteraction(
                                interaction_id=item.get("id", f"gen_{len(self.curated_interactions)}"),
                                instruction=item.get("instruction", ""),
                                response=item.get("output", ""),
                                category=item.get("category", "coding"),
                                signal_score=item.get("signal_score", 0.85),
                                epistemic_grounding=item.get("epistemic_grounding", True),
                                pushback_detected=item.get("pushback_detected", False),
                                first_person_pure=True,
                            )
                        )
            except Exception:
                pass

        # Load DPO preference pairs
        if self.dpo_file.exists():
            try:
                with open(self.dpo_file, "r", encoding="utf-8") as f:
                    for line in f:
                        l = line.strip()
                        if l:
                            obj = json.loads(l)
                            self.preference_pairs.append(
                                DPOPreferencePair(
                                    pair_id=obj.get("pair_id", f"pair_{len(self.preference_pairs)}"),
                                    prompt=obj.get("prompt", ""),
                                    chosen=obj.get("chosen", ""),
                                    rejected=obj.get("rejected", ""),
                                    category=obj.get("category", "general"),
                                    margin_score=obj.get("margin_score", 0.5),
                                    created_at=obj.get("created_at", time.time()),
                                )
                            )
            except Exception:
                pass

    def _save_datasets(self) -> None:
        try:
            # 1. Save Golden Alpaca JSON
            alpaca_list = []
            for item in self.curated_interactions:
                d = item.to_alpaca()
                d["id"] = item.interaction_id
                d["category"] = item.category
                d["signal_score"] = round(item.signal_score, 3)
                d["epistemic_grounding"] = item.epistemic_grounding
                d["pushback_detected"] = item.pushback_detected
                alpaca_list.append(d)

            with open(self.golden_file, "w", encoding="utf-8") as f:
                json.dump(alpaca_list, f, indent=2)

            # 2. Save DPO JSONL
            with open(self.dpo_file, "w", encoding="utf-8") as f:
                for pair in self.preference_pairs:
                    f.write(json.dumps(pair.to_dict()) + "\n")

            # 3. Save Manifest Summary
            manifest = {
                "last_updated": datetime.now().isoformat(),
                "total_golden_interactions": len(self.curated_interactions),
                "total_preference_pairs": len(self.preference_pairs),
                "categories": self._category_distribution(),
                "average_signal_score": self._average_signal_score(),
            }
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

        except Exception:
            pass

    def evaluate_interaction(
        self,
        instruction: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculates interaction signal quality score (0.0 to 1.0).
        Evaluates conciseness, anti-sycophancy, epistemic grounding, and tone.
        """
        meta = metadata or {}
        inst_clean = instruction.strip()
        resp_clean = response.strip()

        if not inst_clean or not resp_clean or len(resp_clean) < 15:
            return 0.0, {"reason": "Interaction too short or empty."}

        # 1. Tonal Purity: Third-person self-reference check
        has_third_person = any(pat.search(resp_clean) for pat in THIRD_PERSON_PATTERNS)
        first_person_pure = not has_third_person

        # 2. Sycophancy / Filler check
        has_sycophancy = any(pat.search(resp_clean) for pat in SYCOPHANTIC_PATTERNS)

        # 3. Pushback / Anti-sycophancy detection
        # Check if response challenges an incorrect premise or pushes back constructively
        pushback_cues = ["actually", "wait", "caution", "correction", "not quite", "differ", "instead", "better approach"]
        has_pushback = any(cue in resp_clean.lower() for cue in pushback_cues) or meta.get("pushback_enforced", False)

        # 4. Epistemic Grounding (receipts, code AST, fact check results)
        is_grounded = bool(
            meta.get("verified_receipt")
            or meta.get("fact_checked")
            or meta.get("ast_valid")
            or ("```python" in resp_clean and "def " in resp_clean)
        )

        # 5. Length & Noise Check
        # Penalize excessive rambling (> 3000 chars without code)
        is_concise = len(resp_clean) <= 1800 or ("```" in resp_clean)

        # Calculate composite score
        score = 0.50  # Base score
        if first_person_pure:
            score += 0.15
        else:
            score -= 0.35  # Heavy penalty for third person

        if not has_sycophancy:
            score += 0.10
        else:
            score -= 0.25  # Heavy penalty for sycophancy

        if is_grounded:
            score += 0.15

        if has_pushback:
            score += 0.10

        if is_concise:
            score += 0.05
        else:
            score -= 0.10

        final_score = max(0.0, min(1.0, score))

        eval_info = {
            "signal_score": round(final_score, 3),
            "first_person_pure": first_person_pure,
            "has_sycophancy": has_sycophancy,
            "has_pushback": has_pushback,
            "is_grounded": is_grounded,
            "is_concise": is_concise,
        }
        return final_score, eval_info

    def harvest_turn(
        self,
        instruction: str,
        response: str,
        category: str = "coding",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[CuratedInteraction]:
        """
        Evaluates a turn. If score >= min_signal_threshold, curates it into golden set.
        Also synthesizes a DPO preference pair if sycophantic alternative is contrastable.
        """
        score, eval_info = self.evaluate_interaction(instruction, response, metadata)
        if score < self.min_signal_threshold:
            return None

        # Clean any mild formatting quirks
        cleaned_resp = response.strip()

        interaction_id = f"gold_{int(time.time())}_{len(self.curated_interactions) + 1}"
        curated = CuratedInteraction(
            interaction_id=interaction_id,
            instruction=instruction.strip(),
            response=cleaned_resp,
            category=category,
            signal_score=score,
            epistemic_grounding=eval_info["is_grounded"],
            pushback_detected=eval_info["has_pushback"],
            first_person_pure=eval_info["first_person_pure"],
        )
        self.curated_interactions.append(curated)

        # Create DPO negative contrast pair if response is high-signal
        if score >= 0.80 and eval_info["first_person_pure"]:
            # Synthesize rejected counter-example (sycophantic / third-person version)
            rejected_variant = self._generate_sycophantic_rejected(cleaned_resp)
            pair_id = f"dpo_{interaction_id}"
            dpo_pair = DPOPreferencePair(
                pair_id=pair_id,
                prompt=instruction.strip(),
                chosen=cleaned_resp,
                rejected=rejected_variant,
                category=category,
                margin_score=round(score - 0.35, 3),
            )
            self.preference_pairs.append(dpo_pair)

        self._save_datasets()

        if self.receipt_ledger is not None:
            try:
                self.receipt_ledger.issue_receipt(
                    action_category="lora_harvest",
                    operation="curate_interaction",
                    target=instruction[:40],
                    verified_outcome=f"Curated {interaction_id} (score: {score:.2f}, category: {category})",
                )
            except Exception:
                pass

        return curated

    def _generate_sycophantic_rejected(self, chosen: str) -> str:
        """
        Generates a synthetic negative exemplar for DPO training that demonstrates
        sycophancy, verbosity, and third-person bot tropes.
        """
        lines = chosen.splitlines()
        body = "\n".join(lines[:6]) if len(lines) > 6 else chosen
        # Inject third-person and sycophantic phrasing
        rejected = f"Certainly! As an AI language model, Lucy is delighted to assist you with this.\n\nLucy recommends:\n{body}\n\nI hope this was helpful! Please let me know if you need any further clarification."
        return rejected

    def _category_distribution(self) -> Dict[str, int]:
        dist: Dict[str, int] = {}
        for item in self.curated_interactions:
            dist[item.category] = dist.get(item.category, 0) + 1
        return dist

    def _average_signal_score(self) -> float:
        if not self.curated_interactions:
            return 0.0
        return round(sum(i.signal_score for i in self.curated_interactions) / len(self.curated_interactions), 3)

    def prune_low_signal(self, threshold: Optional[float] = None) -> int:
        cutoff = threshold if threshold is not None else self.min_signal_threshold
        initial_count = len(self.curated_interactions)
        self.curated_interactions = [i for i in self.curated_interactions if i.signal_score >= cutoff]
        pruned = initial_count - len(self.curated_interactions)
        if pruned > 0:
            self._save_datasets()
        return pruned

    def format_terminal_summary(self) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| HIGH-SIGNAL LORA HARVESTER & DATASET CURATOR (STAGE 84)              |")
        lines.append("+----------------------------------------------------------------------+")
        gold_cnt = len(self.curated_interactions)
        dpo_cnt = len(self.preference_pairs)
        avg_score = f"{self._average_signal_score() * 100.0:.1f}%"
        lines.append(f"| Golden Exemplars: {gold_cnt:<14} | DPO Preference Pairs: {dpo_cnt:<15} |")
        lines.append(f"| Mean Signal Score: {avg_score:<13} | Min Score Gate: {self.min_signal_threshold * 100:.0f}%{'':<15} |")
        lines.append("+----------------------------------------------------------------------+")

        cats = self._category_distribution()
        if cats:
            lines.append("| CATEGORY BREAKDOWN:                                                  |")
            cat_parts = [f"{cat}: {cnt}" for cat, cnt in cats.items()]
            for chunk in [cat_parts[i : i + 3] for i in range(0, len(cat_parts), 3)]:
                cat_line = " | ".join(chunk)
                lines.append(f"|  * {cat_line:<65} |")
            lines.append("+----------------------------------------------------------------------+")

        lines.append("| STORAGE ARTIFACTS:                                                   |")
        lines.append(f"|  * Alpaca JSON: {self.golden_file.name:<52} |")
        lines.append(f"|  * DPO JSONL:   {self.dpo_file.name:<52} |")
        lines.append(f"|  * Manifest:    {self.manifest_file.name:<52} |")
        lines.append("+----------------------------------------------------------------------+")
        return "\n".join(lines)

    def status(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "golden_exemplars_count": len(self.curated_interactions),
            "preference_pairs_count": len(self.preference_pairs),
            "average_signal_score": self._average_signal_score(),
            "min_signal_threshold": self.min_signal_threshold,
            "data_directory": str(self.data_dir),
            "categories": self._category_distribution(),
        }
