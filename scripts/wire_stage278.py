"""
Wiring script for Stage 278: Microscopic Casimir-Polder Vacuum Dispersion Force & Metamaterial Levitation Engine
Author: Senin (Senin Ali K P)
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Import
    target_imp = "from backend.lucy_core.kdv_integrable_soliton_synthesizer import KdVIntegrableSolitonSynthesizerFabric, STAGE as STAGE_277"
    repl_imp = target_imp + "\nfrom backend.lucy_core.casimir_polder_vacuum_engine import CasimirPolderVacuumEngineFabric, STAGE as STAGE_278"
    if target_imp in text and repl_imp not in text:
        text = text.replace(target_imp, repl_imp, 1)

    # Init
    target_init = "self.kdv_soliton_synthesizer = KdVIntegrableSolitonSynthesizerFabric()"
    repl_init = target_init + "\n        # Stage 278: Casimir-Polder Vacuum & Metamaterial Levitation Engine (Era 28)\n        self.casimir_vacuum_engine = CasimirPolderVacuumEngineFabric()"
    if target_init in text and repl_init not in text:
        text = text.replace(target_init, repl_init, 1)

    # Supervisor services
    target_svc = '("kdv_soliton_synthesizer", "core"),'
    repl_svc = target_svc + '\n            ("casimir_vacuum_engine", "core"),'
    if target_svc in text and repl_svc not in text:
        text = text.replace(target_svc, repl_svc, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully wired Stage 278 into lucy_runtime.py")


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = 'return RouterResponse("Usage: /kdv-invariants <kappa>")'
    insertion = """

        # --- Stage 278: Microscopic Casimir-Polder Vacuum Dispersion Force & Metamaterial Levitation Engine ---
        if lowered in ("/casimir-status", "casimir-status"):
            if hasattr(self.runtime, "casimir_vacuum_engine"):
                st = self.runtime.casimir_vacuum_engine.get_status()
                msg = (
                    f"Casimir-Polder Vacuum Engine: Plate Area={st['plate_area_m2']:.1e} m^2, "
                    f"P(100nm)={st['casimir_pressure_at_100nm_pa']:.3f} Pa, Levitation Tests={st['total_levitation_tests']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Casimir Vacuum Engine not initialized.")

        if lowered.startswith("/casimir-ideal ") or lowered.startswith("casimir-ideal "):
            if hasattr(self.runtime, "casimir_vacuum_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    d_nm = float(parts[1])
                    res = self.runtime.casimir_vacuum_engine.compute_ideal_casimir_pressure(separation_d_m=d_nm * 1e-9)
                    msg = (
                        f"Ideal Casimir Force (d={d_nm} nm): Pressure={res['pressure_pascal']:.4e} Pa, "
                        f"Force={res['force_newtons']:.4e} N ({res['force_sign']})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /casimir-ideal <separation_nm>")

        if lowered.startswith("/casimir-polder ") or lowered.startswith("casimir-polder "):
            if hasattr(self.runtime, "casimir_vacuum_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    d_nm = float(parts[1])
                    eps = float(parts[2]) if len(parts) >= 3 else 4.0
                    res = self.runtime.casimir_vacuum_engine.compute_casimir_polder_potential(distance_d_m=d_nm * 1e-9, surface_permittivity=eps)
                    msg = (
                        f"Casimir-Polder Atom Potential (d={d_nm} nm, eps={eps}): U={res['potential_ev']:.4e} eV "
                        f"({res['potential_joules']:.4e} J), Force={res['force_newtons']:.4e} N."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /casimir-polder <distance_nm> [permittivity]")

        if lowered.startswith("/casimir-levitate ") or lowered.startswith("casimir-levitate "):
            if hasattr(self.runtime, "casimir_vacuum_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    e1, em, e2 = float(parts[1]), float(parts[2]), float(parts[3])
                    d_nm = float(parts[4]) if len(parts) >= 5 else 50.0
                    res = self.runtime.casimir_vacuum_engine.evaluate_repulsive_casimir_levitation(
                        eps_plate_1=e1, eps_fluid_medium=em, eps_plate_2=e2, separation_d_m=d_nm * 1e-9
                    )
                    msg = (
                        f"Quantum Levitation Check (eps1={e1}, em={em}, eps2={e2}): DLP Repulsive={res['dlp_condition_satisfied']}, "
                        f"Pressure={res['casimir_pressure_pa']:.2e} Pa, Net Force={res['net_force_n']:.2e} N, Stably Levitated={res['is_stably_levitated']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /casimir-levitate <eps1> <eps_medium> <eps2> [separation_nm]")"""

    if "casimir-status" not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Successfully wired Stage 278 into router.py")
    else:
        print("Stage 278 already wired in router.py")


if __name__ == '__main__':
    wire_runtime()
    wire_router()
