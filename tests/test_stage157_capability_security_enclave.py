r"""
tests/test_stage157_capability_security_enclave.py
Stage 157 Test Suite: Capability-Based Security Tokens & Enclave Sentinel
Era 16: Autonomous Microkernel, Bare-Metal HAL & Sovereign Operating System Primitives
"""

import unittest

from backend.lucy_core.capability_security_enclave import (
    CAP_DELEGATE,
    CAP_EXECUTE,
    CAP_MAP,
    CAP_READ,
    CAP_REVOKE,
    CAP_WRITE,
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    CapabilityToken,
    HardwareEnclaveSentinel,
    SovereignCapabilityManager,
    get_capability_manager,
)


class TestStage157CapabilitySecurityEnclave(unittest.TestCase):
    def setUp(self) -> None:
        self.mgr = SovereignCapabilityManager()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 157)
        self.assertEqual(ERA, 16)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Capability-Based Security Tokens & Enclave Sentinel",
        )

    def test_02_root_capability_minting(self) -> None:
        root_tok = self.mgr.mint_root_capability(owner_task_id=1, target_resource="port://vfs")
        self.assertTrue(root_tok.token_id.startswith("CAP-ROOT-"))
        self.assertEqual(root_tok.owner_task_id, 1)
        self.assertEqual(root_tok.target_resource, "port://vfs")
        self.assertTrue(root_tok.has_permission(CAP_READ))
        self.assertTrue(root_tok.has_permission(CAP_WRITE))
        self.assertTrue(root_tok.has_permission(CAP_DELEGATE))
        self.assertEqual(len(root_tok.hmac_signature), 64)

    def test_03_attenuated_delegation(self) -> None:
        root_tok = self.mgr.mint_root_capability(owner_task_id=1, target_resource="mem://dma_frame")
        # Delegate read-only capability to task 2
        child = self.mgr.delegate_capability(
            parent_token_id=root_tok.token_id,
            new_owner_task_id=2,
            requested_permissions=CAP_READ,
        )
        self.assertIsNotNone(child)
        self.assertEqual(child.owner_task_id, 2)
        self.assertEqual(child.permissions, CAP_READ)
        self.assertEqual(child.attenuation_level, 1)
        self.assertEqual(child.parent_token_id, root_tok.token_id)

    def test_04_privilege_escalation_blocked(self) -> None:
        # Parent with only READ and DELEGATE
        parent = self.mgr.mint_root_capability(owner_task_id=1, target_resource="dev://disk0")
        sub_read = self.mgr.delegate_capability(
            parent_token_id=parent.token_id,
            new_owner_task_id=2,
            requested_permissions=CAP_READ | CAP_DELEGATE,
        )

        # Task 2 attempts to delegate WRITE (which it does not have)
        escalation_tok = self.mgr.delegate_capability(
            parent_token_id=sub_read.token_id,
            new_owner_task_id=3,
            requested_permissions=CAP_READ | CAP_WRITE,
        )
        self.assertIsNone(escalation_tok)

    def test_05_capability_verification_access(self) -> None:
        tok = self.mgr.mint_root_capability(owner_task_id=5, target_resource="port://hal")
        # Verify access for owner with READ
        ok = self.mgr.verify_access(
            token_id=tok.token_id,
            required_permission=CAP_READ,
            target_resource="port://hal",
            task_id=5,
        )
        self.assertTrue(ok)

    def test_06_wrong_owner_or_resource_rejection(self) -> None:
        tok = self.mgr.mint_root_capability(owner_task_id=5, target_resource="port://hal")
        # Wrong owner task_id
        fail_owner = self.mgr.verify_access(
            token_id=tok.token_id,
            required_permission=CAP_READ,
            target_resource="port://hal",
            task_id=99,
        )
        self.assertFalse(fail_owner)

        # Wrong target resource
        fail_res = self.mgr.verify_access(
            token_id=tok.token_id,
            required_permission=CAP_READ,
            target_resource="port://crypto",
            task_id=5,
        )
        self.assertFalse(fail_res)

    def test_07_revocation_cascade(self) -> None:
        root = self.mgr.mint_root_capability(owner_task_id=1, target_resource="port://net")
        c1 = self.mgr.delegate_capability(root.token_id, new_owner_task_id=2, requested_permissions=CAP_READ | CAP_DELEGATE)
        c2 = self.mgr.delegate_capability(c1.token_id, new_owner_task_id=3, requested_permissions=CAP_READ)

        # Revoke root
        revoked_count = self.mgr.revoke_capability(root.token_id)
        self.assertEqual(revoked_count, 3)

        # All 3 must now fail verification
        self.assertFalse(self.mgr.verify_access(root.token_id, CAP_READ, "port://net", 1))
        self.assertFalse(self.mgr.verify_access(c1.token_id, CAP_READ, "port://net", 2))
        self.assertFalse(self.mgr.verify_access(c2.token_id, CAP_READ, "port://net", 3))

    def test_08_hardware_enclave_pcr_extend(self) -> None:
        enclave = self.mgr.enclave
        pcr0_before = enclave.pcr_registers[0]
        pcr0_after = enclave.extend_pcr(0, b"KERNEL_INTEGRITY_STAGE157")
        self.assertNotEqual(pcr0_before, pcr0_after)
        self.assertEqual(len(pcr0_after), 64)

    def test_09_enclave_attestation_quote(self) -> None:
        quote = self.mgr.enclave.generate_attestation_quote(nonce=b"nonce123")
        self.assertEqual(quote["creator"], "Senin")
        self.assertEqual(quote["operator"], "Senin Ali K P")
        self.assertEqual(quote["status"], "ATTESTED_SECURE")
        self.assertEqual(len(quote["enclave_signature"]), 64)

    def test_10_ascii_status_presentation(self) -> None:
        status = self.mgr.format_ascii_status()
        self.assertIn("LUCY STAGE 157", status)
        self.assertIn("Senin", status)
        self.assertIn("CAP-ROOT-", status)
        self.assertIn("Enclave PCR 0", status)


if __name__ == "__main__":
    unittest.main()
