"""
Wiring script for Stage 266: Planetary Magnetohydrodynamic (MHD) Dynamo Alfven Wave Plasma Core Simulator
Author: Senin (Senin Ali K P)
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Import
    target_imp = "from backend.lucy_core.continuous_quantum_walk_search import ContinuousQuantumWalkSearchFabric, STAGE as STAGE_265"
    repl_imp = target_imp + "\nfrom backend.lucy_core.magnetohydrodynamic_dynamo_sim import MagnetohydrodynamicDynamoSimFabric, STAGE as STAGE_266"
    if target_imp in text and repl_imp not in text:
        text = text.replace(target_imp, repl_imp, 1)

    # Init
    target_init = "self.quantum_walk_search = ContinuousQuantumWalkSearchFabric()"
    repl_init = target_init + "\n        # Stage 266: Planetary Magnetohydrodynamic Dynamo Plasma Core (Era 27)\n        self.mhd_dynamo_sim = MagnetohydrodynamicDynamoSimFabric()"
    if target_init in text and repl_init not in text:
        text = text.replace(target_init, repl_init, 1)

    # Supervisor services
    target_svc = '("quantum_walk_search", "core"),'
    repl_svc = target_svc + '\n            ("mhd_dynamo_sim", "core"),'
    if target_svc in text and repl_svc not in text:
        text = text.replace(target_svc, repl_svc, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully wired Stage 266 into lucy_runtime.py")


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = 'return RouterResponse("Usage: /qw-topology <cycle|complete|star>")'
    insertion = """

        # --- Stage 266: Planetary Magnetohydrodynamic (MHD) Dynamo Alfven Wave Plasma Core Simulator ---
        if lowered in ("/mhd-dynamo-status", "mhd-dynamo-status"):
            if hasattr(self.runtime, "mhd_dynamo_sim"):
                st = self.runtime.mhd_dynamo_sim.get_status()
                msg = (
                    f"MHD Dynamo Simulator: Radius={st['core_radius_km']} km, B_pol={st['b_poloidal_tesla']:.2e} T, "
                    f"Rm={st['magnetic_reynolds_Rm']:.0f}, Alfven Speed={st['alfven_velocity_m_s']:.2f} m/s."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("MHD Dynamo simulator not initialized.")

        if lowered.startswith("/mhd-step ") or lowered.startswith("mhd-step "):
            if hasattr(self.runtime, "mhd_dynamo_sim"):
                parts = raw_text.strip().split()
                dt_y = float(parts[1]) if len(parts) >= 2 else 100.0
                res = self.runtime.mhd_dynamo_sim.step_dynamo_evolution(dt_years=dt_y)
                msg = (
                    f"MHD Dynamo Step (dt={dt_y} yr): B_total={res['b_total_tesla']:.2e} T, "
                    f"Alfven={res['alfven_speed_m_s']:.2f} m/s, Dipole M={res['dipole_moment_a_m2']:.2e} A*m^2."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /mhd-step <dt_years>")

        if lowered.startswith("/mhd-alfven-speed ") or lowered.startswith("mhd-alfven-speed "):
            if hasattr(self.runtime, "mhd_dynamo_sim"):
                parts = raw_text.strip().split()
                b_val = float(parts[1]) if len(parts) >= 2 else 0.005
                res = self.runtime.mhd_dynamo_sim.compute_alfven_velocity(b_field_tesla=b_val)
                msg = (
                    f"Alfven Wave Speed (B={b_val} T): v_A={res['alfven_velocity_m_s']:.2f} m/s, "
                    f"Core Transit Time={res['core_transit_time_years']:.2f} years."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /mhd-alfven-speed <b_field_tesla>")

        if lowered.startswith("/mhd-reversal ") or lowered.startswith("mhd-reversal "):
            if hasattr(self.runtime, "mhd_dynamo_sim"):
                parts = raw_text.strip().split()
                dur = float(parts[1]) if len(parts) >= 2 else 10000.0
                res = self.runtime.mhd_dynamo_sim.simulate_magnetic_reversal(duration_years=dur)
                msg = (
                    f"Geomagnetic Reversal Sim ({dur} yr): Flips={res['polarity_flips']}, "
                    f"Final B_pol={res['final_poloidal_b_tesla']:.2e} T, Reversed={res['is_reversed']}."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /mhd-reversal <duration_years>")"""

    if "mhd-dynamo-status" not in text:
        text = text.replace(target, target + insertion, 1)
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Successfully wired Stage 266 into router.py")
    else:
        print("Stage 266 already wired in router.py")


if __name__ == '__main__':
    wire_runtime()
    wire_router()
