r"""
tests/test_stage169_distributed_deadlock_detector.py
Stage 169 Test Suite: Distributed Deadlock Detection & Chandy-Misra Sentinel
Era 17: Distributed Consensus, Mesh Virtualization & High-Availability Primitives
"""

import unittest

from backend.lucy_core.distributed_deadlock_detector import (
    CREATOR,
    ERA,
    OPERATOR,
    STAGE,
    STAGE_NAME,
    CMHProbe,
    DistributedDeadlockSentinel,
    DistributedTx,
    get_deadlock_sentinel,
)


class TestStage169DistributedDeadlockDetector(unittest.TestCase):
    def setUp(self) -> None:
        self.sentinel = DistributedDeadlockSentinel()

    def test_01_metadata_and_constants(self) -> None:
        self.assertEqual(STAGE, 169)
        self.assertEqual(ERA, 17)
        self.assertEqual(CREATOR, "Senin")
        self.assertEqual(OPERATOR, "Senin Ali K P")
        self.assertEqual(
            STAGE_NAME,
            "Distributed Deadlock Detection & Chandy-Misra Sentinel",
        )

    def test_02_tx_registration_and_properties(self) -> None:
        tx = self.sentinel.register_tx(tx_id="tx_1", node_id="node_a", priority=5)
        self.assertEqual(tx.tx_id, "tx_1")
        self.assertEqual(tx.node_id, "node_a")
        self.assertEqual(tx.priority, 5)
        self.assertFalse(tx.is_aborted)

    def test_03_resource_acquisition_uncontended(self) -> None:
        self.sentinel.register_tx(tx_id="tx_1", node_id="node_a")
        ok = self.sentinel.acquire_resource("tx_1", "res_db_users")
        self.assertTrue(ok)
        self.assertIn("res_db_users", self.sentinel.transactions["tx_1"].holding_resources)

    def test_04_resource_conflict_and_waiting(self) -> None:
        self.sentinel.register_tx(tx_id="tx_1", node_id="node_a")
        self.sentinel.register_tx(tx_id="tx_2", node_id="node_b")

        self.sentinel.acquire_resource("tx_1", "res_orders")
        ok_tx2 = self.sentinel.acquire_resource("tx_2", "res_orders")
        self.assertFalse(ok_tx2)
        self.assertEqual(self.sentinel.transactions["tx_2"].waiting_for_resource, "res_orders")

    def test_05_wfg_construction(self) -> None:
        self.sentinel.register_tx(tx_id="tx_1", node_id="node_a")
        self.sentinel.register_tx(tx_id="tx_2", node_id="node_b")

        self.sentinel.acquire_resource("tx_1", "lock_x")
        self.sentinel.acquire_resource("tx_2", "lock_x")

        wfg = self.sentinel.build_wfg()
        self.assertIn("tx_2", wfg)
        self.assertIn("tx_1", wfg["tx_2"])

    def test_06_acyclic_wfg_no_deadlock(self) -> None:
        # Linear wait: tx_3 -> tx_2 -> tx_1
        self.sentinel.register_tx("tx_1", "node_a")
        self.sentinel.register_tx("tx_2", "node_b")
        self.sentinel.register_tx("tx_3", "node_c")

        self.sentinel.acquire_resource("tx_1", "res_1")
        self.sentinel.acquire_resource("tx_2", "res_2")

        self.sentinel.acquire_resource("tx_2", "res_1")  # tx_2 waits on tx_1
        self.sentinel.acquire_resource("tx_3", "res_2")  # tx_3 waits on tx_2

        is_dl, cycle = self.sentinel.run_edge_chasing_probe("tx_3")
        self.assertFalse(is_dl)
        self.assertEqual(len(cycle), 0)

    def test_07_chandy_misra_deadlock_cycle_detection(self) -> None:
        # Create deadlock cycle: tx_1 -> tx_2 -> tx_1
        self.sentinel.register_tx("tx_1", "node_a")
        self.sentinel.register_tx("tx_2", "node_b")

        self.sentinel.acquire_resource("tx_1", "res_a")
        self.sentinel.acquire_resource("tx_2", "res_b")

        self.sentinel.acquire_resource("tx_1", "res_b")  # tx_1 waits for tx_2
        self.sentinel.acquire_resource("tx_2", "res_a")  # tx_2 waits for tx_1

        is_dl, cycle = self.sentinel.run_edge_chasing_probe("tx_1")
        self.assertTrue(is_dl)
        self.assertIn("tx_1", cycle)
        self.assertIn("tx_2", cycle)
        self.assertEqual(self.sentinel.deadlocks_detected, 1)

    def test_08_deadlock_victim_selection(self) -> None:
        # tx_high has priority 20, tx_low has priority 5
        self.sentinel.register_tx("tx_high", "node_a", priority=20)
        self.sentinel.register_tx("tx_low", "node_b", priority=5)

        self.sentinel.acquire_resource("tx_high", "lock_1")
        self.sentinel.acquire_resource("tx_low", "lock_2")

        self.sentinel.acquire_resource("tx_high", "lock_2")
        self.sentinel.acquire_resource("tx_low", "lock_1")

        is_dl, cycle = self.sentinel.run_edge_chasing_probe("tx_high")
        self.assertTrue(is_dl)

        victim = self.sentinel.resolve_deadlock(cycle)
        # Lowest priority tx_low is chosen as victim
        self.assertEqual(victim, "tx_low")
        self.assertTrue(self.sentinel.transactions["tx_low"].is_aborted)
        self.assertEqual(self.sentinel.victims_aborted, 1)

    def test_09_deadlock_recovery_resumption(self) -> None:
        self.sentinel.register_tx("tx_a", "node_a", priority=10)
        self.sentinel.register_tx("tx_b", "node_b", priority=2)

        self.sentinel.acquire_resource("tx_a", "res_x")
        self.sentinel.acquire_resource("tx_b", "res_y")

        self.sentinel.acquire_resource("tx_a", "res_y")
        self.sentinel.acquire_resource("tx_b", "res_x")

        _, cycle = self.sentinel.run_edge_chasing_probe("tx_a")
        victim = self.sentinel.resolve_deadlock(cycle)
        self.assertEqual(victim, "tx_b")

        # Now tx_a can acquire res_y because victim tx_b released it
        ok_a = self.sentinel.acquire_resource("tx_a", "res_y")
        self.assertTrue(ok_a)
        self.assertIn("res_y", self.sentinel.transactions["tx_a"].holding_resources)

    def test_10_ascii_status_and_singleton(self) -> None:
        ascii_out = self.sentinel.format_ascii_status()
        self.assertIn("LUCY STAGE 169: CHANDY-MISRA DISTRIBUTED DEADLOCK SENTINEL", ascii_out)
        self.assertIn("Senin", ascii_out)
        self.assertIn("Senin Ali K P", ascii_out)
        self.assertIn("Active Txs", ascii_out)

        s1 = get_deadlock_sentinel()
        s2 = get_deadlock_sentinel()
        self.assertIs(s1, s2)


if __name__ == "__main__":
    unittest.main()
