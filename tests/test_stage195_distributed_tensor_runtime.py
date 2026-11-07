r"""
tests/test_stage195_distributed_tensor_runtime.py
Stage 195: Autonomous Neural Weights Sharder & Distributed Tensor Runtime
Era 20: The Sovereign Bicentennial AGI Singularity & Autonomous Kernel Transcendence
"""

import unittest
from backend.lucy_core.distributed_tensor_runtime import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    ShardingStrategy,
    TensorShard,
    ActivationCheckpoint,
    DistributedTensorRuntimeFabric,
)


class TestStage195DistributedTensorRuntime(unittest.TestCase):
    """10 Unit Tests for Stage 195 Distributed Tensor Runtime Fabric."""

    def setUp(self):
        self.fabric = DistributedTensorRuntimeFabric(world_size=4)

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric.world_size, 4)
        self.assertEqual(len(self.fabric.sharded_weights), 0)
        self.assertEqual(len(self.fabric.checkpoints), 0)
        with self.assertRaises(ValueError):
            DistributedTensorRuntimeFabric(world_size=1)

    def test_02_replicated_weight_sharding(self):
        matrix = [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
        shards = self.fabric.shard_weight_matrix("w_replicated", matrix, ShardingStrategy.REPLICATED)
        self.assertEqual(len(shards), 4)
        for rank in range(4):
            self.assertEqual(shards[rank].data, matrix)
            self.assertEqual(shards[rank].shard_shape, (2, 2))

    def test_03_row_parallel_weight_sharding(self):
        # 4x2 matrix split across 4 ranks -> 1x2 per rank
        matrix = [
            [1.0, 10.0],
            [2.0, 20.0],
            [3.0, 30.0],
            [4.0, 40.0],
        ]
        shards = self.fabric.shard_weight_matrix("w_row", matrix, ShardingStrategy.ROW_PARALLEL)
        self.assertEqual(len(shards), 4)
        self.assertEqual(shards[0].shard_shape, (1, 2))
        self.assertEqual(shards[0].data, [[1.0, 10.0]])
        self.assertEqual(shards[3].data, [[4.0, 40.0]])

    def test_04_column_parallel_weight_sharding(self):
        # 2x4 matrix split across 4 ranks -> 2x1 per rank
        matrix = [
            [1.0, 2.0, 3.0, 4.0],
            [10.0, 20.0, 30.0, 40.0],
        ]
        shards = self.fabric.shard_weight_matrix("w_col", matrix, ShardingStrategy.COLUMN_PARALLEL)
        self.assertEqual(len(shards), 4)
        self.assertEqual(shards[0].shard_shape, (2, 1))
        self.assertEqual(shards[0].data, [[1.0], [10.0]])
        self.assertEqual(shards[3].data, [[4.0], [40.0]])

    def test_05_sharding_dimension_divisibility_guard(self):
        # 3 rows cannot be evenly row-sharded across 4 ranks
        matrix = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        with self.assertRaises(ValueError):
            self.fabric.shard_weight_matrix("bad_row", matrix, ShardingStrategy.ROW_PARALLEL)

        # 3 cols cannot be evenly col-sharded across 4 ranks
        matrix2 = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0], [10.0, 11.0, 12.0]]
        with self.assertRaises(ValueError):
            self.fabric.shard_weight_matrix("bad_col", matrix2, ShardingStrategy.COLUMN_PARALLEL)

    def test_06_ring_allreduce_collective_sum(self):
        # 4 ranks, each has 4 elements
        rank_data = {
            0: [1.0, 2.0, 3.0, 4.0],
            1: [10.0, 20.0, 30.0, 40.0],
            2: [100.0, 200.0, 300.0, 400.0],
            3: [1000.0, 2000.0, 3000.0, 4000.0],
        }
        res = self.fabric.ring_allreduce(rank_data)
        self.assertEqual(len(res), 4)
        expected = [1111.0, 2222.0, 3333.0, 4444.0]
        for r in range(4):
            self.assertEqual(res[r], expected)

    def test_07_ring_allreduce_validation_guards(self):
        # Mismatched rank count
        with self.assertRaises(ValueError):
            self.fabric.ring_allreduce({0: [1.0], 1: [2.0]})

        # Mismatched tensor length
        with self.assertRaises(ValueError):
            self.fabric.ring_allreduce({
                0: [1.0, 2.0],
                1: [3.0, 4.0],
                2: [5.0, 6.0],
                3: [7.0, 8.0, 9.0],
            })

    def test_08_activation_checkpoint_and_recompute(self):
        anchor = [0.5, 1.5, 2.5]
        cid = self.fabric.checkpoint_activation(stage_id=2, step=10, anchor_data=anchor)
        self.assertEqual(cid, 1)

        def recompute_layer(x: list[float]) -> list[float]:
            return [val * 2.0 for val in x]

        out = self.fabric.recompute_activation(cid, recompute_layer)
        self.assertEqual(out, [1.0, 3.0, 5.0])
        self.assertEqual(self.fabric._recomputations_count, 1)

    def test_09_1f1b_pipeline_execution(self):
        micro_batches = [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
        results = self.fabric.execute_1f1b_pipeline(micro_batches, pipeline_stages=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(self.fabric._pipeline_executions_count, 1)

    def test_10_ascii_status_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 195)
        self.assertEqual(s["era"], 20)
        self.assertEqual(s["world_size"], 4)

        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 195: AUTONOMOUS NEURAL WEIGHTS SHARDER & TENSOR RUNTIME", ascii_out)
        self.assertIn("Virtual Ranks (World) : 4", ascii_out)


if __name__ == "__main__":
    unittest.main()
