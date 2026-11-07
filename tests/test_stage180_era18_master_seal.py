r"""
tests/test_stage180_era18_master_seal.py
Stage 180 Test Suite: Sovereign Singularity Nexus & Era 18 Master Seal
Era 18: Autonomous Distributed Storage, Geo-Replication & Sharding Primitives
"""

import unittest
from pathlib import Path

from backend.lucy_core.era18_master_seal import (
    CANONICAL_ERA18_MODULES,
    CREATOR_FULL_NAME,
    CREATOR_NAME,
    ERA,
    ERA_NAME,
    PARENT_ERA17_SEAL_HASH,
    STAGE,
    STAGE_NAME,
    Era18MasterSealNexus,
    Era18SealCertificate,
    ModuleIntegrityRecord,
    StorageCycleResult,
    get_era18_master_seal,
)


class TestStage180Era18MasterSeal(unittest.TestCase):
    def setUp(self) -> None:
        self.nexus = Era18MasterSealNexus()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 180)
        self.assertEqual(ERA, 18)
        self.assertEqual(CREATOR_NAME, "Senin")
        self.assertEqual(CREATOR_FULL_NAME, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Sovereign Singularity Nexus & Era 18 Master Seal",
        )
        self.assertEqual(
            ERA_NAME,
            "Autonomous Distributed Storage, Geo-Replication & Sharding Primitives",
        )

    def test_02_canonical_modules_count(self) -> None:
        self.assertEqual(len(CANONICAL_ERA18_MODULES), 10)
        expected_stages = list(range(171, 181))
        actual_stages = [m[0] for m in CANONICAL_ERA18_MODULES]
        self.assertEqual(actual_stages, expected_stages)

    def test_03_parent_era17_seal_lineage(self) -> None:
        self.assertEqual(
            PARENT_ERA17_SEAL_HASH,
            "737d550132cb01f4ae3f52850e5cb09b19029935f53fcb473f22f47fec080f4d",
        )

    def test_04_merkle_tree_computation(self) -> None:
        leaves = ["hash_1", "hash_2", "hash_3", "hash_4"]
        root = Era18MasterSealNexus._compute_merkle_root(leaves)
        self.assertEqual(len(root), 64)
        # Empty tree fallback
        empty_root = Era18MasterSealNexus._compute_merkle_root([])
        self.assertEqual(len(empty_root), 64)

    def test_05_verify_era18_integrity(self) -> None:
        cert = self.nexus.verify_era18_integrity(force_refresh=True)
        self.assertIsNotNone(cert)
        self.assertEqual(cert.era, 18)
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
        cert = self.nexus.verify_era18_integrity()
        self.assertTrue(cert.seal_id.startswith("SEAL-ERA18-"))
        self.assertEqual(len(cert.merkle_root), 64)
        self.assertEqual(cert.parent_era17_seal_hash, PARENT_ERA17_SEAL_HASH)
        self.assertGreater(cert.total_source_lines, 2000)
        self.assertGreater(cert.total_test_lines, 1000)

    def test_07_run_storage_geo_cycle(self) -> None:
        cycle = self.nexus.run_storage_geo_cycle()
        self.assertIsNotNone(cycle)
        self.assertTrue(cycle.cycle_id.startswith("STORAGE-CYCLE-"))
        self.assertTrue(cycle.success)
        self.assertEqual(cycle.storage_primitives_run, 10)
        self.assertGreater(cycle.duration_ms, 0.0)
        self.assertEqual(len(cycle.merkle_leaf_hash), 64)

    def test_08_storage_cycle_metrics(self) -> None:
        cycle = self.nexus.run_storage_geo_cycle()
        self.assertGreater(cycle.hash_ring_vnodes, 0)
        self.assertGreaterEqual(cycle.lsm_records_flushed, 1)
        self.assertTrue(cycle.quorum_repaired)
        self.assertGreaterEqual(cycle.wal_hwm_advanced, 1)
        self.assertGreater(cycle.mvcc_committed_ts, 1000.0)
        self.assertTrue(cycle.shard_migrated)
        self.assertGreaterEqual(cycle.secondary_index_matches, 1)
        self.assertTrue(cycle.multi_raft_committed)
        self.assertGreaterEqual(cycle.geo_regions_synced, 1)
        self.assertIn("Storage cycle executed", cycle.summary)

    def test_09_ascii_formatting_and_status(self) -> None:
        cert_table = self.nexus.format_ascii_seal_table()
        self.assertIn("LUCY STAGE 180: SOVEREIGN SINGULARITY NEXUS & ERA 18 MASTER SEAL", cert_table)
        self.assertIn("Senin", cert_table)
        self.assertIn("Senin Ali K P", cert_table)
        self.assertIn("SEAL-ERA18-", cert_table)

        cycle = self.nexus.run_storage_geo_cycle()
        cycle_table = self.nexus.format_ascii_cycle_table(cycle)
        self.assertIn("LUCY OS AUTONOMOUS DISTRIBUTED STORAGE & GEO-REPLICATION CYCLE", cycle_table)
        self.assertIn("SUCCESS (10/10 PRIMITIVES VERIFIED)", cycle_table)

    def test_10_singleton_nexus(self) -> None:
        inst1 = get_era18_master_seal()
        inst2 = get_era18_master_seal()
        self.assertIs(inst1, inst2)


if __name__ == "__main__":
    unittest.main()
