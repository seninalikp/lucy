r"""
tests/test_stage231_neuromorphic_spiking_fabric.py
Stage 231 Unit Tests: Neuromorphic Spiking Neural Network & Leaky Integrate-and-Fire Synaptic Fabric
"""

import threading
import unittest

from backend.lucy_core.neuromorphic_spiking_fabric import (
    LIFNeuron,
    NeuromorphicSpikingFabric,
    Synapse,
    STAGE,
    STAGE_NAME,
)


class TestStage231NeuromorphicSpikingFabric(unittest.TestCase):
    def setUp(self):
        self.fabric = NeuromorphicSpikingFabric()

    def test_01_initialization_and_metadata(self):
        s = self.fabric.status()
        self.assertEqual(s["stage"], 231)
        self.assertEqual(s["stage_name"], STAGE_NAME)
        self.assertEqual(s["total_neurons"], 8)  # 3 in, 3 hid, 2 out
        self.assertEqual(s["total_synapses"], 15)  # 9 + 6
        self.assertEqual(s["total_spikes_fired"], 0)

    def test_02_lif_subthreshold_integration_and_leak(self):
        n = LIFNeuron(neuron_id="test_n")
        # Sub-threshold input: moves from -70 towards -65
        fired = n.update(current_input=5.0, dt_ms=1.0, current_time_ms=1.0)
        self.assertFalse(fired)
        self.assertGreater(n.v_membrane, -70.0)
        self.assertLess(n.v_membrane, -55.0)

        # Passive leak with zero input: decays back towards -70
        curr_v = n.v_membrane
        n.update(current_input=0.0, dt_ms=5.0, current_time_ms=6.0)
        self.assertLess(n.v_membrane, curr_v)

    def test_03_lif_action_potential_spike_generation(self):
        n = LIFNeuron(neuron_id="spike_n", v_threshold=-55.0, v_reset=-75.0)
        # Strong suprathreshold input: dv = 200 * (2/20) = 20 mV -> V reaches -50 mV >= -55 mV
        fired = n.update(current_input=200.0, dt_ms=2.0, current_time_ms=2.0)
        self.assertTrue(fired)
        self.assertEqual(n.v_membrane, -75.0)
        self.assertEqual(n.total_spikes, 1)

    def test_04_refractory_period_enforcement(self):
        n = LIFNeuron(neuron_id="ref_n", refractory_period_ms=5.0)
        # Trigger spike with input 350 -> dv = 350 * (1/20) = 17.5 mV -> V reaches -52.5 mV >= -55 mV
        fired1 = n.update(current_input=350.0, dt_ms=1.0, current_time_ms=1.0)
        self.assertTrue(fired1)
        # Attempt to fire during refractory period: MUST NOT FIRE
        fired2 = n.update(current_input=350.0, dt_ms=1.0, current_time_ms=2.0)
        self.assertFalse(fired2)
        self.assertEqual(n.total_spikes, 1)

    def test_05_stdp_long_term_potentiation(self):
        syn = Synapse(synapse_id="s1", source_id="pre", target_id="post", weight=1.0)
        # Pre fired at 10.0 ms, Post fired at 15.0 ms (Delta_t = +5 ms -> LTP)
        new_w = syn.apply_stdp(pre_spike_time=10.0, post_spike_time=15.0)
        self.assertGreater(new_w, 1.0)

    def test_06_stdp_long_term_depression(self):
        syn = Synapse(synapse_id="s2", source_id="pre", target_id="post", weight=2.0)
        # Pre fired at 20.0 ms, Post fired at 15.0 ms (Delta_t = -5 ms -> LTD)
        new_w = syn.apply_stdp(pre_spike_time=20.0, post_spike_time=15.0)
        self.assertLess(new_w, 2.0)

    def test_07_propagating_spikes_across_synapses(self):
        # Inject strong current into in_0 to cause spike
        spikes = []
        for _ in range(15):
            fired = self.fabric.step(input_currents={"in_0": 40.0})
            spikes.extend(fired)
        self.assertIn("in_0", spikes)
        self.assertGreater(self.fabric.total_spikes_fired, 0)

    def test_08_run_simulation_telemetry(self):
        res = self.fabric.run_simulation(duration_ms=25.0, input_schedule={"in_1": 35.0})
        self.assertEqual(res["duration_ms"], 25.0)
        self.assertGreaterEqual(res["spikes_fired_count"], 1)
        self.assertGreater(res["firing_rate_hz"], 0.0)

    def test_09_cp1252_safe_ascii_table(self):
        tbl = self.fabric.format_ascii_status()
        self.assertIn("STAGE 231", tbl)
        self.assertIn("NEUROMORPHIC SPIKING NEURAL NETWORK", tbl)
        tbl.encode("cp1252")
        self.assertTrue(tbl.startswith("+--"))

    def test_10_multithreaded_concurrency(self):
        def worker(wid: int):
            for _ in range(5):
                _ = self.fabric.step(input_currents={f"in_{wid % 3}": 25.0})
            _ = self.fabric.status()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertGreater(self.fabric.current_time_ms, 0.0)


if __name__ == "__main__":
    unittest.main()
