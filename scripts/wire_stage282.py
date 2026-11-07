import sys

# 1. Update lucy_runtime.py
rt_path = 'backend/lucy_core/lucy_runtime.py'
with open(rt_path, 'r', encoding='utf-8') as f:
    c = f.read()

t_imp = 'from backend.lucy_core.black_hole_thermodynamics import BlackHoleThermodynamicsFabric, STAGE as STAGE_281'
r_imp = t_imp + '\nfrom backend.lucy_core.non_hermitian_pt_symmetric_engine import NonHermitianPTSymmetricFabric, STAGE as STAGE_282'

t_inst = 'self.black_hole_thermodynamics = BlackHoleThermodynamicsFabric()'
r_inst = t_inst + '\n        # Stage 282: Non-Hermitian PT-Symmetric Open Quantum Engine & EP Sensor (Era 29)\n        self.pt_symmetric_engine = NonHermitianPTSymmetricFabric()'

t_serv = '("black_hole_thermodynamics", "core"),'
r_serv = t_serv + '\n            ("pt_symmetric_engine", "core"),'

assert t_imp in c, 't_imp not found in lucy_runtime.py'
assert t_inst in c, 't_inst not found in lucy_runtime.py'
assert t_serv in c, 't_serv not found in lucy_runtime.py'

c = c.replace(t_imp, r_imp, 1)
c = c.replace(t_inst, r_inst, 1)
c = c.replace(t_serv, r_serv, 1)

with open(rt_path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated lucy_runtime.py for Stage 282")

# 2. Update router.py
r_path = 'backend/lucy_core/router.py'
with open(r_path, 'r', encoding='utf-8') as f:
    rc = f.read()

target_anchor = '''        if lowered.startswith("/page-curve") or lowered.startswith("page-curve"):
            if hasattr(self.runtime, "black_hole_thermodynamics"):
                parts = text.split()
                m_sol = float(parts[1]) if len(parts) > 1 else 1.0
                res = self.runtime.black_hole_thermodynamics.simulate_page_curve(mass_solar=m_sol, steps=20)
                msg = f"Unitary Page Curve simulated for {m_sol:.2e} M_sun: Page Time={res['page_time_s']:.4e} s, Points={res['total_points']}, Unitarity=PRESERVED."
                return RouterResponse(msg, data=res)
            return RouterResponse("Black Hole Thermodynamics Engine not initialized.")'''

stage282_router = '''        if lowered.startswith("/page-curve") or lowered.startswith("page-curve"):
            if hasattr(self.runtime, "black_hole_thermodynamics"):
                parts = text.split()
                m_sol = float(parts[1]) if len(parts) > 1 else 1.0
                res = self.runtime.black_hole_thermodynamics.simulate_page_curve(mass_solar=m_sol, steps=20)
                msg = f"Unitary Page Curve simulated for {m_sol:.2e} M_sun: Page Time={res['page_time_s']:.4e} s, Points={res['total_points']}, Unitarity=PRESERVED."
                return RouterResponse(msg, data=res)
            return RouterResponse("Black Hole Thermodynamics Engine not initialized.")

        # --- Stage 282: Non-Hermitian PT-Symmetric Open Quantum Engine & Exceptional Point Sensor ---
        if lowered in ("/pt-status", "pt-status", "/pt-symmetric-status", "pt-symmetric-status"):
            if hasattr(self.runtime, "pt_symmetric_engine"):
                tbl = self.runtime.pt_symmetric_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.pt_symmetric_engine.status())
            return RouterResponse("PT-Symmetric Quantum Engine not initialized.")

        if lowered.startswith("/pt-spectrum") or lowered.startswith("pt-spectrum"):
            if hasattr(self.runtime, "pt_symmetric_engine"):
                parts = text.split()
                gamma = float(parts[1]) if len(parts) > 1 else 0.5
                g = float(parts[2]) if len(parts) > 2 else 1.0
                res = self.runtime.pt_symmetric_engine.solve_dim2_spectrum(gain_loss_gamma=gamma, coupling_g=g)
                msg = (
                    f"PT Spectrum: Phase={res.pt_phase}, Gamma={res.gain_loss_gamma}, g={res.coupling_g}, "
                    f"EP Distance={res.ep_distance:.4e}, Boost={res.perturbation_sensitivity_gain:.2f}x"
                )
                return RouterResponse(msg, data=res.to_dict())
            return RouterResponse("PT-Symmetric Quantum Engine not initialized.")

        if lowered.startswith("/exceptional-point-detect") or lowered.startswith("exceptional-point-detect") or lowered.startswith("/ep-detect"):
            if hasattr(self.runtime, "pt_symmetric_engine"):
                parts = text.split()
                eps = float(parts[1]) if len(parts) > 1 else 1e-6
                order = int(parts[2]) if len(parts) > 2 else 2
                res = self.runtime.pt_symmetric_engine.evaluate_ep_sensor(perturbation_epsilon=eps, order=order)
                msg = (
                    f"EP-{res['order_n']} Sensor Detected: Epsilon={res['perturbation_epsilon']:.2e}, "
                    f"Splitting={res['ep_eigenvalue_splitting']:.4e}, Amp={res['amplification_factor']:.2e}x ({res['sensitivity_order']})"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("PT-Symmetric Quantum Engine not initialized.")'''

if target_anchor not in rc:
    target_anchor_crlf = target_anchor.replace('\n', '\r\n')
    assert target_anchor_crlf in rc, 'target_anchor not found in router.py'
    rc = rc.replace(target_anchor_crlf, stage282_router.replace('\n', '\r\n'), 1)
else:
    rc = rc.replace(target_anchor, stage282_router, 1)

with open(r_path, 'w', encoding='utf-8') as f:
    f.write(rc)

print("Updated router.py for Stage 282")
