r"""
backend/lucy_core/capability_security_enclave.py
Stage 157: Capability-Based Security Tokens & Hardware Enclave Sentinel
Era 16: Autonomous Microkernel, Bare-Metal HAL & Sovereign Operating System Primitives

100% offline, object-capability (ocap) security architecture, cryptographic access tokens,
privilege attenuation, and simulated hardware enclave attestation for Lucy OS:
1. Object-Capability Security Architecture (CapabilityToken):
   - Unforgeable 256-bit cryptographic capability tokens.
   - Granular permissions: CAP_READ, CAP_WRITE, CAP_EXECUTE, CAP_MAP, CAP_DELEGATE, CAP_REVOKE.
   - Per-task capability tables (C-Lists) enforcing strict least-privilege access.
2. Privilege Attenuation & Revocation Cascades:
   - Tasks with CAP_DELEGATE can mint attenuated sub-tokens with strictly subset permissions.
   - Cryptographic parent-child chaining enables instantaneous revocation cascades.
3. Hardware Enclave Sentinel (Measured Boot & Attestation):
   - Simulates secure hardware enclave memory boundary (TPM / SGX style).
   - Platform Configuration Registers (PCR 0..2) measuring kernel boot stages.
   - Attestation quote generation signed with sovereign hardware root key.
4. Cryptographic Provenance:
   - HMAC-SHA256 signature locked to Creator: Senin, Operator: Senin Ali K P.
5. Strict CP1252-Safe ASCII Presentation:
   - /cap-status / /cap-mint / /cap-verify / /enclave-attest
"""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

STAGE: int = 157
STAGE_NAME: str = "Capability-Based Security Tokens & Enclave Sentinel"
ERA: int = 16
CREATOR: str = "Senin"
OPERATOR: str = "Senin Ali K P"
HMAC_SECRET: bytes = b"senin-lucy-sovereign-enclave-secret-2026"
ENCLAVE_ROOT_KEY: bytes = b"senin-lucy-hardware-enclave-root-key-2026"

# Capability Permission Bits
CAP_READ: int = 1 << 0
CAP_WRITE: int = 1 << 1
CAP_EXECUTE: int = 2 << 1
CAP_MAP: int = 1 << 3
CAP_DELEGATE: int = 1 << 4
CAP_REVOKE: int = 1 << 5

PERM_NAMES: Dict[int, str] = {
    CAP_READ: "READ",
    CAP_WRITE: "WRITE",
    CAP_EXECUTE: "EXEC",
    CAP_MAP: "MAP",
    CAP_DELEGATE: "DELEGATE",
    CAP_REVOKE: "REVOKE",
}


@dataclasses.dataclass
class CapabilityToken:
    token_id: str
    target_resource: str
    owner_task_id: int
    permissions: int
    parent_token_id: Optional[str] = None
    attenuation_level: int = 0
    expires_at_tick: Optional[int] = None
    is_revoked: bool = False
    hmac_signature: str = ""

    def has_permission(self, perm: int) -> bool:
        if self.is_revoked:
            return False
        return bool(self.permissions & perm)

    def permission_names(self) -> List[str]:
        names = []
        for bit, name in PERM_NAMES.items():
            if self.permissions & bit:
                names.append(name)
        return names

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "target": self.target_resource,
            "owner_tid": self.owner_task_id,
            "permissions": hex(self.permissions),
            "perm_names": self.permission_names(),
            "parent_id": self.parent_token_id,
            "attenuation": self.attenuation_level,
            "is_revoked": self.is_revoked,
            "signature": self.hmac_signature[:16] + "...",
        }


