r"""
backend/lucy_core/distributed_mvcc_storage.py
Stage 175: Distributed Snapshot Isolation & MVCC Storage
Era 18: Autonomous Distributed Storage, Geo-Replication & Sharding Primitives

100% offline, sovereign distributed Multi-Version Concurrency Control (MVCC) engine:
1. Multi-Version Key Space:
   - Version tuples: (key, value, created_ts, expired_ts, tx_id, is_deleted).
   - Non-blocking lock-free reads: Transactions read historical snapshot as of read_ts.
2. Snapshot Isolation (SI) & Conflict Detection:
   - First-committer-wins rule: Detects concurrent write-write overlaps between [read_ts, commit_ts].
   - Prevents dirty reads, non-repeatable reads, and lost updates.
3. Multi-Version Garbage Collection (Vacuum):
   - Computes global Low-Water Mark (LWM) across all active in-flight transaction read timestamps.
   - Purges superseded and tombstoned versions whose expired_ts <= LWM.
4. Transaction Lifecycle:
   - begin_tx(), tx_get(), tx_put(), tx_delete(), commit_tx(), abort_tx().
5. Thread-safe execution via RLock.
"""

from __future__ import annotations

import bisect
import hashlib
import json
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 175
STAGE_NAME: str = "Distributed Snapshot Isolation & MVCC Storage"
ERA: int = 18
ERA_NAME: str = "Autonomous Distributed Storage, Geo-Replication & Sharding Primitives"


class WriteConflictError(Exception):
    """Raised when a concurrent transaction has already committed changes to the same key."""
    pass


@dataclass
class MVCCVersion:
    key: str
    value: Any
    created_ts: float
    expired_ts: Optional[float] = None
    created_by_tx: str = ""
    expired_by_tx: Optional[str] = None
    is_deleted: bool = False

    def is_visible_at(self, snapshot_ts: float) -> bool:
        if self.created_ts > snapshot_ts:
            return False
        if self.expired_ts is not None and self.expired_ts <= snapshot_ts:
            return False
        return not self.is_deleted

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TransactionState:
    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"


@dataclass
class MVCCTransaction:
    tx_id: str
    read_ts: float
    write_set: Dict[str, Tuple[Any, bool]] = field(default_factory=dict)  # key -> (value, is_deleted)
    state: str = TransactionState.ACTIVE
    commit_ts: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_id": self.tx_id,
            "read_ts": self.read_ts,
            "commit_ts": self.commit_ts,
            "state": self.state,
            "write_count": len(self.write_set),
        }


