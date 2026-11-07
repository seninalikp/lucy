"""
Wiring script for Stage 276: Quantum Teleportation Entanglement Swapping & Multipartite GHZ-W State Repeater Fabric
Author: Senin (Senin Ali K P)
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Import
    target_imp = "from backend.lucy_core.gravitational_lensing_caustic_tracer import GravitationalLensingCausticTracerFabric, STAGE as STAGE_275"
    repl_imp = target_imp + "\nfrom backend.lucy_core.quantum_teleportation_repeater_fabric import QuantumTeleportationRepeaterFabricFabric, STAGE as STAGE_276"
    if target_imp in text and repl_imp not in text:
        text = text.replace(target_imp, repl_imp, 1)

    # Init
    target_init = "self.lensing_caustic_tracer = GravitationalLensingCausticTracerFabric()"
    repl_init = target_init + "\n        # Stage 276: Quantum Teleportation & Entanglement Repeater Fabric (Era 28)\n        self.quantum_repeater_fabric = QuantumTeleportationRepeaterFabricFabric()"
    if target_init in text and repl_init not in text:
        text = text.replace(target_init, repl_init, 1)

    # Supervisor services
    target_svc = '("lensing_caustic_tracer", "core"),'
    repl_svc = target_svc + '\n            ("quantum_repeater_fabric", "core"),'
    if target_svc in text and repl_svc not in text:
        text = text.replace(target_svc, repl_svc, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully wired Stage 276 into lucy_runtime.py")


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = 'return RouterResponse("Usage: /lensing-time-delay <source_beta_arcsec>")'
    insertion = """

        # --- Stage 276: Quantum Teleportation Entanglement Swapping & Multipartite GHZ-W State Repeater Fabric ---
        if lowered in ("/teleport-status", "teleport-status"):
            if hasattr(self.runtime, "quantum_repeater_fabric"):
                st = self.runtime.quantum_repeater_fabric.get_status()
                msg = (
                    f"Quantum Teleportation & Repeater Fabric: Channel Fidelity={st['default_channel_fidelity']}, "
                    f"Swapped Repeater Fidelity={st['swapped_repeater_fidelity']:.4f}, Non-locality={st['chsh_violation_possible']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Quantum Repeater Fabric not initialized.")

        if lowered.startswith("/teleport-state ") or lowered.startswith("teleport-state "):
            if hasattr(self.runtime, "quantum_repeater_fabric"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    a_val = float(parts[1])
                    b_val = float(parts[2])
                    bsm = parts[3] if len(parts) >= 4 else "00"
                    res = self.runtime.quantum_repeater_fabric.execute_teleportation_protocol(
                        alpha=complex(a_val, 0.0), beta=complex(b_val, 0.0), measured_bsm=bsm
                    )
                    msg = (
                        f"Teleported |psi> = {res['input_state']} -> BSM='{res['bsm_outcome']}', "
                        f"Correction='{res['applied_correction']}', Fidelity={res['fidelity']*100:.2f}%."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /teleport-state <alpha_r> <beta_r> [bsm_bits_00_01_10_11]")

        if lowered.startswith("/swap-entanglement") or lowered.startswith("swap-entanglement"):
            if hasattr(self.runtime, "quantum_repeater_fabric"):
                parts = raw_text.strip().split()
                f1 = float(parts[1]) if len(parts) >= 2 else None
                f2 = float(parts[2]) if len(parts) >= 3 else None
                res = self.runtime.quantum_repeater_fabric.execute_entanglement_swapping(link_1_fidelity=f1, link_2_fidelity=f2)
                msg = (
                    f"Entanglement Swapping: Swapped Fidelity={res['swapped_fidelity']:.4f}, "
                    f"CHSH S-Parameter={res['chsh_s_parameter']:.3f} (Violates Local Realism: {res['quantum_nonlocality_verified']})."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /swap-entanglement [f1] [f2]")

        if lowered.startswith("/multipartite-state ") or lowered.startswith("multipartite-state "):
            if hasattr(self.runtime, "quantum_repeater_fabric"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    st_type = parts[1].upper()
                    n_q = int(parts[2]) if len(parts) >= 3 else 3
                    lost_idx = int(parts[3]) if len(parts) >= 4 else None
                    res = self.runtime.quantum_repeater_fabric.synthesize_multipartite_state(
                        state_type=st_type, num_qubits=n_q, qubit_loss_index=lost_idx
                    )
                    msg = (
                        f"Multipartite {st_type} (N={n_q}, Loss={lost_idx}): Residual Concurrence={res['residual_entanglement_concurrence']:.2f}, "
                        f"Robustness={res['loss_robustness']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /multipartite-state <GHZ|W> [num_qubits] [lost_qubit_idx]")"""

    if "teleport-status" not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Successfully wired Stage 276 into router.py")
    else:
        print("Stage 276 already wired in router.py")


if __name__ == '__main__':
    wire_runtime()
    wire_router()
