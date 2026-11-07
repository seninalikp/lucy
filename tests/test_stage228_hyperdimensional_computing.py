r"""
tests/test_stage228_hyperdimensional_computing.py
Stage 228 Unit Tests: High-Dimensional Hyperdimensional Computing & Vector Symbolic Architecture
"""

import threading
import unittest

from backend.lucy_core.hyperdimensional_computing import (
    HyperdimensionalComputingFabric,
    Hypervector,
    bundle_hypervectors,
    STAGE,
    STAGE_NAME,
)


class TestStage228HyperdimensionalComputing(unittest.TestCase):
    def setUp(self):
        self.fabric = HyperdimensionalComputingFabric(dimension=2048)

    def test_01_initialization_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 228)
        self.assertEqual(s["stage_name"], STAGE_NAME)
        self.assertEqual(s["dimension"], 2048)
        self.assertEqual(s["item_memory_size"], 0)

    def test_02_symbol_generation_quasi_orthogonality(self):
        hv1 = self.fabric.generate_symbol("apple")
        hv2 = self.fabric.generate_symbol("banana")
        # In D=2048 space, random bipolar vectors have cosine similarity ~ 0 (|sim| < 0.1)
        sim = hv1.cosine_similarity(hv2)
        self.assertAlmostEqual(sim, 0.0, delta=0.1)
        # Deterministic: retrieving same symbol yields exact vector (sim == 1.0)
        hv1_again = self.fabric.generate_symbol("apple")
        self.assertEqual(hv1.cosine_similarity(hv1_again), 1.0)

    def test_03_binding_operator_invertibility_and_orthogonality(self):
        a = self.fabric.generate_symbol("role_agent")
        b = self.fabric.generate_symbol("value_lucy")
        bound = a.bind(b)

        # Bound vector is quasi-orthogonal to both inputs
        self.assertAlmostEqual(bound.cosine_similarity(a), 0.0, delta=0.1)
        self.assertAlmostEqual(bound.cosine_similarity(b), 0.0, delta=0.1)

        # Unbinding with a recovers b exactly in bipolar space: (a * b) * a == b
        unbound_b = bound.bind(a)
        self.assertEqual(unbound_b.cosine_similarity(b), 1.0)

    def test_04_bundling_superposition_similarity(self):
        a = self.fabric.generate_symbol("dog")
        b = self.fabric.generate_symbol("cat")
        bundled = bundle_hypervectors([a, b])

        # Bundled vector has positive similarity to both constituents (> 0.4)
        sim_a = bundled.cosine_similarity(a)
        sim_b = bundled.cosine_similarity(b)
        self.assertGreater(sim_a, 0.4)
        self.assertGreater(sim_b, 0.4)

    def test_05_permutation_cyclic_shifting(self):
        seq = self.fabric.generate_symbol("token1")
        shifted = seq.permute(shift=10)
        # Shifted vector is quasi-orthogonal to original
        self.assertAlmostEqual(shifted.cosine_similarity(seq), 0.0, delta=0.1)
        # Shifting back by -10 recovers original
        recovered = shifted.permute(shift=-10)
        self.assertEqual(recovered.cosine_similarity(seq), 1.0)

    def test_06_composite_record_encoding(self):
        record = self.fabric.store_composite_record(
            "country_profile",
            {"name": "argentina", "capital": "buenos_aires", "language": "spanish"},
        )
        self.assertIn("country_profile", self.fabric.composite_records)
        self.assertEqual(record.dimension, 2048)

    def test_07_query_composite_record_associative_recall(self):
        self.fabric.store_composite_record(
            "france_data",
            {"capital": "paris", "currency": "euro", "continent": "europe"},
        )
        val, sim = self.fabric.query_record("france_data", "capital")
        self.assertEqual(val, "paris")
        self.assertGreater(sim, 0.25)

        val_curr, sim_curr = self.fabric.query_record("france_data", "currency")
        self.assertEqual(val_curr, "euro")
        self.assertGreater(sim_curr, 0.25)

    def test_08_semantic_analogy_solving(self):
        # USA has currency dollar and capital washington
        self.fabric.store_composite_record(
            "usa_rec",
            {"currency": "dollar", "capital": "washington"},
        )
        # Mexico has currency peso and capital cdmx
        self.fabric.store_composite_record(
            "mexico_rec",
            {"currency": "peso", "capital": "cdmx"},
        )

        # What is the "dollar" of Mexico? (Dollar : USA :: ? : Mexico)
        best_cand, sim = self.fabric.solve_relational_analogy(
            source_record_name="usa_rec",
            target_record_name="mexico_rec",
            source_item="dollar",
        )
        self.assertEqual(best_cand, "peso")
        self.assertGreater(sim, 0.20)

    def test_09_cleanup_associative_memory(self):
        clean_target = self.fabric.generate_symbol("target_vector")
        # Add random noise by flipping 10% of coordinates
        noisy_vals = list(clean_target.values)
        for i in range(0, len(noisy_vals), 10):
            noisy_vals[i] *= -1
        noisy_hv = Hypervector(values=noisy_vals, dimension=2048)

        match_name, sim = self.fabric.cleanup_vector(noisy_hv)
        self.assertEqual(match_name, "target_vector")
        self.assertGreater(sim, 0.7)

    def test_10_cp1252_safe_ascii_and_concurrency(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 228", tbl)
        self.assertIn("HYPERDIMENSIONAL COMPUTING", tbl)
        tbl.encode("cp1252")
        self.assertTrue(tbl.startswith("+--"))

        def worker(wid: int):
            rec_name = f"rec_{wid}"
            self.fabric.store_composite_record(rec_name, {f"k_{wid}": f"v_{wid}"})
            _ = self.fabric.query_record(rec_name, f"k_{wid}")
            _ = self.fabric.status()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertGreaterEqual(len(self.fabric.composite_records), 4)


if __name__ == "__main__":
    unittest.main()
