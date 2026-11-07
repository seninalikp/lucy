with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = '            return RouterResponse("Usage: /opto-squeeze [laser_power_mw] [detuning_ratio]")'
assert target in text, "Target anchor not found in router.py!"

insertion = """

        # --- Stage 264: Autonomous Topological Soliton Skyrmion Lattice Dynamics & Chiral Domain Wall Weaver ---
        if lowered in ("/skyrmion-status", "skyrmion-status"):
            if hasattr(self.runtime, "skyrmion_weaver"):
                st = self.runtime.skyrmion_weaver.get_status()
                msg = (
                    f"Topological Skyrmion Weaver: Grid={st['grid_size']}, Solitons={st['active_solitons']}, "
                    f"Net Topological Charge Q={st['net_topological_charge']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Topological Skyrmion Weaver not initialized.")

        if lowered.startswith("/skyrmion-wind ") or lowered.startswith("skyrmion-wind "):
            if hasattr(self.runtime, "skyrmion_weaver"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    cx, cy, rad = float(parts[1]), float(parts[2]), float(parts[3])
                    res = self.runtime.skyrmion_weaver.inject_skyrmion(center_x=cx, center_y=cy, radius=rad)
                    msg = f"Injected Skyrmion at ({cx}, {cy}) radius={rad} -> Net Q={res['topological_charge']}."
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /skyrmion-wind <center_x> <center_y> <radius>")

        if lowered.startswith("/skyrmion-thiele ") or lowered.startswith("skyrmion-thiele "):
            if hasattr(self.runtime, "skyrmion_weaver"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    j_dens = float(parts[1])
                    res = self.runtime.skyrmion_weaver.compute_thiele_dynamics(current_density_j_a_m2=j_dens)
                    msg = (
                        f"Thiele Dynamics: Q={res['topological_charge']}, Speed={res['speed_m_s']:.2f} m/s, "
                        f"Hall Angle={res['skyrmion_hall_angle_deg']:.2f} deg."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /skyrmion-thiele <current_density_j>")

        if lowered.startswith("/skyrmion-racetrack ") or lowered.startswith("skyrmion-racetrack "):
            if hasattr(self.runtime, "skyrmion_weaver"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    bits = parts[1]
                    res = self.runtime.skyrmion_weaver.encode_racetrack_track(bits)
                    msg = (
                        f"Racetrack Track: Bits='{res['encoded_bits']}', Net Q={res['total_topological_charge']}, "
                        f"Fidelity={res['fidelity']*100:.1f}%."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /skyrmion-racetrack <bit_sequence>")"""

if "skyrmion-status" not in text:
    text = text.replace(target, target + insertion, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Wired Stage 264 into router.py successfully")
else:
    print("Stage 264 already wired in router.py")
