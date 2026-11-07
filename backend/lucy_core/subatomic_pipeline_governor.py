r"""
backend/lucy_core/subatomic_pipeline_governor.py
Stage 223: Sub-Atomic Micro-Architecture Pipeline Emulation & Speculative Execution Governor
Era 23: Universal Multi-Verse State Synthesis, Sub-Atomic Hyper-Computing & Sovereign Holographic Swarm Intelligence

100% offline, sovereign micro-architecture pipeline emulation and speculative execution governor:
1. Superscalar Out-of-Order Instruction Pipeline Emulation:
   - Instruction pipeline stages: Fetch, Decode, Reservation Station Dispatch, Out-of-Order Execution,
     Reorder Buffer (ROB) tracking, and in-order Commit/Retire.
2. Dynamic Branch Prediction & Speculative Execution:
   - 2-bit saturating counter branch target buffer.
   - Speculative instruction issue with branch checkpointing.
   - Deterministic pipeline rollback on branch mispredictions.
3. Speculative Side-Channel & Transient Execution Governor:
   - Intercepts speculative out-of-bounds memory dereferences and side-channel leakage hazards
     (Spectre-V1/Meltdown emulation safeguards).
   - Configurable serialization barriers (LFENCE / Speculation Fences).
4. Thread-safe execution fabric and CP1252-safe ASCII table formatting.
"""

from __future__ import annotations

import collections
import copy
import enum
import hashlib
import threading
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

STAGE: int = 223
STAGE_NAME: str = "Sub-Atomic Micro-Architecture Pipeline Emulation & Speculative Execution Governor"
ERA: int = 23
ERA_NAME: str = "Universal Multi-Verse State Synthesis, Sub-Atomic Hyper-Computing & Sovereign Holographic Swarm Intelligence"


class Opcode(enum.Enum):
    NOP = "NOP"
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    LOAD = "LOAD"
    STORE = "STORE"
    BRANCH_EQ = "BRANCH_EQ"
    BRANCH_NE = "BRANCH_NE"
    FENCE = "FENCE"


class GovernorMode(enum.Enum):
    STRICT_MITIGATION = "STRICT_MITIGATION"
    MONITOR_ONLY = "MONITOR_ONLY"
    PERMISSIVE = "PERMISSIVE"


@dataclass
class Instruction:
    inst_id: int
    opcode: Opcode
    dest_reg: Optional[str] = None
    src_reg1: Optional[str] = None
    src_reg2: Optional[str] = None
    immediate: int = 0
    pc: int = 0
    predicted_taken: bool = False
    actual_taken: bool = False
    is_speculative: bool = False
    transient_hazard_detected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inst_id": self.inst_id,
            "opcode": self.opcode.value,
            "dest_reg": self.dest_reg,
            "src_reg1": self.src_reg1,
            "src_reg2": self.src_reg2,
            "immediate": self.immediate,
            "pc": self.pc,
            "predicted_taken": self.predicted_taken,
            "actual_taken": self.actual_taken,
            "is_speculative": self.is_speculative,
            "transient_hazard_detected": self.transient_hazard_detected,
        }


@dataclass
class ROBEntry:
    rob_id: int
    instruction: Instruction
    ready: bool = False
    result: Optional[int] = None
    speculative: bool = False
    mispredicted: bool = False


class BranchPredictor:
    """
    2-bit saturating counter branch predictor table.
    States:
      0: Strongly Not Taken
      1: Weakly Not Taken
      2: Weakly Taken
      3: Strongly Taken
    """

    def __init__(self, table_size: int = 64) -> None:
        self.table_size: int = table_size
        self.table: Dict[int, int] = {i: 2 for i in range(table_size)}  # default Weakly Taken

    def _index(self, pc: int) -> int:
        return (pc >> 2) % self.table_size

    def predict(self, pc: int) -> bool:
        idx = self._index(pc)
        state = self.table.get(idx, 2)
        return state >= 2

    def update(self, pc: int, actually_taken: bool) -> None:
        idx = self._index(pc)
        state = self.table.get(idx, 2)
        if actually_taken:
            self.table[idx] = min(3, state + 1)
        else:
            self.table[idx] = max(0, state - 1)


