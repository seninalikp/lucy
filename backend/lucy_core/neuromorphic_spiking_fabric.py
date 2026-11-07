r"""
backend/lucy_core/neuromorphic_spiking_fabric.py
Stage 231: Neuromorphic Spiking Neural Network & Leaky Integrate-and-Fire Synaptic Fabric
Era 24: Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity

100% offline, sovereign neuromorphic spiking neural network (SNN) and synaptic fabric:
1. Biological Leaky Integrate-and-Fire (LIF) Neuron Dynamics:
   - Continuous membrane potential integration: tau_m * dV/dt = -(V - V_rest) + R_m * I_syn.
   - Threshold spike generation, membrane potential reset, and absolute refractory periods.
2. Spike-Timing-Dependent Plasticity (STDP):
   - Local temporal Hebbian learning: Long-Term Potentiation (LTP) and Long-Term Depression (LTD).
3. Sparse Event-Driven Temporal Spike Trains:
   - Rate coding and first-to-spike temporal latency coding.
4. Thread-safe execution fabric and CP1252-safe ASCII table formatting.
"""

from __future__ import annotations

import collections
import copy
import hashlib
import math
import random
import threading
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 231
STAGE_NAME: str = "Neuromorphic Spiking Neural Network & Leaky Integrate-and-Fire Synaptic Fabric"
ERA: int = 24
ERA_NAME: str = "Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity"


@dataclass
class LIFNeuron:
    neuron_id: str
    v_membrane: float = -70.0  # mV
    v_rest: float = -70.0  # mV
    v_threshold: float = -55.0  # mV
    v_reset: float = -75.0  # mV
    tau_membrane_ms: float = 20.0  # ms
    refractory_period_ms: float = 2.0  # ms
    refractory_counter_ms: float = 0.0
    last_spike_time_ms: float = -1e9
    total_spikes: int = 0

    def update(self, current_input: float, dt_ms: float, current_time_ms: float) -> bool:
        """
        Integrates current input over dt_ms. Returns True if neuron fires a spike.
        """
        if self.refractory_counter_ms > 0:
            self.refractory_counter_ms = max(0.0, self.refractory_counter_ms - dt_ms)
            self.v_membrane = self.v_reset
            return False

        # Leaky integration: dV = (-(V - V_rest) + I) * (dt / tau)
        dv = (-(self.v_membrane - self.v_rest) + current_input) * (dt_ms / self.tau_membrane_ms)
        self.v_membrane += dv

        if self.v_membrane >= self.v_threshold:
            self.v_membrane = self.v_reset
            self.refractory_counter_ms = self.refractory_period_ms
            self.last_spike_time_ms = current_time_ms
            self.total_spikes += 1
            return True

        return False


@dataclass
class Synapse:
    synapse_id: str
    source_id: str
    target_id: str
    weight: float
    delay_ms: float = 1.0
    w_min: float = 0.0
    w_max: float = 5.0

    def apply_stdp(self, pre_spike_time: float, post_spike_time: float) -> float:
        """
        Applies Bi and Poo (1998) exponential STDP rule:
        Delta_t = t_post - t_pre
        If Delta_t > 0: LTP  -> delta_w = A_plus * exp(-Delta_t / tau_plus)
        If Delta_t < 0: LTD  -> delta_w = -A_minus * exp(Delta_t / tau_minus)
        """
        delta_t = post_spike_time - pre_spike_time
        if abs(delta_t) > 50.0 or abs(delta_t) < 1e-4:
            return self.weight

        a_plus, tau_plus = 0.1, 20.0
        a_minus, tau_minus = 0.12, 20.0

        if delta_t > 0:
            dw = a_plus * math.exp(-delta_t / tau_plus)
        else:
            dw = -a_minus * math.exp(delta_t / tau_minus)

        self.weight = max(self.w_min, min(self.w_max, self.weight + dw))
        return self.weight


