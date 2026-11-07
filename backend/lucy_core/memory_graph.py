"""
memory_graph.py
Stage 54 / Stage 63 Upgraded = Temporal Memory Graph with Semantic Contradiction & Conflict Resolution.

Capabilities:
1. BM25 + Temporal Decay + Pinned Priority Retrieval.
2. Canonical Slot Extraction: Detects subject slots (focus, project, editor, stack, gpu, os, etc.)
   and automatically supersedes older nodes holding a different value for the same slot.
3. Explicit Pivot & Retraction Resolution: Parses "switch from A to B", "stop using A, use B",
   "instead of A use B", and "I don't use A anymore" to retire stale facts immediately.
4. Causal Lineage & Conflict Audit Trail: Tracks `supersedes_ids`, `superseded_by_id`, and
   `conflicts_resolved` history so Lucy never hallucinates from outdated preferences.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE = "63 semantic memory contradiction and conflict resolver"

STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "your", "have", "are",
    "was", "were", "will", "would", "could", "should", "into", "about", "currently",
    "right", "now", "please", "remember", "note", "keep", "mind", "fact",
}

# Canonical subject slot patterns: (slot_name, regex_extracting_value)
SLOT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "slot:primary_focus",
        re.compile(
            r"(?:my\s+)?(?:current\s+|main\s+|primary\s+)?(?:focus|priority)\s+(?:is|changed\s+to|is\s+now)\s+([^.!?\n;]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "slot:active_project",
        re.compile(
            r"(?:my\s+)?(?:current\s+|main\s+|primary\s+|active\s+)?project\s+(?:is|changed\s+to|is\s+now)\s+([^.!?\n;]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "slot:working_on",
        re.compile(
            r"i\s+am\s+(?:currently\s+|now\s+)?(?:working\s+on|building)\s+([^.!?\n;]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "slot:editor",
        re.compile(
            r"(?:my\s+)?(?:preferred\s+|current\s+|main\s+|default\s+)?(?:code\s+)?(?:editor|ide)\s+(?:is|changed\s+to|is\s+now)\s+([^.!?\n;]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "slot:os",
        re.compile(
            r"(?:my\s+)?(?:preferred\s+|current\s+|main\s+|primary\s+)?(?:os|operating\s+system|distro)\s+(?:is|changed\s+to|is\s+now)\s+([^.!?\n;]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "slot:database",
        re.compile(
            r"(?:my\s+|our\s+|the\s+)?(?:preferred\s+|current\s+|main\s+|primary\s+|active\s+)?(?:database|db)\s+(?:is|changed\s+to|is\s+now)\s+([^.!?\n;]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "slot:stack",
        re.compile(
            r"(?:my\s+)?(?:preferred\s+|current\s+|main\s+|primary\s+)?(?:stack|framework|language)\s+(?:is|changed\s+to|is\s+now)\s+([^.!?\n;]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "slot:gpu",
        re.compile(
            r"(?:my\s+)?(?:current\s+|main\s+|primary\s+)?gpu\s+(?:is|changed\s+to|is\s+now)\s+([^.!?\n;]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "slot:laptop",
        re.compile(
            r"(?:my\s+)?(?:current\s+|main\s+|primary\s+)?(?:laptop|machine)\s+(?:is|changed\s+to|is\s+now)\s+([^.!?\n;]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "slot:deadline",
        re.compile(
            r"(?:my\s+|the\s+)?(?:current\s+|main\s+|next\s+)?deadline\s+(?:is|changed\s+to|is\s+now)\s+([^.!?\n;]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "slot:ui_mode",
        re.compile(
            r"(?:my\s+|the\s+|lucy\'?s?\s+)?(?:ui\s+mode|interface\s+mode)\s+(?:is|changed\s+to|is\s+now)\s+([^.!?\n;]+)",
            re.IGNORECASE,
        ),
    ),
]

# Explicit transition/replacement patterns: extracts (old_target, new_target)
TRANSITION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?:switch|change|move|migrate)\s+(?:[\w\s]{0,25}?from\s+)([^.!?\n,;]+?)\s+to\s+([^.!?\n,;]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:stop\s+using|drop|replace|quit\s+using)\s+([^.!?\n,;]+?)\s*(?:,|and)?\s*(?:use|switch\s+to|with)\s+([^.!?\n,;]+?)(?:\s+instead)?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"instead\s+of\s+([^.!?\n,;]+?)\s*,\s*(?:use|we\s+use|i\s+use|switch\s+to)\s+([^.!?\n,;]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"no\s+longer\s+(?:using|working\s+on)\s+([^.!?\n,;]+?)\s*[,;]\s*(?:now\s+)?(?:using|working\s+on)\s+([^.!?\n,;]+)",
        re.IGNORECASE,
    ),
]

# Explicit negation/retraction patterns: extracts (retracted_target)
RETRACTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?:i\s+don\'?t|i\s+do\s+not|we\s+don\'?t|no\s+longer)\s+(?:use|want|work\s+on|need)\s+([^.!?\n,;]+?)(?:\s+anymore|\s+any\s+longer)?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:stop\s+using|drop|abandon|scrap)\s+([^.!?\n,;]+)$",
        re.IGNORECASE,
    ),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower()).rstrip(".,;!?")


def _tokens(text: str) -> list[str]:
    raw = re.findall(r"[a-z0-9_]+", str(text or "").lower())
    return [t for t in raw if len(t) > 2 and t not in STOPWORDS]


class TemporalMemoryGraph:
    """BM25 + Temporal Decay + Slot/Semantic Contradiction Memory Graph."""

    def __init__(self, memory_dir: Path) -> None:
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.graph_file = self.memory_dir / "memory_graph.json"
        self._ensure_file()

    def _default_data(self) -> dict[str, Any]:
        return {
            "version": "2.0.0",
            "stage": STAGE,
            "created_at": _now(),
            "updated_at": _now(),
            "nodes": [],
            "conflicts_resolved": [],
        }

    def _ensure_file(self) -> None:
        if not self.graph_file.exists():
            self._write(self._default_data())

    def _read(self) -> dict[str, Any]:
        try:
            data = json.loads(self.graph_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("nodes", [])
                data.setdefault("conflicts_resolved", [])
                return data
        except Exception:
            pass
        return self._default_data()

    def _write(self, data: dict[str, Any]) -> None:
        data["updated_at"] = _now()
        data["stage"] = STAGE
        temp = self.graph_file.with_suffix(".tmp")
        temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(self.graph_file)

    def extract_slot(self, fact_text: str) -> tuple[str | None, str | None]:
        """Extracts (slot_key, normalized_slot_value) if the fact assigns a state/preference slot."""
        cleaned = str(fact_text or "").strip().rstrip(".,;!?")
        for slot_key, pattern in SLOT_PATTERNS:
            m = pattern.search(cleaned)
            if m:
                val = _normalize(m.group(1))
                if val:
                    return slot_key, val
        return None, None

    def extract_transition(self, fact_text: str) -> tuple[str | None, str | None]:
        """Extracts (old_target, new_target) from explicit pivot sentences."""
        cleaned = str(fact_text or "").strip().rstrip(".,;!?")
        for pattern in TRANSITION_PATTERNS:
            m = pattern.search(cleaned)
            if m:
                old_t = _normalize(m.group(1))
                new_t = _normalize(m.group(2))
                if old_t and new_t and old_t != new_t:
                    return old_t, new_t
        return None, None

    def extract_retraction(self, fact_text: str) -> str | None:
        """Extracts retracted target from negation sentences like 'I don't use X anymore'."""
        cleaned = str(fact_text or "").strip().rstrip(".,;!?")
        # Ignore if it's a two-part transition ("stop using X, use Y")
        if self.extract_transition(cleaned)[0] is not None:
            return None
        for pattern in RETRACTION_PATTERNS:
            m = pattern.search(cleaned)
            if m:
                target = _normalize(m.group(1))
                if target and len(target) >= 2:
                    return target
        return None

    def _detect_contradictions(
        self,
        active_nodes: list[dict[str, Any]],
        new_fact: str,
        new_slot: str | None,
        new_slot_val: str | None,
        old_target: str | None,
        retracted_target: str | None,
    ) -> list[ tuple[dict[str, Any], str] ]:
        """
        Finds active memory nodes that are contradicted or superseded by `new_fact`.
        Returns list of (node, conflict_reason).
        """
        superseded: list[tuple[dict[str, Any], str]] = []
        new_tokens = set(_tokens(new_fact))

        for node in active_nodes:
            node_fact = str(node.get("fact") or node.get("content") or "")
            node_norm = _normalize(node_fact)
            node_slot = node.get("slot_key")
            node_slot_val = node.get("slot_value")

            # Backfill slot for older Stage 54 nodes if not yet tagged
            if not node_slot:
                node_slot, node_slot_val = self.extract_slot(node_fact)

            # Rule 1: Same canonical slot with a new value
            if new_slot and node_slot == new_slot and new_slot_val and node_slot_val != new_slot_val:
                superseded.append((node, f"slot_override:{new_slot} ({node_slot_val} -> {new_slot_val})"))
                continue

            # Rule 2: Explicit transition ("switch from <old_target> to <new_target>")
            if old_target and len(old_target) >= 2:
                if old_target in node_norm or (node_slot_val and old_target in node_slot_val):
                    superseded.append((node, f"explicit_pivot_from:{old_target}"))
                    continue

            # Rule 3: Explicit retraction ("I don't use <retracted_target> anymore")
            if retracted_target and len(retracted_target) >= 2:
                if retracted_target in node_norm and "don't" not in node_norm and "no longer" not in node_norm:
                    superseded.append((node, f"explicit_retraction_of:{retracted_target}"))
                    continue

            # Rule 4: High lexical subject overlap with conflicting predicate/value
            node_tokens = set(_tokens(node_fact))
            if len(new_tokens) >= 3 and len(node_tokens) >= 3:
                overlap = len(new_tokens & node_tokens) / float(min(len(new_tokens), len(node_tokens)))
                if overlap >= 0.75 and node_norm != _normalize(new_fact):
                    superseded.append((node, f"high_lexical_overlap:{overlap:.2f}"))

        return superseded

    def upsert_fact(
        self,
        fact: str,
        category: str = "general",
        source: str = "user",
        pinned: bool = False,
    ) -> dict[str, Any]:
        """Inserts a new fact node and resolves any contradictions against active nodes."""
        cleaned = re.sub(r"\s+", " ", str(fact or "")).strip()
        if not cleaned:
            return {"saved": False, "reason": "Empty fact.", "superseded_ids": []}

        norm = _normalize(cleaned)
        data = self._read()
        nodes: list[dict[str, Any]] = data["nodes"]
        active_nodes = [n for n in nodes if n.get("status", "active") == "active" and not n.get("deleted")]

        # Check exact duplicate among active nodes
        for existing in active_nodes:
            if _normalize(existing.get("fact", "")) == norm:
                existing["updated_at"] = _now()
                existing["access_count"] = int(existing.get("access_count", 0)) + 1
                if pinned:
                    existing["pinned"] = True
                self._write(data)
                return {
                    "saved": False,
                    "duplicate": True,
                    "node": existing,
                    "superseded_ids": [],
                }

        slot_key, slot_val = self.extract_slot(cleaned)
        old_target, new_target = self.extract_transition(cleaned)
        retracted_target = self.extract_retraction(cleaned)

        contradictions = self._detect_contradictions(
            active_nodes=active_nodes,
            new_fact=cleaned,
            new_slot=slot_key,
            new_slot_val=slot_val,
            old_target=old_target,
            retracted_target=retracted_target,
        )

        new_id = f"mnode_{len(nodes) + 1:04d}"
        superseded_ids: list[str] = []
        now_ts = _now()

        for old_node, reason in contradictions:
            old_id = str(old_node.get("id", ""))
            old_node["status"] = "superseded"
            old_node["active"] = False
            old_node["superseded_at"] = now_ts
            old_node["superseded_by"] = new_id
            old_node["supersession_reason"] = reason
            superseded_ids.append(old_id)

            data["conflicts_resolved"].append({
                "timestamp": now_ts,
                "old_node_id": old_id,
                "old_fact": old_node.get("fact", ""),
                "new_node_id": new_id,
                "new_fact": cleaned,
                "reason": reason,
            })

        new_node = {
            "id": new_id,
            "fact": cleaned,
            "content": cleaned,
            "normalized": norm,
            "category": category,
            "source": source,
            "slot_key": slot_key,
            "slot_value": slot_val,
            "tokens": _tokens(cleaned),
            "pinned": bool(pinned),
            "status": "active",
            "active": True,
            "deleted": False,
            "supersedes": superseded_ids,
            "superseded_by": None,
            "access_count": 1,
            "created_at": now_ts,
            "updated_at": now_ts,
        }
        nodes.append(new_node)
        self._write(data)

        return {
            "saved": True,
            "duplicate": False,
            "node": new_node,
            "superseded_ids": superseded_ids,
            "conflicts_resolved": len(superseded_ids),
        }

    # Alias for compatibility
    remember = upsert_fact
    add_fact = upsert_fact

    def query(self, query_text: str = "", limit: int = 8, include_superseded: bool = False) -> list[dict[str, Any]]:
        """BM25 + Temporal Recency + Pinned Priority retrieval over active memory nodes."""
        data = self._read()
        nodes = data.get("nodes", [])
        if include_superseded:
            pool = [n for n in nodes if not n.get("deleted")]
        else:
            pool = [
                n for n in nodes
                if n.get("status", "active") == "active"
                and n.get("active", True)
                and not n.get("deleted")
            ]

        if not pool:
            return []

        q_clean = str(query_text or "").strip()
        if not q_clean:
            # Sort pinned first, then most recent
            ordered = sorted(
                pool,
                key=lambda n: (bool(n.get("pinned")), str(n.get("updated_at") or n.get("created_at") or "")),
                reverse=True,
            )
            return ordered[:limit]

        q_tokens = _tokens(q_clean)
        q_lower = q_clean.lower()

        # Compute simple BM25 + recency + pinned boost
        N = len(pool)
        avgdl = max(1.0, sum(len(n.get("tokens") or _tokens(n.get("fact", ""))) for n in pool) / float(N))
        k1 = 1.5
        b = 0.75

        df: dict[str, int] = {}
        for tok in set(q_tokens):
            df[tok] = sum(1 for n in pool if tok in (n.get("tokens") or _tokens(n.get("fact", ""))))

        scored: list[tuple[float, dict[str, Any]]] = []
        for idx, node in enumerate(pool):
            doc_tokens = node.get("tokens") or _tokens(node.get("fact", ""))
            dl = len(doc_tokens)
            score = 0.0

            if q_lower in str(node.get("fact", "")).lower():
                score += 4.0

            for tok in q_tokens:
                tf = doc_tokens.count(tok)
                if tf > 0:
                    n_q = df.get(tok, 0)
                    idf = math.log(1.0 + (N - n_q + 0.5) / (n_q + 0.5))
                    denom = tf + k1 * (1.0 - b + b * (dl / avgdl))
                    score += idf * ((tf * (k1 + 1.0)) / denom)

            if score > 0:
                if node.get("pinned"):
                    score += 5.0
                # Slight recency tie-breaker based on position
                score += (idx / float(max(1, N))) * 0.25
                scored.append((score, node))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]

    recall = query

    def pin_fact(self, selector: str, pinned: bool = True) -> dict[str, Any]:
        """Pins or unpins an active memory node by ID or substring."""
        sel = str(selector or "").strip().lower()
        if not sel:
            return {"ok": False, "reason": "Selector was empty."}

        data = self._read()
        for node in reversed(data.get("nodes", [])):
            if node.get("deleted"):
                continue
            if str(node.get("id", "")).lower() == sel or sel in str(node.get("fact", "")).lower():
                node["pinned"] = bool(pinned)
                node["updated_at"] = _now()
                self._write(data)
                return {"ok": True, "node": node, "pinned": bool(pinned)}
        return {"ok": False, "reason": f"No memory node matched '{selector}'."}

    def unpin_fact(self, selector: str) -> dict[str, Any]:
        return self.pin_fact(selector, pinned=False)

    def explain_lineage(self, query_or_id: str = "") -> dict[str, Any]:
        """Traces the full causal supersession chain for a memory ID, slot, or topic."""
        data = self._read()
        nodes = data.get("nodes", [])
        by_id = {str(n.get("id")): n for n in nodes}
        q = str(query_or_id or "").strip().lower()

        target_node = None
        if q in by_id:
            target_node = by_id[q]
        else:
            for n in reversed(nodes):
                if (
                    q in str(n.get("fact", "")).lower()
                    or q in str(n.get("slot_key", "")).lower()
                ):
                    target_node = n
                    break

        if target_node is None:
            return {
                "ok": False,
                "query": query_or_id,
                "chain": [],
                "message": f"No memory lineage found for '{query_or_id}'.",
            }

        # Walk backward to the earliest ancestor
        visited: set[str] = set()
        ancestors: list[dict[str, Any]] = []

        def _walk_back(node: dict[str, Any]) -> None:
            for old_id in node.get("supersedes", []):
                if old_id in by_id and old_id not in visited:
                    visited.add(old_id)
                    _walk_back(by_id[old_id])
                    ancestors.append(by_id[old_id])

        _walk_back(target_node)

        # Walk forward if target_node itself was superseded
        descendants: list[dict[str, Any]] = []
        curr = target_node
        while curr.get("superseded_by") and curr["superseded_by"] in by_id:
            nxt_id = curr["superseded_by"]
            if nxt_id in visited:
                break
            visited.add(nxt_id)
            nxt_node = by_id[nxt_id]
            descendants.append(nxt_node)
            curr = nxt_node

        chain = ancestors + [target_node] + descendants
        formatted_steps = [
            f"{item['id']} [{item.get('status', 'active').upper()}] {item.get('fact', '')}"
            for item in chain
        ]
        return {
            "ok": True,
            "query": query_or_id,
            "chain_length": len(chain),
            "chain": chain,
            "formatted_chain": " -> ".join(formatted_steps),
        }

    def list_conflicts(self, limit: int = 15) -> list[dict[str, Any]]:
        """Returns the history of resolved semantic contradictions."""
        data = self._read()
        conflicts = data.get("conflicts_resolved", [])
        return list(reversed(conflicts))[:limit]

    def forget(self, query: str) -> dict[str, Any]:
        cleaned = str(query or "").strip().lower()
        if not cleaned or cleaned in {"all", "everything", "memory"}:
            return {"forgotten": 0, "ids": [], "reason": "Specify a memory to forget."}

        data = self._read()
        forgotten_ids: list[str] = []
        for node in data.get("nodes", []):
            if node.get("deleted") or node.get("status") == "archived":
                continue
            if cleaned == str(node.get("id", "")).lower() or cleaned in str(node.get("fact", "")).lower():
                node["deleted"] = True
                node["active"] = False
                node["status"] = "archived"
                node["deleted_at"] = _now()
                forgotten_ids.append(str(node.get("id")))

        if forgotten_ids:
            self._write(data)
        return {"forgotten": len(forgotten_ids), "ids": forgotten_ids}

    def status(self) -> dict[str, Any]:
        data = self._read()
        nodes = data.get("nodes", [])
        active = [n for n in nodes if n.get("status") == "active" and not n.get("deleted")]
        superseded = [n for n in nodes if n.get("status") == "superseded" and not n.get("deleted")]
        pinned = [n for n in active if n.get("pinned")]
        conflicts = data.get("conflicts_resolved", [])
        return {
            "stage": STAGE,
            "memory_graph": "active",
            "file": str(self.graph_file),
            "total_nodes": len(nodes),
            "active_nodes": len(active),
            "superseded_nodes": len(superseded),
            "pinned_nodes": len(pinned),
            "conflicts_resolved_count": len(conflicts),
            "recent_conflicts": conflicts[-5:],
        }
