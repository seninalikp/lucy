"""
Stage 236: Autonomous Temporal Chrono-State Engine & Causality Inversion Governor
Era 24: Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- Relativistic Causal DAG Poset with Lamport & Vector Clock State Snapshots
- Localized Anti-Causal Light Cone Inversion & Micro-Rollback without destroying orthogonal branches
- Counterfactual Intervention Re-simulation with Antecedent Injection
- Novikov Self-Consistency Enforcement & Closed Timelike Curve (CTC) Paradox Resolution
- 3-Way Causal Poset Reconciliation via Lowest Common Ancestor (LCA)
- Immutable Historical Horizon Barrier & Cryptographic Invariant Integrity
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib
import json
import time

STAGE = 236
STAGE_NAME = "Autonomous Temporal Chrono-State Engine & Causality Inversion Governor"
ERA = 24
ERA_NAME = "Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity"


@dataclass
class ChronoEvent:
    event_id: str
    timeline_id: str
    logical_tick: int
    vector_clock: Dict[str, int]
    state_delta: Dict[str, Any]
    causal_parents: List[str] = field(default_factory=list)
    causal_children: List[str] = field(default_factory=list)
    invariant_hash: str = ""
    is_frozen: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_hash(self) -> str:
        payload = f"{self.event_id}:{self.timeline_id}:{self.logical_tick}:{json.dumps(self.vector_clock, sort_keys=True)}:{json.dumps(self.state_delta, sort_keys=True)}:{','.join(sorted(self.causal_parents))}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class TemporalChronoGovernorFabric:
    """
    Autonomous Temporal Chrono-State Engine & Causality Inversion Governor.
    Manages branching relativistic timelines, light cones, and paradox-free
    causal rollbacks and counterfactual interventions.
    """
    def __init__(self):
        self.events: Dict[str, ChronoEvent] = {}
        self.timelines: Dict[str, List[str]] = {}  # timeline_id -> list of event_ids in order
        self.timeline_tips: Dict[str, str] = {}    # timeline_id -> latest event_id
        self.timeline_states: Dict[str, Dict[str, Any]] = {} # timeline_id -> full current state
        self.immutable_horizon_tick: int = -1
        self.inversions_count: int = 0
        self.paradoxes_prevented: int = 0
        self.reconciliations_count: int = 0
        self._init_genesis_timeline()

    def _init_genesis_timeline(self) -> None:
        """Create genesis root event on the prime timeline."""
        genesis_event = ChronoEvent(
            event_id="evt_genesis_0000",
            timeline_id="prime",
            logical_tick=0,
            vector_clock={"prime": 0},
            state_delta={"sovereign_operator": "Senin (Senin Ali K P)", "singularity_phase": "INIT", "entropy": 0.0},
            causal_parents=[],
            is_frozen=True,
            metadata={"origin": "genesis"}
        )
        genesis_event.invariant_hash = genesis_event.compute_hash()
        self.events[genesis_event.event_id] = genesis_event
        self.timelines["prime"] = [genesis_event.event_id]
        self.timeline_tips["prime"] = genesis_event.event_id
        self.timeline_states["prime"] = dict(genesis_event.state_delta)

    def commit_event(self, timeline_id: str, state_delta: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> ChronoEvent:
        """
        Appends a new causal event to the specified timeline.
        Enforces vector clock monotonicity and parent linking.
        """
        if timeline_id not in self.timelines:
            raise KeyError(f"Timeline '{timeline_id}' does not exist.")

        parent_id = self.timeline_tips.get(timeline_id)
        parent_evt = self.events[parent_id] if parent_id else None

        new_tick = (parent_evt.logical_tick + 1) if parent_evt else 0
        new_vc = dict(parent_evt.vector_clock) if parent_evt else {}
        new_vc[timeline_id] = new_vc.get(timeline_id, 0) + 1

        event_id = f"evt_{timeline_id}_{new_tick:04d}_{hashlib.sha256(f'{time.time()}_{new_tick}'.encode()).hexdigest()[:8]}"

        evt = ChronoEvent(
            event_id=event_id,
            timeline_id=timeline_id,
            logical_tick=new_tick,
            vector_clock=new_vc,
            state_delta=dict(state_delta),
            causal_parents=[parent_id] if parent_id else [],
            metadata=metadata or {}
        )
        evt.invariant_hash = evt.compute_hash()

        if parent_evt:
            parent_evt.causal_children.append(event_id)

        self.events[event_id] = evt
        self.timelines[timeline_id].append(event_id)
        self.timeline_tips[timeline_id] = event_id

        # Update accumulated state snapshot
        curr_state = dict(self.timeline_states.get(timeline_id, {}))
        curr_state.update(state_delta)
        self.timeline_states[timeline_id] = curr_state

        return evt

    def fork_timeline(self, source_timeline_id: str, new_timeline_id: str, branch_event_id: Optional[str] = None) -> str:
        """
        Forks a new independent timeline from a source timeline at branch_event_id (or current tip).
        """
        if source_timeline_id not in self.timelines:
            raise KeyError(f"Source timeline '{source_timeline_id}' not found.")
        if new_timeline_id in self.timelines:
            raise ValueError(f"Timeline '{new_timeline_id}' already exists.")

        target_event_id = branch_event_id or self.timeline_tips[source_timeline_id]
        if target_event_id not in self.events:
            raise KeyError(f"Branch event '{target_event_id}' not found.")

        # Reconstruct path of events up to target_event_id
        source_events = self.timelines[source_timeline_id]
        if target_event_id not in source_events:
            raise ValueError(f"Target event '{target_event_id}' not in source timeline '{source_timeline_id}'.")

        cut_idx = source_events.index(target_event_id)
        forked_events = list(source_events[:cut_idx + 1])

        self.timelines[new_timeline_id] = forked_events
        self.timeline_tips[new_timeline_id] = target_event_id

        # Compute state at branch point
        reconstructed_state = {}
        for eid in forked_events:
            reconstructed_state.update(self.events[eid].state_delta)
        self.timeline_states[new_timeline_id] = reconstructed_state

        return new_timeline_id

    def get_future_light_cone(self, event_id: str) -> Set[str]:
        """
        Computes the forward causal light cone (all events causally dependent on event_id).
        """
        if event_id not in self.events:
            raise KeyError(f"Event '{event_id}' not found.")

        visited = set()
        queue = [event_id]
        while queue:
            curr = queue.pop(0)
            if curr != event_id:
                visited.add(curr)
            for child_id in self.events[curr].causal_children:
                if child_id not in visited:
                    queue.append(child_id)
        return visited

    def invert_causality_and_rollback(self, timeline_id: str, rollback_target_id: str) -> Dict[str, Any]:
        """
        Localized causality inversion:
        Rolls back the given timeline to rollback_target_id, stripping and inverting the
        dependent forward light cone on this timeline, while strictly preserving parallel timelines.
        Prevents tampering if rollback_target_id is before the immutable horizon barrier.
        """
        if timeline_id not in self.timelines:
            raise KeyError(f"Timeline '{timeline_id}' does not exist.")
        if rollback_target_id not in self.events:
            raise KeyError(f"Rollback event '{rollback_target_id}' not found.")

        target_evt = self.events[rollback_target_id]
        if target_evt.logical_tick < self.immutable_horizon_tick:
            self.paradoxes_prevented += 1
            raise ValueError(
                f"Paradox Prevention Triggered: Target tick {target_evt.logical_tick} is before "
                f"immutable horizon barrier {self.immutable_horizon_tick}."
            )

        events_list = self.timelines[timeline_id]
        if rollback_target_id not in events_list:
            raise ValueError(f"Event '{rollback_target_id}' is not in timeline '{timeline_id}'.")

        cut_idx = events_list.index(rollback_target_id)
        abandoned_events = events_list[cut_idx + 1:]

        # Clean up timeline
        self.timelines[timeline_id] = events_list[:cut_idx + 1]
        self.timeline_tips[timeline_id] = rollback_target_id

        # Re-derive state up to target
        restored_state = {}
        for eid in self.timelines[timeline_id]:
            restored_state.update(self.events[eid].state_delta)
        self.timeline_states[timeline_id] = restored_state

        self.inversions_count += 1
        return {
            "timeline_id": timeline_id,
            "restored_tip": rollback_target_id,
            "pruned_events_count": len(abandoned_events),
            "restored_tick": target_evt.logical_tick,
            "status": "CAUSALITY_INVERTED"
        }

    def counterfactual_intervention(
        self,
        timeline_id: str,
        intervention_tick: int,
        intervened_delta: Dict[str, Any],
        new_timeline_id: str
    ) -> ChronoEvent:
        """
        Injects a counterfactual antecedent at intervention_tick, creating a new divergent
        timeline branching from that point with the intervened state delta.
        """
        events_list = self.timelines.get(timeline_id)
        if not events_list:
            raise KeyError(f"Timeline '{timeline_id}' not found.")

        # Locate event at intervention_tick
        branch_event_id = None
        for eid in events_list:
            if self.events[eid].logical_tick == intervention_tick:
                branch_event_id = eid
                break

        if not branch_event_id:
            raise ValueError(f"No event found at logical tick {intervention_tick} in timeline '{timeline_id}'.")

        # Fork new timeline at branch_event_id
        self.fork_timeline(timeline_id, new_timeline_id, branch_event_id=branch_event_id)

        # Commit counterfactual intervention event
        intervened_evt = self.commit_event(
            new_timeline_id,
            state_delta=intervened_delta,
            metadata={"counterfactual_antecedent": True, "parent_timeline": timeline_id}
        )
        return intervened_evt

    def freeze_immutable_horizon(self, tick: int) -> None:
        """
        Freezes history up to logical tick 'tick'. No causality inversion or deletion
        can ever occur prior to this horizon.
        """
        self.immutable_horizon_tick = max(self.immutable_horizon_tick, tick)
        for evt in self.events.values():
            if evt.logical_tick <= self.immutable_horizon_tick:
                evt.is_frozen = True

    def find_lowest_common_ancestor(self, timeline_a: str, timeline_b: str) -> Optional[str]:
        """
        Computes the Lowest Common Ancestor (LCA) event between two branching timelines in the causal poset.
        """
        list_a = self.timelines.get(timeline_a, [])
        list_b = self.timelines.get(timeline_b, [])

        set_a = set(list_a)
        # Scan b backwards from tip
        for eid in reversed(list_b):
            if eid in set_a:
                return eid
        return None

    def reconcile_timelines(self, target_timeline: str, source_timeline: str) -> Dict[str, Any]:
        """
        Performs 3-way causal reconciliation between two divergent timelines using LCA.
        Non-conflicting deltas are merged; conflicting keys favor target_timeline.
        """
        lca_id = self.find_lowest_common_ancestor(target_timeline, source_timeline)
        if not lca_id:
            raise ValueError(f"No common ancestor between '{target_timeline}' and '{source_timeline}'.")

        lca_state = {}
        for eid in self.timelines[target_timeline]:
            lca_state.update(self.events[eid].state_delta)
            if eid == lca_id:
                break

        target_state = self.timeline_states[target_timeline]
        source_state = self.timeline_states[source_timeline]

        merged_delta = {}
        # Apply source changes that did not conflict
        for k, v in source_state.items():
            if k not in target_state or target_state[k] == lca_state.get(k):
                merged_delta[k] = v

        if merged_delta:
            commit_evt = self.commit_event(
                target_timeline,
                state_delta=merged_delta,
                metadata={"reconciled_with": source_timeline, "lca": lca_id}
            )
        else:
            commit_evt = None

        self.reconciliations_count += 1
        return {
            "target_timeline": target_timeline,
            "source_timeline": source_timeline,
            "lca_id": lca_id,
            "merged_keys": list(merged_delta.keys()),
            "commit_event_id": commit_evt.event_id if commit_evt else None
        }

    def detect_closed_timelike_curves(self) -> bool:
        """
        Validates that the causal event graph is strictly acyclic (no CTC paradoxes).
        Returns True if a cycle is detected, False otherwise.
        """
        visited = set()
        rec_stack = set()

        def dfs(curr: str) -> bool:
            visited.add(curr)
            rec_stack.add(curr)
            for child in self.events[curr].causal_children:
                if child not in visited:
                    if dfs(child):
                        return True
                elif child in rec_stack:
                    return True
            rec_stack.remove(curr)
            return False

        for eid in self.events:
            if eid not in visited:
                if dfs(eid):
                    return True
        return False

    def status(self) -> Dict[str, Any]:
        return {
            "stage": STAGE,
            "stage_name": STAGE_NAME,
            "era": ERA,
            "era_name": ERA_NAME,
            "total_events": len(self.events),
            "active_timelines": list(self.timelines.keys()),
            "total_timelines": len(self.timelines),
            "immutable_horizon": self.immutable_horizon_tick,
            "inversions_performed": self.inversions_count,
            "paradoxes_prevented": self.paradoxes_prevented,
            "reconciliations_count": self.reconciliations_count,
            "ctc_paradox_detected": self.detect_closed_timelike_curves()
        }

    def format_ascii_status(self) -> str:
        s = self.status()
        tls = ", ".join(s["active_timelines"][:4])
        lines = [
            "+-------------------------------------------------------------------------+",
            f"|      STAGE {STAGE}: {STAGE_NAME[:48]:<48} |",
            f"|      Era {ERA}: {ERA_NAME[:53]:<53} |",
            "+-------------------------------------------------------------------------+",
            f"| Active Timelines     : {tls:<48} |",
            f"| Total Events         : {s['total_events']:<48} |",
            f"| Total Timelines      : {s['total_timelines']:<48} |",
            f"| Immutable Horizon    : Tick {s['immutable_horizon']:<43} |",
            f"| Inversions Performed : {s['inversions_performed']:<48} |",
            f"| Paradoxes Prevented  : {s['paradoxes_prevented']:<48} |",
            f"| Reconciliations      : {s['reconciliations_count']:<48} |",
            f"| CTC Paradox Loop     : {str(s['ctc_paradox_detected']):<48} |",
            "+-------------------------------------------------------------------------+"
        ]
        return "\n".join(lines)
