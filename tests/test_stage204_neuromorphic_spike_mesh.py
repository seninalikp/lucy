r"""
tests/test_stage204_neuromorphic_spike_mesh.py
Stage 204: Neuromorphic Event-Driven Spike Router & Sparse Activation Mesh
Era 21: Autonomous Hyper-Scale Multi-Kernel Federation, Quantum-Resistant Keys & Post-Singularity Architecture
"""

import unittest
from backend.lucy_core.neuromorphic_spike_mesh import (
    STAGE,
    STAGE_NAME,
    ERA,
    ERA_NAME,
    SpikeEvent,
    LIFNeuron,
    Synapse,
    NeuromorphicSpikeMeshFabric,
)


class TestStage204NeuromorphicSpikeMesh(unittest.TestCase):
    """10 Unit Tests for Stage 204 Neuromorphic Spike Mesh Fabric."""

    def setUp(self):
        self.fabric = NeuromorphicSpikeMeshFabric(neuron_count=16)

    def test_01_fabric_initialization(self):
        self.assertEqual(self.fabric.neuron_count, 16)
        self.assertEqual(len(self.fabric.neurons), 16)
        self.assertEqual(self.fabric.current_timestep, 0)
        self.assertEqual(self.fabric.status()["stage"], 204)
        self.assertEqual(self.fabric.status()["era"], 21)

    def test_02_connect_synapse(self):
        syn = self.fabric.connect_synapse(pre_id=2, post_id=10, weight=0.75, delay=2)
        self.assertEqual(syn.pre_id, 2)
        self.assertEqual(syn.post_id, 10)
        self.assertEqual(syn.weight, 0.75)
        self.assertEqual(syn.delay, 2)
        self.assertIn((2, 10), self.fabric.synapses)

    def test_03_lif_subthreshold_integration_and_decay(self):
        neuron = self.fabric.neurons[0]
        # Inject small current below threshold (1.0)
        spikes = self.fabric.step_simulation(external_currents={0: 0.5})
        self.assertEqual(len(spikes), 0)
        self.assertAlmostEqual(neuron.v_membrane, 0.5, places=3)

        # Next step with no current: membrane must decay by beta (0.85)
        self.fabric.step_simulation()
        self.assertAlmostEqual(neuron.v_membrane, 0.5 * 0.85, places=3)

    def test_04_lif_spike_emission_and_reset(self):
        neuron = self.fabric.neurons[1]
        # Inject strong current exceeding threshold 1.0
        spikes = self.fabric.step_simulation(external_currents={1: 1.5})
        self.assertEqual(len(spikes), 1)
        self.assertEqual(spikes[0].source_neuron_id, 1)
        self.assertEqual(neuron.v_membrane, neuron.v_reset)
        self.assertEqual(neuron.last_spike_timestep, 1)
        self.assertEqual(neuron.total_spikes_emitted, 1)

    def test_05_synaptic_delay_propagation(self):
        # Disconnect other synapses to isolate test
        self.fabric.synapses.clear()
        self.fabric.connect_synapse(pre_id=0, post_id=1, weight=1.2, delay=2)

        # Step 1: Fire neuron 0 (external current 1.5)
        s1 = self.fabric.step_simulation(external_currents={0: 1.5})
        self.assertEqual(len(s1), 1)
        self.assertEqual(s1[0].source_neuron_id, 0)
        # Neuron 1 has not received the spike yet (delay = 2)
        self.assertEqual(self.fabric.neurons[1].v_membrane, 0.0)

        # Step 2: In-transit
        s2 = self.fabric.step_simulation()
        self.assertEqual(len(s2), 0)

        # Step 3: Spike delivered (1 + 2 = 3) -> Neuron 1 fires!
        s3 = self.fabric.step_simulation()
        self.assertEqual(len(s3), 1)
        self.assertEqual(s3[0].source_neuron_id, 1)

    def test_06_sparse_chain_cascade(self):
        # Fire neuron 0 with chain synapses of weight 1.2
        self.fabric.synapses.clear()
        self.fabric.connect_synapse(0, 1, weight=1.2, delay=1)
        self.fabric.connect_synapse(1, 2, weight=1.2, delay=1)

        # Trigger neuron 0
        self.fabric.step_simulation(external_currents={0: 1.5})
        self.assertEqual(self.fabric.neurons[0].total_spikes_emitted, 1)

        # Step 2: Neuron 1 fires
        s2 = self.fabric.step_simulation()
        self.assertEqual(len(s2), 1)
        self.assertEqual(s2[0].source_neuron_id, 1)

        # Step 3: Neuron 2 fires
        s3 = self.fabric.step_simulation()
        self.assertEqual(len(s3), 1)
        self.assertEqual(s3[0].source_neuron_id, 2)

    def test_07_stdp_long_term_potentiation(self):
        self.fabric.synapses.clear()
        syn = self.fabric.connect_synapse(0, 1, weight=0.5, delay=1)

        # Set pre-spike at t=5, post-spike at t=10 (delta_t = 5 > 0 -> Potentiation)
        self.fabric.neurons[0].last_spike_timestep = 5
        self.fabric.neurons[1].last_spike_timestep = 10

        w_new = self.fabric.apply_stdp(0, 1)
        self.assertIsNotNone(w_new)
        self.assertGreater(w_new, 0.5)

    def test_08_stdp_long_term_depression(self):
        self.fabric.synapses.clear()
        syn = self.fabric.connect_synapse(0, 1, weight=0.5, delay=1)

        # Set pre-spike at t=10, post-spike at t=5 (delta_t = -5 < 0 -> Depression)
        self.fabric.neurons[0].last_spike_timestep = 10
        self.fabric.neurons[1].last_spike_timestep = 5

        w_new = self.fabric.apply_stdp(0, 1)
        self.assertIsNotNone(w_new)
        self.assertLess(w_new, 0.5)

    def test_09_weight_bounding(self):
        self.fabric.synapses.clear()
        self.fabric.connect_synapse(0, 1, weight=0.01, delay=1)
        self.fabric.neurons[0].last_spike_timestep = 10
        self.fabric.neurons[1].last_spike_timestep = 5

        # Repeated depression should not drop below 0.0
        for _ in range(10):
            self.fabric.apply_stdp(0, 1)
        self.assertGreaterEqual(self.fabric.synapses[(0, 1)].weight, 0.0)

    def test_10_ascii_status_and_metadata(self):
        ascii_out = self.fabric.format_ascii_status()
        self.assertIn("STAGE 204: NEUROMORPHIC EVENT-DRIVEN SPIKE ROUTER & MESH", ascii_out)
        self.assertIn("LIF Neurons Active    : 16 Neurons", ascii_out)


if __name__ == "__main__":
    unittest.main()
