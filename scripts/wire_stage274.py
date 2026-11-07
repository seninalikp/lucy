"""
Wiring script for Stage 274: Relativistic Plasma Shock Magnetosonic Wave Accelerator & Fermi Cosmic-Ray Compressor
Author: Senin (Senin Ali K P)
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Import
    target_imp = "from backend.lucy_core.fractional_anyon_braiding_processor import FractionalAnyonBraidingProcessorFabric, STAGE as STAGE_273"
    repl_imp = target_imp + "\nfrom backend.lucy_core.relativistic_plasma_shock_accelerator import RelativisticPlasmaShockAcceleratorFabric, STAGE as STAGE_274"
    if target_imp in text and repl_imp not in text:
        text = text.replace(target_imp, repl_imp, 1)

    # Init
    target_init = "self.anyon_processor = FractionalAnyonBraidingProcessorFabric()"
    repl_init = target_init + "\n        # Stage 274: Relativistic Plasma Shock Accelerator & Fermi Engine (Era 28)\n        self.plasma_shock_accelerator = RelativisticPlasmaShockAcceleratorFabric()"
    if target_init in text and repl_init not in text:
        text = text.replace(target_init, repl_init, 1)

    # Supervisor services
    target_svc = '("anyon_processor", "core"),'
    repl_svc = target_svc + '\n            ("plasma_shock_accelerator", "core"),'
    if target_svc in text and repl_svc not in text:
        text = text.replace(target_svc, repl_svc, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully wired Stage 274 into lucy_runtime.py")


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = 'return RouterResponse("Usage: /anyon-braid <move1> <move2> ... (e.g. 1 2 1)")'
    insertion = """

        # --- Stage 274: Relativistic Plasma Shock Magnetosonic Wave Accelerator & Fermi Cosmic-Ray Compressor ---
        if lowered in ("/shock-status", "shock-status"):
            if hasattr(self.runtime, "plasma_shock_accelerator"):
                st = self.runtime.plasma_shock_accelerator.get_status()
                msg = (
                    f"Plasma Shock Accelerator: Shock Speed={st['shock_speed_c']} c, "
                    f"Compression Ratio r={st['compression_ratio_r']:.2f}, Spectral Index p={st['asymptotic_spectral_index_p']:.2f}, "
                    f"Hillas Max={st['hillas_max_energy_pev']:.2f} PeV."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Plasma Shock Accelerator not initialized.")

        if lowered.startswith("/shock-jumps") or lowered.startswith("shock-jumps"):
            if hasattr(self.runtime, "plasma_shock_accelerator"):
                parts = raw_text.strip().split()
                m_val = float(parts[1]) if len(parts) >= 2 else 20.0
                res = self.runtime.plasma_shock_accelerator.compute_shock_jump_conditions(mach_number=m_val)
                msg = (
                    f"Rankine-Hugoniot Shock (Mach={m_val}): Compression r={res['compression_ratio_r']:.3f} "
                    f"(r_max={res['asymptotic_r_max']}), B_2={res['downstream_b_tesla']:.2e} T, u_2={res['downstream_speed_m_s']:.1f} m/s."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /shock-jumps [mach_number]")

        if lowered.startswith("/fermi-acceleration") or lowered.startswith("fermi-acceleration"):
            if hasattr(self.runtime, "plasma_shock_accelerator"):
                parts = raw_text.strip().split()
                m_val = float(parts[1]) if len(parts) >= 2 else 20.0
                cycles = int(parts[2]) if len(parts) >= 3 else 50
                res = self.runtime.plasma_shock_accelerator.compute_fermi_acceleration_spectrum(mach_number=m_val, num_cycles=cycles)
                msg = (
                    f"Fermi Shock Acceleration ({cycles} cycles): E_final={res['final_energy_gev']:.2f} GeV "
                    f"({res['energy_amplification_factor']:.1f}x gain), Spectral Index p={res['spectral_index_p']:.2f}."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /fermi-acceleration [mach_number] [cycles]")

        if lowered.startswith("/hillas-limit") or lowered.startswith("hillas-limit"):
            if hasattr(self.runtime, "plasma_shock_accelerator"):
                parts = raw_text.strip().split()
                r_pc = float(parts[1]) if len(parts) >= 2 else 10.0
                z_chg = int(parts[2]) if len(parts) >= 3 else 1
                r_m = r_pc * 3.086e16
                res = self.runtime.plasma_shock_accelerator.compute_hillas_maximum_energy(shock_radius_m=r_m, charge_number_z=z_chg)
                msg = (
                    f"Hillas Upper Bound (R={r_pc} pc, Z={z_chg}): E_max={res['max_energy_pev']:.4f} PeV "
                    f"({res['max_energy_ev']:.2e} eV, Knee Regime: {res['cosmic_ray_knee_regime']})."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /hillas-limit [shock_radius_pc] [charge_z]")"""

    if "shock-status" not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Successfully wired Stage 274 into router.py")
    else:
        print("Stage 274 already wired in router.py")


if __name__ == '__main__':
    wire_runtime()
    wire_router()
