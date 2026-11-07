"""
backend/lucy_core/atomic_patcher.py
Stage 78: Multi-File Refactor & Atomic Patch Orchestrator

Provides all-or-nothing atomic file refactoring across multiple files with
syntax pre-validation, journaled rollback safety, and transactional recovery
for Lucy's sovereign terminal runtime.
"""

from __future__ import annotations

import ast
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

STAGE: int = 78


@dataclass
class FilePatchOperation:
    file_path: str
    original_content: Optional[str]
    new_content: Optional[str]
    is_creation: bool = False
    is_deletion: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FilePatchOperation:
        return cls(
            file_path=data.get("file_path", ""),
            original_content=data.get("original_content"),
            new_content=data.get("new_content"),
            is_creation=data.get("is_creation", False),
            is_deletion=data.get("is_deletion", False),
        )


@dataclass
class PatchTransaction:
    tx_id: str
    description: str
    timestamp: str
    status: str  # "PENDING", "COMMITTED", "ROLLED_BACK", "FAILED"
    operations: List[FilePatchOperation] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_id": self.tx_id,
            "description": self.description,
            "timestamp": self.timestamp,
            "status": self.status,
            "error_message": self.error_message,
            "operations": [op.to_dict() for op in self.operations],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PatchTransaction:
        ops = [FilePatchOperation.from_dict(o) for o in data.get("operations", [])]
        return cls(
            tx_id=data.get("tx_id", ""),
            description=data.get("description", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            status=data.get("status", "PENDING"),
            operations=ops,
            error_message=data.get("error_message"),
        )


class AtomicPatchOrchestrator:
    """
    Coordinates multi-file transactions, AST syntax pre-validation,
    all-or-nothing execution, and instant rollback on error.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        journal_file: Optional[Path] = None,
        receipt_ledger: Optional[Any] = None,
    ) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent
        self.journal_file = journal_file or (self.project_root / "data" / "lucy" / "patch_journal.json")
        self.receipt_ledger = receipt_ledger

        self.journal_file.parent.mkdir(parents=True, exist_ok=True)
        self.transactions: Dict[str, PatchTransaction] = {}
        self.active_tx: Optional[PatchTransaction] = None
        self._load_journal()

    def _load_journal(self) -> None:
        if not self.journal_file.exists():
            return
        try:
            with open(self.journal_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for item in raw.get("transactions", []):
                tx = PatchTransaction.from_dict(item)
                self.transactions[tx.tx_id] = tx
        except Exception:
            self.transactions = {}

    def _save_journal(self) -> None:
        try:
            data = {
                "version": STAGE,
                "updated_at": datetime.now().isoformat(),
                "transactions": [tx.to_dict() for tx in self.transactions.values()],
            }
            with open(self.journal_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def begin_transaction(self, description: str = "") -> PatchTransaction:
        """Starts a new atomic patch transaction."""
        tx_id = f"tx_{uuid.uuid4().hex[:8]}"
        tx = PatchTransaction(
            tx_id=tx_id,
            description=description.strip() or f"Refactor transaction {tx_id}",
            timestamp=datetime.now().isoformat(),
            status="PENDING",
            operations=[],
        )
        self.transactions[tx_id] = tx
        self.active_tx = tx
        self._save_journal()
        return tx

    def stage_file_patch(
        self,
        file_path: Path | str,
        new_content: str,
        tx_id: Optional[str] = None,
    ) -> bool:
        """
        Stages a modified or newly created file into the transaction.
        """
        tx = self.transactions.get(tx_id) if tx_id else self.active_tx
        if not tx or tx.status != "PENDING":
            return False

        path_obj = Path(file_path)
        if not path_obj.is_absolute():
            path_obj = self.project_root / path_obj

        rel_path = str(path_obj.relative_to(self.project_root))
        original_content = None
        is_creation = not path_obj.exists()

        if path_obj.exists():
            try:
                original_content = path_obj.read_text(encoding="utf-8", errors="replace")
            except Exception:
                return False

        # Replace existing op for this file if already staged
        tx.operations = [op for op in tx.operations if op.file_path != rel_path]

        op = FilePatchOperation(
            file_path=rel_path,
            original_content=original_content,
            new_content=new_content,
            is_creation=is_creation,
            is_deletion=False,
        )
        tx.operations.append(op)
        self._save_journal()
        return True

    def stage_file_delete(
        self,
        file_path: Path | str,
        tx_id: Optional[str] = None,
    ) -> bool:
        """
        Stages a file deletion into the transaction.
        """
        tx = self.transactions.get(tx_id) if tx_id else self.active_tx
        if not tx or tx.status != "PENDING":
            return False

        path_obj = Path(file_path)
        if not path_obj.is_absolute():
            path_obj = self.project_root / path_obj

        if not path_obj.exists():
            return False

        rel_path = str(path_obj.relative_to(self.project_root))
        original_content = path_obj.read_text(encoding="utf-8", errors="replace")

        tx.operations = [op for op in tx.operations if op.file_path != rel_path]
        op = FilePatchOperation(
            file_path=rel_path,
            original_content=original_content,
            new_content=None,
            is_creation=False,
            is_deletion=True,
        )
        tx.operations.append(op)
        self._save_journal()
        return True

    def validate_transaction(self, tx_id: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Pre-validates that all python code in the transaction has valid AST syntax.
        """
        tx = self.transactions.get(tx_id) if tx_id else self.active_tx
        if not tx:
            return False, ["Transaction not found."]

        errors: List[str] = []
        for op in tx.operations:
            if op.is_deletion or op.new_content is None:
                continue
            if op.file_path.endswith(".py"):
                try:
                    ast.parse(op.new_content, filename=op.file_path)
                except SyntaxError as e:
                    errors.append(f"{op.file_path}:{e.lineno}:{e.offset}: SyntaxError: {e.msg}")
                except Exception as e:
                    errors.append(f"{op.file_path}: ValidationError: {str(e)}")

        return len(errors) == 0, errors

    def commit_transaction(
        self,
        tx_id: Optional[str] = None,
        auto_rollback_on_failure: bool = True,
    ) -> Tuple[bool, str]:
        """
        Applies all staged file changes. If syntax checks or write operations fail,
        instantly rolls back all files to their pristine states.
        """
        tx = self.transactions.get(tx_id) if tx_id else self.active_tx
        if not tx:
            return False, "No active transaction to commit."
        if tx.status != "PENDING":
            return False, f"Transaction status is {tx.status}, cannot commit."

        # 1. Pre-validation
        valid, errors = self.validate_transaction(tx.tx_id)
        if not valid:
            tx.status = "FAILED"
            tx.error_message = "; ".join(errors)
            self._save_journal()
            return False, f"Pre-commit validation failed: {tx.error_message}"

        written_ops: List[FilePatchOperation] = []
        try:
            for op in tx.operations:
                full_path = self.project_root / op.file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                if op.is_deletion:
                    if full_path.exists():
                        full_path.unlink()
                else:
                    full_path.write_text(op.new_content or "", encoding="utf-8")
                written_ops.append(op)

            # Post-write AST double check on disk
            for op in written_ops:
                if not op.is_deletion and op.file_path.endswith(".py"):
                    full_path = self.project_root / op.file_path
                    code_disk = full_path.read_text(encoding="utf-8")
                    ast.parse(code_disk, filename=str(full_path))

            tx.status = "COMMITTED"
            tx.error_message = None
            if self.active_tx and self.active_tx.tx_id == tx.tx_id:
                self.active_tx = None
            self._save_journal()

            if self.receipt_ledger is not None:
                try:
                    self.receipt_ledger.issue_receipt(
                        action_category="atomic_patch",
                        operation="commit_transaction",
                        target=tx.tx_id,
                        verified_outcome=f"Committed {len(tx.operations)} files atomically",
                    )
                except Exception:
                    pass

            return True, f"Committed transaction {tx.tx_id} successfully ({len(tx.operations)} files modified)."

        except Exception as exc:
            # Atomic rollback on any disk or syntax failure
            tx.status = "FAILED"
            tx.error_message = f"Write/Validation failure: {str(exc)}"
            if auto_rollback_on_failure:
                self._rollback_operations(written_ops)
                tx.status = "ROLLED_BACK"
            self._save_journal()
            return False, f"Transaction {tx.tx_id} failed and was automatically rolled back: {exc}"

    def rollback_transaction(self, tx_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Manually rolls back a committed or failed transaction.
        """
        tx = self.transactions.get(tx_id) if tx_id else self._get_latest_committed_tx()
        if not tx:
            return False, "No transaction available to rollback."

        if tx.status not in ("COMMITTED", "FAILED", "PENDING"):
            return False, f"Cannot rollback transaction in status {tx.status}."

        self._rollback_operations(tx.operations)
        tx.status = "ROLLED_BACK"
        if self.active_tx and self.active_tx.tx_id == tx.tx_id:
            self.active_tx = None
        self._save_journal()

        if self.receipt_ledger is not None:
            try:
                self.receipt_ledger.issue_receipt(
                    action_category="atomic_patch",
                    operation="rollback_transaction",
                    target=tx.tx_id,
                    verified_outcome=f"Rolled back {len(tx.operations)} files",
                )
            except Exception:
                pass

        return True, f"Rolled back transaction {tx.tx_id} successfully."

    def _rollback_operations(self, ops: List[FilePatchOperation]) -> None:
        for op in reversed(ops):
            full_path = self.project_root / op.file_path
            try:
                if op.is_creation:
                    if full_path.exists():
                        full_path.unlink()
                elif op.original_content is not None:
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(op.original_content, encoding="utf-8")
            except Exception:
                pass

    def _get_latest_committed_tx(self) -> Optional[PatchTransaction]:
        committed = [tx for tx in self.transactions.values() if tx.status == "COMMITTED"]
        if not committed:
            return None
        return sorted(committed, key=lambda t: t.timestamp, reverse=True)[0]

    def list_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        sorted_txs = sorted(self.transactions.values(), key=lambda t: t.timestamp, reverse=True)
        return [tx.to_dict() for tx in sorted_txs[:limit]]

    def format_terminal_summary(self) -> str:
        lines = []
        lines.append("+----------------------------------------------------------------------+")
        lines.append("| ATOMIC PATCH ORCHESTRATOR (STAGE 78)                                 |")
        lines.append("+----------------------------------------------------------------------+")
        active_id = self.active_tx.tx_id if self.active_tx else "None"
        lines.append(f"| Active Transaction: {active_id:<20} | Total Recorded: {len(self.transactions):<18} |")
        lines.append("+----------------------------------------------------------------------+")

        if not self.transactions:
            lines.append("|  (No patch transactions recorded yet. Use /patch-plan to start.)    |")
            lines.append("+----------------------------------------------------------------------+")
        else:
            lines.append(f"| {'TX ID':<12} | {'STATUS':<11} | {'FILES':<5} | {'DESCRIPTION':<30} |")
            lines.append("+--------------+-------------+-------+--------------------------------+")
            for tx in sorted(self.transactions.values(), key=lambda t: t.timestamp, reverse=True)[:8]:
                status_str = tx.status[:11]
                files_count = str(len(tx.operations))[:5]
                desc_str = tx.description[:30]
                lines.append(f"| {tx.tx_id:<12} | {status_str:<11} | {files_count:<5} | {desc_str:<30} |")
            lines.append("+--------------+-------------+-------+--------------------------------+")

        return "\n".join(lines)
