r"""
tests/test_stage203_sovereign_contract_engine.py
Stage 203: Autonomous Decentralized Sovereign Contract & State Verifier
Era 21: Autonomous Hyper-Scale Multi-Kernel Federation, Quantum-Resistant Keys & Post-Singularity Architecture
"""

import unittest
from backend.lucy_core.sovereign_contract_engine import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    ContractInstruction,
    ExecutionResult,
    SovereignContract,
    SovereignContractEngineFabric,
)


class TestStage203SovereignContractEngine(unittest.TestCase):
    """10 Unit Tests for Stage 203 Sovereign Contract Engine Fabric."""

    def setUp(self):
        self.fabric = SovereignContractEngineFabric()

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric.sovereign_operator, "Senin")
        self.assertEqual(len(self.fabric.contracts), 0)
        self.assertEqual(self.fabric.status()["stage"], 203)
        self.assertEqual(self.fabric.status()["era"], 21)

    def test_02_contract_deployment(self):
        code = [
            ContractInstruction("PUSH", 10),
            ContractInstruction("PUSH", 20),
            ContractInstruction("ADD"),
            ContractInstruction("RETURN"),
        ]
        cid = self.fabric.deploy_contract("Senin", code, initial_storage={"balance": 100})
        self.assertIn(cid, self.fabric.contracts)
        c = self.fabric.contracts[cid]
        self.assertEqual(c.owner, "Senin")
        self.assertEqual(c.storage["balance"], 100)

    def test_03_execute_arithmetic_computation(self):
        code = [
            ContractInstruction("PUSH", 5),
            ContractInstruction("PUSH", 3),
            ContractInstruction("MUL"),
            ContractInstruction("RETURN"),
        ]
        cid = self.fabric.deploy_contract("Senin", code)
        res = self.fabric.execute_contract(cid, caller="Senin", input_args=[])
        self.assertTrue(res.success)
        self.assertEqual(res.output, 15)
        self.assertGreater(res.gas_consumed, 0)

    def test_04_execute_storage_store_and_load(self):
        code = [
            # stack: [key, val] -> STORE -> storage[key] = val
            ContractInstruction("PUSH", 500),      # val
            ContractInstruction("PUSH", "points"),  # key
            ContractInstruction("STORE"),
            # LOAD points
            ContractInstruction("PUSH", "points"),
            ContractInstruction("LOAD"),
            ContractInstruction("RETURN"),
        ]
        cid = self.fabric.deploy_contract("Senin", code)
        res = self.fabric.execute_contract(cid, caller="Senin", input_args=[])
        self.assertTrue(res.success)
        self.assertEqual(res.output, 500)
        self.assertEqual(self.fabric.contracts[cid].storage.get("points"), 500)

    def test_05_state_hash_commitment_verification(self):
        code = [
            ContractInstruction("PUSH", 42),
            ContractInstruction("PUSH", "data"),
            ContractInstruction("STORE"),
            ContractInstruction("RETURN"),
        ]
        cid = self.fabric.deploy_contract("Senin", code)
        ok1, h1 = self.fabric.verify_contract_state(cid)
        self.assertTrue(ok1)

        self.fabric.execute_contract(cid, "Senin", [])
        ok2, h2 = self.fabric.verify_contract_state(cid)
        self.assertTrue(ok2)
        self.assertNotEqual(h1, h2)  # Storage updated -> hash must change

    def test_06_division_by_zero_protection(self):
        code = [
            ContractInstruction("PUSH", 10),
            ContractInstruction("PUSH", 0),
            ContractInstruction("DIV"),
            ContractInstruction("RETURN"),
        ]
        cid = self.fabric.deploy_contract("Senin", code)
        res = self.fabric.execute_contract(cid, "Senin", [])
        self.assertFalse(res.success)
        self.assertIn("Division by zero", res.error)

    def test_07_stack_underflow_protection(self):
        code = [
            ContractInstruction("ADD"),  # Needs 2 operands, stack empty
            ContractInstruction("RETURN"),
        ]
        cid = self.fabric.deploy_contract("Senin", code)
        res = self.fabric.execute_contract(cid, "Senin", [])
        self.assertFalse(res.success)
        self.assertIn("underflow", res.error)

    def test_08_gas_metering_out_of_gas_limit(self):
        code = [
            ContractInstruction("PUSH", 1),
            ContractInstruction("PUSH", 2),
            ContractInstruction("ADD"),
            ContractInstruction("PUSH", 3),
            ContractInstruction("MUL"),
            ContractInstruction("RETURN"),
        ]
        cid = self.fabric.deploy_contract("Senin", code)
        # Limit gas to 2 ops (code needs 6)
        res = self.fabric.execute_contract(cid, "Senin", [], gas_limit=2)
        self.assertFalse(res.success)
        self.assertIn("Out of gas", res.error)

    def test_09_assertion_opcode_enforcement(self):
        # 10 == 20 is False -> ASSERT fails
        code = [
            ContractInstruction("PUSH", 10),
            ContractInstruction("PUSH", 20),
            ContractInstruction("EQ"),
            ContractInstruction("ASSERT", "values must match"),
            ContractInstruction("RETURN"),
        ]
        cid = self.fabric.deploy_contract("Senin", code)
        res = self.fabric.execute_contract(cid, "Senin", [])
        self.assertFalse(res.success)
        self.assertIn("Assertion failed", res.error)

    def test_10_ascii_status_and_metadata(self):
        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 203: SOVEREIGN CONTRACT ENGINE & STATE VERIFIER", ascii_out)
        self.assertIn("Sovereign Operator    : Senin", ascii_out)
        self.assertIn("Era 21 (Post-Singularity Autonomous Contracts)", ascii_out)


if __name__ == "__main__":
    unittest.main()
