r"""
backend/lucy_core/distributed_hash_join.py
Stage 184: Distributed Hash Join & Broadcast Shuffle Fabric
Era 19: Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine

100% offline, sovereign distributed join execution fabric:
1. Distributed Partitioned Hash Join (Shuffle Hash Join):
   - Consistent hashing over join keys (hash(k) % num_partitions) for both left (probe) and right (build) relations.
   - Network shuffle simulation measuring byte transfer volume and network partition skew.
2. Broadcast Hash Join:
   - Dynamic threshold evaluation: broadcasts small build table to all cluster worker nodes.
   - Probe relation streams locally with zero network redistribution.
3. Asymmetric Skew Sentinel & Key Salting:
   - Online detection of high-frequency join keys exceeding skew threshold.
   - Automatic key-salting mitigation: salts heavy keys across sub-partitions while replicating build rows.
4. Join Semantics:
   - Full support for INNER, LEFT_OUTER, RIGHT_OUTER, FULL_OUTER, SEMI, and ANTI joins.
5. Thread-safe execution fabric and CP1252-safe ASCII table formatting.
"""

from __future__ import annotations

import collections
import hashlib
import json
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 184
STAGE_NAME: str = "Distributed Hash Join & Broadcast Shuffle Fabric"
ERA: int = 19
ERA_NAME: str = "Distributed Query Planning, Columnar Vector Storage & OLAP Analytics Engine"

DEFAULT_NUM_PARTITIONS: int = 8
DEFAULT_BROADCAST_ROW_THRESHOLD: int = 500
DEFAULT_SKEW_RATIO_THRESHOLD: float = 0.25


# -------------------------------------------------------------------------
# Telemetry & Configuration
# -------------------------------------------------------------------------

class JoinType:
    INNER = "INNER"
    LEFT_OUTER = "LEFT_OUTER"
    RIGHT_OUTER = "RIGHT_OUTER"
    FULL_OUTER = "FULL_OUTER"
    SEMI = "SEMI"
    ANTI = "ANTI"


class JoinStrategy:
    BROADCAST = "BROADCAST"
    SHUFFLE_HASH = "SHUFFLE_HASH"
    SKEW_MITIGATED_SHUFFLE = "SKEW_MITIGATED_SHUFFLE"


@dataclass
class JoinTelemetry:
    strategy_used: str = JoinStrategy.SHUFFLE_HASH
    join_type: str = JoinType.INNER
    left_rows: int = 0
    right_rows: int = 0
    output_rows: int = 0
    network_bytes_shuffled: int = 0
    num_partitions: int = DEFAULT_NUM_PARTITIONS
    skewed_keys_detected: List[str] = field(default_factory=list)
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# -------------------------------------------------------------------------
# Partition Worker Node
# -------------------------------------------------------------------------

class PartitionWorker:
    """Simulates an individual cluster node performing local in-memory hash join."""

    def __init__(self, partition_id: int) -> None:
        self.partition_id = partition_id
        self.build_hash_table: Dict[Any, List[Dict[str, Any]]] = collections.defaultdict(list)
        self.probe_buffer: List[Dict[str, Any]] = []

    def clear(self) -> None:
        self.build_hash_table.clear()
        self.probe_buffer.clear()

    def add_build_row(self, key: Any, row: Dict[str, Any]) -> None:
        self.build_hash_table[key].append(row)

    def add_probe_row(self, row: Dict[str, Any]) -> None:
        self.probe_buffer.append(row)

    def execute_local_join(self, left_key: str, right_key: str,
                           join_type: str = JoinType.INNER) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        matched_build_keys: Set[Any] = set()

        for p_row in self.probe_buffer:
            k = p_row.get(left_key)
            matches = self.build_hash_table.get(k, [])

            if join_type == JoinType.INNER:
                for b_row in matches:
                    merged = dict(p_row)
                    for bk, bv in b_row.items():
                        if bk not in merged or bk == right_key:
                            merged[bk] = bv
                        else:
                            merged[f"right_{bk}"] = bv
                    results.append(merged)

            elif join_type == JoinType.LEFT_OUTER:
                if matches:
                    for b_row in matches:
                        merged = dict(p_row)
                        for bk, bv in b_row.items():
                            if bk not in merged or bk == right_key:
                                merged[bk] = bv
                            else:
                                merged[f"right_{bk}"] = bv
                        results.append(merged)
                else:
                    results.append(dict(p_row))

            elif join_type == JoinType.SEMI:
                if matches:
                    results.append(dict(p_row))

            elif join_type == JoinType.ANTI:
                if not matches:
                    results.append(dict(p_row))

            elif join_type == JoinType.RIGHT_OUTER or join_type == JoinType.FULL_OUTER:
                if matches:
                    matched_build_keys.add(k)
                    for b_row in matches:
                        merged = dict(p_row)
                        for bk, bv in b_row.items():
                            if bk not in merged or bk == right_key:
                                merged[bk] = bv
                            else:
                                merged[f"right_{bk}"] = bv
                        results.append(merged)
                elif join_type == JoinType.FULL_OUTER:
                    results.append(dict(p_row))

        # Handle unmatched build rows for RIGHT_OUTER and FULL_OUTER
        if join_type in (JoinType.RIGHT_OUTER, JoinType.FULL_OUTER):
            for bk, b_rows in self.build_hash_table.items():
                if bk not in matched_build_keys:
                    for b_row in b_rows:
                        results.append(dict(b_row))

        return results