class HardwareEnclaveSentinel:
    """
    Simulated Hardware Enclave & Measured Boot Engine (TPM / SGX style).
    Maintains Platform Configuration Registers (PCRs) and generates attestation quotes.
    """

    def __init__(self) -> None:
        self.pcr_registers: Dict[int, str] = {
            0: hashlib.sha256(b"PCR0_INIT_BARE_METAL_HAL").hexdigest(),
            1: hashlib.sha256(b"PCR1_INIT_MICROKERNEL_CORE").hexdigest(),
            2: hashlib.sha256(b"PCR2_INIT_SECURITY_POLICY").hexdigest(),
        }
        self.enclave_memory: Dict[str, bytes] = {}
        self._lock = threading.RLock()

    def extend_pcr(self, pcr_index: int, measurement_bytes: bytes) -> str:
        """Extends PCR register: PCR[i] = SHA256(PCR[i] || measurement)."""
        with self._lock:
            old_val = self.pcr_registers.get(pcr_index, hashlib.sha256(b"").hexdigest())
            combined = bytes.fromhex(old_val) + measurement_bytes
            new_val = hashlib.sha256(combined).hexdigest()
            self.pcr_registers[pcr_index] = new_val
            return new_val

    def generate_attestation_quote(self, nonce: bytes = b"lucy_attest_nonce") -> Dict[str, Any]:
        """Synthesizes a cryptographic attestation quote over PCR measurements."""
        with self._lock:
            pcr_dump = "".join(self.pcr_registers[i] for i in sorted(self.pcr_registers.keys()))
            quote_payload = pcr_dump.encode("utf-8") + nonce
            sig = hmac.new(ENCLAVE_ROOT_KEY, quote_payload, hashlib.sha256).hexdigest()
            return {
                "creator": CREATOR,
                "operator": OPERATOR,
                "pcr_registers": dict(self.pcr_registers),
                "nonce": nonce.hex(),
                "enclave_signature": sig,
                "timestamp": time.time(),
                "status": "ATTESTED_SECURE",
            }


