r"""
tests/test_stage205_knowledge_distillation_pruner.py
Stage 205: Autonomous Semantic Knowledge Distillation & Model Pruner
Era 21: Autonomous Hyper-Scale Multi-Kernel Federation, Quantum-Resistant Keys & Post-Singularity Architecture
"""

import unittest
from backend.lucy_core.knowledge_distillation_pruner import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    CSRMatrix,
    KnowledgeDistillationPrunerFabric,
)


class TestStage205KnowledgeDistillationPruner(unittest.TestCase):
    """10 Unit Tests for Stage 205 Knowledge Distillation & Model Pruner Fabric."""

    def setUp(self):
        self.fabric = KnowledgeDistillationPrunerFabric()

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric._pruning_runs_count, 0)
        self.assertEqual(self.fabric._distillation_evals_count, 0)
        self.assertEqual(self.fabric.status()["stage"], 205)
        self.assertEqual(self.fabric.status()["era"], 21)

    def test_02_unstructured_pruning_50_percent(self):
        matrix = [
            [1.0, 2.0, 3.0, 4.0],
            [5.0, 6.0, 7.0, 8.0],
            [9.0, 10.0, 11.0, 12.0],
            [13.0, 14.0, 15.0, 16.0],
        ]
        dense_p, csr, sparsity = self.fabric.prune_unstructured(matrix, target_sparsity=0.5)
        self.assertAlmostEqual(sparsity, 0.5, places=2)
        zero_count = sum(1 for row in dense_p for val in row if val == 0.0)
        self.assertEqual(zero_count, 8)
        self.assertEqual(len(csr.values), 8)

    def test_03_unstructured_pruning_75_percent(self):
        matrix = [
            [1.0, 2.0, 3.0, 4.0],
            [5.0, 6.0, 7.0, 8.0],
            [9.0, 10.0, 11.0, 12.0],
            [13.0, 14.0, 15.0, 16.0],
        ]
        dense_p, csr, sparsity = self.fabric.prune_unstructured(matrix, target_sparsity=0.75)
        self.assertAlmostEqual(sparsity, 0.75, places=2)
        zero_count = sum(1 for row in dense_p for val in row if val == 0.0)
        self.assertEqual(zero_count, 12)
        self.assertEqual(len(csr.values), 4)

    def test_04_csr_matrix_to_dense_conversion(self):
        matrix = [
            [0.0, 5.0, 0.0],
            [1.0, 0.0, 2.0],
            [0.0, 0.0, 3.0],
        ]
        dense_p, csr, _ = self.fabric.prune_unstructured(matrix, target_sparsity=0.0)
        reconstructed = csr.to_dense()
        self.assertEqual(reconstructed, matrix)

    def test_05_csr_matrix_properties(self):
        csr = CSRMatrix(
            values=[10.0, 20.0],
            col_indices=[0, 1],
            row_ptrs=[0, 1, 2],
            shape=(2, 2),
        )
        d = csr.to_dict()
        self.assertEqual(d["nnz"], 2)
        self.assertEqual(d["density"], 0.5)

    def test_06_structured_column_pruning(self):
        # 3 rows, 4 cols. Col 0 and 1 have small values, col 2 and 3 have large values
        matrix = [
            [0.1, 0.2, 10.0, 20.0],
            [0.1, 0.1, 10.0, 20.0],
            [0.2, 0.1, 10.0, 20.0],
        ]
        # Keep top 50% columns (2 columns out of 4)
        pruned = self.fabric.prune_structured_columns(matrix, keep_ratio=0.5)
        self.assertEqual(len(pruned), 3)
        self.assertEqual(len(pruned[0]), 2)
        # Should keep cols 2 and 3
        self.assertEqual(pruned[0], [10.0, 20.0])

    def test_07_distillation_loss_identical_logits(self):
        logits = [2.0, 1.0, 0.1]
        loss = self.fabric.compute_distillation_loss(logits, logits, temperature=1.0)
        self.assertAlmostEqual(loss, 0.0, places=4)

    def test_08_distillation_loss_different_logits(self):
        student = [1.0, 0.5, 0.0]
        teacher = [5.0, 1.0, -1.0]
        loss = self.fabric.compute_distillation_loss(student, teacher, temperature=2.0)
        self.assertGreater(loss, 0.0)

    def test_09_temperature_scaling_effect(self):
        student = [2.0, 0.0]
        teacher = [0.0, 2.0]
        loss_t1 = self.fabric.compute_distillation_loss(student, teacher, temperature=1.0)
        loss_t3 = self.fabric.compute_distillation_loss(student, teacher, temperature=3.0)
        # Distillation loss scales with T^2
        self.assertGreater(loss_t3, 0.0)
        self.assertGreater(loss_t1, 0.0)

    def test_10_ascii_status_and_metadata(self):
        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 205: KNOWLEDGE DISTILLATION & SPARSE MODEL PRUNER", ascii_out)
        self.assertIn("Era 21 (Post-Singularity Compression)", ascii_out)


if __name__ == "__main__":
    unittest.main()