class SubatomicPipelineGovernorFabric:
    """
    Thread-safe micro-architecture pipeline emulator & speculative execution governor.
    """

    def __init__(
        self,
        governor_mode: GovernorMode = GovernorMode.STRICT_MITIGATION,
        rob_capacity: int = 16,
        memory_size: int = 1024,
    ) -> None:
        self._lock = threading.RLock()
        self.governor_mode: GovernorMode = governor_mode
        self.rob_capacity: int = rob_capacity
        self.memory_size: int = memory_size

        # Architectural State
        self.registers: Dict[str, int] = {f"R{i}": 0 for i in range(8)}
        self.memory: Dict[int, int] = {i: 0 for i in range(memory_size)}
        self.pc: int = 0

        # Speculative Checkpoint State
        self._speculative_depth: int = 0
        self._checkpointed_registers: Optional[Dict[str, int]] = None

        # Pipeline Queues & Structures
        self.branch_predictor: BranchPredictor = BranchPredictor()
        self.program: List[Instruction] = []
        self.fetch_queue: List[Instruction] = []
        self.reservation_stations: List[Instruction] = []
        self.rob: List[ROBEntry] = []

        # Metrics & Telemetry
        self.cycles: int = 0
        self.instructions_retired: int = 0
        self.branches_total: int = 0
        self.branches_mispredicted: int = 0
        self.speculative_flushes: int = 0
        self.hazards_intercepted: int = 0
        self.execution_log: List[str] = []

    def set_governor_mode(self, mode: GovernorMode) -> None:
        with self._lock:
            self.governor_mode = mode

    def load_program(self, instructions: List[Instruction]) -> None:
        with self._lock:
            self.program = copy.deepcopy(instructions)
            for idx, inst in enumerate(self.program):
                inst.pc = idx * 4
            self.reset_pipeline()

    def reset_pipeline(self) -> None:
        with self._lock:
            self.pc = 0
            self._speculative_depth = 0
            self._checkpointed_registers = None
            self.fetch_queue.clear()
            self.reservation_stations.clear()
            self.rob.clear()
            self.execution_log.clear()

    def step_cycle(self) -> Dict[str, Any]:
        """
        Executes one clock cycle across all pipeline stages:
        1. Commit / Retire from head of ROB.
        2. Execute ready instructions in Reservation Stations.
        3. Dispatch decoded instructions into RS & ROB.
        4. Fetch next instruction based on PC & branch prediction.
        """
        with self._lock:
            self.cycles += 1
            cycle_events: List[str] = []

            # 1. Commit / Retire Stage
            if self.rob:
                head = self.rob[0]
                if head.ready:
                    if head.mispredicted:
                        # Flush pipeline on branch misprediction!
                        self._handle_misprediction_rollback(head)
                        cycle_events.append(f"Cycle {self.cycles}: Branch mispredict flush ROB#{head.rob_id}")
                    else:
                        # Commit result to architectural register
                        inst = head.instruction
                        if inst.dest_reg and head.result is not None:
                            self.registers[inst.dest_reg] = head.result
                        elif inst.opcode == Opcode.STORE and inst.src_reg1 and inst.src_reg2:
                            addr = self.registers.get(inst.src_reg1, 0)
                            val = self.registers.get(inst.src_reg2, 0)
                            if 0 <= addr < self.memory_size:
                                self.memory[addr] = val
                        
                        self.instructions_retired += 1
                        self.rob.pop(0)
                        if inst.is_speculative and self._speculative_depth > 0:
                            self._speculative_depth -= 1
                            if self._speculative_depth == 0:
                                self._checkpointed_registers = None
                        cycle_events.append(f"Cycle {self.cycles}: Retired Inst#{inst.inst_id} ({inst.opcode.value})")

            # 2. Execution Stage (Out-of-Order execution of RS entries)
            executed_indices: List[int] = []
            for idx, inst in enumerate(self.reservation_stations):
                # Find matching ROB entry
                matching_rob = next((entry for entry in self.rob if entry.instruction.inst_id == inst.inst_id), None)
                if not matching_rob or matching_rob.ready:
                    continue

                # Hazard Detection: Check for speculative out-of-bounds access
                if inst.opcode == Opcode.LOAD and inst.is_speculative:
                    base_addr = self._resolve_reg_value(inst.src_reg1, inst.inst_id) + inst.immediate
                    if base_addr < 0 or base_addr >= self.memory_size:
                        inst.transient_hazard_detected = True
                        self.hazards_intercepted += 1
                        cycle_events.append(
                            f"Cycle {self.cycles}: HAZARD INTERCEPTED - Speculative out-of-bounds load at 0x{base_addr:X}"
                        )
                        if self.governor_mode == GovernorMode.STRICT_MITIGATION:
                            # Mitigate by serializing: mark ROB entry ready with 0 without updating cache/mem
                            matching_rob.ready = True
                            matching_rob.result = 0
                            executed_indices.append(idx)
                            continue

                # Execute instruction
                res, is_mispredict = self._execute_instruction(inst)
                matching_rob.result = res
                matching_rob.ready = True
                matching_rob.mispredicted = is_mispredict
                executed_indices.append(idx)
                cycle_events.append(f"Cycle {self.cycles}: Executed Inst#{inst.inst_id} -> Result: {res}")

            # Remove executed from reservation stations
            for idx in sorted(executed_indices, reverse=True):
                self.reservation_stations.pop(idx)

            # 3. Dispatch Stage (Move from fetch queue to RS & ROB if space available)
            if self.fetch_queue and len(self.rob) < self.rob_capacity:
                inst = self.fetch_queue.pop(0)
                rob_id = len(self.rob) + 1
                rob_entry = ROBEntry(rob_id=rob_id, instruction=inst, speculative=inst.is_speculative)
                self.rob.append(rob_entry)

                # Speculative Governor Inspection at Dispatch:
                if inst.opcode == Opcode.LOAD and inst.is_speculative:
                    base_addr = self._resolve_reg_value(inst.src_reg1, inst.inst_id) + inst.immediate
                    if base_addr < 0 or base_addr >= self.memory_size:
                        inst.transient_hazard_detected = True
                        self.hazards_intercepted += 1
                        cycle_events.append(
                            f"Cycle {self.cycles}: HAZARD INTERCEPTED - Speculative out-of-bounds load at 0x{base_addr:X}"
                        )
                        if self.governor_mode == GovernorMode.STRICT_MITIGATION:
                            rob_entry.ready = True
                            rob_entry.result = 0
                            cycle_events.append(f"Cycle {self.cycles}: Dispatched Inst#{inst.inst_id} to ROB#{rob_id} (mitigated)")
                            inst = None

                if inst is not None:
                    self.reservation_stations.append(inst)
                    cycle_events.append(f"Cycle {self.cycles}: Dispatched Inst#{inst.inst_id} to ROB#{rob_id}")

            # 4. Fetch Stage
            prog_idx = self.pc // 4
            if 0 <= prog_idx < len(self.program) and len(self.fetch_queue) < 4:
                inst_to_fetch = copy.deepcopy(self.program[prog_idx])
                if self._speculative_depth > 0:
                    inst_to_fetch.is_speculative = True

                if inst_to_fetch.opcode in (Opcode.BRANCH_EQ, Opcode.BRANCH_NE):
                    self.branches_total += 1
                    pred = self.branch_predictor.predict(inst_to_fetch.pc)
                    inst_to_fetch.predicted_taken = pred

                    # Checkpoint registers if entering new speculative epoch
                    if self._speculative_depth == 0:
                        self._checkpointed_registers = copy.deepcopy(self.registers)
                    self._speculative_depth += 1
                    inst_to_fetch.is_speculative = True

                    if pred:
                        self.pc = inst_to_fetch.immediate
                    else:
                        self.pc += 4
                elif inst_to_fetch.opcode == Opcode.FENCE:
                    # Speculation fence prevents speculative issue until preceding branch commits
                    if self._speculative_depth > 0 and self.governor_mode != GovernorMode.PERMISSIVE:
                        cycle_events.append(f"Cycle {self.cycles}: FENCE stalled fetch until speculation resolves")
                        # Do not advance PC, stall
                        inst_to_fetch = None
                    else:
                        self.pc += 4
                else:
                    self.pc += 4

                if inst_to_fetch:
                    self.fetch_queue.append(inst_to_fetch)
                    cycle_events.append(f"Cycle {self.cycles}: Fetched Inst#{inst_to_fetch.inst_id} (PC={inst_to_fetch.pc})")

            self.execution_log.extend(cycle_events)
            return {
                "cycle": self.cycles,
                "retired": self.instructions_retired,
                "rob_depth": len(self.rob),
                "rs_depth": len(self.reservation_stations),
                "events": cycle_events,
            }

    def _resolve_reg_value(self, reg_name: Optional[str], current_inst_id: int) -> int:
        if not reg_name:
            return 0
        with self._lock:
            # Check ROB in reverse for the latest value written to reg_name prior to this instruction
            for entry in reversed(self.rob):
                if entry.instruction.inst_id < current_inst_id and entry.instruction.dest_reg == reg_name:
                    if entry.ready and entry.result is not None:
                        return entry.result
            return self.registers.get(reg_name, 0)

    def _execute_instruction(self, inst: Instruction) -> Tuple[Optional[int], bool]:
        """Computes instruction output and returns (result, is_mispredicted)."""
        val1 = self._resolve_reg_value(inst.src_reg1, inst.inst_id)
        val2 = self._resolve_reg_value(inst.src_reg2, inst.inst_id)
        imm = inst.immediate

        if inst.opcode == Opcode.NOP:
            return 0, False
        elif inst.opcode == Opcode.ADD:
            return (val1 + (val2 if inst.src_reg2 else imm)), False
        elif inst.opcode == Opcode.SUB:
            return (val1 - (val2 if inst.src_reg2 else imm)), False
        elif inst.opcode == Opcode.MUL:
            return (val1 * (val2 if inst.src_reg2 else imm)), False
        elif inst.opcode == Opcode.LOAD:
            addr = val1 + imm
            if 0 <= addr < self.memory_size:
                return self.memory.get(addr, 0), False
            return 0, False
        elif inst.opcode == Opcode.STORE:
            return val2, False
        elif inst.opcode == Opcode.FENCE:
            return 0, False
        elif inst.opcode == Opcode.BRANCH_EQ:
            actual = (val1 == val2)
            inst.actual_taken = actual
            self.branch_predictor.update(inst.pc, actual)
            mispredict = (actual != inst.predicted_taken)
            return 1 if actual else 0, mispredict
        elif inst.opcode == Opcode.BRANCH_NE:
            actual = (val1 != val2)
            inst.actual_taken = actual
            self.branch_predictor.update(inst.pc, actual)
            mispredict = (actual != inst.predicted_taken)
            return 1 if actual else 0, mispredict

        return None, False

    def _handle_misprediction_rollback(self, head_entry: ROBEntry) -> None:
        """Flushes speculative pipeline and restores checkpointed registers."""
        self.branches_mispredicted += 1
        self.speculative_flushes += 1

        # Restore architectural register checkpoint
        if self._checkpointed_registers is not None:
            self.registers = copy.deepcopy(self._checkpointed_registers)
            self._checkpointed_registers = None

        self._speculative_depth = 0
        inst = head_entry.instruction

        # Determine target PC based on actual branch condition
        if inst.actual_taken:
            self.pc = inst.immediate
        else:
            self.pc = inst.pc + 4

        # Flush fetch queue, reservation stations, and subsequent ROB entries
        self.fetch_queue.clear()
        self.reservation_stations.clear()
        self.rob.clear()

    def run_until_complete(self, max_cycles: int = 500) -> Dict[str, Any]:
        """Runs the pipeline simulation until all instructions retire or max_cycles is reached."""
        with self._lock:
            start_cycle = self.cycles
            while self.cycles - start_cycle < max_cycles:
                has_work = (
                    (self.pc // 4 < len(self.program))
                    or len(self.fetch_queue) > 0
                    or len(self.reservation_stations) > 0
                    or len(self.rob) > 0
                )
                if not has_work:
                    break
                self.step_cycle()
            return self.status()

    def status(self) -> Dict[str, Any]:
        with self._lock:
            ipc = (self.instructions_retired / max(1, self.cycles))
            mispredict_rate = (
                (self.branches_mispredicted / max(1, self.branches_total)) * 100.0
                if self.branches_total > 0
                else 0.0
            )
            return {
                "stage": STAGE,
                "stage_name": STAGE_NAME,
                "era": ERA,
                "era_name": ERA_NAME,
                "governor_mode": self.governor_mode.value,
                "cycles": self.cycles,
                "instructions_retired": self.instructions_retired,
                "ipc": round(ipc, 4),
                "branches_total": self.branches_total,
                "branches_mispredicted": self.branches_mispredicted,
                "mispredict_rate_pct": round(mispredict_rate, 2),
                "speculative_flushes": self.speculative_flushes,
                "hazards_intercepted": self.hazards_intercepted,
                "rob_depth": len(self.rob),
                "rs_depth": len(self.reservation_stations),
                "registers": copy.deepcopy(self.registers),
            }

    def format_ascii_status(self) -> str:
        s = self.status()
        header = f"+-------------------------------------------------------------------------+\n|      STAGE {s['stage']}: {s['stage_name'].upper()[:52]:<52} |\n|      Era {s['era']}: {s['era_name'][:56]:<56} |\n+-------------------------------------------------------------------------+"
        body = (
            f"| Governor Mode        : {s['governor_mode']:<48} |\n"
            f"| Total Cycles         : {s['cycles']:<48} |\n"
            f"| Instructions Retired : {s['instructions_retired']:<48} |\n"
            f"| Instructions/Cycle   : {s['ipc']:<48} |\n"
            f"| Total Branches       : {s['branches_total']:<48} |\n"
            f"| Mispredictions       : {s['branches_mispredicted']:<48} |\n"
            f"| Mispredict Rate      : {s['mispredict_rate_pct']}%{' ' * (47 - len(str(s['mispredict_rate_pct'])))}|\n"
            f"| Speculative Flushes  : {s['speculative_flushes']:<48} |\n"
            f"| Hazards Intercepted  : {s['hazards_intercepted']:<48} |\n"
            f"| Active ROB Entries   : {s['rob_depth']:<48} |\n"
            f"| Active RS Entries    : {s['rs_depth']:<48} |"
        )
        footer = "+-------------------------------------------------------------------------+"
        return f"{header}\n{body}\n{footer}"
