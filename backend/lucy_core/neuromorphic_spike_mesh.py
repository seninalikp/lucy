r"""
backend/lucy_core/neuromorphic_spike_mesh.py
Stage 204: Neuromorphic Event-Driven Spike Router & Sparse Activation Mesh
Era 21: Autonomous Hyper-Scale Multi-Kernel Federation, Quantum-Resistant Keys & Post-Singularity Architecture

100% offline, sovereign neuromorphic spiking engine:
1. Leaky Integrate-and-Fire (LIF) Dynamics:
   - Discrete-time membrane potential integration with decay parameter beta.
   - Threshold-triggered binary/analog spike generation with refractory reset.
2. Event-Driven Sparse Routing:
   - Propagates activation signals strictly along firing paths (>90% energy/compute sparsity).
   - Synaptic delay queues and directed graph topologies.
3. Spike-Timing-Dependent Plasticity (STDP):
   - Biologically inspired temporal synaptic weight modulation based on pre/post spike intervals.
4. Thread-safe execution fabric and CP1252-safe ASCII table formatting.
"""

from __future__ import annotations

import collections
import copy
import math
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 204
STAGE_NAME: str = "Neuromorphic Event-Driven Spike Router & Sparse Activation Mesh"
ERA: int = 21
ERA_NAME: str = "Autonomous Hyper-Scale Multi-Kernel Federation, Quantum-Resistant Keys & Post-Singularity Architecture"

DEFAULT_NEURON_COUNT: int = 32
DEFAULT_V_TH: float = 1.0
DEFAULT_V_RESET: float = 0.0
DEFAULT_BETA: float = 0.85
STDP_A_PLUS: float = 0.05
STDP_A_MINUS: float = 0.03
STDP_TAU: float = 20.0


