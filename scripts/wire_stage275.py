"""
Wiring script for Stage 275: Autonomous Gravitational Lensing Caustic & Relativistic Light-Deflection Raytracer
Author: Senin (Senin Ali K P)
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Import
    target_imp = "from backend.lucy_core.relativistic_plasma_shock_accelerator import RelativisticPlasmaShockAcceleratorFabric, STAGE as STAGE_274"
    repl_imp = target_imp + "\nfrom backend.lucy_core.gravitational_lensing_caustic_tracer import GravitationalLensingCausticTracerFabric, STAGE as STAGE_275"
    if target_imp in text and repl_imp not in text:
        text = text.replace(target_imp, repl_imp, 1)

    # Init
    target_init = "self.plasma_shock_accelerator = RelativisticPlasmaShockAcceleratorFabric()"
    repl_init = target_init + "\n        # Stage 275: Gravitational Lensing Caustic Raytracer (Era 28)\n        self.lensing_caustic_tracer = GravitationalLensingCausticTracerFabric()"
    if target_init in text and repl_init not in text:
        text = text.replace(target_init, repl_init, 1)

    # Supervisor services
    target_svc = '("plasma_shock_accelerator", "core"),'
    repl_svc = target_svc + '\n            ("lensing_caustic_tracer", "core"),'
    if target_svc in text and repl_svc not in text:
        text = text.replace(target_svc, repl_svc, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully wired Stage 275 into lucy_runtime.py")


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = 'return RouterResponse("Usage: /hillas-limit [shock_radius_pc] [charge_z]")'
    insertion = """

        # --- Stage 275: Autonomous Gravitational Lensing Caustic & Relativistic Light-Deflection Raytracer ---
        if lowered in ("/lensing-status", "lensing-status"):
            if hasattr(self.runtime, "lensing_caustic_tracer"):
                st = self.runtime.lensing_caustic_tracer.get_status()
                msg = (
                    f"Gravitational Lensing Tracer: Lens Mass={st['lens_mass_solar']:.1e} M_sun, "
                    f"Einstein Radius={st['einstein_radius_arcsec']:.4f} arcsec ({st['einstein_radius_kpc']:.2f} kpc), Simulations={st['total_raytrace_simulations']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Gravitational Lensing tracer not initialized.")

        if lowered in ("/lensing-einstein", "lensing-einstein"):
            if hasattr(self.runtime, "lensing_caustic_tracer"):
                res = self.runtime.lensing_caustic_tracer.compute_einstein_radius()
                msg = (
                    f"Einstein Ring Radius: theta_E={res['theta_e_arcsec']:.4f} arcsec "
                    f"({res['theta_e_rad']:.2e} rad), Physical Radius={res['einstein_radius_kpc']:.2f} kpc, R_s={res['schwarzschild_radius_m']:.2e} m."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Gravitational Lensing tracer not initialized.")

        if lowered.startswith("/lensing-images ") or lowered.startswith("lensing-images "):
            if hasattr(self.runtime, "lensing_caustic_tracer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    beta_val = float(parts[1])
                    res = self.runtime.lensing_caustic_tracer.solve_image_positions(source_pos_arcsec=beta_val)
                    msg = (
                        f"Lensed Images (beta={beta_val} arcsec): theta_+={res['image_plus_arcsec']:.4f} (mu_+={res['magnification_plus']:.2f}), "
                        f"theta_-={res['image_minus_arcsec']:.4f} (mu_-={res['magnification_minus']:.2f}), Total Mag={res['magnification_total']:.2f}x."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /lensing-images <source_beta_arcsec>")

        if lowered.startswith("/lensing-time-delay ") or lowered.startswith("lensing-time-delay "):
            if hasattr(self.runtime, "lensing_caustic_tracer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    beta_val = float(parts[1])
                    res = self.runtime.lensing_caustic_tracer.compute_relative_time_delay(source_pos_arcsec=beta_val)
                    msg = (
                        f"Lensing Time Delay (beta={beta_val} arcsec): Delta_t={res['time_delay_days']:.2f} days "
                        f"({res['time_delay_seconds']:.2e} s, Geometric Fraction={res['geometric_component_fraction']:.2f})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /lensing-time-delay <source_beta_arcsec>")"""

    if "lensing-status" not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Successfully wired Stage 275 into router.py")
    else:
        print("Stage 275 already wired in router.py")


if __name__ == '__main__':
    wire_runtime()
    wire_router()
