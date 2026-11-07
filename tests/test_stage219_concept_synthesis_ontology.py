r"""
tests/test_stage219_concept_synthesis_ontology.py
Stage 219: Continuous Self-Supervised Concept Synthesis & Autonomous Ontology Evolution Engine
Era 22: Autonomous Galactic Hyper-Mesh, Hardware-Accelerated Photonic Emulation & Trans-Universal Reasoning Fabrics
"""

import unittest
from backend.lucy_core.concept_synthesis_ontology import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    ConceptNode,
    ConceptSynthesisOntologyFabric,
    OntologyEdge,
    RelationType,
)


class TestStage219ConceptSynthesisOntology(unittest.TestCase):
    """10 Unit Tests for Stage 219 Concept Synthesis Ontology Fabric."""

    def setUp(self):
        self.fabric = ConceptSynthesisOntologyFabric()

    def test_01_fabric_initialization(self):
        self.assertEqual(STAGE, 219)
        self.assertEqual(ERA, 22)
        self.assertEqual(len(self.fabric.concepts), 0)
        self.assertEqual(len(self.fabric.edges), 0)
        self.assertEqual(self.fabric.status()["stage"], 219)

    def test_02_add_concept_id_deterministic(self):
        c1 = self.fabric.add_concept("Quantum Processor", category="hardware")
        c2 = self.fabric.add_concept("quantum processor", category="hardware")
        self.assertEqual(c1.concept_id, c2.concept_id)
        self.assertEqual(c1.name, "Quantum Processor")

    def test_03_add_relation_typing(self):
        c_core = self.fabric.add_concept("Qubit Core")
        c_proc = self.fabric.add_concept("Quantum Processor")
        edge = self.fabric.add_relation(c_core.concept_id, c_proc.concept_id, RelationType.PART_OF, weight=0.95)
        self.assertEqual(edge.relation, RelationType.PART_OF)
        self.assertIn(edge.edge_id, self.fabric.edges)

    def test_04_query_ancestors_direct(self):
        c_dog = self.fabric.add_concept("Dog")
        c_canine = self.fabric.add_concept("Canine")
        self.fabric.add_relation(c_dog.concept_id, c_canine.concept_id, RelationType.IS_A)

        anc = self.fabric.query_ancestors(c_dog.concept_id)
        self.assertEqual(anc, [c_canine.concept_id])

    def test_05_query_ancestors_transitive_multihop(self):
        # A IS_A B, B IS_A C, C IS_A D
        cA = self.fabric.add_concept("Falcon9")
        cB = self.fabric.add_concept("Rocket")
        cC = self.fabric.add_concept("LaunchVehicle")
        cD = self.fabric.add_concept("Spacecraft")

        self.fabric.add_relation(cA.concept_id, cB.concept_id, RelationType.IS_A)
        self.fabric.add_relation(cB.concept_id, cC.concept_id, RelationType.IS_A)
        self.fabric.add_relation(cC.concept_id, cD.concept_id, RelationType.IS_A)

        anc = self.fabric.query_ancestors(cA.concept_id)
        self.assertEqual(len(anc), 3)
        self.assertIn(cB.concept_id, anc)
        self.assertIn(cC.concept_id, anc)
        self.assertIn(cD.concept_id, anc)

    def test_06_synthesize_higher_order_concept(self):
        c1 = self.fabric.add_concept("Neural Spiking Engine")
        c2 = self.fabric.add_concept("Photonic Core")
        meta = self.fabric.synthesize_higher_order_concept(
            [c1.concept_id, c2.concept_id], "Neuromorphic Photonic Substrate"
        )
        self.assertIsNotNone(meta)
        self.assertEqual(meta.name, "Neuromorphic Photonic Substrate")
        self.assertEqual(self.fabric.syntheses_count, 1)

        # Verify cluster elements have IS_A meta
        anc1 = self.fabric.query_ancestors(c1.concept_id)
        anc2 = self.fabric.query_ancestors(c2.concept_id)
        self.assertIn(meta.concept_id, anc1)
        self.assertIn(meta.concept_id, anc2)

    def test_07_prune_contradictions_cycle_elimination(self):
        # A IS_A B (weight 1.0) and B IS_A A (weight 0.4) -> Contradiction!
        cA = self.fabric.add_concept("Agent")
        cB = self.fabric.add_concept("Program")
        e_fwd = self.fabric.add_relation(cA.concept_id, cB.concept_id, RelationType.IS_A, weight=1.0)
        e_rev = self.fabric.add_relation(cB.concept_id, cA.concept_id, RelationType.IS_A, weight=0.4)

        self.assertEqual(len(self.fabric.edges), 2)
        pruned_count = self.fabric.prune_contradictions()
        self.assertEqual(pruned_count, 1)
        self.assertEqual(len(self.fabric.edges), 1)
        # Kept the stronger edge e_fwd
        self.assertIn(e_fwd.edge_id, self.fabric.edges)
        self.assertNotIn(e_rev.edge_id, self.fabric.edges)

    def test_08_no_contradiction_on_acyclic(self):
        c1 = self.fabric.add_concept("Subsystem")
        c2 = self.fabric.add_concept("System")
        self.fabric.add_relation(c1.concept_id, c2.concept_id, RelationType.PART_OF)
        pruned = self.fabric.prune_contradictions()
        self.assertEqual(pruned, 0)
        self.assertEqual(len(self.fabric.edges), 1)

    def test_09_status_metrics(self):
        self.fabric.add_concept("Entity Alpha")
        s = self.fabric.status()
        self.assertEqual(s["total_concepts"], 1)
        self.assertEqual(s["total_edges"], 0)

    def test_10_ascii_status_formatting(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 219: SELF-EVOLVING CONCEPT SYNTHESIS & ONTOLOGY ENGINE", tbl)
        self.assertIn("Concept Nodes (DAG)", tbl)
        self.assertIn("Autonomous Dynamic Taxonomical Evolution", tbl)


if __name__ == "__main__":
    unittest.main()
