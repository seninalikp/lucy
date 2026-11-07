"""
Wiring script for Stage 272: Non-Commutative Moyal-Weyl Spacetime Star-Product Algebra & Quantum Gravity Uncertainty Engine
Author: Senin (Senin Ali K P)
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Import
    target_imp = "from backend.lucy_core.qcd_color_flux_confinement import QCDColorFluxConfinementFabric, STAGE as STAGE_271"
    repl_imp = target_imp + "\nfrom backend.lucy_core.noncommutative_moyal_star_algebra import NoncommutativeMoyalStarAlgebraFabric, STAGE as STAGE_272"
    if target_imp in text and repl_imp not in text:
        text = text.replace(target_imp, repl_imp, 1)

    # Init
    target_init = "self.qcd_confinement = QCDColorFluxConfinementFabric()"
    repl_init = target_init + "\n        # Stage 272: Non-Commutative Moyal Star Algebra & GUP (Era 28)\n        self.moyal_algebra = NoncommutativeMoyalStarAlgebraFabric()"
    if target_init in text and repl_init not in text:
        text = text.replace(target_init, repl_init, 1)

    # Supervisor services
    target_svc = '("qcd_confinement", "core"),'
    repl_svc = target_svc + '\n            ("moyal_algebra", "core"),'
    if target_svc in text and repl_svc not in text:
        text = text.replace(target_svc, repl_svc, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully wired Stage 272 into lucy_runtime.py")


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = 'return RouterResponse("Usage: /qcd-hadronize [quark_mass_gev]")'
    insertion = """

        # --- Stage 272: Non-Commutative Moyal-Weyl Spacetime Star-Product Algebra & Quantum Gravity Uncertainty Engine ---
        if lowered in ("/moyal-status", "moyal-status"):
            if hasattr(self.runtime, "moyal_algebra"):
                st = self.runtime.moyal_algebra.get_status()
                msg = (
                    f"Moyal Star Algebra: Theta={st['theta_scale_m2']:.2e} m^2, "
                    f"GUP Minimal Length={st['minimal_observable_length_m']:.2e} m, Star Operations={st['total_star_evaluations']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Moyal Star Algebra engine not initialized.")

        if lowered.startswith("/moyal-star ") or lowered.startswith("moyal-star "):
            if hasattr(self.runtime, "moyal_algebra"):
                parts = raw_text.strip().split()
                if len(parts) >= 7:
                    fv, fx, fy, gv, gx, gy = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]), float(parts[5]), float(parts[6])
                    res = self.runtime.moyal_algebra.compute_moyal_star_product_2d(
                        f_val=fv, df_dx=fx, df_dy=fy, d2f_dxdy=0.0,
                        g_val=gv, dg_dx=gx, dg_dy=gy, d2g_dxdy=0.0
                    )
                    msg = (
                        f"Moyal Star Product: (f * g) = {res['star_product_repr']}, "
                        f"Poisson Bracket={res['poisson_bracket']:.4f}, Moyal Bracket={res['moyal_bracket']:.2e}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /moyal-star <f_val> <df_dx> <df_dy> <g_val> <dg_dx> <dg_dy>")

        if lowered.startswith("/gup-uncertainty ") or lowered.startswith("gup-uncertainty "):
            if hasattr(self.runtime, "moyal_algebra"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    dp = float(parts[1])
                    res = self.runtime.moyal_algebra.compute_gup_uncertainty(delta_p_kg_m_s=dp)
                    msg = (
                        f"GUP Bound (dp={dp:.2e}): dx_GUP={res['gup_dx_m']:.2e} m, "
                        f"dx_Heisenberg={res['heisenberg_dx_m']:.2e} m, dx_min={res['minimal_observable_length_m']:.2e} m."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /gup-uncertainty <delta_p>")

        if lowered.startswith("/uv-ir-mixing ") or lowered.startswith("uv-ir-mixing "):
            if hasattr(self.runtime, "moyal_algebra"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    p_val = float(parts[1])
                    res = self.runtime.moyal_algebra.compute_uv_ir_mixing_scale(external_momentum_p=p_val)
                    msg = (
                        f"UV/IR Mixing (p={p_val:.2e}): Lambda_eff={res['effective_cutoff_lambda_eff']:.2e}, "
                        f"Mixing Ratio={res['mixing_ratio']:.2e}, IR Dominated={res['is_ir_divergence_dominated']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /uv-ir-mixing <momentum_p>")"""

    if "moyal-status" not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Successfully wired Stage 272 into router.py")
    else:
        print("Stage 272 already wired in router.py")


if __name__ == '__main__':
    wire_runtime()
    wire_router()
