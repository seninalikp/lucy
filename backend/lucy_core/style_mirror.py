"""
backend/lucy_core/style_mirror.py
Stage 88: Dynamic Few-Shot Operator Style Mirror & Semantic Preference Ingestion

Dynamically mirrors operator technical style, ingests explicit and implicit
operator preferences, and selects context-relevant few-shot exemplars to personalize
Lucy's responses in zero-latency real time without waiting for nightly weight updates.
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

from backend.lucy_core.lora_harvester import CuratedInteraction, HighSignalLoRAHarvester

STAGE: int = 88


@dataclass
class OperatorPreference:
    key: str
    value: str
    category: str  # "tooling", "syntax", "verbosity", "architecture", "tone"
    confidence: float
    source: str   # "explicit_command", "implicit_feedback", "inferred_habit"
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "category": self.category,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "updated_at": self.updated_at,
        }


class DynamicStyleMirror:
    """
    Manages operator style preferences, extracts implicit feedback rules,
    and dynamically selects high-signal few-shot exemplars tailored to the prompt.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        harvester: Optional[HighSignalLoRAHarvester] = None,
        receipt_ledger: Optional[Any] = None,
        preferences_dir: Optional[Path] = None,
    ) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.harvester = harvester or HighSignalLoRAHarvester(project_root=self.project_root)
        self.receipt_ledger = receipt_ledger

        self.preferences_dir = preferences_dir or (self.project_root / "data" / "lucy" / "preferences")
        self.preferences_dir.mkdir(parents=True, exist_ok=True)
        self.preferences_file = self.preferences_dir / "operator_preferences.json"

        self.preferences: Dict[str, OperatorPreference] = {}
        self._load_preferences()

        # Seed defaults if brand new
        if not self.preferences:
            self._seed_default_preferences()

    def _seed_default_preferences(self) -> None:
        defaults = [
            OperatorPreference(key="tone_voice", value="authentic first-person peer systems engineer ('I', 'we')", category="tone", confidence=1.0, source="system_policy"),
            OperatorPreference(key="anti_third_person", value="strictly never speak in third-person ('Lucy thinks/will')", category="tone", confidence=1.0, source="system_policy"),
            OperatorPreference(key="verbosity_pacing", value="concise, direct, technically dense; zero sycophancy or apologies", category="verbosity", confidence=0.95, source="system_policy"),
            OperatorPreference(key="python_style", value="type hints, explicit error handling, pathlib over os.path", category="syntax", confidence=0.90, source="inferred_habit"),
            OperatorPreference(key="testing_framework", value="pytest with AST pre-validation and isolated tempfiles", category="tooling", confidence=0.90, source="inferred_habit"),
        ]
        for p in defaults:
            self.preferences[p.key] = p
        self._save_preferences()

    def _load_preferences(self) -> None:
        if not self.preferences_file.exists():
            return
        try:
            with open(self.preferences_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    self.preferences[k] = OperatorPreference(
                        key=v["key"],
                        value=v["value"],
                        category=v.get("category", "general"),
                        confidence=v.get("confidence", 0.8),
                        source=v.get("source", "loaded"),
                        updated_at=v.get("updated_at", time.time()),
                    )
        except Exception:
            pass

    def _save_preferences(self) -> None:
        try:
            payload = {k: p.to_dict() for k, p in self.preferences.items()}
            with open(self.preferences_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass

    def ingest_preference(
        self,
        key: str,
        value: str,
        category: str = "general",
        confidence: float = 0.90,
        source: str = "explicit_command",
    ) -> OperatorPreference:
        """
        Explicitly registers or updates an operator preference.
        """
        clean_key = re.sub(r"[^a-zA-Z0-9_]", "_", key.strip().lower())
        pref = OperatorPreference(
            key=clean_key,
            value=value.strip(),
            category=category,
            confidence=max(0.1, min(1.0, confidence)),
            source=source,
            updated_at=time.time(),
        )
        self.preferences[clean_key] = pref
        self._save_preferences()

        if self.receipt_ledger is not None:
            try:
                self.receipt_ledger.issue_receipt(
                    action_category="style_mirror",
                    operation="ingest_preference",
                    target=clean_key,
                    verified_outcome=f"Updated preference: {value[:35]} (conf: {confidence:.2f})",
                )
            except Exception:
                pass

        return pref

    def detect_implicit_preferences(self, user_statement: str) -> List[OperatorPreference]:
        """
        Analyzes operator statements for implicit preferences (e.g. 'prefer X over Y', 'use A instead of B').
        """
        detected: List[OperatorPreference] = []
        stmt = user_statement.strip()

        # Pattern: prefer X over Y / prefer X to Y
        m_prefer = re.search(r"\bprefer\s+([a-zA-Z0-9_\-\.]+)\s+(?:over|to|instead of)\s+([a-zA-Z0-9_\-\.]+)", stmt, re.I)
        if m_prefer:
            favored = m_prefer.group(1).strip()
            avoided = m_prefer.group(2).strip()
            pref = self.ingest_preference(
                key=f"prefer_{favored}",
                value=f"Use {favored} rather than {avoided}",
                category="tooling",
                confidence=0.88,
                source="implicit_feedback",
            )
            detected.append(pref)

        # Pattern: always use X
        m_always = re.search(r"\balways\s+use\s+([a-zA-Z0-9_\-\.]+)", stmt, re.I)
        if m_always and not m_prefer:
            tool = m_always.group(1).strip()
            pref = self.ingest_preference(
                key=f"always_{tool}",
                value=f"Always use {tool}",
                category="tooling",
                confidence=0.92,
                source="implicit_feedback",
            )
            detected.append(pref)

        # Pattern: don't use X / never use X
        m_never = re.search(r"\b(?:never|don't|do not)\s+use\s+([a-zA-Z0-9_\-\.]+)", stmt, re.I)
        if m_never:
            avoided_tool = m_never.group(1).strip()
            pref = self.ingest_preference(
                key=f"avoid_{avoided_tool}",
                value=f"Avoid using {avoided_tool}",
                category="tooling",
                confidence=0.92,
                source="implicit_feedback",
            )
            detected.append(pref)

        return detected

    def select_few_shot_exemplars(self, prompt: str, max_exemplars: int = 2) -> List[CuratedInteraction]:
        """
        Selects top semantically relevant, high-signal exemplars from the harvester
        based on token overlap with the current operator prompt.
        """
        if not self.harvester or not hasattr(self.harvester, "curated_interactions"):
            return []

        tokens = set(re.findall(r"\b[a-zA-Z0-9_]{3,}\b", prompt.lower()))
        if not tokens:
            return self.harvester.curated_interactions[:max_exemplars]

        scored: List[Tuple[float, CuratedInteraction]] = []
        for item in self.harvester.curated_interactions:
            # Score lexical overlap with instruction + category match
            inst_tokens = set(re.findall(r"\b[a-zA-Z0-9_]{3,}\b", item.instruction.lower()))
            overlap = len(tokens & inst_tokens)
            score = (overlap * 0.4) + (item.signal_score * 0.6)
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:max_exemplars]]

    def build_style_steering_block(self, current_prompt: str) -> str:
        """
        Builds a compact in-context prompt block containing operator preferences
        and dynamic few-shot exemplars to steer tone in real-time.
        """
        lines = ["[OPERATOR STYLE & ALIGNMENT DIRECTIVES]"]

        # 1. Active preferences
        for p in sorted(self.preferences.values(), key=lambda x: x.category):
            lines.append(f"- {p.category.capitalize()}: {p.value}")

        # 2. Dynamic exemplars
        exemplars = self.select_few_shot_exemplars(current_prompt, max_exemplars=2)
        if exemplars:
            lines.append("\n[HIGH-SIGNAL IN-CONTEXT EXEMPLARS]")
            for i, ex in enumerate(exemplars, start=1):
                clean_inst = ex.instruction.strip().replace("\n", " ")
                clean_resp = ex.response.strip().replace("\n", " ")
                lines.append(f"Example {i} User: {clean_inst[:80]}")
                lines.append(f"Example {i} Response: {clean_resp[:120]}")

        return "\n".join(lines)

    def format_terminal_summary(self) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| DYNAMIC FEW-SHOT OPERATOR STYLE MIRROR (STAGE 88)                    |")
        lines.append("+----------------------------------------------------------------------+")
        total_prefs = len(self.preferences)
        lines.append(f"| Registered Preferences: {total_prefs:<15} | Storage: operator_preferences.json |")
        lines.append("+----------------------------------------------------------------------+")

        if self.preferences:
            lines.append("| ACTIVE OPERATOR PREFERENCES:                                         |")
            for p in self.preferences.values():
                val_snippet = p.value[:45]
                lines.append(f"|  * {p.key:<20} ({p.category:<9}): {val_snippet:<30} |")
            lines.append("+----------------------------------------------------------------------+")

        gold_cnt = len(self.harvester.curated_interactions) if self.harvester else 0
        lines.append(f"| Available Exemplar Pool: {gold_cnt:<14} | Zero-Latency In-Context Steering: ON |")
        lines.append("+----------------------------------------------------------------------+")
        return "\n".join(lines)

    def status(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "preferences_count": len(self.preferences),
            "preferences_file": str(self.preferences_file),
            "categories": sorted(list({p.category for p in self.preferences.values()})),
        }
