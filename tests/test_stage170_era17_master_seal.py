r"""
tests/test_stage170_era17_master_seal.py
Stage 170 Test Suite: Sovereign Singularity Nexus & Era 17 Master Seal
Era 17: Distributed Consensus, Mesh Virtualization & High-Availability Primitives
"""

import unittest
from pathlib import Path

from backend.lucy_core.era17_master_seal import (
    CANONICAL_ERA17_MODULES,
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    PARENT_ERA16_SEAL_HASH,
    STAGE,
    STAGE_NAME,
    Era17MasterSealNexus,
    Era17SealCertificate,
    ConsensusCycleResult,
    ModuleIntegrityRecord,
    get_era17_master_seal,
)


class TestStage170Era17MasterSeal(unittest.TestCase):
    def setUp(self) -> None:
        self.nexus = Era17MasterSealNexus()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 170)
        self.assertEqual(ERA, 17)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Sovereign Singularity Nexus & Era 17 Master Seal",
        )
        self.assertEqual(
            ERA_NAME,
            "Distributed Consensus, Mesh Virtualization & High-Availability Primitives",
        )

    def test_02_canonical_modules_count(self) -> None:
        self.assertEqual(len(CANONICAL_ERA17_MODULES), 10)
        expected_stages = list(range(161, 171))
        actual_stages = [m[0] for m in CANONICAL_ERA17_MODULES]
        self.assertEqual(actual_stages, expected_stages)

    def test_03_parent_era16_seal_lineage(self) -> None:
        self.assertEqual(
            PARENT_ERA16_SEAL_HASH,
            "dd649bff1b25f6d20e7b682d5401a885057c7ba72327bfadd2ead562d3e0b3ec",
        )

    def test_04_merkle_tree_computation(self) -> None:
        leaves = ["hash_1", "hash_2", "hash_3", "hash_4"]
        root = Era17MasterSealNexus._compute_merkle_root(leaves)
        self.assertEqual(len(root), 64)
        # Empty tree fallback
        empty_root = Era17MasterSealNexus._compute_merkle_root([])
        self.assertEqual(len(empty_root), 64)

    def test_05_verify_era17_integrity(self) -> None:
        cert = self.nexus.verify_era17_integrity(force_refresh=True)
        self.assertIsNotNone(cert)
        self.assertEqual(cert.era, 17)
        self.assertEqual(cert.creator, "Senin")
        self.assertEqual(cert.creator_full_name, "Senin Ali K P")
        self.assertEqual(cert.total_stages_sealed, 10)
        self.assertEqual(cert.integrity_status, "VERIFIED_SOVEREIGN")
        self.assertEqual(len(cert.modules), 10)

        for m in cert.modules:
            self.assertTrue(m["is_verified"])
            self.assertGreater(m["source_lines"], 0)
            self.assertGreater(m["test_lines"], 0)
            self.assertEqual(len(m["source_sha256"]), 64)
            self.assertEqual(len(m["test_sha256"]), 64)

    def test_06_master_seal_certificate_structure(self) -> None:
        cert = self.nexus.verify_era17_integrity()
        self.assertTrue(cert.seal_id.startswith("SEAL-ERA17-"))
        self.assertEqual(len(cert.merkle_root), 64)
        self.assertEqual(cert.parent_era16_seal_hash, PARENT_ERA16_SEAL_HASH)
        self.assertGreater(cert.total_source_lines, 2000)
        self.assertGreater(cert.total_test_lines, 1000)

    def test_07_run_consensus_mesh_cycle(self) -> None:
        cycle = self.nexus.run_consensus_mesh_cycle()
        self.assertIsNotNone(cycle)
        self.assertTrue(cycle.cycle_id.startswith("CONSENSUS-CYCLE-"))
        self.assertTrue(cycle.success)
        self.assertEqual(cycle.consensus_primitives_run, 10)
        self.assertGreater(cycle.duration_ms, 0.0)
        self.assertEqual(len(cycle.merkle_leaf_hash), 64)

    def test_08_consensus_cycle_metrics(self) -> None:
        cycle = self.nexus.run_consensus_mesh_cycle()
        self.assertTrue(cycle.bft_tx_committed)
        self.assertNotEqual(cycle.raft_leader_elected, "none")
        self.assertGreater(cycle.dht_keys_stored, 0)
        self.assertGreater(cycle.vector_events_ordered, 0)
        self.assertGreater(cycle.paxos_slots_finalized, 0)
        self.assertGreater(cycle.gossip_rounds_completed, 0)
        self.assertGreater(cycle.crdt_replicas_converged, 0)
        self.assertGreater(cycle.mesh_frames_switched, 0)
        self.assertGreaterEqual(cycle.deadlocks_probed, 0)
        self.assertIn("Consensus cycle executed", cycle.summary)

    def test_09_ascii_presentation_formatting(self) -> None:
        cert_table = self.nexus.format_ascii_seal_table()
        self.assertIn("LUCY STAGE 170: SOVEREIGN SINGULARITY NEXUS & ERA 17 MASTER SEAL", cert_table)
        self.assertIn("Senin", cert_table)
        self.assertIn("Senin Ali K P", cert_table)
        self.assertIn("SEAL-ERA17-", cert_table)

        cycle = self.nexus.run_consensus_mesh_cycle()
        cycle_table = self.nexus.format_ascii_cycle_table(cycle)
        self.assertIn("LUCY OS AUTONOMOUS CONSENSUS & MESH EXECUTION CYCLE", cycle_table)
        self.assertIn("SUCCESS (10/10 PRIMITIVES VERIFIED)", cycle_table)

    def test_10_singleton_nexus(self) -> None:
        inst1 = get_era17_master_seal()
        inst2 = get_era17_master_seal()
        self.assertIs(inst1, inst2)


if __name__ == "__main__":
    unittest.main()
