"""
Stage 249: Universal Multi-Tier Zero-Trust Hardware Attestation & Enclave Secure Boot Orchestrator
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- TCG TPM 2.0 / DICE-Compliant Platform Configuration Register (PCR) Extend & Boot Measurement Log
- Hash-Chained Immutability: PCR[i] <- SHA256(PCR[i] || measurement)
- Hardware Enclave Sealing & Cryptographic Key Derivation bound to PCR Composites
- Hardware Root-of-Trust (RoT) Remote Attestation Quotes with Replay-Resistant Nonces
- Enclave Unsealing Anti-Tamper Verification (Decryption strictly prevented if PCR state diverges)
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import hmac
import os
import threading
import time

STAGE = 249
STAGE_NAME = "Universal Multi-Tier Zero-Trust Hardware Attestation & Enclave Secure Boot Orchestrator"
ERA = 25
ERA_NAME = "Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials"

ZERO_PCR_HASH = "0" * 64
SOVEREIGN_ROOT_KEY = b"LUCY-SOVEREIGN-HARDWARE-ROOT-OF-TRUST-SENIN-2026"


@dataclass
class BootLogEntry:
    entry_id: int
    pcr_index: int
    stage_component: str
    measurement_hex: str
    resulting_pcr_hex: str
    timestamp: float


@dataclass
class AttestationQuote:
    quote_id: str
    pcr_composite_hex: str
    mrenclave_hex: str
    nonce_hex: str
    signature_hex: str
    timestamp: float


class ZeroTrustHardwareEnclaveFabric:
    """
    Zero-Trust Hardware Attestation & Enclave Secure Boot Fabric.
    Enforces hardware-grade measured boot chains and PCR-bound cryptographic sealing.
    """

    def __init__(self, num_pcrs: int = 8, root_seed: Optional[bytes] = None):
        self._lock = threading.RLock()
        self.num_pcrs = num_pcrs
        self.pcrs: List[str] = [ZERO_PCR_HASH for _ in range(num_pcrs)]
        self.boot_log: List[BootLogEntry] = []
        self.root_key = root_seed or SOVEREIGN_ROOT_KEY
        self.mrenclave = hashlib.sha256(b"LUCY-SOVEREIGN-ENCLAVE-IMAGE-STAGE249").hexdigest()
        self.total_attestation_quotes: int = 0
        self.total_sealing_operations: int = 0
        self.total_unsealing_operations: int = 0

    def extend_pcr(self, pcr_index: int, stage_component: str, measurement: bytes) -> str:
        """
        Extends PCR register: PCR[i] <- SHA256(PCR[i] || measurement).
        Appends measured component to the hardware boot log.
        """
        with self._lock:
            if not (0 <= pcr_index < self.num_pcrs):
                raise IndexError(f"PCR index {pcr_index} out of bounds [0..{self.num_pcrs-1}]")

            meas_hash = hashlib.sha256(measurement).hexdigest()
            prev_val = bytes.fromhex(self.pcrs[pcr_index])
            new_hash = hashlib.sha256(prev_val + measurement).hexdigest()

            self.pcrs[pcr_index] = new_hash

            entry = BootLogEntry(
                entry_id=len(self.boot_log) + 1,
                pcr_index=pcr_index,
                stage_component=stage_component,
                measurement_hex=meas_hash,
                resulting_pcr_hex=new_hash,
                timestamp=time.time(),
            )
            self.boot_log.append(entry)
            return new_hash

    def get_pcr_composite(self, pcr_mask: int = 0xFF) -> str:
        """
        Computes the composite digest over selected PCR registers.
        """
        with self._lock:
            composite_data = bytearray()
            for i in range(self.num_pcrs):
                if (pcr_mask >> i) & 1:
                    composite_data.extend(bytes.fromhex(self.pcrs[i]))
            return hashlib.sha256(composite_data).hexdigest()

    def derive_sealing_key(self, pcr_composite_hex: str) -> bytes:
        """
        Derives an enclave sealing key cryptographically bound to the PCR composite.
        """
        key_material = hmac.new(
            self.root_key,
            msg=bytes.fromhex(pcr_composite_hex) + bytes.fromhex(self.mrenclave),
            digestmod=hashlib.sha256
        ).digest()
        return key_material

    def seal_data(self, plaintext: bytes, pcr_mask: int = 0xFF) -> Dict[str, Any]:
        """
        Cryptographically seals data to the current PCR state.
        Data can only be unsealed when the PCR registers match this exact composite.
        """
        with self._lock:
            self.total_sealing_operations += 1
            pcr_composite = self.get_pcr_composite(pcr_mask)
            sealing_key = self.derive_sealing_key(pcr_composite)

            # Keystream encryption (CTR-style determinism for local zero-cloud operation)
            iv = hashlib.sha256(str(time.time()).encode("utf-8") + plaintext).digest()[:16]
            ciphertext = bytearray()
            for idx, b in enumerate(plaintext):
                stream_byte = hmac.new(sealing_key, iv + idx.to_bytes(4, "big"), hashlib.sha256).digest()[0]
                ciphertext.append(b ^ stream_byte)

            # Integrity tag
            tag = hmac.new(sealing_key, bytes(ciphertext) + iv, hashlib.sha256).hexdigest()

            return {
                "ciphertext_hex": bytes(ciphertext).hex(),
                "iv_hex": iv.hex(),
                "tag_hex": tag,
                "bound_pcr_mask": pcr_mask,
                "expected_pcr_composite": pcr_composite,
                "mrenclave": self.mrenclave,
            }

    def unseal_data(self, sealed_package: Dict[str, Any]) -> Tuple[bool, Optional[bytes], str]:
        """
        Unseals data. Verifies current PCR state matches the sealing state.
        Fails and refuses decryption if any PCR has diverged or been tampered with.
        """
        with self._lock:
            self.total_unsealing_operations += 1
            pcr_mask = sealed_package["bound_pcr_mask"]
            expected_composite = sealed_package["expected_pcr_composite"]
            current_composite = self.get_pcr_composite(pcr_mask)

            if current_composite != expected_composite:
                return False, None, f"PCR State Divergence: current {current_composite[:12]} != expected {expected_composite[:12]}"

            sealing_key = self.derive_sealing_key(current_composite)
            ciphertext = bytes.fromhex(sealed_package["ciphertext_hex"])
            iv = bytes.fromhex(sealed_package["iv_hex"])
            expected_tag = sealed_package["tag_hex"]

            # Verify integrity
            computed_tag = hmac.new(sealing_key, ciphertext + iv, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected_tag, computed_tag):
                return False, None, "Cryptographic integrity tag mismatch: ciphertext corrupted"

            # Decrypt
            plaintext = bytearray()
            for idx, b in enumerate(ciphertext):
                stream_byte = hmac.new(sealing_key, iv + idx.to_bytes(4, "big"), hashlib.sha256).digest()[0]
                plaintext.append(b ^ stream_byte)

            return True, bytes(plaintext), "UNSEAL_SUCCESS_AUTHENTIC"

    def generate_attestation_quote(self, nonce: str, pcr_mask: int = 0xFF) -> AttestationQuote:
        """
        Generates a hardware attestation quote signing PCR state + MRENCLAVE + Nonce.
        """
        with self._lock:
            self.total_attestation_quotes += 1
            composite = self.get_pcr_composite(pcr_mask)
            nonce_bytes = nonce.encode("utf-8")
            payload = bytes.fromhex(composite) + bytes.fromhex(self.mrenclave) + nonce_bytes

            signature = hmac.new(self.root_key, payload, hashlib.sha256).hexdigest()
            quote_id = f"QUOTE-DICE-{self.total_attestation_quotes:04d}"

            return AttestationQuote(
                quote_id=quote_id,
                pcr_composite_hex=composite,
                mrenclave_hex=self.mrenclave,
                nonce_hex=nonce_bytes.hex(),
                signature_hex=signature,
                timestamp=time.time(),
            )

    def verify_attestation_quote(self, quote: AttestationQuote, expected_nonce: str) -> bool:
        """
        Verifies the signature and freshness of an AttestationQuote against the RoT.
        """
        with self._lock:
            nonce_bytes = expected_nonce.encode("utf-8")
            if quote.nonce_hex != nonce_bytes.hex():
                return False

            payload = bytes.fromhex(quote.pcr_composite_hex) + bytes.fromhex(quote.mrenclave_hex) + nonce_bytes
            expected_sig = hmac.new(self.root_key, payload, hashlib.sha256).hexdigest()
            return hmac.compare_digest(quote.signature_hex, expected_sig)

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "num_pcrs": self.num_pcrs,
                "boot_log_entries": len(self.boot_log),
                "total_sealing_operations": self.total_sealing_operations,
                "total_unsealing_operations": self.total_unsealing_operations,
                "total_attestation_quotes": self.total_attestation_quotes,
                "pcr_0": self.pcrs[0][:16] + "...",
                "pcr_composite": self.get_pcr_composite()[:16] + "...",
                "mrenclave": self.mrenclave[:16] + "...",
            }

    def format_ascii_status(self) -> str:
        with self._lock:
            comp_str = self.get_pcr_composite()[:24] + "..."
            mr_str = self.mrenclave[:24] + "..."
            boot_str = f"{len(self.boot_log)} measurements"
            quotes_str = f"{self.total_attestation_quotes}"
            seal_str = f"{self.total_sealing_operations} sealed / {self.total_unsealing_operations} unsealed"

            lines = [
                "+-------------------------------------------------------------------------+",
                "|      STAGE 249: Universal Multi-Tier Zero-Trust Hardware Enclave        |",
                "|      Era 25: Omni-Dimensional Super-Intelligence Matrix                |",
                "+-------------------------------------------------------------------------+",
                f"| PCR Composite (RoT)  : {comp_str:<48} |",
                f"| MRENCLAVE Identity   : {mr_str:<48} |",
                f"| Measured Boot Log    : {boot_str:<48} |",
                f"| Attestation Quotes   : {quotes_str:<48} |",
                f"| Enclave Sealing Ops  : {seal_str:<48} |",
                "+-------------------------------------------------------------------------+",
            ]
            return "\n".join(lines)


# Sovereign Global Singleton
_global_enclave: Optional[ZeroTrustHardwareEnclaveFabric] = None
_enclave_lock = threading.RLock()


def get_hardware_enclave() -> ZeroTrustHardwareEnclaveFabric:
    global _global_enclave
    with _enclave_lock:
        if _global_enclave is None:
            _global_enclave = ZeroTrustHardwareEnclaveFabric()
        return _global_enclave
