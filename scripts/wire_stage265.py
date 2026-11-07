"""
Wiring script for Stage 265: Continuous-Time Quantum Walk & Graph-Topological Spatial Search Accelerator
Author: Senin (Senin Ali K P)
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Import
    target_imp = "from backend.lucy_core.topological_skyrmion_weaver import TopologicalSkyrmionWeaverFabric, STAGE as STAGE_264"
    repl_imp = target_imp + "\nfrom backend.lucy_core.continuous_quantum_walk_search import ContinuousQuantumWalkSearchFabric, STAGE as STAGE_265"
    if target_imp in text and repl_imp not in text:
        text = text.replace(target_imp, repl_imp, 1)

    # Init
    target_init = "self.skyrmion_weaver = TopologicalSkyrmionWeaverFabric()"
    repl_init = target_init + "\n        # Stage 265: Continuous-Time Quantum Walk & Spatial Search (Era 27)\n        self.quantum_walk_search = ContinuousQuantumWalkSearchFabric()"
    if target_init in text and repl_init not in text:
        text = text.replace(target_init, repl_init, 1)

    # Supervisor services
    target_svc = '("skyrmion_weaver", "core"),'
    repl_svc = target_svc + '\n            ("quantum_walk_search", "core"),'
    if target_svc in text and repl_svc not in text:
        text = text.replace(target_svc, repl_svc, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully wired Stage 265 into lucy_runtime.py")


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = 'return RouterResponse("Usage: /skyrmion-racetrack <bit_sequence>")'
    insertion = """

        # --- Stage 265: Continuous-Time Quantum Walk & Graph-Topological Spatial Search Accelerator ---
        if lowered in ("/quantum-walk-status", "quantum-walk-status"):
            if hasattr(self.runtime, "quantum_walk_search"):
                st = self.runtime.quantum_walk_search.get_status()
                msg = (
                    f"Quantum Walk Accelerator: Nodes={st['num_nodes']}, Edges={st['num_edges']}, "
                    f"Gamma={st['hopping_rate_gamma']}, Searches Executed={st['total_searches_executed']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Quantum Walk Search accelerator not initialized.")

        if lowered.startswith("/qw-propagate ") or lowered.startswith("qw-propagate "):
            if hasattr(self.runtime, "quantum_walk_search"):
                parts = raw_text.strip().split()
                t_val = float(parts[1]) if len(parts) >= 2 else 1.0
                res = self.runtime.quantum_walk_search.propagate_quantum_state(evolution_time=t_val)
                msg = (
                    f"Quantum Walk Propagate (t={t_val}): Norm={res['state_norm']}, "
                    f"Max Prob={max(res['probabilities']):.4f}."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /qw-propagate <evolution_time>")

        if lowered.startswith("/qw-search ") or lowered.startswith("qw-search "):
            if hasattr(self.runtime, "quantum_walk_search"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    tgt = int(parts[1])
                    depth = float(parts[2]) if len(parts) >= 3 else 2.0
                    res = self.runtime.quantum_walk_search.execute_spatial_search(target_node=tgt, oracle_depth=depth)
                    msg = (
                        f"Continuous Quantum Search: Target={res['target_node']}, Peak Prob={res['peak_success_probability']:.4f} "
                        f"at t={res['optimal_time_t']:.2f} (Speedup: {res['quantum_advantage_factor']:.2f}x)."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /qw-search <target_node> [oracle_depth]")

        if lowered.startswith("/qw-topology ") or lowered.startswith("qw-topology "):
            if hasattr(self.runtime, "quantum_walk_search"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    top = parts[1].lower()
                    if top == "complete":
                        self.runtime.quantum_walk_search.set_topology_complete()
                    elif top == "star":
                        self.runtime.quantum_walk_search.set_topology_star()
                    else:
                        self.runtime.quantum_walk_search.set_topology_cycle()
                    st = self.runtime.quantum_walk_search.get_status()
                    msg = f"Quantum Walk Topology switched to '{top}': Nodes={st['num_nodes']}, Edges={st['num_edges']}."
                    return RouterResponse(msg, data=st)
            return RouterResponse("Usage: /qw-topology <cycle|complete|star>")"""

    if "quantum-walk-status" not in text:
        text = text.replace(target, target + insertion, 1)
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Successfully wired Stage 265 into router.py")
    else:
        print("Stage 265 already wired in router.py")


if __name__ == '__main__':
    wire_runtime()
    wire_router()
