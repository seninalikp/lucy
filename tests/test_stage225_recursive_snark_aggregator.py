r"""
tests/test_stage225_recursive_snark_aggregator.py
Stage 225 Unit Tests: Autonomous Zero-Knowledge Proof Aggregator & Recursive SNARK Verifier
"""

import threading
import unittest

from backend.lucy_core.recursive_snark_aggregator import (
    FIELD_MODULUS,
    R1CSConstraint,
    RecursiveSNARKAggregatorFabric,
    ZKProof,
    field_add,
    field_mul,
    STAGE,
    STAGE_NAME,
)


class TestStage225RecursiveSNARKAggregator(unittest.TestCase):
    def setUp(self):
        self.fabric = RecursiveSNARKAggregatorFabric()

    def test_01_initialization_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 225)
        self.assertEqual(s["stage_name"], STAGE_NAME)
        self.assertIn("multiplier", s["registered_circuits"])
        self.assertIn("adder", s["registered_circuits"])
        self.assertEqual(s["total_proofs_generated"], 0)

    def test_02_r1cs_constraint_satisfaction(self):
        # Multiplier constraint: w[1] * w[2] == w[3]
        c = R1CSConstraint(a={1: 1}, b={2: 1}, c={3: 1})
        valid_witness = [1, 6, 7, 42]
        invalid_witness = [1, 6, 7, 43]
        self.assertTrue(c.evaluate(valid_witness))
        self.assertFalse(c.evaluate(invalid_witness))

    def test_03_prove_multiplier_circuit(self):
        witness = [1, 12, 11, 132]
        proof = self.fabric.prove_circuit("multiplier", witness=witness, public_inputs=[132])
        self.assertEqual(proof.circuit_name, "multiplier")
        self.assertEqual(proof.public_inputs, [132])
        self.assertFalse(proof.is_aggregated)
        self.assertEqual(proof.recursion_depth, 0)
        self.assertEqual(field_mul(proof.commitment_a, proof.commitment_b), proof.commitment_c)

    def test_04_verify_valid_proof(self):
        witness = [1, 3, 5, 15]
        proof = self.fabric.prove_circuit("multiplier", witness=witness, public_inputs=[15])
        is_valid = self.fabric.verify_proof(proof)
        self.assertTrue(is_valid)
        self.assertIn(proof.proof_id, self.fabric.verified_proofs_archive)

    def test_05_reject_tampered_proof(self):
        witness = [1, 4, 4, 16]
        proof = self.fabric.prove_circuit("multiplier", witness=witness, public_inputs=[16])
        # Tamper commitment_c
        proof.commitment_c = (proof.commitment_c + 1) % FIELD_MODULUS
        is_valid = self.fabric.verify_proof(proof)
        self.assertFalse(is_valid)

    def test_06_recursive_proof_aggregation(self):
        w1 = [1, 2, 3, 6]
        p1 = self.fabric.prove_circuit("multiplier", witness=w1, public_inputs=[6])
        w2 = [1, 5, 5, 25]
        p2 = self.fabric.prove_circuit("multiplier", witness=w2, public_inputs=[25])

        agg = self.fabric.aggregate_proofs([p1, p2])
        self.assertTrue(agg.is_aggregated)
        self.assertEqual(agg.recursion_depth, 1)
        self.assertEqual(len(agg.aggregated_proof_ids), 2)
        self.assertTrue(self.fabric.verify_proof(agg))

    def test_07_nested_recursive_aggregation(self):
        # Two base proofs
        p1 = self.fabric.prove_circuit("multiplier", witness=[1, 2, 4, 8], public_inputs=[8])
        p2 = self.fabric.prove_circuit("multiplier", witness=[1, 3, 3, 9], public_inputs=[9])
        agg1 = self.fabric.aggregate_proofs([p1, p2])

        # Third base proof
        p3 = self.fabric.prove_circuit("multiplier", witness=[1, 7, 7, 49], public_inputs=[49])
        # Fold agg1 and p3 together
        agg2 = self.fabric.aggregate_proofs([agg1, p3])
        self.assertEqual(agg2.recursion_depth, 2)
        self.assertTrue(self.fabric.verify_proof(agg2))

    def test_08_batch_verification(self):
        p1 = self.fabric.prove_circuit("multiplier", witness=[1, 2, 2, 4], public_inputs=[4])
        p2 = self.fabric.prove_circuit("multiplier", witness=[1, 3, 4, 12], public_inputs=[12])
        p3 = self.fabric.prove_circuit("multiplier", witness=[1, 10, 10, 100], public_inputs=[100])

        all_ok, failed = self.fabric.batch_verify([p1, p2, p3])
        self.assertTrue(all_ok)
        self.assertEqual(len(failed), 0)

        # Tamper one
        p3.commitment_c = 0
        all_ok2, failed2 = self.fabric.batch_verify([p1, p2, p3])
        self.assertFalse(all_ok2)
        self.assertIn(p3.proof_id, failed2)

    def test_09_cp1252_safe_ascii_table(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 225", tbl)
        self.assertIn("AUTONOMOUS ZERO-KNOWLEDGE", tbl)
        tbl.encode("cp1252")
        self.assertTrue(tbl.startswith("+--"))

    def test_10_multithreaded_concurrency(self):
        def worker(wid: int):
            for i in range(5):
                p = self.fabric.prove_circuit(
                    "multiplier",
                    witness=[1, wid + 1, i + 1, (wid + 1) * (i + 1)],
                    public_inputs=[(wid + 1) * (i + 1)],
                )
                self.fabric.verify_proof(p)
            _ = self.fabric.status()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertGreaterEqual(self.fabric.total_proofs_generated, 20)


if __name__ == "__main__":
    unittest.main()
