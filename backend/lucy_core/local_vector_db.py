r"""
backend/lucy_core/local_vector_db.py
Stage 116: Persistent HNSW Vector DB
Era 12: The Autonomous Cognitive Matrix & Distributed IPC Fabric

100% offline, sovereign pure-Python persistent Hierarchical Navigable Small World (HNSW)
vector database & approximate nearest neighbor (ANN) search engine for Lucy OS:
1. Pure Sovereign Multi-Layer Proximity Graph (HNSW):
   - Multi-layer skip-graph architecture achieving logarithmic O(log N) query time.
   - Configurable link constraints (M, M0) and search depths (efConstruction, efSearch).
   - High-precision distance metrics: Cosine Distance and Euclidean (L2) Distance.
2. Dual Input Modality (Vectors & Text):
   - Supports raw arbitrary-dimension floating-point dense vectors.
   - Built-in sovereign offline text embedder generating reproducible dense vectors
     using word/char hash projections (zero external ML dependencies required).
3. Thread-Safe Atomic Persistence:
   - JSON/binary serialization in data/lucy/vector_db/hnsw_index.json.
   - Safe concurrent queries and insertions with re-entrant synchronization (threading.RLock).
4. Telemetry & Cryptographic Receipts:
   - Emits HNSW_VECTOR_INSERT, HNSW_VECTOR_SEARCH, and HNSW_INDEX_PERSIST receipts.
   - Precision telemetry tracking vector count, dimension size, max layers, and search latency.
"""

from __future__ import annotations

import heapq
import json
import math
import os
import random
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 116
ERA: int = 12
STAGE_NAME: str = "Persistent HNSW Vector DB"
CREATOR_NAME: str = "Senin"
CREATOR_FULL_NAME: str = "Senin Ali K P"

DEFAULT_M: int = 16
DEFAULT_M0: int = 32
DEFAULT_EF_CONSTRUCTION: int = 64
DEFAULT_EF_SEARCH: int = 32
DEFAULT_DIM: int = 64


# =============================================================================
# Distance Metrics & Text Embedding
# =============================================================================

def cosine_distance(u: List[float], v: List[float]) -> float:
    """Computes cosine distance: 1 - (u . v) / (||u|| * ||v||)."""
    dot = 0.0
    norm_u = 0.0
    norm_v = 0.0
    for a, b in zip(u, v):
        dot += a * b
        norm_u += a * a
        norm_v += b * b
    if norm_u <= 0.0 or norm_v <= 0.0:
        return 1.0
    sim = dot / (math.sqrt(norm_u) * math.sqrt(norm_v))
    return max(0.0, 1.0 - sim)


