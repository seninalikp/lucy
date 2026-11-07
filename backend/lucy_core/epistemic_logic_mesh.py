"""
Stage 235: Decentralized Multi-Agent Epistemic Logic & Dynamic Common Knowledge Mesh
Era 24: Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity

Sovereign Human Operator: Senin (Senin Ali K P)

Provides:
- Epistemic Modal Logic (S5 Modal Axiomatization with Reflexivity, Symmetry, Transitivity)
- Multi-Agent Kripke Frame Possible Worlds Semantics (W, R_i, V)
- Modal Operators: K_i(phi), E_G(phi), C_G(phi) [Common Knowledge], D_G(phi) [Distributed Knowledge]
- Dynamic Epistemic Logic (DEL) with Truthful Public Announcements [phi!] and Model Restriction
- Automated Resolution of Multi-Agent Knowledge Puzzles (Muddy Children, Consensus Convergence)
- Epistemic Dissonance / Contradiction Detection across Decentralized Swarm Nodes
- 100% Offline, Pure Python, Deterministic, Zero Cloud Dependencies
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import copy

STAGE = 235
STAGE_NAME = "Decentralized Multi-Agent Epistemic Logic & Dynamic Common Knowledge Mesh"
ERA = 24
ERA_NAME = "Trans-Dimensional Cognitive Resonance, Neuromorphic Spiking Fabrics & Autonomous Sovereign AGI Singularity"


class FormulaType(Enum):
    ATOM = "ATOM"
    NOT = "NOT"
    AND = "AND"
    OR = "OR"
    IMPLIES = "IMPLIES"
    KNOWS = "KNOWS"
    EVERYONE_KNOWS = "EVERYONE_KNOWS"
    COMMON_KNOWLEDGE = "COMMON_KNOWLEDGE"
    DISTRIBUTED_KNOWLEDGE = "DISTRIBUTED_KNOWLEDGE"


@dataclass
class EpistemicFormula:
    formula_type: FormulaType
    name: Optional[str] = None
    agent: Optional[str] = None
    group: Optional[Tuple[str, ...]] = None
    sub1: Optional["EpistemicFormula"] = None
    sub2: Optional["EpistemicFormula"] = None

    @classmethod
    def atom(cls, name: str) -> "EpistemicFormula":
        return cls(FormulaType.ATOM, name=name)

    @classmethod
    def neg(cls, sub: "EpistemicFormula") -> "EpistemicFormula":
        return cls(FormulaType.NOT, sub1=sub)

    @classmethod
    def conj(cls, left: "EpistemicFormula", right: "EpistemicFormula") -> "EpistemicFormula":
        return cls(FormulaType.AND, sub1=left, sub2=right)

    @classmethod
    def disj(cls, left: "EpistemicFormula", right: "EpistemicFormula") -> "EpistemicFormula":
        return cls(FormulaType.OR, sub1=left, sub2=right)

    @classmethod
    def impl(cls, left: "EpistemicFormula", right: "EpistemicFormula") -> "EpistemicFormula":
        return cls(FormulaType.IMPLIES, sub1=left, sub2=right)

    @classmethod
    def knows(cls, agent: str, sub: "EpistemicFormula") -> "EpistemicFormula":
        return cls(FormulaType.KNOWS, agent=agent, sub1=sub)

    @classmethod
    def everyone(cls, group: Tuple[str, ...], sub: "EpistemicFormula") -> "EpistemicFormula":
        return cls(FormulaType.EVERYONE_KNOWS, group=group, sub1=sub)

    @classmethod
    def common(cls, group: Tuple[str, ...], sub: "EpistemicFormula") -> "EpistemicFormula":
        return cls(FormulaType.COMMON_KNOWLEDGE, group=group, sub1=sub)

    @classmethod
    def distributed(cls, group: Tuple[str, ...], sub: "EpistemicFormula") -> "EpistemicFormula":
        return cls(FormulaType.DISTRIBUTED_KNOWLEDGE, group=group, sub1=sub)

    def to_string(self) -> str:
        if self.formula_type == FormulaType.ATOM:
            return self.name or ""
        elif self.formula_type == FormulaType.NOT:
            return f"~({self.sub1.to_string()})"
        elif self.formula_type == FormulaType.AND:
            return f"({self.sub1.to_string()} & {self.sub2.to_string()})"
        elif self.formula_type == FormulaType.OR:
            return f"({self.sub1.to_string()} | {self.sub2.to_string()})"
        elif self.formula_type == FormulaType.IMPLIES:
            return f"({self.sub1.to_string()} -> {self.sub2.to_string()})"
        elif self.formula_type == FormulaType.KNOWS:
            return f"K_{self.agent}({self.sub1.to_string()})"
        elif self.formula_type == FormulaType.EVERYONE_KNOWS:
            grp = ",".join(self.group) if self.group else ""
            return f"E_{{{grp}}}({self.sub1.to_string()})"
        elif self.formula_type == FormulaType.COMMON_KNOWLEDGE:
            grp = ",".join(self.group) if self.group else ""
            return f"C_{{{grp}}}({self.sub1.to_string()})"
        elif self.formula_type == FormulaType.DISTRIBUTED_KNOWLEDGE:
            grp = ",".join(self.group) if self.group else ""
            return f"D_{{{grp}}}({self.sub1.to_string()})"
        return "<?>"


@dataclass
class PossibleWorld:
    world_id: str
    valuations: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class KripkeModel:
    """
    S5 Multi-Agent Kripke Model (W, R_i, V)
    Where R_i is an equivalence relation for each agent i in Agents.
    """
    def __init__(self, agents: Optional[List[str]] = None):
        self.worlds: Dict[str, PossibleWorld] = {}
        self.agents: Set[str] = set(agents or [])
        # relations[agent] = set of pairs (w1, w2)
        self.relations: Dict[str, Set[Tuple[str, str]]] = {ag: set() for ag in self.agents}

    def add_agent(self, agent_id: str) -> None:
        self.agents.add(agent_id)
        if agent_id not in self.relations:
            self.relations[agent_id] = set()
            # reflexive closure for existing worlds
            for wid in self.worlds:
                self.relations[agent_id].add((wid, wid))

    def add_world(self, world_id: str, valuations: Dict[str, bool], metadata: Optional[Dict[str, Any]] = None) -> None:
        pw = PossibleWorld(world_id=world_id, valuations=dict(valuations), metadata=metadata or {})
        self.worlds[world_id] = pw
        # Reflexive closure: every agent considers world w indistinguishable from itself
        for ag in self.agents:
            self.relations[ag].add((world_id, world_id))

    def set_indistinguishable(self, agent_id: str, w1: str, w2: str) -> None:
        """Add bidirectional equivalence edge between w1 and w2 for agent_id and close transitively."""
        if agent_id not in self.agents:
            self.add_agent(agent_id)
        self.relations[agent_id].add((w1, w2))
        self.relations[agent_id].add((w2, w1))
        self._close_transitive(agent_id)

    def _close_transitive(self, agent_id: str) -> None:
        """Warshall-style transitive closure for equivalence relation."""
        rel = self.relations[agent_id]
        changed = True
        while changed:
            changed = False
            new_pairs = set()
            for (a, b) in rel:
                for (c, d) in rel:
                    if b == c and (a, d) not in rel:
                        new_pairs.add((a, d))
            if new_pairs:
                rel.update(new_pairs)
                changed = True

    def evaluate(self, formula: EpistemicFormula, world_id: str) -> bool:
        """
        Evaluate epistemic formula at a given world in this Kripke model.
        """
        if world_id not in self.worlds:
            raise KeyError(f"World '{world_id}' not found in Kripke model.")

        ft = formula.formula_type
        if ft == FormulaType.ATOM:
            return bool(self.worlds[world_id].valuations.get(formula.name, False))

        elif ft == FormulaType.NOT:
            return not self.evaluate(formula.sub1, world_id)

        elif ft == FormulaType.AND:
            return self.evaluate(formula.sub1, world_id) and self.evaluate(formula.sub2, world_id)

        elif ft == FormulaType.OR:
            return self.evaluate(formula.sub1, world_id) or self.evaluate(formula.sub2, world_id)

        elif ft == FormulaType.IMPLIES:
            return (not self.evaluate(formula.sub1, world_id)) or self.evaluate(formula.sub2, world_id)

        elif ft == FormulaType.KNOWS:
            ag = formula.agent
            if ag not in self.relations:
                return False
            # K_i phi is true at w iff for all w' such that w ~_i w', phi is true at w'
            accessible_worlds = [w2 for (w1, w2) in self.relations[ag] if w1 == world_id]
            for w_acc in accessible_worlds:
                if not self.evaluate(formula.sub1, w_acc):
                    return False
            return True

        elif ft == FormulaType.EVERYONE_KNOWS:
            # E_G phi = bigwedge_{i in G} K_i phi
            group = formula.group or tuple(self.agents)
            for ag in group:
                k_form = EpistemicFormula.knows(ag, formula.sub1)
                if not self.evaluate(k_form, world_id):
                    return False
            return True

        elif ft == FormulaType.COMMON_KNOWLEDGE:
            # C_G phi is true at w iff phi is true at all worlds reachable via transitive closure of union of ~_i for i in G
            group = set(formula.group or tuple(self.agents))
            reachable = self._reachable_worlds_for_group(group, world_id)
            for w_target in reachable:
                if not self.evaluate(formula.sub1, w_target):
                    return False
            return True

        elif ft == FormulaType.DISTRIBUTED_KNOWLEDGE:
            # D_G phi is true at w iff phi is true at all worlds in intersection of ~_i for i in G
            group = list(formula.group or tuple(self.agents))
            if not group:
                return self.evaluate(formula.sub1, world_id)
            # Find worlds accessible in all relations simultaneously
            first_ag = group[0]
            intersected = set([w2 for (w1, w2) in self.relations[first_ag] if w1 == world_id])
            for other_ag in group[1:]:
                other_acc = set([w2 for (w1, w2) in self.relations[other_ag] if w1 == world_id])
                intersected.intersection_update(other_acc)

            for w_acc in intersected:
                if not self.evaluate(formula.sub1, w_acc):
                    return False
            return True

        return False

    def _reachable_worlds_for_group(self, group: Set[str], start_world: str) -> Set[str]:
        """Compute reflexive-transitive closure of accessible worlds for a group of agents."""
        visited = set([start_world])
        queue = [start_world]

        while queue:
            curr = queue.pop(0)
            for ag in group:
                if ag in self.relations:
                    for (w1, w2) in self.relations[ag]:
                        if w1 == curr and w2 not in visited:
                            visited.add(w2)
                            queue.append(w2)
        return visited

    def public_announcement(self, formula: EpistemicFormula) -> "KripkeModel":
        """
        Dynamic Epistemic Logic Public Announcement [phi!].
        Restricts model to only those worlds where formula evaluates to True.
        """
        surviving_worlds = [wid for wid in self.worlds if self.evaluate(formula, wid)]
        new_model = KripkeModel(agents=list(self.agents))

        for wid in surviving_worlds:
            pw = self.worlds[wid]
            new_model.add_world(wid, pw.valuations, pw.metadata)

        for ag in self.agents:
            old_rel = self.relations[ag]
            for (w1, w2) in old_rel:
                if w1 in new_model.worlds and w2 in new_model.worlds:
                    new_model.relations[ag].add((w1, w2))

        return new_model

    def is_valid(self, formula: EpistemicFormula) -> bool:
        """True if formula holds in all possible worlds."""
        if not self.worlds:
            return False
        return all(self.evaluate(formula, wid) for wid in self.worlds)

    def is_satisfiable(self, formula: EpistemicFormula) -> bool:
        """True if formula holds in at least one possible world."""
        return any(self.evaluate(formula, wid) for wid in self.worlds)


class EpistemicLogicMeshFabric:
    """
    Decentralized Multi-Agent Epistemic Logic Mesh Fabric.
    Coordinates distributed knowledge synthesis, common knowledge generation,
    and epistemic consistency across autonomous agent collectives.
    """
    def __init__(self, agents: Optional[List[str]] = None):
        self.agents: List[str] = agents or ["agent_alpha", "agent_beta", "agent_gamma"]
        self.model: KripkeModel = KripkeModel(agents=self.agents)
        self.announcement_history: List[str] = []
        self.current_world: Optional[str] = None
        self.round_counter: int = 0
        self._init_default_consensus_scenario()

    def _init_default_consensus_scenario(self) -> None:
        """Initialize standard 3-agent multi-state verification universe."""
        self.setup_muddy_children_scenario(n_children=3, n_muddy=2)

    def setup_muddy_children_scenario(self, n_children: int = 3, n_muddy: int = 2) -> None:
        """
        Sets up the classical Muddy Children epistemic puzzle benchmark.
        Children: c1, c2, c3...
        muddy: True/False for each child.
        An agent can see whether all other agents are muddy, but cannot see their own forehead.
        """
        self.agents = [f"child_{i+1}" for i in range(n_children)]
        self.model = KripkeModel(agents=self.agents)
        self.announcement_history = []
        self.round_counter = 0

        # Generate all 2^n possible worlds
        import itertools
        states = list(itertools.product([False, True], repeat=n_children))
        target_state = tuple([True if i < n_muddy else False for i in range(n_children)])

        for state in states:
            wid = "".join("1" if b else "0" for b in state)
            val = {f"muddy_{i+1}": state[i] for i in range(n_children)}
            self.model.add_world(wid, val, metadata={"state": state})

        self.current_world = "".join("1" if b else "0" for b in target_state)

        # Accessibility relations: agent i considers two worlds indistinguishable iff
        # they agree on all other agents' muddy statuses (agent cannot see self)
        for (w1_id, pw1) in self.model.worlds.items():
            s1 = pw1.metadata["state"]
            for (w2_id, pw2) in self.model.worlds.items():
                s2 = pw2.metadata["state"]
                for i, ag in enumerate(self.agents):
                    # Check if all other agents match
                    other_match = all(s1[j] == s2[j] for j in range(n_children) if j != i)
                    if other_match:
                        self.model.relations[ag].add((w1_id, w2_id))

    def step_muddy_children_round(self) -> Dict[str, Any]:
        """
        Executes one epistemic step of the Muddy Children puzzle.
        In round 0: Father announces 'At least one of you is muddy' -> phi = muddy_1 | muddy_2 | ...
        In round >= 1: Each child announces simultaneously whether they know their own status.
        If child doesn't know, announcement is ~K_i(muddy_i) & ~K_i(~muddy_i).
        """
        self.round_counter += 1
        n = len(self.agents)

        if self.round_counter == 1:
            # Round 1 announcement: at least one child is muddy
            at_least_one = EpistemicFormula.atom("muddy_1")
            for i in range(2, n + 1):
                at_least_one = EpistemicFormula.disj(at_least_one, EpistemicFormula.atom(f"muddy_{i}"))

            self.model = self.model.public_announcement(at_least_one)
            self.announcement_history.append("Father: At least one of you has mud on your forehead!")
            return {
                "round": 1,
                "announcement": "At least one child is muddy",
                "remaining_worlds": len(self.model.worlds),
                "agent_states": {ag: "Does not know" for ag in self.agents}
            }

        # Subsequent rounds: Each agent checks if they know their status
        knowledge_dict = {}
        conjuncts = []

        for i, ag in enumerate(self.agents):
            k_muddy = EpistemicFormula.knows(ag, EpistemicFormula.atom(f"muddy_{i+1}"))
            k_clean = EpistemicFormula.knows(ag, EpistemicFormula.neg(EpistemicFormula.atom(f"muddy_{i+1}")))

            knows_muddy = self.model.evaluate(k_muddy, self.current_world)
            knows_clean = self.model.evaluate(k_clean, self.current_world)

            if knows_muddy:
                knowledge_dict[ag] = "I know I AM MUDDY"
                conjuncts.append(k_muddy)
            elif knows_clean:
                knowledge_dict[ag] = "I know I AM CLEAN"
                conjuncts.append(k_clean)
            else:
                knowledge_dict[ag] = "I do not know"
                conjuncts.append(EpistemicFormula.conj(EpistemicFormula.neg(k_muddy), EpistemicFormula.neg(k_clean)))

        # Build composite public announcement from agents' utterances
        if conjuncts:
            compound = conjuncts[0]
            for next_c in conjuncts[1:]:
                compound = EpistemicFormula.conj(compound, next_c)
            self.model = self.model.public_announcement(compound)

        self.announcement_history.append(f"Round {self.round_counter}: " + "; ".join(f"{k}: {v}" for k, v in knowledge_dict.items()))
        return {
            "round": self.round_counter,
            "agent_states": knowledge_dict,
            "remaining_worlds": len(self.model.worlds)
        }

    def verify_common_knowledge(self, proposition: str, group: Optional[List[str]] = None) -> bool:
        """
        Checks if proposition is Common Knowledge among the specified group in the current world.
        """
        if not self.current_world or self.current_world not in self.model.worlds:
            return False
        grp_tuple = tuple(group or self.agents)
        ck_formula = EpistemicFormula.common(grp_tuple, EpistemicFormula.atom(proposition))
        return self.model.evaluate(ck_formula, self.current_world)

    def verify_distributed_knowledge(self, proposition: str, group: Optional[List[str]] = None) -> bool:
        """
        Checks if proposition is Distributed Knowledge among the specified group in the current world.
        """
        if not self.current_world or self.current_world not in self.model.worlds:
            return False
        grp_tuple = tuple(group or self.agents)
        dk_formula = EpistemicFormula.distributed(grp_tuple, EpistemicFormula.atom(proposition))
        return self.model.evaluate(dk_formula, self.current_world)

    def detect_epistemic_dissonance(self) -> bool:
        """
        Epistemic dissonance occurs if the model collapses into an impossible state (empty worlds).
        """
        return len(self.model.worlds) == 0

    def query_agent_knowledge(self, agent_id: str, proposition: str) -> bool:
        """Returns True if agent_id knows proposition in the current world."""
        if not self.current_world or self.current_world not in self.model.worlds:
            return False
        form = EpistemicFormula.knows(agent_id, EpistemicFormula.atom(proposition))
        return self.model.evaluate(form, self.current_world)

    def status(self) -> Dict[str, Any]:
        return {
            "stage": STAGE,
            "stage_name": STAGE_NAME,
            "era": ERA,
            "era_name": ERA_NAME,
            "active_agents": self.agents,
            "total_agents": len(self.agents),
            "possible_worlds_count": len(self.model.worlds),
            "current_world": self.current_world,
            "rounds_executed": self.round_counter,
            "dissonance_detected": self.detect_epistemic_dissonance(),
            "history_length": len(self.announcement_history)
        }

    def format_ascii_status(self) -> str:
        s = self.status()
        ag_str = ", ".join(s["active_agents"])
        lines = [
            "+-------------------------------------------------------------------------+",
            f"|      STAGE {STAGE}: {STAGE_NAME[:48]:<48} |",
            f"|      Era {ERA}: {ERA_NAME[:53]:<53} |",
            "+-------------------------------------------------------------------------+",
            f"| Active Agents        : {ag_str:<48} |",
            f"| Total Agents         : {s['total_agents']:<48} |",
            f"| Possible Worlds      : {s['possible_worlds_count']:<48} |",
            f"| Current World        : {str(s['current_world']):<48} |",
            f"| Rounds Executed      : {s['rounds_executed']:<48} |",
            f"| Dissonance Detected  : {str(s['dissonance_detected']):<48} |",
            f"| Announcement Events  : {s['history_length']:<48} |",
            "+-------------------------------------------------------------------------+"
        ]
        return "\n".join(lines)
