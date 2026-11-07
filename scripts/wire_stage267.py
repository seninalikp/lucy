"""
Wiring script for Stage 267: Geometric Berry-Pancharatnam Phase & Non-Abelian Wilczek-Zee Holonomy Gate
Author: Senin (Senin Ali K P)
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Import
    target_imp = "from backend.lucy_core.magnetohydrodynamic_dynamo_sim import MagnetohydrodynamicDynamoSimFabric, STAGE as STAGE_266"
    repl_imp = target_imp + "\nfrom backend.lucy_core.berry_wilczek_zee_holonomy import BerryWilczekZeeHolonomyFabric, STAGE as STAGE_267"
    if target_imp in text and repl_imp not in text:
        text = text.replace(target_imp, repl_imp, 1)

    # Init
    target_init = "self.mhd_dynamo_sim = MagnetohydrodynamicDynamoSimFabric()"
    repl_init = target_init + "\n        # Stage 267: Geometric Berry Phase & Non-Abelian Holonomy Gate (Era 27)\n        self.berry_holonomy = BerryWilczekZeeHolonomyFabric()"
    if target_init in text and repl_init not in text:
        text = text.replace(target_init, repl_init, 1)

    # Supervisor services
    target_svc = '("mhd_dynamo_sim", "core"),'
    repl_svc = target_svc + '\n            ("berry_holonomy", "core"),'
    if target_svc in text and repl_svc not in text:
        text = text.replace(target_svc, repl_svc, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully wired Stage 267 into lucy_runtime.py")


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = 'return RouterResponse("Usage: /mhd-reversal <duration_years>")'
    insertion = """

        # --- Stage 267: Geometric Berry-Pancharatnam Phase & Non-Abelian Wilczek-Zee Holonomy Gate ---
        if lowered in ("/berry-phase-status", "berry-phase-status"):
            if hasattr(self.runtime, "berry_holonomy"):
                st = self.runtime.berry_holonomy.get_status()
                msg = (
                    f"Berry-Wilczek-Zee Holonomy Engine: hbar={st['hbar']}, "
                    f"Holonomic Gates Synthesized={st['holonomy_gates_synthesized']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Berry-Wilczek-Zee Holonomy engine not initialized.")

        if lowered.startswith("/berry-spin ") or lowered.startswith("berry-spin "):
            if hasattr(self.runtime, "berry_holonomy"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    deg = float(parts[1])
                    loops = int(parts[2]) if len(parts) >= 3 else 1
                    theta = deg * 3.141592653589793 / 180.0
                    res = self.runtime.berry_holonomy.compute_spin_berry_phase(cone_angle_theta_rad=theta, loops=loops)
                    msg = (
                        f"Spin-1/2 Berry Phase (theta={deg} deg, {loops} loops): gamma={res['berry_phase_deg']:.2f} deg "
                        f"({res['berry_phase_rad']:.4f} rad), Solid Angle={res['solid_angle_steradians']:.3f} sr, C_1={res['first_chern_number']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /berry-spin <cone_angle_deg> [loops]")

        if lowered in ("/pancharatnam-phase", "pancharatnam-phase"):
            if hasattr(self.runtime, "berry_holonomy"):
                res = self.runtime.berry_holonomy.compute_pancharatnam_phase()
                msg = (
                    f"Pancharatnam Geometric Phase: Phi_P={res['pancharatnam_phase_deg']:.2f} deg "
                    f"({res['pancharatnam_phase_rad']:.4f} rad), Enclosed Solid Angle={res['enclosed_solid_angle']:.3f} sr."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Berry-Wilczek-Zee Holonomy engine not initialized.")

        if lowered.startswith("/wilczek-zee-gate ") or lowered.startswith("wilczek-zee-gate "):
            if hasattr(self.runtime, "berry_holonomy"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    g_type = parts[1].upper()
                    angle_deg = float(parts[2]) if len(parts) >= 3 else 180.0
                    angle_rad = angle_deg * 3.141592653589793 / 180.0
                    res = self.runtime.berry_holonomy.synthesize_wilczek_zee_gate(gate_type=g_type, alpha_angle=angle_rad)
                    msg = (
                        f"Wilczek-Zee Holonomy Gate '{g_type}': Angle={res['holonomy_angle_deg']:.1f} deg, "
                        f"Unitary={res['is_unitary']}, Matrix={res['matrix']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /wilczek-zee-gate <NOT|PHASE|HADAMARD> [angle_deg]")"""

    if "berry-phase-status" not in text:
        text = text.replace(target, target + insertion, 1)
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Successfully wired Stage 267 into router.py")
    else:
        print("Stage 267 already wired in router.py")


if __name__ == '__main__':
    wire_runtime()
    wire_router()
