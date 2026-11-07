"""
Wiring script for Stage 271: Quantum Chromodynamic (QCD) Asymptotic Freedom, Color Flux Tube Confinement & Hadronization Engine
Author: Senin (Senin Ali K P)
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Import
    target_imp = "from backend.lucy_core.era27_master_seal import Era27MasterSealFabric, STAGE as STAGE_270"
    repl_imp = target_imp + "\nfrom backend.lucy_core.qcd_color_flux_confinement import QCDColorFluxConfinementFabric, STAGE as STAGE_271"
    if target_imp in text and repl_imp not in text:
        text = text.replace(target_imp, repl_imp, 1)

    # Init
    target_init = "self.era27_master_seal = Era27MasterSealFabric()"
    repl_init = target_init + "\n        # Stage 271: QCD Color Flux Confinement & Hadronization (Era 28)\n        self.qcd_confinement = QCDColorFluxConfinementFabric()"
    if target_init in text and repl_init not in text:
        text = text.replace(target_init, repl_init, 1)

    # Supervisor services
    target_svc = '("era27_master_seal", "core"),'
    repl_svc = target_svc + '\n            ("qcd_confinement", "core"),'
    if target_svc in text and repl_svc not in text:
        text = text.replace(target_svc, repl_svc, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully wired Stage 271 into lucy_runtime.py")


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = 'return RouterResponse("Era 27 Master Seal not initialized.")'
    insertion = """

        # --- Stage 271: Quantum Chromodynamic (QCD) Asymptotic Freedom, Color Flux Tube Confinement & Hadronization Engine ---
        if lowered in ("/qcd-status", "qcd-status"):
            if hasattr(self.runtime, "qcd_confinement"):
                st = self.runtime.qcd_confinement.get_status()
                msg = (
                    f"QCD Confinement Engine: Lambda_QCD={st['lambda_qcd_gev']} GeV, Sigma={st['string_tension_sigma_gev_fm']} GeV/fm, "
                    f"alpha_s(1 GeV)={st['alpha_s_at_1_gev']:.3f}, alpha_s(100 GeV)={st['alpha_s_at_100_gev']:.3f}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("QCD Confinement engine not initialized.")

        if lowered.startswith("/qcd-coupling ") or lowered.startswith("qcd-coupling "):
            if hasattr(self.runtime, "qcd_confinement"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    q_val = float(parts[1])
                    res = self.runtime.qcd_confinement.compute_running_coupling(q_gev=q_val)
                    msg = (
                        f"QCD Running Coupling at Q={q_val} GeV: alpha_s={res['alpha_s']:.4f} "
                        f"(Asymptotically Free: {res['is_asymptotically_free']}, beta_0={res['beta_0']})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /qcd-coupling <q_gev>")

        if lowered.startswith("/qcd-cornell ") or lowered.startswith("qcd-cornell "):
            if hasattr(self.runtime, "qcd_confinement"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    r_val = float(parts[1])
                    res = self.runtime.qcd_confinement.compute_cornell_potential(separation_r_fm=r_val)
                    msg = (
                        f"Cornell Potential at r={r_val} fm: V_total={res['v_total_gev']:.3f} GeV "
                        f"(Coulomb: {res['v_coulomb_gev']:.3f} GeV, String: {res['v_string_gev']:.3f} GeV, Force: {res['restoring_force_gev_fm']:.3f} GeV/fm)."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /qcd-cornell <separation_r_fm>")

        if lowered.startswith("/qcd-hadronize") or lowered.startswith("qcd-hadronize"):
            if hasattr(self.runtime, "qcd_confinement"):
                parts = raw_text.strip().split()
                mq = float(parts[1]) if len(parts) >= 2 else 0.33
                res = self.runtime.qcd_confinement.simulate_flux_tube_breaking(quark_mass_gev=mq)
                msg = (
                    f"Color Flux Tube Snap (m_q={mq} GeV): Snapped={res['tube_snapped']}, "
                    f"Threshold={res['pair_creation_threshold_gev']} GeV, Fragments={res['hadron_fragments']}."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /qcd-hadronize [quark_mass_gev]")"""

    if "qcd-status" not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Successfully wired Stage 271 into router.py")
    else:
        print("Stage 271 already wired in router.py")


if __name__ == '__main__':
    wire_runtime()
    wire_router()
