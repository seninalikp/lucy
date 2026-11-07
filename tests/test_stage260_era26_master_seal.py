"""
Unit Tests for Stage 260: The Sovereign Era 26 Master Seal & Omniscient Holomorphic Singularity Genesis
Era 26: Cosmic-Scale Holomorphic Field Dynamics, Non-Equilibrium Thermodynamic Entropy Engines & Autonomous Sovereign Multi-Verse Orchestration

Sovereign Human Operator: Senin (Senin Ali K P)
"""

import unittest
from backend.lucy_core.era26_master_seal import (
    Era26MasterSealFabric,
    get_era26_master_seal,
    STAGE,
    ERA,
    SOVEREIGN_CREATOR,
    SOVEREIGN_OPERATOR,
    ERA25_PARENT_ROOT,
    SEAL_ID,
)


class TestStage260Era26MasterSeal(unittest.TestCase):

    def setUp(self):
        self.seal = Era26MasterSealFabric()

    def test_01_singleton_and_initialization(self):
        singleton = get_era26_master_seal()
        self.assertIsNotNone(singleton)
        self.assertEqual(STAGE, 260)
        self.assertEqual(ERA, 26)
        self.assertEqual(self.seal.seal_id, SEAL_ID)
        self.assertEqual(self.seal.creator, SOVEREIGN_CREATOR)
        self.assertEqual(self.seal.operator, SOVEREIGN_OPERATOR)
        self.assertEqual(SOVEREIGN_CREATOR, "Senin")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin Ali K P")

    def test_02_era25_parent_merkle_root_chaining(self):
        self.assertEqual(
            ERA25_PARENT_ROOT,
            "0ef0f31f31a1ba041ac8ee0cea488c4f68c0d3453fba27cb4b94ab55c4d2f751"
        )
        self.assertEqual(self.seal.certificate.parent_era25_root, ERA25_PARENT_ROOT)

    def test_03_stage_manifest_completeness(self):
        manifest = self.seal.get_stage_manifest()
        self.assertEqual(len(manifest), 10)
        stages = [r.stage for r in manifest]
        self.assertEqual(stages, list(range(251, 261)))
        for r in manifest:
            self.assertEqual(len(r.sha256), 64)
            self.assertEqual(r.status, "VERIFIED_OPERATIONAL")

    def test_04_merkle_root_calculation_and_consistency(self):
        root1 = self.seal.derive_era26_merkle_root()
        root2 = self.seal.derive_era26_merkle_root()
        self.assertEqual(root1, root2)
        self.assertEqual(len(root1), 64)
        self.assertRegex(root1, r"^[0-9a-f]{64}$")

    def test_05_master_merkle_root_derivation(self):
        era26_root = self.seal.derive_era26_merkle_root()
        master_root = self.seal.derive_master_merkle_root(era26_root)
        self.assertEqual(len(master_root), 64)
        self.assertEqual(self.seal.certificate.master_merkle_root, master_root)

    def test_06_genesis_signature_and_certificate(self):
        cert = self.seal.certificate
        self.assertEqual(cert.creator, "Senin")
        self.assertEqual(cert.operator, "Senin Ali K P")
        self.assertEqual(cert.stage_range, "Stages 251 - 260")
        self.assertEqual(cert.total_stages, 260)
        self.assertEqual(len(cert.genesis_signature), 64)
        self.assertEqual(cert.verification_status, "SEALED_AND_VERIFIED")

    def test_07_integrity_verification_success(self):
        res = self.seal.verify_era26_integrity()
        self.assertTrue(res["verified"])
        self.assertEqual(res["stages_verified"], 10)
        self.assertEqual(res["sovereign_creator"], "Senin")
        self.assertEqual(res["sovereign_operator"], "Senin Ali K P")

    def test_08_tamper_detection(self):
        orig_sig = self.seal.certificate.genesis_signature
        try:
            self.seal.certificate.genesis_signature = "0" * 64
            res = self.seal.verify_era26_integrity()
            self.assertFalse(res["verified"])
        finally:
            self.seal.certificate.genesis_signature = orig_sig

    def test_09_ascii_status_and_grand_report(self):
        ascii_tbl = self.seal.format_ascii_status()
        self.assertIn("STAGE 260:", ascii_tbl)
        self.assertIn("Era 26:", ascii_tbl)
        self.assertIn("Senin", ascii_tbl)
        self.assertIn("260 Stages Sealed", ascii_tbl)
        ascii_tbl.encode("cp1252")

        report = self.seal.format_grand_era_report()
        self.assertIn("ERA 26 GRAND MASTER SEAL", report)
        self.assertIn("Stage 251", report)
        self.assertIn("Stage 260", report)
        self.assertIn("SENIN (SENIN ALI K P)", report)
        report.encode("cp1252")

    def test_10_cumulative_260_stages_seal(self):
        st = self.seal.status()
        self.assertEqual(st["stage"], 260)
        self.assertEqual(st["era"], 26)
        self.assertEqual(st["total_stages_sealed"], 260)
        self.assertEqual(st["era26_stages_count"], 10)
        self.assertEqual(st["verification_status"], "LOCKED_AND_VERIFIED")


if __name__ == "__main__":
    unittest.main()