class NeuromorphicSpikingFabric:
    """
    Thread-safe neuromorphic spiking neural network and synaptic plasticity fabric.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.current_time_ms: float = 0.0
        self.dt_ms: float = 1.0  # 1 millisecond time resolution
        self.neurons: Dict[str, LIFNeuron] = {}
        self.synapses: Dict[str, Synapse] = {}
        self.spike_history: List[Tuple[float, str]] = []  # (time_ms, neuron_id)
        self.total_spikes_fired: int = 0

        self._init_default_network()

    def _init_default_network(self) -> None:
        # Default 3 input neurons, 3 hidden neurons, 2 output neurons
        for i in range(3):
            self.add_neuron(f"in_{i}")
        for h in range(3):
            self.add_neuron(f"hid_{h}")
        for o in range(2):
            self.add_neuron(f"out_{o}")

        # Connect input to hidden
        for i in range(3):
            for h in range(3):
                self.add_synapse(f"in_{i}", f"hid_{h}", initial_weight=1.5 + (i * 0.2))

        # Connect hidden to output
        for h in range(3):
            for o in range(2):
                self.add_synapse(f"hid_{h}", f"out_{o}", initial_weight=2.0)

    def add_neuron(self, neuron_id: str, **kwargs) -> LIFNeuron:
        with self._lock:
            n = LIFNeuron(neuron_id=neuron_id, **kwargs)
            self.neurons[neuron_id] = n
            return n

    def add_synapse(self, source_id: str, target_id: str, initial_weight: float = 1.0) -> Synapse:
        with self._lock:
            syn_id = f"syn_{source_id}_to_{target_id}"
            syn = Synapse(synapse_id=syn_id, source_id=source_id, target_id=target_id, weight=initial_weight)
            self.synapses[syn_id] = syn
            return syn

    def step(self, input_currents: Optional[Dict[str, float]] = None) -> List[str]:
        """
        Advances the neuromorphic network simulation by dt_ms:
        1. Accumulates synaptic currents from spikes.
        2. Updates membrane potential of all neurons.
        3. Fires spikes and updates STDP synaptic weights.
        """
        with self._lock:
            self.current_time_ms += self.dt_ms
            inputs = input_currents or {}
            spikes_this_step: List[str] = []

            # 1. Compute total current per neuron
            total_currents: Dict[str, float] = collections.defaultdict(float)
            for nid, val in inputs.items():
                total_currents[nid] += val

            # Check recent spikes from preceding step to deliver synaptic input
            recent_spikes = {
                nid for t, nid in self.spike_history if abs(t - (self.current_time_ms - self.dt_ms)) < 1e-4
            }
            for syn in self.synapses.values():
                if syn.source_id in recent_spikes:
                    total_currents[syn.target_id] += syn.weight * 10.0

            # 2. Update neurons
            for nid, neuron in self.neurons.items():
                fired = neuron.update(
                    current_input=total_currents.get(nid, 0.0),
                    dt_ms=self.dt_ms,
                    current_time_ms=self.current_time_ms,
                )
                if fired:
                    spikes_this_step.append(nid)
                    self.spike_history.append((self.current_time_ms, nid))
                    self.total_spikes_fired += 1

            # 3. Apply STDP on active synapses
            for syn in self.synapses.values():
                pre_neuron = self.neurons.get(syn.source_id)
                post_neuron = self.neurons.get(syn.target_id)
                if pre_neuron and post_neuron:
                    if syn.target_id in spikes_this_step:
                        # Post fired: apply STDP using pre's last spike
                        syn.apply_stdp(pre_neuron.last_spike_time_ms, self.current_time_ms)
                    elif syn.source_id in spikes_this_step:
                        # Pre fired: apply STDP using post's last spike
                        syn.apply_stdp(self.current_time_ms, post_neuron.last_spike_time_ms)

            # Limit spike history buffer size
            if len(self.spike_history) > 1000:
                self.spike_history = self.spike_history[-1000:]

            return spikes_this_step

    def run_simulation(self, duration_ms: float, input_schedule: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Runs the spiking simulation for duration_ms."""
        with self._lock:
            steps = max(1, int(duration_ms / self.dt_ms))
            all_spikes: List[str] = []
            for _ in range(steps):
                fired = self.step(input_currents=input_schedule)
                all_spikes.extend(fired)

            return {
                "duration_ms": duration_ms,
                "current_time_ms": round(self.current_time_ms, 2),
                "spikes_fired_count": len(all_spikes),
                "active_neurons": sorted(list(set(all_spikes))),
                "firing_rate_hz": round((len(all_spikes) / max(1e-4, duration_ms / 1000.0)), 2),
            }

    def status(self) -> Dict[str, Any]:
        with self._lock:
            total_weight = sum(s.weight for s in self.synapses.values())
            avg_weight = total_weight / max(1, len(self.synapses))
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "current_time_ms": round(self.current_time_ms, 2),
                "total_neurons": len(self.neurons),
                "total_synapses": len(self.synapses),
                "total_spikes_fired": self.total_spikes_fired,
                "average_synaptic_weight": round(avg_weight, 4),
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = f"+-------------------------------------------------------------------------+\n|      STAGE {s['stage']}: {s['stage_name'].upper()[:52]:<52} |\n|      Era {s['era']}: {s['era_name'][:56]:<56} |\n+-------------------------------------------------------------------------+"
        body = (
            f"| Simulation Clock     : {s['current_time_ms']:.1f} ms{' ' * 38}|\n"
            f"| Total LIF Neurons    : {s['total_neurons']:<48} |\n"
            f"| Plastic Synapses     : {s['total_synapses']:<48} |\n"
            f"| Total Spikes Fired   : {s['total_spikes_fired']:<48} |\n"
            f"| Mean Synaptic Weight : {s['average_synaptic_weight']:<48} |"
        )
        footer = "+-------------------------------------------------------------------------+"
        return f"{header}\n{body}\n{footer}"