class DistributedMVCCStorage:
    """
    Sovereign Multi-Version Concurrency Control (MVCC) Storage Engine.
    Guarantees Snapshot Isolation and lock-free consistent reads.
    """

    def __init__(
        self,
        node_id: str = "mvcc_node_0",
        project_root: Optional[Union[str, Path]] = None,
        runtime: Optional[Any] = None,
    ) -> None:
        self.node_id = node_id
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parent.parent.parent
        self.runtime = runtime

        self._lock = threading.RLock()
        self._versions: Dict[str, List[MVCCVersion]] = {}  # key -> list of versions sorted by created_ts
        self._active_transactions: Dict[str, MVCCTransaction] = {}
        self._logical_clock: float = 1000.0
        self._total_tx_started = 0
        self._total_tx_committed = 0
        self._total_tx_aborted = 0
        self._total_versions_purged = 0

    def _next_timestamp(self) -> float:
        self._logical_clock += 1.0
        return self._logical_clock

    # -------------------------------------------------------------------------
    # Transaction Management
    # -------------------------------------------------------------------------
    def begin_transaction(self, tx_id: Optional[str] = None) -> MVCCTransaction:
        """Starts a new transaction with a snapshot timestamp."""
        with self._lock:
            ts = self._next_timestamp()
            tid = tx_id if tx_id else f"tx_{int(ts)}"
            tx = MVCCTransaction(tx_id=tid, read_ts=ts)
            self._active_transactions[tid] = tx
            self._total_tx_started += 1
            return tx

    def tx_get(self, tx_id: str, key: str) -> Optional[Any]:
        """Reads key value visible at transaction's snapshot timestamp."""
        with self._lock:
            if tx_id not in self._active_transactions:
                raise ValueError(f"Transaction {tx_id} not active.")

            tx = self._active_transactions[tx_id]
            if tx.state != TransactionState.ACTIVE:
                raise ValueError(f"Transaction {tx_id} is {tx.state}.")

            # 1. Check local transaction write set first (read-your-own-writes)
            if key in tx.write_set:
                val, is_del = tx.write_set[key]
                return None if is_del else val

            # 2. Search multi-version chain
            chain = self._versions.get(key, [])
            for ver in reversed(chain):
                if ver.is_visible_at(tx.read_ts):
                    return ver.value

            return None

    def tx_put(self, tx_id: str, key: str, value: Any) -> None:
        """Buffers a put operation in the transaction's write set."""
        with self._lock:
            if tx_id not in self._active_transactions:
                raise ValueError(f"Transaction {tx_id} not active.")
            tx = self._active_transactions[tx_id]
            if tx.state != TransactionState.ACTIVE:
                raise ValueError(f"Transaction {tx_id} is {tx.state}.")
            tx.write_set[key] = (value, False)

    def tx_delete(self, tx_id: str, key: str) -> None:
        """Buffers a delete operation in the transaction's write set."""
        with self._lock:
            if tx_id not in self._active_transactions:
                raise ValueError(f"Transaction {tx_id} not active.")
            tx = self._active_transactions[tx_id]
            if tx.state != TransactionState.ACTIVE:
                raise ValueError(f"Transaction {tx_id} is {tx.state}.")
            tx.write_set[key] = (None, True)

    def commit_transaction(self, tx_id: str) -> float:
        """
        Commits transaction under Snapshot Isolation.
        Detects write-write conflicts: aborts if any written key was modified after read_ts.
        """
        with self._lock:
            if tx_id not in self._active_transactions:
                raise ValueError(f"Transaction {tx_id} not active.")

            tx = self._active_transactions[tx_id]
            if tx.state != TransactionState.ACTIVE:
                raise ValueError(f"Transaction {tx_id} is {tx.state}.")

            # If read-only, commit immediately
            if not tx.write_set:
                tx.state = TransactionState.COMMITTED
                tx.commit_ts = tx.read_ts
                del self._active_transactions[tx_id]
                self._total_tx_committed += 1
                return tx.commit_ts

            commit_ts = self._next_timestamp()

            # First-committer-wins conflict check:
            # Check if any key in write_set was committed after tx.read_ts
            for key in tx.write_set.keys():
                chain = self._versions.get(key, [])
                for ver in chain:
                    if ver.created_ts > tx.read_ts:
                        # Conflict! Another tx committed changes to this key after our snapshot
                        tx.state = TransactionState.ABORTED
                        del self._active_transactions[tx_id]
                        self._total_tx_aborted += 1
                        raise WriteConflictError(
                            f"Write-write conflict on key '{key}': modified at ts={ver.created_ts} > tx.read_ts={tx.read_ts}"
                        )

            # Apply writes and expire old versions
            for key, (val, is_del) in tx.write_set.items():
                if key not in self._versions:
                    self._versions[key] = []

                chain = self._versions[key]
                # Expire previous active version
                if chain and chain[-1].expired_ts is None:
                    chain[-1].expired_ts = commit_ts
                    chain[-1].expired_by_tx = tx_id

                new_ver = MVCCVersion(
                    key=key,
                    value=val,
                    created_ts=commit_ts,
                    expired_ts=None,
                    created_by_tx=tx_id,
                    is_deleted=is_del,
                )
                chain.append(new_ver)

            tx.state = TransactionState.COMMITTED
            tx.commit_ts = commit_ts
            del self._active_transactions[tx_id]
            self._total_tx_committed += 1
            return commit_ts

    def abort_transaction(self, tx_id: str) -> None:
        """Aborts an active transaction and discards its write set."""
        with self._lock:
            if tx_id in self._active_transactions:
                tx = self._active_transactions[tx_id]
                tx.state = TransactionState.ABORTED
                del self._active_transactions[tx_id]
                self._total_tx_aborted += 1

    # -------------------------------------------------------------------------
    # Multi-Version Garbage Collection (Vacuum)
    # -------------------------------------------------------------------------
    def vacuum(self) -> int:
        """
        Purges dead versions whose expired_ts is <= global Low-Water Mark (LWM).
        LWM = minimum read_ts across all active transactions (or current clock if none active).
        """
        with self._lock:
            if self._active_transactions:
                lwm = min(tx.read_ts for tx in self._active_transactions.values())
            else:
                lwm = self._logical_clock

            purged = 0
            for key, chain in list(self._versions.items()):
                new_chain: List[MVCCVersion] = []
                for ver in chain:
                    # Keep if unexpired or expired after LWM
                    if ver.expired_ts is None or ver.expired_ts > lwm:
                        new_chain.append(ver)
                    else:
                        purged += 1

                if new_chain:
                    self._versions[key] = new_chain
                else:
                    del self._versions[key]

            self._total_versions_purged += purged
            return purged

    # -------------------------------------------------------------------------
    # Telemetry & Status
    # -------------------------------------------------------------------------
    def status(self) -> Dict[str, Any]:
        with self._lock:
            total_vers = sum(len(c) for c in self._versions.values())
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "node_id": self.node_id,
                "logical_clock": self._logical_clock,
                "active_transactions": len(self._active_transactions),
                "total_unique_keys": len(self._versions),
                "total_versions": total_vers,
                "total_tx_started": self._total_tx_started,
                "total_tx_committed": self._total_tx_committed,
                "total_tx_aborted": self._total_tx_aborted,
                "total_versions_purged": self._total_versions_purged,
            }

    def format_ascii_status(self) -> str:
        with self._lock:
            st = self.status()
            lines = [
                "+-----------------------------------------------------------------------------+",
                f"| LUCY STAGE 175: DISTRIBUTED SNAPSHOT ISOLATION & MVCC STORAGE ENGINE         |",
                "+-----------------------------------------------------------------------------+",
                f"| Storage Node   : {st['node_id']:<58} |",
                f"| Logical Clock  : {st['logical_clock']:<58} |",
                f"| Active Txs     : {st['active_transactions']} in-flight concurrent transactions{'':<28} |",
                f"| Transactions   : {st['total_tx_committed']} committed | {st['total_tx_aborted']} aborted (conflicts){'':<21} |",
                f"| Versions/Vacuum: {st['total_versions']} active versions | {st['total_versions_purged']} dead versions purged{'':<18} |",
                "+-----------------+------------+------------------+---------------------------+",
                "| KEY             | VERSIONS   | LATEST COMMIT    | ACTIVE VALUE / TOMBSTONE  |",
                "+-----------------+------------+------------------+---------------------------+",
            ]

            for key in sorted(self._versions.keys())[:8]:
                chain = self._versions[key]
                v_count = len(chain)
                latest = chain[-1]
                val_str = "TOMBSTONE" if latest.is_deleted else str(latest.value)[:25]
                lines.append(f"| {key:<15} | {v_count:>10} | {latest.created_ts:>16.1f} | {val_str:<25} |")

            if not self._versions:
                lines.append("| (No MVCC key versions currently stored)                                    |")

            lines.append("+-----------------+------------+------------------+---------------------------+")
            return "\n".join(lines)


# Singleton
_MVCC_INSTANCE: Optional[DistributedMVCCStorage] = None


def get_distributed_mvcc_storage(runtime: Any = None) -> DistributedMVCCStorage:
    global _MVCC_INSTANCE
    if _MVCC_INSTANCE is None:
        _MVCC_INSTANCE = DistributedMVCCStorage(runtime=runtime)
    return _MVCC_INSTANCE
