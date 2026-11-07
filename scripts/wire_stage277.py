"""
Wiring script for Stage 277: Autonomous Non-Linear Soliton Korteweg-de Vries (KdV) Integrable Wave Synthesizer
Author: Senin (Senin Ali K P)
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Import
    target_imp = "from backend.lucy_core.quantum_teleportation_repeater_fabric import QuantumTeleportationRepeaterFabricFabric, STAGE as STAGE_276"
    repl_imp = target_imp + "\nfrom backend.lucy_core.kdv_integrable_soliton_synthesizer import KdVIntegrableSolitonSynthesizerFabric, STAGE as STAGE_277"
    if target_imp in text and repl_imp not in text:
        text = text.replace(target_imp, repl_imp, 1)

    # Init
    target_init = "self.quantum_repeater_fabric = QuantumTeleportationRepeaterFabricFabric()"
    repl_init = target_init + "\n        # Stage 277: KdV Non-Linear Soliton Integrable Synthesizer (Era 28)\n        self.kdv_soliton_synthesizer = KdVIntegrableSolitonSynthesizerFabric()"
    if target_init in text and repl_init not in text:
        text = text.replace(target_init, repl_init, 1)

    # Supervisor services
    target_svc = '("quantum_repeater_fabric", "core"),'
    repl_svc = target_svc + '\n            ("kdv_soliton_synthesizer", "core"),'
    if target_svc in text and repl_svc not in text:
        text = text.replace(target_svc, repl_svc, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully wired Stage 277 into lucy_runtime.py")


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = 'return RouterResponse("Usage: /multipartite-state <GHZ|W> [num_qubits] [lost_qubit_idx]")'
    insertion = """

        # --- Stage 277: Autonomous Non-Linear Soliton Korteweg-de Vries (KdV) Integrable Wave Synthesizer ---
        if lowered in ("/kdv-status", "kdv-status"):
            if hasattr(self.runtime, "kdv_soliton_synthesizer"):
                st = self.runtime.kdv_soliton_synthesizer.get_status()
                msg = (
                    f"KdV Soliton Synthesizer: Grid Points={st['grid_points']}, "
                    f"Mass I1={st['canonical_mass_i1']:.4f}, Energy I2={st['canonical_energy_i2']:.4f}, Syntheses={st['total_syntheses']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("KdV Soliton Synthesizer not initialized.")

        if lowered.startswith("/kdv-1soliton ") or lowered.startswith("kdv-1soliton "):
            if hasattr(self.runtime, "kdv_soliton_synthesizer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    k_val = float(parts[1])
                    t_val = float(parts[2]) if len(parts) >= 3 else 0.0
                    x0 = float(parts[3]) if len(parts) >= 4 else 0.0
                    res = self.runtime.kdv_soliton_synthesizer.evaluate_1_soliton(kappa=k_val, t=t_val, x_0=x0)
                    msg = (
                        f"KdV 1-Soliton (kappa={k_val}, t={t_val}): Amplitude={res['peak_amplitude']:.4f}, "
                        f"Speed={res['soliton_speed']:.4f}, Mass I1={res['exact_mass_i1']:.4f}, Energy I2={res['exact_energy_i2']:.4f}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /kdv-1soliton <kappa> [t] [x0]")

        if lowered.startswith("/kdv-2soliton ") or lowered.startswith("kdv-2soliton "):
            if hasattr(self.runtime, "kdv_soliton_synthesizer"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    k1 = float(parts[1])
                    k2 = float(parts[2])
                    t_val = float(parts[3]) if len(parts) >= 4 else 0.0
                    res = self.runtime.kdv_soliton_synthesizer.evaluate_2_soliton_collision(kappa_1=k1, kappa_2=k2, t=t_val)
                    msg = (
                        f"KdV 2-Soliton Collision (k1={k1}, k2={k2}, t={t_val}): Coupling A12={res['interaction_coupling_a12']:.5f}, "
                        f"Phase Shifts: delta1={res['phase_shift_1']:.3f}, delta2={res['phase_shift_2']:.3f}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /kdv-2soliton <kappa1> <kappa2> [t]")

        if lowered.startswith("/kdv-invariants ") or lowered.startswith("kdv-invariants "):
            if hasattr(self.runtime, "kdv_soliton_synthesizer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    k_val = float(parts[1])
                    sol = self.runtime.kdv_soliton_synthesizer.evaluate_1_soliton(kappa=k_val)
                    inv = self.runtime.kdv_soliton_synthesizer.compute_discrete_invariants(sol["profile"])
                    msg = f"KdV Invariants (kappa={k_val}): Discrete Mass I1={inv['mass_i1']:.4f}, Discrete Energy I2={inv['energy_i2']:.4f}."
                    return RouterResponse(msg, data={"analytical": sol, "discrete": inv})
            return RouterResponse("Usage: /kdv-invariants <kappa>")"""

    if "kdv-status" not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Successfully wired Stage 277 into router.py")
    else:
        print("Stage 277 already wired in router.py")


if __name__ == '__main__':
    wire_runtime()
    wire_router()
