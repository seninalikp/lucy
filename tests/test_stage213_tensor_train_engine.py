r"""
tests/test_stage213_tensor_train_engine.py
Stage 213: Autonomous Tensor-Train Decomposer & Quantum Tensor Network Contraction Engine
Era 22: Autonomous Galactic Hyper-Mesh, Hardware-Accelerated Photonic Emulation & Trans-Universal Reasoning Fabrics
"""

import math
import unittest
from backend.lucy_core.tensor_train_engine import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    TTCore,
    TensorTrain,
    TensorTrainEngineFabric,
)


class TestStage213TensorTrainEngine(unittest.TestCase):
    """10 Unit Tests for Stage 213 Tensor-Train Engine Fabric."""

    def setUp(self):
        self.fabric = TensorTrainEngineFabric()

    def test_01_fabric_initialization(self):
        self.assertEqual(STAGE, 213)
        self.assertEqual(ERA, 22)
        self.assertEqual(self.fabric.decompositions_count, 0)
        self.assertEqual(self.fabric.contractions_count, 0)
        self.assertEqual(self.fabric.status()["stage"], 213)

    def test_02_create_canonical_rank1_tt(self):
        tt = self.fabric.create_canonical_rank1_tt(mode_dims=[2, 3, 4], scaling=8.0)
        self.assertEqual(len(tt.cores), 3)
        self.assertEqual(tt.mode_dimensions, [2, 3, 4])
        self.assertEqual(tt.ranks, [1, 1, 1, 1])

    def test_03_tt_core_slice_mode(self):
        data = [[[1.0, 2.0]], [[3.0, 4.0]]]  # Shape (2, 1, 2)
        core = TTCore(r_left=2, n_k=1, r_right=2, data=data)
        slice_mat = core.slice_mode(0)
        self.assertEqual(len(slice_mat), 2)
        self.assertEqual(len(slice_mat[0]), 2)
        self.assertEqual(slice_mat[0][1], 2.0)
        self.assertEqual(slice_mat[1][0], 3.0)

    def test_04_evaluate_element_rank1(self):
        # Rank-1 uniform with scaling = 1.0 (all 1.0)
        tt = self.fabric.create_canonical_rank1_tt(mode_dims=[2, 2, 2], scaling=1.0)
        val = tt.evaluate_element([0, 1, 0])
        self.assertAlmostEqual(val, 1.0, places=4)

    def test_05_evaluate_element_dimension_mismatch(self):
        tt = self.fabric.create_canonical_rank1_tt(mode_dims=[2, 2], scaling=1.0)
        with self.assertRaises(ValueError):
            tt.evaluate_element([0, 1, 0])  # 3 indices for 2-dim tensor

    def test_06_create_structured_tt_multi_rank(self):
        tt = self.fabric.create_structured_tt(mode_dims=[3, 4, 3], rank=3)
        self.assertEqual(len(tt.cores), 3)
        self.assertEqual(tt.ranks, [1, 3, 3, 1])
        # Element evaluation produces finite number
        val = tt.evaluate_element([1, 2, 0])
        self.assertIsInstance(val, float)
        self.assertGreater(val, 0.0)

    def test_07_inner_product_identical_norm(self):
        tt = self.fabric.create_canonical_rank1_tt(mode_dims=[2, 2], scaling=2.0)
        ip = tt.inner_product(tt)
        fn = tt.frobenius_norm()
        self.assertAlmostEqual(fn ** 2, ip, places=4)

    def test_08_inner_product_mode_mismatch(self):
        tt_a = self.fabric.create_canonical_rank1_tt(mode_dims=[2, 2])
        tt_b = self.fabric.create_canonical_rank1_tt(mode_dims=[3, 3])
        with self.assertRaises(ValueError):
            tt_a.inner_product(tt_b)

    def test_09_fabric_contraction_counter(self):
        tt1 = self.fabric.create_canonical_rank1_tt(mode_dims=[2, 3])
        tt2 = self.fabric.create_canonical_rank1_tt(mode_dims=[2, 3])
        res = self.fabric.contract_inner_product(tt1, tt2)
        self.assertIsInstance(res, float)
        self.assertEqual(self.fabric.contractions_count, 1)

    def test_10_ascii_status_formatting(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 213: TENSOR-TRAIN DECOMPOSER & MPS CONTRACTION ENGINE", tbl)
        self.assertIn("Active TT Networks", tbl)
        self.assertIn("Matrix Product State (MPS) Chain SVD Truncation", tbl)


if __name__ == "__main__":
    unittest.main()
