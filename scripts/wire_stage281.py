import sys

path = 'backend/lucy_core/router.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

target = '            return RouterResponse("Era 28 Master Seal not initialized.")\n            return RouterResponse("FLRW Cosmological Engine not initialized.")'

stage281_code = '''            return RouterResponse("Era 28 Master Seal not initialized.")

        # --- Stage 281: Black Hole Holographic Thermodynamics & Bekenstein-Hawking Entropy Engine ---
        if lowered in ("/bh-status", "bh-status", "/black-hole-status", "black-hole-status"):
            if hasattr(self.runtime, "black_hole_thermodynamics"):
                tbl = self.runtime.black_hole_thermodynamics.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.black_hole_thermodynamics.status())
            return RouterResponse("Black Hole Thermodynamics Engine not initialized.")

        if lowered.startswith("/hawking-temp") or lowered.startswith("hawking-temp"):
            if hasattr(self.runtime, "black_hole_thermodynamics"):
                parts = message.strip().split()
                m_sol = float(parts[1]) if len(parts) > 1 else 1.0
                res = self.runtime.black_hole_thermodynamics.calculate_schwarzschild(mass_solar=m_sol)
                msg = f"Hawking Temperature for {m_sol:.2e} M_sun: {res['hawking_temperature_k']:.4e} K (Horizon r_s={res['schwarzschild_radius_m']:.2e} m)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Black Hole Thermodynamics Engine not initialized.")

        if lowered.startswith("/bh-entropy") or lowered.startswith("bh-entropy"):
            if hasattr(self.runtime, "black_hole_thermodynamics"):
                parts = message.strip().split()
                m_sol = float(parts[1]) if len(parts) > 1 else 1.0
                res = self.runtime.black_hole_thermodynamics.calculate_schwarzschild(mass_solar=m_sol)
                msg = f"Bekenstein-Hawking Entropy for {m_sol:.2e} M_sun: S_BH/kB={res['dimensionless_entropy']:.4e} Planck units (Area={res['horizon_area_m2']:.4e} m^2)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Black Hole Thermodynamics Engine not initialized.")

        if lowered.startswith("/page-curve") or lowered.startswith("page-curve"):
            if hasattr(self.runtime, "black_hole_thermodynamics"):
                parts = message.strip().split()
                m_sol = float(parts[1]) if len(parts) > 1 else 1.0
                res = self.runtime.black_hole_thermodynamics.simulate_page_curve(mass_solar=m_sol, steps=20)
                msg = f"Unitary Page Curve simulated for {m_sol:.2e} M_sun: Page Time={res['page_time_s']:.4e} s, Points={res['total_points']}, Unitarity=PRESERVED."
                return RouterResponse(msg, data=res)
            return RouterResponse("Black Hole Thermodynamics Engine not initialized.")'''

if target not in c:
    # Check CRLF
    target_crlf = target.replace('\n', '\r\n')
    assert target_crlf in c, 'Target not found in router.py'
    c = c.replace(target_crlf, stage281_code.replace('\n', '\r\n'), 1)
else:
    c = c.replace(target, stage281_code, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Successfully wired Stage 281 into router.py")
