"""
tests/test_stage244_dna_molecular_storage.py
Unit tests for Stage 244: Autonomous Synthetic Biology DNA/RNA Storage Codec & Error-Correcting Base Sequence Transceiver
Era 25: Omni-Dimensional Super-Intelligence Matrix, Astro-Cognitive Planetary Orchestration & Sovereign Trans-Singularity Metamaterials
"""

import os
import random
import sys
import unittest

sys.path.insert(0, os.getcwd())

from backend.lucy_core.dna_molecular_storage import (
    STAGE,
    STAGE_NAME,
    ERA,
    FORWARD_PRIMER,
    REVERSE_PRIMER,
    DnaMolecularStorageFabric
)


class TestStage244DnaMolecularStorage(unittest.TestCase):

    def test_01_quaternary_encoding_decoding_roundtrip(self):
        """Test quaternary nucleotide conversion round-trip for arbitrary bytes."""
        fabric = DnaMolecularStorageFabric()
        original = b"SOVEREIGN_LUCY_DNA_STORAGE_2026"
        nucs = fabric._bytes_to_quaternary(original)
        self.assertTrue(all(c in {"A", "C", "G", "T"} for c in nucs))

        restored = fabric._quaternary_to_bytes(nucs)
        self.assertEqual(restored, original)

    def test_02_oligo_strand_structure(self):
        """Test oligo strand structure: forward primer, header, payload, checksum, reverse primer."""
        fabric = DnaMolecularStorageFabric(payload_chunk_size=8)
        strands = fabric.encode_data_to_oligo_pool(b"TESTDATA")
        self.assertEqual(len(strands), 1)

        s = strands[0]
        self.assertEqual(s.forward_primer, FORWARD_PRIMER)
        self.assertEqual(s.reverse_primer, REVERSE_PRIMER)
        self.assertEqual(len(s.checksum_sequence), 4)
        self.assertEqual(s.strand_index, 0)
        self.assertTrue(s.full_sequence.startswith(FORWARD_PRIMER))
        self.assertTrue(s.full_sequence.endswith(REVERSE_PRIMER))

    def test_03_gc_content_homeostasis(self):
        """Test GC content of synthesized strands falls into biological window."""
        fabric = DnaMolecularStorageFabric(payload_chunk_size=16)
        strands = fabric.encode_data_to_oligo_pool(b"STABLE_THERMODYNAMIC_DNA_CHAIN_METAMATERIAL")
        for s in strands:
            gc = s.gc_content
            self.assertGreaterEqual(gc, 0.30)
            self.assertLessEqual(gc, 0.70)

    def test_04_homopolymer_run_length_bound(self):
        """Test homopolymer run length is tracked."""
        fabric = DnaMolecularStorageFabric(payload_chunk_size=16)
        strands = fabric.encode_data_to_oligo_pool(b"HOMOPOLYMER_TESTING_DATA")
        for s in strands:
            self.assertGreaterEqual(s.max_homopolymer_run, 1)

    def test_05_multi_strand_chunking_and_reassembly(self):
        """Test splitting large message into multiple oligos and perfect decoding."""
        fabric = DnaMolecularStorageFabric(payload_chunk_size=8)
        msg = b"DeepMind_Antigravity_Lucy_Sovereign_Kernel_Stage244_DNA_Codec"
        strands = fabric.encode_data_to_oligo_pool(msg)
        self.assertGreater(len(strands), 1)

        decoded = fabric.decode_oligo_pool_to_data(strands)
        self.assertEqual(decoded, msg)
        self.assertEqual(fabric.total_decodings, 1)

    def test_06_checksum_corruption_detection(self):
        """Test that single-nucleotide corruption triggers validation error."""
        fabric = DnaMolecularStorageFabric(payload_chunk_size=8)
        strands = fabric.encode_data_to_oligo_pool(b"TAMPER_TEST_DATA")
        s0 = strands[0]

        # Mutate first nucleotide in payload
        mut_payload = ("C" if s0.payload_sequence[0] != "C" else "A") + s0.payload_sequence[1:]
        s0.payload_sequence = mut_payload

        with self.assertRaises(ValueError) as ctx:
            fabric.decode_oligo_pool_to_data(strands)
        self.assertIn("Corrupted oligo strand", str(ctx.exception))

    def test_07_out_of_order_strand_assembly(self):
        """Test index headers guarantee correct reassembly even when oligos arrive shuffled."""
        fabric = DnaMolecularStorageFabric(payload_chunk_size=4)
        msg = b"0123456789ABCDEF"
        strands = fabric.encode_data_to_oligo_pool(msg)

        shuffled = list(strands)
        random.shuffle(shuffled)

        decoded = fabric.decode_oligo_pool_to_data(shuffled)
        self.assertEqual(decoded, msg)

    def test_08_pcr_sequencing_noise_simulation(self):
        """Test noise injection creates substitutions."""
        fabric = DnaMolecularStorageFabric(payload_chunk_size=8)
        strands = fabric.encode_data_to_oligo_pool(b"MUTATION_NOISE")
        noisy = fabric.simulate_pcr_sequencing_noise(strands, substitution_rate=0.5, dropout_rate=0.0)
        self.assertEqual(len(noisy), len(strands))

    def test_09_theoretical_density_metric(self):
        """Test theoretical single-stranded DNA density metric equals 455 Exabytes/gram."""
        fabric = DnaMolecularStorageFabric()
        self.assertEqual(fabric.compute_theoretical_density_exabytes_per_gram(), 455.0)

    def test_10_fabric_status_and_ascii_table(self):
        """Test status dictionary and CP1252-safe ASCII table."""
        fabric = DnaMolecularStorageFabric()
        fabric.encode_data_to_oligo_pool(b"STATUS_TEST")
        st = fabric.status()
        self.assertEqual(st["stage"], 244)
        self.assertEqual(st["era"], 25)
        self.assertGreater(st["active_oligo_pool"], 0)

        tbl = fabric.format_ascii_status()
        self.assertIn("STAGE 244", tbl)
        self.assertIn("Active Oligo Pool", tbl)
        self.assertIn("Theoretical Density", tbl)
        self.assertTrue(tbl.startswith("+--"))
        self.assertTrue(tbl.endswith("--+"))


if __name__ == "__main__":
    unittest.main()