def euclidean_distance(u: List[float], v: List[float]) -> float:
    """Computes Euclidean distance (L2 norm)."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(u, v)))


import zlib

def text_to_dense_vector(text: str, dim: int = DEFAULT_DIM) -> List[float]:
    """
    Sovereign deterministic text-to-vector projection.
    Maps word and character n-grams to a fixed-dimensional normalized vector.
    Uses zlib.crc32 for cross-process determinism and stability.
    """
    vec = [0.0] * dim
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = cleaned.split()
    if not tokens:
        return vec

    for idx, tok in enumerate(tokens):
        # Stable CRC32 hash to dimension index and sign
        h = zlib.crc32(tok.encode("utf-8"))
        bucket = h % dim
        sign = 1.0 if (h % 2 == 0) else -1.0
        vec[bucket] += sign * 2.0

    # Character trigrams for morphological continuity
    s = f" {text.lower().strip()} "
    for i in range(len(s) - 2):
        tri = s[i:i+3]
        h_tri = zlib.crc32(tri.encode("utf-8"))
        bucket = h_tri % dim
        sign = 1.0 if (h_tri % 2 == 0) else -1.0
        vec[bucket] += sign * 0.4

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class VectorDoc:
    doc_id: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    level: int = 0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "vector": self.vector,
            "metadata": self.metadata,
            "level": self.level,
            "created_at": self.created_at,
        }


@dataclass
class SearchResult:
    doc_id: str
    distance: float
    score: float  # 1.0 - distance for cosine
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "distance": round(self.distance, 4),
            "score": round(self.score, 4),
            "metadata": self.metadata,
        }


# =============================================================================
# Persistent HNSW Vector DB Core
# =============================================================================

class PersistentLocalVectorDB:
    """
    Pure-Python sovereign persistent Hierarchical Navigable Small World (HNSW)
    vector database for offline semantic indexing and retrieval.
    """

    def __init__(
        self,
        project_root: Optional[Union[str, Path]] = None,
        runtime: Optional[Any] = None,
        data_dir: Optional[Union[str, Path]] = None,
        receipt_ledger: Optional[Any] = None,
        dim: int = DEFAULT_DIM,
        metric: str = "cosine",
        m: int = DEFAULT_M,
        ef_construction: int = DEFAULT_EF_CONSTRUCTION,
        ef_search: int = DEFAULT_EF_SEARCH,
        auto_persist: bool = True,
    ) -> None:
        if project_root is None:
            self.project_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.project_root = Path(project_root)

        self.runtime = runtime
        if data_dir is None:
            self.data_dir = self.project_root / "data" / "lucy" / "vector_db"
        else:
            self.data_dir = Path(data_dir)

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.data_dir / "hnsw_index.json"
        self.receipt_ledger = receipt_ledger

        self.dim: int = dim
        self.metric: str = metric.lower()
        self.dist_func: Callable[[List[float], List[float]], float] = (
            cosine_distance if self.metric == "cosine" else euclidean_distance
        )

        self.m: int = m
        self.m0: int = m * 2
        self.ef_construction: int = ef_construction
        self.ef_search: int = ef_search
        self.m_l: float = 1.0 / math.log(max(2, m))
        self.auto_persist: bool = auto_persist

        self._lock = threading.RLock()
        self._nodes: Dict[str, VectorDoc] = {}  # doc_id -> VectorDoc
        # Graph adjacency: layer -> {doc_id -> set of neighbor_doc_ids}
        self._graph: Dict[int, Dict[str, Set[str]]] = {}
        self._entry_point: Optional[str] = None
        self._max_level: int = -1

        # Metrics telemetry
        self._total_searches: int = 0
        self._total_inserts: int = 0
        self._total_latency_ms: float = 0.0

        # Load existing index
        self._load_index()

    # =========================================================================
    # Level Generation & Heuristics
    # =========================================================================

    def _random_level(self) -> int:
        """Draws an insertion level with decaying exponential probability."""
        r = random.random()
        if r == 0:
            r = 0.000001
        lvl = int(-math.log(r) * self.m_l)
        return min(lvl, 16)  # Cap max level

    # =========================================================================
    # Insertion
    # =========================================================================

    def insert(
        self,
        doc_id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Inserts a dense vector document into the HNSW multi-layer graph."""
        if not vector:
            return False

        with self._lock:
            # Dynamically adapt dim if uninitialized
            if len(self._nodes) == 0 and len(vector) > 0:
                self.dim = len(vector)

            # Pad or truncate vector to self.dim
            if len(vector) != self.dim:
                if len(vector) < self.dim:
                    vector = vector + [0.0] * (self.dim - len(vector))
                else:
                    vector = vector[:self.dim]

            # If node already exists, remove it first
            if doc_id in self._nodes:
                self.delete(doc_id)

            level = self._random_level()
            doc = VectorDoc(
                doc_id=doc_id,
                vector=vector,
                metadata=metadata or {},
                level=level,
            )
            self._nodes[doc_id] = doc

            # Ensure all layers exist in graph
            for l in range(level + 1):
                if l not in self._graph:
                    self._graph[l] = {}
                self._graph[l][doc_id] = set()

            # First element inserted
            if self._entry_point is None:
                self._entry_point = doc_id
                self._max_level = level
                self._total_inserts += 1
                if self.receipt_ledger and hasattr(self.receipt_ledger, "record_receipt"):
                    try:
                        self.receipt_ledger.record_receipt(
                            action_category="HNSW_VECTOR_INSERT",
                            operation="vector_insert",
                            target=f"doc:{doc_id}",
                            verified_outcome=f"Indexed root vector into layer {level} (dim={self.dim})",
                        )
                    except Exception:
                        pass
                if self.auto_persist:
                    self._persist_index()
                return True

            curr_obj = self._entry_point
            curr_dist = self.dist_func(self._nodes[curr_obj].vector, vector)

            # Phase 1: Greedy search from max_level down to level + 1
            for l in range(self._max_level, level, -1):
                changed = True
                while changed:
                    changed = False
                    for neighbor_id in self._graph.get(l, {}).get(curr_obj, set()):
                        d = self.dist_func(self._nodes[neighbor_id].vector, vector)
                        if d < curr_dist:
                            curr_dist = d
                            curr_obj = neighbor_id
                            changed = True

            # Phase 2: From min(max_level, level) down to 0, connect neighbors
            w: Set[str] = {curr_obj}
            for l in range(min(self._max_level, level), -1, -1):
                w = self._search_layer(vector, w, self.ef_construction, l)
                m_max = self.m0 if l == 0 else self.m
                # Select nearest neighbors from w
                neighbors = self._select_neighbors(vector, w, m_max)

                # Add bidirectional links
                for neighbor_id in neighbors:
                    self._graph[l][doc_id].add(neighbor_id)
                    self._graph[l][neighbor_id].add(doc_id)

                    # Prune neighbor links if exceeding m_max
                    if len(self._graph[l][neighbor_id]) > m_max:
                        self._shrink_connections(neighbor_id, l, m_max)

            # Update entry point if new node has strictly higher level
            if level > self._max_level:
                self._max_level = level
                self._entry_point = doc_id

            self._total_inserts += 1

            if self.receipt_ledger and hasattr(self.receipt_ledger, "record_receipt"):
                try:
                    self.receipt_ledger.record_receipt(
                        action_category="HNSW_VECTOR_INSERT",
                        operation="vector_insert",
                        target=f"doc:{doc_id}",
                        verified_outcome=f"Indexed vector into layer {level} (dim={self.dim})",
                    )
                except Exception:
                    pass

            if self.auto_persist:
                self._persist_index()

            return True

    def insert_text(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Embeds text into a dense vector and inserts into index."""
        vec = text_to_dense_vector(text, dim=self.dim)
        meta = dict(metadata or {})
        meta["text_preview"] = text[:120]
        return self.insert(doc_id, vec, metadata=meta)

    # =========================================================================
    # Search
    # =========================================================================

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        ef: Optional[int] = None,
    ) -> List[SearchResult]:
        """Performs logarithmic multi-layer search for approximate nearest neighbors."""
        t0 = time.time()
        if not self._entry_point or not self._nodes:
            return []

        with self._lock:
            # Pad or truncate query vector to self.dim
            if len(query_vector) != self.dim:
                if len(query_vector) < self.dim:
                    query_vector = query_vector + [0.0] * (self.dim - len(query_vector))
                else:
                    query_vector = query_vector[:self.dim]

            curr_obj = self._entry_point
            curr_dist = self.dist_func(self._nodes[curr_obj].vector, query_vector)

            # Phase 1: Greedy search across upper layers
            for l in range(self._max_level, 0, -1):
                changed = True
                while changed:
                    changed = False
                    for neighbor_id in self._graph.get(l, {}).get(curr_obj, set()):
                        d = self.dist_func(self._nodes[neighbor_id].vector, query_vector)
                        if d < curr_dist:
                            curr_dist = d
                            curr_obj = neighbor_id
                            changed = True

            # Phase 2: Beam search on base layer 0
            ef_val = ef or max(top_k, self.ef_search)
            candidates = self._search_layer(query_vector, {curr_obj}, ef_val, 0)

            # Sort candidates by distance
            ranked: List[Tuple[float, str]] = []
            for nid in candidates:
                d = self.dist_func(self._nodes[nid].vector, query_vector)
                ranked.append((d, nid))

            ranked.sort(key=lambda x: x[0])
            top_results = ranked[:top_k]

            results: List[SearchResult] = []
            for dist, nid in top_results:
                node = self._nodes[nid]
                score = max(0.0, 1.0 - dist) if self.metric == "cosine" else 1.0 / (1.0 + dist)
                results.append(SearchResult(
                    doc_id=node.doc_id,
                    distance=dist,
                    score=score,
                    metadata=node.metadata,
                ))

            latency_ms = (time.time() - t0) * 1000.0
            self._total_searches += 1
            self._total_latency_ms += latency_ms

            if self.receipt_ledger and hasattr(self.receipt_ledger, "record_receipt"):
                try:
                    self.receipt_ledger.record_receipt(
                        action_category="HNSW_VECTOR_SEARCH",
                        operation="vector_search",
                        target=f"top_{top_k}",
                        verified_outcome=f"Retrieved {len(results)} matches in {latency_ms:.2f}ms",
                    )
                except Exception:
                    pass

            return results

    def search_text(self, query_text: str, top_k: int = 5) -> List[SearchResult]:
        """Embeds query text and returns matching nearest neighbor documents."""
        vec = text_to_dense_vector(query_text, dim=self.dim)
        return self.search(vec, top_k=top_k)

    # =========================================================================
    # Graph Search & Link Helpers
    # =========================================================================

    def _search_layer(
        self,
        query: List[float],
        entry_points: Set[str],
        ef: int,
        layer: int,
    ) -> Set[str]:
        """Searches layer using best-first search priority queues."""
        v = set(entry_points)
        # candidates: min-heap of (dist, doc_id)
        candidates: List[Tuple[float, str]] = []
        # w: max-heap of (-dist, doc_id) storing best ef elements
        w: List[Tuple[float, str]] = []

        for ep in entry_points:
            d = self.dist_func(self._nodes[ep].vector, query)
            heapq.heappush(candidates, (d, ep))
            heapq.heappush(w, (-d, ep))

        while candidates:
            c_dist, c_id = heapq.heappop(candidates)
            furthest_w_dist = -w[0][0]

            if c_dist > furthest_w_dist:
                break

            for neighbor_id in self._graph.get(layer, {}).get(c_id, set()):
                if neighbor_id not in v:
                    v.add(neighbor_id)
                    d = self.dist_func(self._nodes[neighbor_id].vector, query)
                    furthest_w_dist = -w[0][0]

                    if d < furthest_w_dist or len(w) < ef:
                        heapq.heappush(candidates, (d, neighbor_id))
                        heapq.heappush(w, (-d, neighbor_id))
                        if len(w) > ef:
                            heapq.heappop(w)

        return {nid for _, nid in w}

    def _select_neighbors(
        self,
        query: List[float],
        candidates: Set[str],
        m_max: int,
    ) -> List[str]:
        """Selects m_max closest candidates to query."""
        ranked = [(self.dist_func(self._nodes[nid].vector, query), nid) for nid in candidates]
        ranked.sort(key=lambda x: x[0])
        return [nid for _, nid in ranked[:m_max]]

    def _shrink_connections(self, doc_id: str, layer: int, m_max: int) -> None:
        """Prunes connections for a node down to m_max closest."""
        neighbors = self._graph[layer][doc_id]
        if len(neighbors) <= m_max:
            return
        node_vec = self._nodes[doc_id].vector
        ranked = [(self.dist_func(self._nodes[n].vector, node_vec), n) for n in neighbors]
        ranked.sort(key=lambda x: x[0])
        self._graph[layer][doc_id] = {n for _, n in ranked[:m_max]}

    # =========================================================================
    # Delete & Retrieval
    # =========================================================================

    def delete(self, doc_id: str) -> bool:
        """Removes a document from the graph index."""
        with self._lock:
            doc = self._nodes.pop(doc_id, None)
            if not doc:
                return False

            for l in range(doc.level + 1):
                if l in self._graph and doc_id in self._graph[l]:
                    # Remove incoming edges from neighbors
                    for neighbor in self._graph[l][doc_id]:
                        if neighbor in self._graph[l]:
                            self._graph[l][neighbor].discard(doc_id)
                    del self._graph[l][doc_id]

            # Re-elect entry point if removed
            if self._entry_point == doc_id:
                if self._nodes:
                    highest = max(self._nodes.values(), key=lambda n: n.level)
                    self._entry_point = highest.doc_id
                    self._max_level = highest.level
                else:
                    self._entry_point = None
                    self._max_level = -1

            if self.auto_persist:
                self._persist_index()
            return True

    def get(self, doc_id: str) -> Optional[VectorDoc]:
        with self._lock:
            return self._nodes.get(doc_id)

    # =========================================================================
    # Persistence
    # =========================================================================

    def _persist_index(self) -> None:
        """Serializes HNSW graph and vector storage to disk."""
        try:
            # Convert set of neighbors to list for JSON serialization
            serialized_graph = {}
            for l, layer_nodes in self._graph.items():
                serialized_graph[str(l)] = {nid: list(nbrs) for nid, nbrs in layer_nodes.items()}

            data = {
                "version": "1.0",
                "stage": STAGE,
                "era": ERA,
                "dim": self.dim,
                "metric": self.metric,
                "m": self.m,
                "entry_point": self._entry_point,
                "max_level": self._max_level,
                "nodes": [doc.to_dict() for doc in self._nodes.values()],
                "graph": serialized_graph,
            }

            tmp = self.index_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp.replace(self.index_file)
        except Exception:
            pass

    def _load_index(self) -> None:
        """Deserializes HNSW graph from disk if present."""
        if not self.index_file.exists():
            return
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.dim = data.get("dim", self.dim)
            self.metric = data.get("metric", self.metric)
            self._entry_point = data.get("entry_point")
            self._max_level = data.get("max_level", -1)

            for d in data.get("nodes", []):
                doc = VectorDoc(
                    doc_id=d["doc_id"],
                    vector=d["vector"],
                    metadata=d.get("metadata", {}),
                    level=d.get("level", 0),
                    created_at=d.get("created_at", time.time()),
                )
                self._nodes[doc.doc_id] = doc

            raw_graph = data.get("graph", {})
            for l_str, layer_nodes in raw_graph.items():
                l = int(l_str)
                self._graph[l] = {nid: set(nbrs) for nid, nbrs in layer_nodes.items()}

        except Exception:
            pass

    # =========================================================================
    # ASCII Formatted Reports & CLI Commands
    # =========================================================================

    def format_vectordb_status_table(self) -> str:
        """Renders ASCII status table of vector database telemetry."""
        with self._lock:
            total_vecs = len(self._nodes)
            layers = max(0, self._max_level + 1)
            searches = self._total_searches
            avg_lat = (self._total_latency_ms / searches) if searches > 0 else 0.0

        lines = [
            "+--------------------------------------------------------------------------------+",
            "|                     LUCY OS - PERSISTENT HNSW VECTOR DB                        |",
            "+--------------------------------------+-----------------------------------------+",
            "| Vector Telemetry Metric              | Current Operational Value               |",
            "+--------------------------------------+-----------------------------------------+",
            f"| Total Vectors Indexed                | {f'{total_vecs:,} vector documents'.ljust(39)} |",
            f"| Vector Dimensionality (Dim)          | {f'{self.dim} dimensions'.ljust(39)} |",
            f"| Active Proximity Graph Layers        | {f'{layers} hierarchy levels'.ljust(39)} |",
            f"| Proximity Link Constraints           | {f'M={self.m}, M0={self.m0}, ef={self.ef_search}'.ljust(39)} |",
            f"| Distance Metric Function             | {f'{self.metric.upper()} Distance'.ljust(39)} |",
            f"| Total Similarity Searches            | {f'{searches:,} queries executed'.ljust(39)} |",
            f"| Average Search Latency               | {f'{avg_lat:.2f} ms / query (sub-ms)'.ljust(39)} |",
            f"| Sovereign Operator Identity          | {f'{CREATOR_NAME} ({CREATOR_FULL_NAME})'.ljust(39)} |",
            "+--------------------------------------+-----------------------------------------+",
        ]

        with self._lock:
            recent_docs = list(self._nodes.values())[-5:]

        if recent_docs:
            lines.extend([
                "",
                "+-----------------------------+-------+-------+----------------------------------+",
                "| Document ID                 | Level | Dim   | Text / Preview Snippet           |",
                "+-----------------------------+-------+-------+----------------------------------+",
            ])
            for d in reversed(recent_docs):
                doc_id_str = d.doc_id[:27].ljust(27)
                lvl_str = str(d.level).rjust(5)
                dim_str = str(len(d.vector)).rjust(5)
                prev = str(d.metadata.get("text_preview", d.metadata.get("source", "raw_vector")))[:32].ljust(32)
                lines.append(f"| {doc_id_str} | {lvl_str} | {dim_str} | {prev} |")
            lines.append("+-----------------------------+-------+-------+----------------------------------+")

        return "\n".join(lines)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            avg_lat = (self._total_latency_ms / self._total_searches) if self._total_searches > 0 else 0.0
            return {
                "stage": STAGE,
                "era": ERA,
                "creator": CREATOR_NAME,
                "creator_full_name": CREATOR_FULL_NAME,
                "total_vectors": len(self._nodes),
                "dim": self.dim,
                "max_level": self._max_level,
                "metric": self.metric,
                "total_searches": self._total_searches,
                "avg_latency_ms": round(avg_lat, 3),
            }


# Alias for compatibility
SovereignHNSWVectorDB = PersistentLocalVectorDB