@dataclass
class SpikeEvent:
    timestep: int
    source_neuron_id: int
    amplitude: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LIFNeuron:
    neuron_id: int
    v_membrane: float = DEFAULT_V_RESET
    v_threshold: float = DEFAULT_V_TH
    v_reset: float = DEFAULT_V_RESET
    decay_beta: float = DEFAULT_BETA
    last_spike_timestep: int = -9999
    total_spikes_emitted: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Synapse:
    pre_id: int
    post_id: int
    weight: float
    delay: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NeuromorphicSpikeMeshFabric:
    """
    Sovereign Neuromorphic Spike Mesh Fabric:
    Simulates event-driven spiking neural dynamics, sparse routing,
    and STDP synaptic plasticity.
    """

    def __init__(self, neuron_count: int = DEFAULT_NEURON_COUNT) -> None:
        self.neuron_count = neuron_count
        self._lock = threading.RLock()
        self.current_timestep: int = 0

        self.neurons: Dict[int, LIFNeuron] = {}
        for i in range(neuron_count):
            self.neurons[i] = LIFNeuron(neuron_id=i)

        # Synapses: (pre_id, post_id) -> Synapse
        self.synapses: Dict[Tuple[int, int], Synapse] = {}
        # Pending spikes in transit: (delivery_timestep, post_id) -> accumulated current
        self.spike_queue: Dict[Tuple[int, int], float] = collections.defaultdict(float)

        self._total_spikes: int = 0
        self._total_timesteps: int = 0
        self._stdp_updates_count: int = 0

        # Wire default sparse chain & loop connections
        for i in range(neuron_count - 1):
            self.connect_synapse(i, i + 1, weight=0.6, delay=1)

    def connect_synapse(self, pre_id: int, post_id: int, weight: float = 0.5, delay: int = 1) -> Synapse:
        with self._lock:
            if pre_id not in self.neurons or post_id not in self.neurons:
                raise ValueError(f"Invalid neuron IDs: pre={pre_id}, post={post_id}")
            syn = Synapse(pre_id=pre_id, post_id=post_id, weight=weight, delay=max(1, delay))
            self.synapses[(pre_id, post_id)] = syn
            return syn

    def step_simulation(self, external_currents: Optional[Dict[int, float]] = None) -> List[SpikeEvent]:
        """
        Advances the neuromorphic mesh by one discrete timestep:
        1. Accumulates in-flight spikes from delay queue.
        2. Integrates membrane potentials: V = beta * V + I.
        3. Fires spikes if V >= V_th, resets V, routes across outgoing synapses.
        """
        with self._lock:
            self.current_timestep += 1
            self._total_timesteps += 1
            ext = external_currents or {}
            emitted_spikes: List[SpikeEvent] = []

            for nid, neuron in self.neurons.items():
                in_current = ext.get(nid, 0.0)
                # Add current delivered from spike queue
                q_key = (self.current_timestep, nid)
                in_current += self.spike_queue.pop(q_key, 0.0)

                # Leaky integration
                neuron.v_membrane = neuron.decay_beta * neuron.v_membrane + in_current

                # Threshold check
                if neuron.v_membrane >= neuron.v_threshold:
                    # Spike emitted!
                    neuron.v_membrane = neuron.v_reset
                    neuron.last_spike_timestep = self.current_timestep
                    neuron.total_spikes_emitted += 1
                    self._total_spikes += 1

                    spike = SpikeEvent(
                        timestep=self.current_timestep,
                        source_neuron_id=nid,
                        amplitude=1.0,
                    )
                    emitted_spikes.append(spike)

                    # Event-driven sparse routing across outgoing synapses
                    for (pre, post), syn in self.synapses.items():
                        if pre == nid:
                            delivery_step = self.current_timestep + syn.delay
                            self.spike_queue[(delivery_step, post)] += syn.weight

            return emitted_spikes

    def apply_stdp(self, pre_id: int, post_id: int) -> Optional[float]:
        """
        Applies Spike-Timing-Dependent Plasticity (STDP) to synapse (pre, post):
        delta_t = t_post - t_pre
        if delta_t > 0: dw = A_plus * exp(-delta_t / tau)
        if delta_t < 0: dw = -A_minus * exp(delta_t / tau)
        """
        with self._lock:
            syn = self.synapses.get((pre_id, post_id))
            if not syn:
                return None

            t_pre = self.neurons[pre_id].last_spike_timestep
            t_post = self.neurons[post_id].last_spike_timestep
            if t_pre < 0 or t_post < 0:
                return None  # One of the neurons hasn't spiked yet

            dt = t_post - t_pre
            if dt > 0:
                dw = STDP_A_PLUS * math.exp(-dt / STDP_TAU)
            elif dt < 0:
                dw = -STDP_A_MINUS * math.exp(dt / STDP_TAU)
            else:
                dw = 0.0

            # Update weight with soft bounds [0.0, 2.0]
            syn.weight = max(0.0, min(2.0, syn.weight + dw))
            self._stdp_updates_count += 1
            return syn.weight

    def status(self) -> Dict[str, Any]:
        with self._lock:
            active_synapses = len(self.synapses)
            total_possible = self.neuron_count * (self.neuron_count - 1)
            sparsity = 1.0 - (active_synapses / max(1, total_possible))
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "neuron_count": self.neuron_count,
                "synapse_count": active_synapses,
                "synaptic_sparsity": f"{sparsity * 100:.1f}%",
                "current_timestep": self.current_timestep,
                "total_spikes_emitted": self._total_spikes,
                "stdp_updates": self._stdp_updates_count,
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = (
            "+-------------------------------------------------------------------------+\n"
            "|      STAGE 204: NEUROMORPHIC EVENT-DRIVEN SPIKE ROUTER & MESH           |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        body = (
            f"| LIF Neurons Active    : {s['neuron_count']} Neurons{' ':<38} |\n"
            f"| Synaptic Topology     : {s['synapse_count']} Directed Synapses (Sparsity: {s['synaptic_sparsity']}){' ':<11} |\n"
            f"| Simulation Clock      : Timestep {s['current_timestep']:<40} |\n"
            f"| Total Spikes Fired    : {s['total_spikes_emitted']} Events Generated{' ':<27} |\n"
            f"| STDP Plasticity Runs  : {s['stdp_updates']} Synapses Adapted{' ':<26} |\n"
            "+-------------------------------------------------------------------------+\n"
        )
        return header + body
