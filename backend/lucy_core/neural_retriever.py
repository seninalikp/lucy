r"""
backend/lucy_core/neural_retriever.py
Stage 103: Hybrid Neural-Lexical Vector RAG Engine
Era 11: The Sovereign Super-Autonomous Core & Hyper-Resilient Operating Fabric

Sovereign offline local RAG architecture for Lucy OS:
1. Lexical BM25 Okapi Indexer:
   - High-performance tokenization, inverted index, document lengths, and IDF calculations.
2. Dense Semantic Vector Projection:
   - Zero-cloud deterministic n-gram and syntactic feature hash projection into normalized unit hyperspace (dim=64).
   - Fast cosine dot-product similarity ranking.
3. Reciprocal Rank Fusion (RRF):
   - Merges lexical BM25 ranks and dense vector ranks: RRF(d) = sum(w / (k + rank(d))).
   - Exact symbol boosting for direct class/function identifier hits.
4. Semantic Code Chunker:
   - Breaks Python files into structured AST/symbol chunks with line coordinates.
5. Context Window Assembler:
   - Prepares token-budgeted prompt contexts for local LLM consumption.
6. Execution Receipt Auditing:
   - Records HYBRID_RETRIEVAL_QUERY and RAG_REINDEX receipts.
7. Commands:
   - /neural-search
   - /reindex-rag
   - /rag-status
   - /retrieve-context
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 103

CREATOR_NAME: str = "Senin"
CREATOR_FULL_NAME: str = "Senin Ali K P"

VECTOR_DIM: int = 64
RRF_K: float = 60.0
BM25_K1: float = 1.5
BM25_B: float = 0.75


@dataclass
class CodeChunk:
    chunk_id: str
    file_path: str
    symbol_name: str
    chunk_type: str  # function, class, module, docstring
    start_line: int
    end_line: int
    content: str
    tokens_count: int
    dense_vector: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "file_path": self.file_path,
            "symbol_name": self.symbol_name,
            "chunk_type": self.chunk_type,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "tokens_count": self.tokens_count,
            "content": self.content,
        }


@dataclass
class SearchResultItem:
    chunk: CodeChunk
    bm25_score: float
    vector_score: float
    rrf_score: float
    exact_match: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk": self.chunk.to_dict(),
            "bm25_score": round(self.bm25_score, 4),
            "vector_score": round(self.vector_score, 4),
            "rrf_score": round(self.rrf_score, 6),
            "exact_match": self.exact_match,
        }


@dataclass
class SearchResponse:
    query: str
    total_chunks_scanned: int
    results_count: int
    results: List[SearchResultItem]
    duration_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "total_chunks_scanned": self.total_chunks_scanned,
            "results_count": self.results_count,
            "results": [r.to_dict() for r in self.results],
            "duration_ms": round(self.duration_ms, 3),
        }

    def format_terminal_summary(self) -> str:
        lines: List[str] = [
            "+======================================================================+",
            "|               LUCY OS - HYBRID NEURAL-LEXICAL RAG                    |",
            "|                 STAGE 103: DENSE BM25 + VECTOR RRF                   |",
            "+======================================================================+",
            f"| Query:         {self.query[:45]:<45} |",
            f"| Scanned Chunks:{self.total_chunks_scanned:<10} | Hits: {self.results_count:<6} | Latency: {self.duration_ms:>6.2f} ms |",
            "+----------------------------------------------------------------------+",
            "| TOP RELEVANT CODE CHUNKS:                                            |",
            "| File / Symbol               | Type    | Line    | BM25   | Vec  | RRF    |",
            "+-----------------------------+---------+---------+--------+------+--------+",
        ]
        for item in self.results[:6]:
            c = item.chunk
            fname = Path(c.file_path).name[:14]
            sym = c.symbol_name[:12]
            label = f"{fname}:{sym}"[:27]
            ctype = c.chunk_type[:7]
            lrange = f"{c.start_line}-{c.end_line}"[:7]
            b_sc = f"{item.bm25_score:.2f}"[:6]
            v_sc = f"{item.vector_score:.2f}"[:4]
            rrf = f"{item.rrf_score:.4f}"[:6]
            lines.append(f"| {label:<27} | {ctype:<7} | {lrange:<7} | {b_sc:<6} | {v_sc:<4} | {rrf:<6} |")

        lines.append("+======================================================================+")
        return "\n".join(lines)


class HybridNeuralRetriever:
    """
    Stage 103 Hybrid Neural-Lexical Vector RAG Engine.
    Combines BM25 lexical inverted search with sovereign dense vector projection
    using Reciprocal Rank Fusion (RRF) and exact symbol boosting.
    """

    def __init__(
        self,
        project_root: Optional[Union[str, Path]] = None,
        runtime: Optional[Any] = None,
        receipt_ledger: Optional[Any] = None,
        data_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parent.parent.parent
        self.runtime = runtime
        self.receipt_ledger = receipt_ledger
        self.data_dir = Path(data_dir) if data_dir else (self.project_root / "data" / "lucy" / "rag")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.data_dir / "hybrid_index.json"

        self.chunks: List[CodeChunk] = []
        self._doc_lens: List[int] = []
        self._avg_doc_len: float = 1.0
        self._inverted_index: Dict[str, List[Tuple[int, int]]] = {}  # term -> [(chunk_idx, count)]
        self._idf: Dict[str, float] = {}

        self._load_or_build_index()

    def search(
        self,
        query: str,
        top_k: int = 5,
        bm25_weight: float = 1.0,
        vec_weight: float = 1.0,
    ) -> SearchResponse:
        """Executes hybrid reciprocal rank fusion search across all indexed code chunks."""
        t0 = time.perf_counter_ns()
        if not self.chunks:
            self.reindex()

        q_clean = query.strip()
        q_tokens = self._tokenize(q_clean)
        q_dense = self._project_dense_vector(q_clean)

        total_chunks = len(self.chunks)
        if total_chunks == 0:
            elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000.0
            return SearchResponse(query=query, total_chunks_scanned=0, results_count=0, results=[], duration_ms=elapsed_ms)

        # 1. Lexical BM25 Scoring
        bm25_scores: Dict[int, float] = {}
        for term in q_tokens:
            if term in self._inverted_index:
                idf = self._idf.get(term, 0.5)
                for c_idx, freq in self._inverted_index[term]:
                    doc_len = self._doc_lens[c_idx]
                    num = freq * (BM25_K1 + 1.0)
                    denom = freq + BM25_K1 * (1.0 - BM25_B + BM25_B * (doc_len / max(1.0, self._avg_doc_len)))
                    bm25_scores[c_idx] = bm25_scores.get(c_idx, 0.0) + idf * (num / max(0.001, denom))

        # 2. Dense Vector Scoring (Cosine Similarity)
        vec_scores: Dict[int, float] = {}
        for c_idx, chunk in enumerate(self.chunks):
            if chunk.dense_vector:
                sim = self._cosine_sim(q_dense, chunk.dense_vector)
                if sim > 0.05:
                    vec_scores[c_idx] = sim

        # 3. Reciprocal Rank Fusion
        bm25_sorted = sorted(bm25_scores.keys(), key=lambda i: bm25_scores[i], reverse=True)
        vec_sorted = sorted(vec_scores.keys(), key=lambda i: vec_scores[i], reverse=True)

        bm25_ranks = {c_idx: rank + 1 for rank, c_idx in enumerate(bm25_sorted)}
        vec_ranks = {c_idx: rank + 1 for rank, c_idx in enumerate(vec_sorted)}

        candidate_indices = set(bm25_ranks.keys()) | set(vec_ranks.keys())
        if not candidate_indices:
            # Fallback to top-K closest vectors if no lexical hits
            all_sorted_vec = sorted(range(total_chunks), key=lambda i: self._cosine_sim(q_dense, self.chunks[i].dense_vector), reverse=True)
            candidate_indices = set(all_sorted_vec[:top_k])

        rrf_results: List[SearchResultItem] = []
        for c_idx in candidate_indices:
            chunk = self.chunks[c_idx]
            b_sc = bm25_scores.get(c_idx, 0.0)
            v_sc = vec_scores.get(c_idx, self._cosine_sim(q_dense, chunk.dense_vector))

            r_bm25 = bm25_ranks.get(c_idx, 9999)
            r_vec = vec_ranks.get(c_idx, 9999)

            score_rrf = (bm25_weight / (RRF_K + r_bm25)) + (vec_weight / (RRF_K + r_vec))

            # Exact symbol boost
            exact_match = (
                q_clean.lower() in chunk.symbol_name.lower()
                or chunk.symbol_name.lower() in q_clean.lower()
            )
            if exact_match and len(q_clean) > 2:
                score_rrf *= 1.35

            rrf_results.append(
                SearchResultItem(
                    chunk=chunk,
                    bm25_score=b_sc,
                    vector_score=v_sc,
                    rrf_score=score_rrf,
                    exact_match=exact_match,
                )
            )

        rrf_results.sort(key=lambda x: x.rrf_score, reverse=True)
        final_results = rrf_results[:top_k]

        elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000.0

        # Record receipt
        top_sym = final_results[0].chunk.symbol_name if final_results else "none"
        self._record_receipt(
            "HYBRID_RETRIEVAL_QUERY",
            "neural_search",
            query[:30],
            f"hits={len(final_results)}, top={top_sym}, wall_ms={elapsed_ms:.2f}",
        )

        return SearchResponse(
            query=query,
            total_chunks_scanned=total_chunks,
            results_count=len(final_results),
            results=final_results,
            duration_ms=elapsed_ms,
        )

    def retrieve_context_window(self, query: str, max_tokens: int = 1500) -> str:
        """Assembles a markdown context block of relevant chunks respecting max token limit."""
        resp = self.search(query, top_k=6)
        if not resp.results:
            return f"[No relevant code context found for query: '{query}']"

        lines: List[str] = [f"### [Sovereign Neural RAG Context: '{query}']", ""]
        accum_tokens = 0

        for idx, res in enumerate(resp.results, start=1):
            c = res.chunk
            if accum_tokens + c.tokens_count > max_tokens and idx > 1:
                break

            lines.append(f"#### Reference {idx}: `{c.file_path}` ({c.chunk_type} `{c.symbol_name}`, Lines {c.start_line}-{c.end_line})")
            lines.append("```python")
            lines.append(c.content.strip())
            lines.append("```")
            lines.append("")
            accum_tokens += c.tokens_count

        return "\n".join(lines)

    def reindex(self) -> Dict[str, Any]:
        """Scans backend/lucy_core and builds fresh BM25 and vector indices."""
        t0 = time.perf_counter_ns()
        core_dir = self.project_root / "backend" / "lucy_core"
        if not core_dir.exists():
            return {"error": "backend/lucy_core directory not found", "chunks_indexed": 0}

        chunks: List[CodeChunk] = []
        for py_file in sorted(core_dir.glob("*.py")):
            if py_file.is_file() and not py_file.name.endswith(".bak"):
                file_chunks = self._chunk_python_file(py_file)
                chunks.extend(file_chunks)

        self.chunks = chunks
        self._doc_lens = [c.tokens_count for c in self.chunks]
        self._avg_doc_len = sum(self._doc_lens) / max(1, len(self._doc_lens))

        # Build Inverted Index
        self._inverted_index.clear()
        doc_term_freqs: List[Dict[str, int]] = []
        doc_count_containing: Dict[str, int] = {}

        for c_idx, chunk in enumerate(self.chunks):
            tokens = self._tokenize(chunk.content + " " + chunk.symbol_name)
            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            doc_term_freqs.append(tf)

            for term in tf.keys():
                doc_count_containing[term] = doc_count_containing.get(term, 0) + 1
                if term not in self._inverted_index:
                    self._inverted_index[term] = []
                self._inverted_index[term].append((c_idx, tf[term]))

        # Compute IDF
        total_docs = len(self.chunks)
        self._idf.clear()
        for term, doc_cnt in doc_count_containing.items():
            # Standard BM25 IDF: ln((N - n + 0.5) / (n + 0.5) + 1)
            idf = math.log(((total_docs - doc_cnt + 0.5) / (doc_cnt + 0.5)) + 1.0)
            self._idf[term] = max(0.1, idf)

        self._save_index()

        elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000.0
        self._record_receipt(
            "RAG_REINDEX",
            "reindex",
            "backend/lucy_core",
            f"chunks={len(self.chunks)}, terms={len(self._inverted_index)}, wall_ms={elapsed_ms:.1f}",
        )

        return {
            "chunks_indexed": len(self.chunks),
            "unique_terms": len(self._inverted_index),
            "avg_doc_len": round(self._avg_doc_len, 1),
            "duration_ms": round(elapsed_ms, 2),
        }

    def status(self) -> Dict[str, Any]:
        """Returns structured diagnostic status dictionary."""
        return {
            "stage": STAGE,
            "creator": CREATOR_NAME,
            "creator_full_name": CREATOR_FULL_NAME,
            "total_chunks": len(self.chunks),
            "unique_terms": len(self._inverted_index),
            "avg_chunk_tokens": round(self._avg_doc_len, 1),
            "vector_dimension": VECTOR_DIM,
            "index_persisted": self.index_file.exists(),
        }

    # --- Internal Tokenization & Vector Projection ---

    def _tokenize(self, text: str) -> List[str]:
        """Extracts normalized words, identifiers, and snake/camel-case components."""
        raw_tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
        results: List[str] = []
        for tok in raw_tokens:
            results.append(tok)
            # Split snake_case
            if "_" in tok:
                parts = tok.split("_")
                results.extend([p for p in parts if len(p) > 1])
        return results

    def _project_dense_vector(self, text: str) -> List[float]:
        """
        Projects arbitrary text into a normalized dense float vector of size VECTOR_DIM.
        Zero cloud or network dependencies: uses deterministic semantic feature hashing.
        """
        vec = [0.0] * VECTOR_DIM
        tokens = self._tokenize(text)
        if not tokens:
            return vec

        for idx, tok in enumerate(tokens):
            weight = 1.0 / math.sqrt(idx + 1.0)
            # Word hash
            h_word = int(hashlib.sha256(tok.encode("utf-8")).hexdigest()[:8], 16)
            dim_idx = h_word % VECTOR_DIM
            vec[dim_idx] += weight * (1.0 if (h_word & 1) else -1.0)

            # Character n-grams (3-grams) for subword semantic capture
            if len(tok) >= 3:
                for i in range(len(tok) - 2):
                    ng = tok[i : i + 3]
                    h_ng = int(hashlib.md5(ng.encode("utf-8")).hexdigest()[:6], 16)
                    d_ng = h_ng % VECTOR_DIM
                    vec[d_ng] += (weight * 0.4) * (1.0 if (h_ng & 1) else -1.0)

        # L2-normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 1e-6:
            vec = [round(v / norm, 5) for v in vec]
        return vec

    def _cosine_sim(self, v1: List[float], v2: List[float]) -> float:
        """Computes dot product between two L2-normalized vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        return max(0.0, sum(a * b for a, b in zip(v1, v2)))

    def _chunk_python_file(self, file_path: Path) -> List[CodeChunk]:
        """Extracts classes, functions, and top-level definitions from a Python source file."""
        chunks: List[CodeChunk] = []
        rel_path = str(file_path.relative_to(self.project_root)).replace("\\", "/")
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(file_path))
            lines = source.splitlines()

            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start = node.lineno
                    end = getattr(node, "end_lineno", start + 20)
                    chunk_text = "\n".join(lines[start - 1 : end])
                    ctype = "class" if isinstance(node, ast.ClassDef) else "function"

                    c_id = f"{rel_path}:{node.name}:{start}"
                    tok_cnt = len(chunk_text.split())
                    vec = self._project_dense_vector(chunk_text + " " + node.name)

                    chunks.append(
                        CodeChunk(
                            chunk_id=c_id,
                            file_path=rel_path,
                            symbol_name=node.name,
                            chunk_type=ctype,
                            start_line=start,
                            end_line=end,
                            content=chunk_text[:1200],  # cap length per chunk
                            tokens_count=tok_cnt,
                            dense_vector=vec,
                        )
                    )

            # If no classes or functions found, chunk whole file
            if not chunks and lines:
                chunk_text = "\n".join(lines[:100])
                c_id = f"{rel_path}:module:1"
                chunks.append(
                    CodeChunk(
                        chunk_id=c_id,
                        file_path=rel_path,
                        symbol_name=file_path.stem,
                        chunk_type="module",
                        start_line=1,
                        end_line=min(100, len(lines)),
                        content=chunk_text[:1200],
                        tokens_count=len(chunk_text.split()),
                        dense_vector=self._project_dense_vector(chunk_text),
                    )
                )

        except Exception:
            pass

        return chunks

    def _save_index(self) -> None:
        try:
            data = {
                "chunks": [
                    {
                        "chunk_id": c.chunk_id,
                        "file_path": c.file_path,
                        "symbol_name": c.symbol_name,
                        "chunk_type": c.chunk_type,
                        "start_line": c.start_line,
                        "end_line": c.end_line,
                        "content": c.content,
                        "tokens_count": c.tokens_count,
                        "dense_vector": c.dense_vector,
                    }
                    for c in self.chunks
                ],
                "avg_doc_len": self._avg_doc_len,
            }
            self.index_file.write_text(json.dumps(data), encoding="utf-8")
        except Exception:
            pass

    def _load_or_build_index(self) -> None:
        if self.index_file.exists():
            try:
                raw = json.loads(self.index_file.read_text(encoding="utf-8"))
                loaded_chunks: List[CodeChunk] = []
                for item in raw.get("chunks", []):
                    loaded_chunks.append(
                        CodeChunk(
                            chunk_id=item["chunk_id"],
                            file_path=item["file_path"],
                            symbol_name=item["symbol_name"],
                            chunk_type=item["chunk_type"],
                            start_line=item["start_line"],
                            end_line=item["end_line"],
                            content=item["content"],
                            tokens_count=item["tokens_count"],
                            dense_vector=item.get("dense_vector", []),
                        )
                    )
                self.chunks = loaded_chunks
                self._avg_doc_len = raw.get("avg_doc_len", 100.0)
                self._doc_lens = [c.tokens_count for c in self.chunks]

                # Rebuild inverted index and IDF in memory
                self._rebuild_memory_index()
                return
            except Exception:
                pass

        # Build fresh if not found or corrupted
        self.reindex()

    def _rebuild_memory_index(self) -> None:
        self._inverted_index.clear()
        doc_count_containing: Dict[str, int] = {}

        for c_idx, chunk in enumerate(self.chunks):
            tokens = self._tokenize(chunk.content + " " + chunk.symbol_name)
            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1

            for term, count in tf.items():
                doc_count_containing[term] = doc_count_containing.get(term, 0) + 1
                if term not in self._inverted_index:
                    self._inverted_index[term] = []
                self._inverted_index[term].append((c_idx, count))

        total_docs = len(self.chunks)
        self._idf.clear()
        for term, doc_cnt in doc_count_containing.items():
            idf = math.log(((total_docs - doc_cnt + 0.5) / (doc_cnt + 0.5)) + 1.0)
            self._idf[term] = max(0.1, idf)

    def _record_receipt(
        self,
        action_category: str,
        operation: str,
        target: str,
        verified_outcome: str,
    ) -> Optional[Dict[str, Any]]:
        ledger = self.receipt_ledger or (getattr(self.runtime, "receipt_ledger", None) if self.runtime else None)
        if ledger:
            try:
                if hasattr(ledger, "issue_receipt"):
                    return ledger.issue_receipt(action_category, operation, target, verified_outcome)
                elif hasattr(ledger, "record_receipt"):
                    return ledger.record_receipt(action_category, operation, target, verified_outcome)
            except Exception:
                pass
        return None
