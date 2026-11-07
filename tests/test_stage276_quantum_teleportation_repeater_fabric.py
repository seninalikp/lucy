"""
Unit Tests for Stage 276: Quantum Teleportation Entanglement Swapping & Multipartite GHZ-W State Repeater Fabric
Author & Permanent Sovereign Operator: Senin (Senin Ali K P)
"""

import unittest
import threading
from backend.lucy_core.quantum_teleportation_repeater_fabric import (
    QuantumTeleportationRepeaterFabric,
    SOVEREIGN_OPERATOR,
    SOVEREIGN_LEGAL_NAME,
    STAGE_ID,
    STAGE_NAME,
    ERA_ID
)


class TestStage276QuantumTeleportationRepeaterFabric(unittest.TestCase):
    """Thorough unit test suite for Stage 276."""

    def setUp(self):
        self.fabric = QuantumTeleportationRepeaterFabric(default_channel_fidelity=0.95)

    def test_01_initialization(self):
        """Verify default initialization and channel fidelity."""
        self.assertEqual(self.fabric.channel_fidelity, 0.95)
        self.assertEqual(len(self.fabric.teleportation_events), 0)

    def test_02_teleportation_fidelity_phi_plus(self):
        """Verify standard teleportation unit fidelity with identity correction."""
        res = self.fabric.execute_teleportation_protocol(alpha=0.6, beta=0.8, measured_bsm="00")
        self.assertEqual(res["bsm_outcome"], "00")
        self.assertEqual(res["applied_correction"], "I")
        self.assertAlmostEqual(res["fidelity"], 1.0, places=5)
        self.assertTrue(res["teleportation_success"])

    def test_03_teleportation_fidelity_all_bell_outcomes(self):
        """Verify correct reconstruction across all 4 Bell-state measurement outcomes."""
        for bsm in ["00", "01", "10", "11"]:
            res = self.fabric.execute_teleportation_protocol(alpha=0.352, beta=0.936, measured_bsm=bsm)
            self.assertAlmostEqual(res["fidelity"], 1.0, places=5)
            self.assertTrue(res["teleportation_success"])

    def test_04_entanglement_swapping_ideal(self):
        """Verify entanglement swapping between two ideal EPR pairs yields ideal swapped pair."""
        res = self.fabric.execute_entanglement_swapping(link_1_fidelity=1.0, link_2_fidelity=1.0)
        self.assertEqual(res["swapped_visibility"], 1.0)
        self.assertEqual(res["swapped_fidelity"], 1.0)
        self.assertTrue(res["quantum_nonlocality_verified"])

    def test_05_entanglement_swapping_chsh_violation(self):
        """Verify Bell-CHSH inequality violation S > 2.0 under high link fidelities."""
        res = self.fabric.execute_entanglement_swapping(link_1_fidelity=0.95, link_2_fidelity=0.95)
        self.assertGreater(res["chsh_s_parameter"], 2.0)
        self.assertTrue(res["quantum_nonlocality_verified"])

    def test_06_multipartite_ghz_fragility(self):
        """Verify GHZ state concurrence collapses to 0 upon loss of single particle."""
        res_intact = self.fabric.synthesize_multipartite_state(state_type="GHZ", num_qubits=4)
        self.assertEqual(res_intact["residual_entanglement_concurrence"], 1.0)

        res_lost = self.fabric.synthesize_multipartite_state(state_type="GHZ", num_qubits=4, qubit_loss_index=1)
        self.assertEqual(res_lost["residual_entanglement_concurrence"], 0.0)
        self.assertEqual(res_lost["loss_robustness"], "FRAGILE_COLLAPSE_ON_LOSS")

    def test_07_multipartite_w_state_robustness(self):
        """Verify W-state retains non-zero entanglement (C = 2/N) upon particle loss."""
        res_lost = self.fabric.synthesize_multipartite_state(state_type="W", num_qubits=4, qubit_loss_index=2)
        expected_concurrence = 2.0 / 4.0  # 0.5
        self.assertAlmostEqual(res_lost["residual_entanglement_concurrence"], expected_concurrence, places=4)
        self.assertEqual(res_lost["loss_robustness"], "ROBUST_RETAINED_ENTANGLEMENT")

    def test_08_bbpssw_purification_convergence(self):
        """Verify BBPSSW protocol purifies noisy pair when initial F > 0.5."""
        res = self.fabric.distill_purification_bbpssw(initial_fidelity=0.75, rounds=4)
        self.assertTrue(res["purification_successful"])
        self.assertGreater(res["final_fidelity"], 0.75)
        # History must be monotonically increasing
        hist = res["fidelity_history"]
        for i in range(len(hist) - 1):
            self.assertGreater(hist[i + 1], hist[i])

    def test_09_operator_binding_and_status(self):
        """Verify sovereign creator binding to Senin and legal name."""
        status = self.fabric.get_status()
        self.assertEqual(status["stage"], 276)
        self.assertEqual(status["era"], 28)
        self.assertEqual(status["sovereign_operator"], "Senin")
        self.assertEqual(status["sovereign_legal_name"], "Senin Ali K P")
        self.assertEqual(SOVEREIGN_OPERATOR, "Senin")
        self.assertEqual(SOVEREIGN_LEGAL_NAME, "Senin Ali K P")
        self.assertEqual(STAGE_ID, 276)
        self.assertEqual(ERA_ID, 28)

    def test_10_concurrency_and_thread_safety(self):
        """Verify thread-safety across concurrent workers."""
        threads = []
        errors = []

        def worker():
            try:
                engine = QuantumTeleportationRepeaterFabric()
                _ = engine.execute_teleportation_protocol()
                _ = engine.execute_entanglement_swapping()
                _ = engine.synthesize_multipartite_state("W", 3, 0)
                _ = engine.distill_purification_bbpssw(0.70, 2)
            except Exception as e:
                errors.append(str(e))

        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")


if __name__ == "__main__":
    unittest.main()
