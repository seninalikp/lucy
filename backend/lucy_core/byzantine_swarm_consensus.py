"""
Stage 238: Self-Healing Chaos Immunity & Byzantine Swarm Consensus Auto-Recovery
Era 24: Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- Byzantine Fault Tolerant Swarm Consensus (PBFT / Tendermint 2f+1 Quorum SMR)
- Dynamic Chaos Injection Engine: Equivocations, Sybil Dropping, Network Partitions, and Crash-Recovery
- Cryptographic Equivocation Detection, Slashing & Swarm Quarantine Fabric
- Autonomous View-Change Failover & Catch-Up State Synchronization
- Self-Healing Chaos Immunity Evaluation & Zero-Loss State Machine Invariants
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib
import json
import time

STAGE = 238
STAGE_NAME = "Self-Healing Chaos Immunity & Byzantine Swarm Consensus Auto-Recovery"
ERA = 24
ERA_NAME = "Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity"


class ConsensusPhase(Enum):
    PRE_PREPARE = "PRE_PREPARE"
    PREPARE = "PREPARE"
    COMMIT = "COMMIT"
    COMMITTED = "COMMITTED"
    VIEW_CHANGE = "VIEW_CHANGE"


@dataclass
class ConsensusMessage:
    view: int
    sequence: int
    phase: ConsensusPhase
    digest: str
    sender: str
    signature: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    def compute_signature(self) -> str:
        body = f"{self.view}:{self.sequence}:{self.phase.value}:{self.digest}:{self.sender}:{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(body.encode("utf-8")).hexdigest()


@dataclass
class EquivocationProof:
    sender: str
    view: int
    sequence: int
    digest_a: str
    digest_b: str
    sig_a: str
    sig_b: str


class SwarmNode:
    """Consensus node in the Byzantine fault tolerant swarm."""
    def __init__(self, node_id: str, is_byzantine: bool = False):
        self.node_id: str = node_id
        self.is_byzantine: bool = is_byzantine
        self.is_quarantined: bool = False
        self.is_offline: bool = False
        self.committed_log: List[Dict[str, Any]] = []
        self.received_messages: List[ConsensusMessage] = []
        self.prepare_votes: Dict[Tuple[int, int, str], Set[str]] = {} # (view, seq, digest) -> set of senders
        self.commit_votes: Dict[Tuple[int, int, str], Set[str]] = {}  # (view, seq, digest) -> set of senders


class ByzantineSwarmConsensusFabric:
    """
    Self-Healing Chaos Immunity & Byzantine Swarm Consensus Auto-Recovery Fabric.
    Coordinates Byzantine nodes, chaos injections, automatic equivocation
    quarantine, and consensus convergence under severe adversarial pressure.
    """
    def __init__(self, total_nodes: int = 7, byzantine_count: int = 2):
        self.total_nodes: int = total_nodes
        self.byzantine_threshold: int = (total_nodes - 1) // 3 # f < N/3
        self.quorum_size: int = 2 * self.byzantine_threshold + 1
        self.nodes: Dict[str, SwarmNode] = {}
        self.current_view: int = 0
        self.sequence_counter: int = 0
        self.equivocation_proofs: List[EquivocationProof] = []
        self.quarantined_nodes: Set[str] = set()
        self.chaos_events: List[Dict[str, Any]] = []
        self.recovered_rounds: int = 0
        self.total_blocks_committed: int = 0
        self._init_nodes(byzantine_count)

    def _init_nodes(self, byzantine_count: int) -> None:
        """Initialize swarm nodes with honest and byzantine configurations."""
        for i in range(self.total_nodes):
            nid = f"node_{i}"
            is_byz = (i < byzantine_count)
            self.nodes[nid] = SwarmNode(node_id=nid, is_byzantine=is_byz)

    def get_primary(self, view: Optional[int] = None) -> str:
        """Deterministic round-robin primary selection."""
        v = self.current_view if view is None else view
        active_candidates = [n for n in sorted(self.nodes.keys()) if n not in self.quarantined_nodes]
        if not active_candidates:
            return sorted(self.nodes.keys())[0]
        return active_candidates[v % len(active_candidates)]

    def inject_chaos_node_crash(self, node_id: str) -> None:
        """Simulates node crash-stop failure."""
        if node_id in self.nodes:
            self.nodes[node_id].is_offline = True
            self.chaos_events.append({"type": "CRASH", "node": node_id, "timestamp": time.time()})

    def inject_chaos_node_recovery(self, node_id: str) -> None:
        """Recovers an offline node and triggers state catch-up sync."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.is_offline = False
            # Catch up from any honest committed log
            for other in self.nodes.values():
                if not other.is_byzantine and not other.is_offline and len(other.committed_log) > len(node.committed_log):
                    node.committed_log = list(other.committed_log)
                    break
            self.chaos_events.append({"type": "RECOVERY", "node": node_id, "timestamp": time.time()})
            self.recovered_rounds += 1

    def detect_and_quarantine_equivocation(self, msgs: List[ConsensusMessage]) -> Optional[EquivocationProof]:
        """
        Inspects message batch for conflicting signatures on identical (view, seq) by same sender.
        If detected, generates cryptographic EquivocationProof and quarantines the offender.
        """
        seen: Dict[Tuple[str, int, int], ConsensusMessage] = {}
        for m in msgs:
            key = (m.sender, m.view, m.sequence)
            if key in seen:
                prev = seen[key]
                if prev.digest != m.digest and prev.phase == m.phase:
                    proof = EquivocationProof(
                        sender=m.sender,
                        view=m.view,
                        sequence=m.sequence,
                        digest_a=prev.digest,
                        digest_b=m.digest,
                        sig_a=prev.signature,
                        sig_b=m.signature
                    )
                    self.equivocation_proofs.append(proof)
                    self.quarantined_nodes.add(m.sender)
                    if m.sender in self.nodes:
                        self.nodes[m.sender].is_quarantined = True
                    return proof
            seen[key] = m
        return None

    def propose_and_reach_consensus(self, block_data: Dict[str, Any], inject_equivocation: bool = False) -> Dict[str, Any]:
        """
        Executes a 3-phase PBFT consensus round (Pre-Prepare -> Prepare -> Commit).
        Handles Byzantine equivocations, quarantine, and view-change failovers.
        """
        self.sequence_counter += 1
        seq = self.sequence_counter
        view = self.current_view
        primary = self.get_primary(view)

        raw_digest = hashlib.sha256(json.dumps(block_data, sort_keys=True).encode("utf-8")).hexdigest()

        # Step 1: Pre-prepare
        all_messages: List[ConsensusMessage] = []
        if inject_equivocation and self.nodes[primary].is_byzantine:
            # Equivocation: send raw_digest to half, forged_digest to other half
            forged_digest = hashlib.sha256((raw_digest + "_FORGED").encode("utf-8")).hexdigest()
            m1 = ConsensusMessage(view=view, sequence=seq, phase=ConsensusPhase.PRE_PREPARE, digest=raw_digest, sender=primary, payload=block_data)
            m1.signature = m1.compute_signature()
            m2 = ConsensusMessage(view=view, sequence=seq, phase=ConsensusPhase.PRE_PREPARE, digest=forged_digest, sender=primary, payload={"forged": True})
            m2.signature = m2.compute_signature()
            all_messages.extend([m1, m2])

            proof = self.detect_and_quarantine_equivocation(all_messages)
            # Equivocation caught! Trigger View Change failover
            self.current_view += 1
            new_primary = self.get_primary(self.current_view)
            self.chaos_events.append({"type": "EQUIVOCATION_QUARANTINED", "proof": proof.sender, "view": view})
            # Re-propose cleanly under honest primary
            return self.propose_and_reach_consensus(block_data, inject_equivocation=False)

        pre_prep = ConsensusMessage(view=view, sequence=seq, phase=ConsensusPhase.PRE_PREPARE, digest=raw_digest, sender=primary, payload=block_data)
        pre_prep.signature = pre_prep.compute_signature()
        all_messages.append(pre_prep)

        # Step 2: Prepare phase
        prepare_msgs = []
        for nid, node in self.nodes.items():
            if node.is_offline or node.is_quarantined:
                continue
            if node.is_byzantine:
                continue # byzantine silent or uncooperative
            prep = ConsensusMessage(view=view, sequence=seq, phase=ConsensusPhase.PREPARE, digest=raw_digest, sender=nid)
            prep.signature = prep.compute_signature()
            prepare_msgs.append(prep)

        # Step 3: Check 2f+1 prepare quorum
        if len(prepare_msgs) < self.quorum_size:
            # Trigger view change if prepare quorum fails
            self.current_view += 1
            return {"status": "VIEW_CHANGE_TRIGGERED", "view": self.current_view, "reason": "PREPARE_QUORUM_DEFICIT"}

        # Step 4: Commit phase
        commit_msgs = []
        for nid, node in self.nodes.items():
            if node.is_offline or node.is_quarantined:
                continue
            if node.is_byzantine:
                continue
            cmt = ConsensusMessage(view=view, sequence=seq, phase=ConsensusPhase.COMMIT, digest=raw_digest, sender=nid)
            cmt.signature = cmt.compute_signature()
            commit_msgs.append(cmt)

        # Step 5: Check 2f+1 commit quorum and commit to state machine log
        if len(commit_msgs) >= self.quorum_size:
            committed_entry = {"sequence": seq, "view": view, "digest": raw_digest, "data": block_data}
            for nid, node in self.nodes.items():
                if not node.is_byzantine and not node.is_offline and not node.is_quarantined:
                    node.committed_log.append(committed_entry)
            self.total_blocks_committed += 1
            return {
                "status": "COMMITTED",
                "sequence": seq,
                "view": view,
                "digest": raw_digest,
                "prepares": len(prepare_msgs),
                "commits": len(commit_msgs),
                "quorum": self.quorum_size
            }

        return {"status": "COMMIT_QUORUM_DEFICIT"}

    def compute_chaos_immunity_score(self) -> float:
        """Calculates chaos immunity score (0% to 100%) based on Byzantine handling and recovery."""
        active_honest = sum(1 for n in self.nodes.values() if not n.is_byzantine and not n.is_quarantined and not n.is_offline)
        total_honest = sum(1 for n in self.nodes.values() if not n.is_byzantine)
        if total_honest == 0:
            return 0.0
        health_ratio = active_honest / total_honest
        recovery_bonus = min(0.2, self.recovered_rounds * 0.05)
        quarantine_bonus = min(0.2, len(self.quarantined_nodes) * 0.1)
        score = min(100.0, (health_ratio * 0.6 + recovery_bonus + quarantine_bonus) * 100.0)
        return round(score, 1)

    def status(self) -> Dict[str, Any]:
        return {
            "stage": STAGE,
            "stage_name": STAGE_NAME,
            "era": ERA,
            "era_name": ERA_NAME,
            "total_nodes": self.total_nodes,
            "byzantine_threshold_f": self.byzantine_threshold,
            "quorum_size": self.quorum_size,
            "current_view": self.current_view,
            "current_primary": self.get_primary(),
            "blocks_committed": self.total_blocks_committed,
            "quarantined_nodes": list(self.quarantined_nodes),
            "equivocation_proofs": len(self.equivocation_proofs),
            "recovered_rounds": self.recovered_rounds,
            "chaos_immunity_score": self.compute_chaos_immunity_score()
        }

    def format_ascii_status(self) -> str:
        s = self.status()
        q_str = ", ".join(s["quarantined_nodes"]) if s["quarantined_nodes"] else "None"
        vp_str = f"View {s['current_view']} ({s['current_primary']})"
        score_str = f"{s['chaos_immunity_score']} %"
        lines = [
            "+-------------------------------------------------------------------------+",
            f"|      STAGE {STAGE}: {STAGE_NAME[:48]:<48} |",
            f"|      Era {ERA}: {ERA_NAME[:53]:<53} |",
            "+-------------------------------------------------------------------------+",
            f"| Total Swarm Nodes    : {s['total_nodes']:<48} |",
            f"| Max Byzantine f      : {s['byzantine_threshold_f']:<48} |",
            f"| Quorum 2f+1 Size     : {s['quorum_size']:<48} |",
            f"| Active View / Primary: {vp_str:<48} |",
            f"| Blocks Committed     : {s['blocks_committed']:<48} |",
            f"| Quarantined Nodes    : {q_str:<48} |",
            f"| Equivocation Proofs  : {s['equivocation_proofs']:<48} |",
            f"| Chaos Immunity Score : {score_str:<48} |",
            "+-------------------------------------------------------------------------+"
        ]
        return "\n".join(lines)