# -------------------------------------------------------------------------
# Distributed Hash Join Fabric
# -------------------------------------------------------------------------

class DistributedHashJoinFabric:
    """
    Sovereign Distributed Join Fabric:
    - Automatically selects between Broadcast Hash Join and Shuffle Hash Join.
    - Monitors partition data skew and handles key-salting mitigations.
    - Tracks network shuffle byte volumes and execution metrics.
    """

    def __init__(self, num_partitions: int = DEFAULT_NUM_PARTITIONS,
                 broadcast_threshold: int = DEFAULT_BROADCAST_ROW_THRESHOLD,
                 skew_threshold: float = DEFAULT_SKEW_RATIO_THRESHOLD) -> None:
        self.num_partitions = max(1, num_partitions)
        self.broadcast_threshold = broadcast_threshold
        self.skew_threshold = skew_threshold
        self.workers = [PartitionWorker(i) for i in range(self.num_partitions)]
        self._lock = threading.RLock()
        self._joins_executed: int = 0
        self._total_shuffled_bytes: int = 0
        self._last_telemetry: Optional[JoinTelemetry] = None

    def _hash_key(self, key_val: Any) -> int:
        s = str(key_val).encode("utf-8")
        return int(hashlib.md5(s).hexdigest()[:8], 16) % self.num_partitions

    def _estimate_row_bytes(self, row: Dict[str, Any]) -> int:
        return sum(len(str(k)) + len(str(v)) for k, v in row.items()) + 16

    def detect_skew(self, rows: List[Dict[str, Any]], key_col: str) -> List[Tuple[Any, int, float]]:
        """Identifies keys whose frequency exceeds skew_threshold ratio."""
        if not rows:
            return []
        freqs = collections.Counter(r.get(key_col) for r in rows)
        n = len(rows)
        skewed = []
        for k, count in freqs.items():
            ratio = count / n
            if ratio >= self.skew_threshold and count > 10:
                skewed.append((k, count, ratio))
        return skewed

    def execute_join(self, left_rows: List[Dict[str, Any]],
                     right_rows: List[Dict[str, Any]],
                     left_key: str,
                     right_key: str,
                     join_type: str = JoinType.INNER,
                     force_strategy: Optional[str] = None) -> Tuple[List[Dict[str, Any]], JoinTelemetry]:
        """
        Executes distributed join across simulated partition workers.
        left_rows: probe relation (or preserved outer)
        right_rows: build relation (or broadcast side)
        """
        with self._lock:
            t0 = time.perf_counter()
            self._joins_executed += 1

            for w in self.workers:
                w.clear()

            # 1. Determine Join Strategy
            strategy = force_strategy
            if strategy is None:
                if len(right_rows) <= self.broadcast_threshold:
                    strategy = JoinStrategy.BROADCAST
                else:
                    skew_probe = self.detect_skew(left_rows, left_key)
                    strategy = JoinStrategy.SKEW_MITIGATED_SHUFFLE if skew_probe else JoinStrategy.SHUFFLE_HASH

            shuffled_bytes = 0
            skewed_keys: List[str] = []

            # 2. Execution based on strategy
            if strategy == JoinStrategy.BROADCAST:
                # Replicate right_rows to every worker build hash table
                bcast_bytes_per_row = [self._estimate_row_bytes(r) for r in right_rows]
                total_bcast_row_bytes = sum(bcast_bytes_per_row)
                shuffled_bytes += total_bcast_row_bytes * self.num_partitions

                for w in self.workers:
                    for r in right_rows:
                        w.add_build_row(r.get(right_key), r)

                # Partition left_rows locally round-robin / partition hash
                for r in left_rows:
                    pid = self._hash_key(r.get(left_key))
                    self.workers[pid].add_probe_row(r)

            elif strategy == JoinStrategy.SKEW_MITIGATED_SHUFFLE:
                skew_info = self.detect_skew(left_rows, left_key)
                skewed_key_set = {k for k, _, _ in skew_info}
                skewed_keys = [str(k) for k in skewed_key_set]

                # Salt skewed keys in left_rows across all workers, replicate right_rows for skewed keys
                salt_factor = self.num_partitions

                # Shuffle right (build) rows
                for r in right_rows:
                    rk = r.get(right_key)
                    r_bytes = self._estimate_row_bytes(r)
                    if rk in skewed_key_set:
                        # Replicate build row to all partitions
                        for pid in range(self.num_partitions):
                            self.workers[pid].add_build_row(rk, r)
                            shuffled_bytes += r_bytes
                    else:
                        pid = self._hash_key(rk)
                        self.workers[pid].add_build_row(rk, r)
                        shuffled_bytes += r_bytes

                # Shuffle left (probe) rows
                for idx, r in enumerate(left_rows):
                    lk = r.get(left_key)
                    r_bytes = self._estimate_row_bytes(r)
                    if lk in skewed_key_set:
                        # Round-robin spread skewed probe rows across partitions
                        pid = idx % self.num_partitions
                        self.workers[pid].add_probe_row(r)
                        shuffled_bytes += r_bytes
                    else:
                        pid = self._hash_key(lk)
                        self.workers[pid].add_probe_row(r)
                        shuffled_bytes += r_bytes

            else:  # Standard SHUFFLE_HASH
                # Shuffle right (build) rows
                for r in right_rows:
                    pid = self._hash_key(r.get(right_key))
                    self.workers[pid].add_build_row(r.get(right_key), r)
                    shuffled_bytes += self._estimate_row_bytes(r)

                # Shuffle left (probe) rows
                for r in left_rows:
                    pid = self._hash_key(r.get(left_key))
                    self.workers[pid].add_probe_row(r)
                    shuffled_bytes += self._estimate_row_bytes(r)

            # 3. Parallel local worker join execution
            all_results: List[Dict[str, Any]] = []
            for w in self.workers:
                local_res = w.execute_local_join(left_key, right_key, join_type)
                all_results.extend(local_res)

            elapsed = (time.perf_counter() - t0) * 1000.0  # ms
            self._total_shuffled_bytes += shuffled_bytes

            telemetry = JoinTelemetry(
                strategy_used=strategy,
                join_type=join_type,
                left_rows=len(left_rows),
                right_rows=len(right_rows),
                output_rows=len(all_results),
                network_bytes_shuffled=shuffled_bytes,
                num_partitions=self.num_partitions,
                skewed_keys_detected=skewed_keys,
                elapsed_ms=round(elapsed, 3),
            )
            self._last_telemetry = telemetry
            return all_results, telemetry

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "num_partitions": self.num_partitions,
                "broadcast_threshold": self.broadcast_threshold,
                "skew_threshold": self.skew_threshold,
                "joins_executed": self._joins_executed,
                "total_shuffled_bytes": self._total_shuffled_bytes,
                "last_telemetry": self._last_telemetry.to_dict() if self._last_telemetry else None,
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = (
            "+-------------------------------------------------------------------------+\n"
            "|      STAGE 184: DISTRIBUTED HASH JOIN & BROADCAST SHUFFLE FABRIC        |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        body = (
            f"| Cluster Partitions    : {s['num_partitions']:<48} |\n"
            f"| Broadcast Threshold   : {s['broadcast_threshold']} rows{' ':<38} |\n"
            f"| Skew Threshold Ratio  : {s['skew_threshold'] * 100:.1f}%{' ':<42} |\n"
            f"| Total Joins Executed  : {s['joins_executed']:<48} |\n"
            f"| Shuffled Network Bytes: {s['total_shuffled_bytes']:<48} |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        last_section = ""
        if s["last_telemetry"]:
            lt = s["last_telemetry"]
            last_section = (
                "| LAST JOIN TELEMETRY                                                     |\n"
                f"| Strategy: {lt['strategy_used']:<15} | Type: {lt['join_type']:<15} | Rows Out: {lt['output_rows']:<9} |\n"
                f"| Left Rows: {lt['left_rows']:<14} | Right Rows: {lt['right_rows']:<12} | Latency: {lt['elapsed_ms']}ms{' ':<8} |\n"
                f"| Network Shuffled Bytes: {lt['network_bytes_shuffled']:<48} |\n"
                "+-------------------------------------------------------------------------+"
            )
        else:
            last_section = "+-------------------------------------------------------------------------+"
        return header + body + last_section