class SovereignCapabilityManager:
    """
    Stage 157: Object-Capability Manager & Enclave Sentinel.
    Issues, attenuates, verifies, and revokes capability tokens for kernel resources.
    """

    def __init__(self, project_root: Optional[str | Path] = None, runtime: Any = None) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.runtime = runtime
        self._lock = threading.RLock()

        self.tokens: Dict[str, CapabilityToken] = {}
        # Task C-Lists: task_id -> set of token_ids
        self.task_clists: Dict[int, Set[str]] = {}
        # Children map: parent_token_id -> set of child_token_ids
        self.token_children: Dict[str, Set[str]] = {}

        self.enclave = HardwareEnclaveSentinel()

        # Telemetry
        self.total_tokens_minted: int = 0
        self.total_verifications: int = 0
        self.total_violations_intercepted: int = 0
        self.next_token_seq: int = 1

        # Mint root kernel capability for task 0 (system kernel)
        self.mint_root_capability(owner_task_id=0, target_resource="*")

    def _sign_token(self, token_id: str, target: str, tid: int, perms: int) -> str:
        body = f"{token_id}:{target}:{tid}:{perms}".encode("utf-8")
        return hmac.new(HMAC_SECRET, body, hashlib.sha256).hexdigest()

    def mint_root_capability(self, owner_task_id: int, target_resource: str) -> CapabilityToken:
        """Mints full-privilege root capability token."""
        with self._lock:
            all_perms = CAP_READ | CAP_WRITE | CAP_EXECUTE | CAP_MAP | CAP_DELEGATE | CAP_REVOKE
            tok_id = f"CAP-ROOT-{self.next_token_seq:04d}"
            self.next_token_seq += 1

            sig = self._sign_token(tok_id, target_resource, owner_task_id, all_perms)
            token = CapabilityToken(
                token_id=tok_id,
                target_resource=target_resource,
                owner_task_id=owner_task_id,
                permissions=all_perms,
                attenuation_level=0,
                hmac_signature=sig,
            )
            self._register_token(token)
            return token

    def delegate_capability(
        self,
        parent_token_id: str,
        new_owner_task_id: int,
        requested_permissions: int,
        target_override: Optional[str] = None,
        expires_at_tick: Optional[int] = None,
    ) -> Optional[CapabilityToken]:
        """
        Derives an attenuated capability token.
        Requested permissions must be a strict subset of parent permissions.
        Parent must have CAP_DELEGATE.
        """
        with self._lock:
            parent = self.tokens.get(parent_token_id)
            if not parent or parent.is_revoked:
                self.total_violations_intercepted += 1
                return None

            if not parent.has_permission(CAP_DELEGATE):
                self.total_violations_intercepted += 1
                return None

            # Attenuation check: requested permissions cannot exceed parent permissions
            if (requested_permissions & ~parent.permissions) != 0:
                self.total_violations_intercepted += 1
                return None  # Privilege escalation attempted

            target = target_override or parent.target_resource
            tok_id = f"CAP-SUB-{self.next_token_seq:04d}"
            self.next_token_seq += 1

            sig = self._sign_token(tok_id, target, new_owner_task_id, requested_permissions)
            child = CapabilityToken(
                token_id=tok_id,
                target_resource=target,
                owner_task_id=new_owner_task_id,
                permissions=requested_permissions,
                parent_token_id=parent_token_id,
                attenuation_level=parent.attenuation_level + 1,
                expires_at_tick=expires_at_tick,
                hmac_signature=sig,
            )

            self._register_token(child)
            if parent_token_id not in self.token_children:
                self.token_children[parent_token_id] = set()
            self.token_children[parent_token_id].add(tok_id)

            return child

    def verify_access(
        self,
        token_id: str,
        required_permission: int,
        target_resource: str,
        task_id: int,
        current_tick: int = 0,
    ) -> bool:
        """Verifies validity and authority of a capability token."""
        with self._lock:
            self.total_verifications += 1
            tok = self.tokens.get(token_id)
            if not tok or tok.is_revoked:
                self.total_violations_intercepted += 1
                return False

            if tok.owner_task_id != task_id:
                self.total_violations_intercepted += 1
                return False

            if tok.expires_at_tick is not None and current_tick >= tok.expires_at_tick:
                self.total_violations_intercepted += 1
                return False

            # Check target resource match (or wildcard '*')
            if tok.target_resource != "*" and tok.target_resource != target_resource:
                self.total_violations_intercepted += 1
                return False

            if not tok.has_permission(required_permission):
                self.total_violations_intercepted += 1
                return False

            # Cryptographic signature check
            expected_sig = self._sign_token(tok.token_id, tok.target_resource, tok.owner_task_id, tok.permissions)
            if not hmac.compare_digest(tok.hmac_signature, expected_sig):
                self.total_violations_intercepted += 1
                return False

            return True

    def revoke_capability(self, token_id: str) -> int:
        """Recursively revokes a capability token and all derived sub-tokens."""
        with self._lock:
            revoked_count = 0
            queue = [token_id]

            while queue:
                curr_id = queue.pop(0)
                tok = self.tokens.get(curr_id)
                if tok and not tok.is_revoked:
                    tok.is_revoked = True
                    revoked_count += 1
                    for child_id in self.token_children.get(curr_id, set()):
                        queue.append(child_id)

            return revoked_count

    def _register_token(self, token: CapabilityToken) -> None:
        self.tokens[token.token_id] = token
        tid = token.owner_task_id
        if tid not in self.task_clists:
            self.task_clists[tid] = set()
        self.task_clists[tid].add(token.token_id)
        self.total_tokens_minted += 1

    # -------------------------------------------------------------------------
    # ASCII Presentation
    # -------------------------------------------------------------------------
    def format_ascii_status(self) -> str:
        with self._lock:
            active_count = sum(1 for t in self.tokens.values() if not t.is_revoked)
            lines = [
                "+-----------------------------------------------------------------------------+",
                f"| LUCY STAGE 157: CAPABILITY SECURITY TOKENS & ENCLAVE SENTINEL               |",
                "+-----------------------------------------------------------------------------+",
                f"| Creator        : {CREATOR:<58} |",
                f"| Operator       : {OPERATOR:<58} |",
                f"| Active Tokens  : {active_count:<58} |",
                f"| Total Minted   : {self.total_tokens_minted:<58} |",
                f"| Verified Checks: {self.total_verifications:<58} |",
                f"| Intercepted    : {self.total_violations_intercepted:<58} |",
                f"| Enclave PCR 0  : {self.enclave.pcr_registers[0][:32]}...{'':<26} |",
                "+-----------------------------------------------------------------------------+",
                "| Token ID      | Target Resource         | Owner | Permissions       | Revoked |",
                "+---------------+-------------------------+-------+-------------------+---------+",
            ]
            for tid, t in sorted(self.tokens.items())[:12]:
                perms_str = ",".join(t.permission_names())[:17]
                lines.append(
                    f"| {t.token_id:<13} | {t.target_resource[:23]:<23} | {t.owner_task_id:<5} | "
                    f"{perms_str:<17} | {('YES' if t.is_revoked else 'NO'):<7} |"
                )
            lines.append("+---------------+-------------------------+-------+-------------------+---------+")
            return "\n".join(lines)


# Singleton
_INSTANCE: Optional[SovereignCapabilityManager] = None


def get_capability_manager(runtime: Any = None) -> SovereignCapabilityManager:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = SovereignCapabilityManager(runtime=runtime)
    return _INSTANCE
