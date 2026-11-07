import sys

# 1. Update lucy_runtime.py
rt_path = 'backend/lucy_core/lucy_runtime.py'
with open(rt_path, 'r', encoding='utf-8') as f:
    c = f.read()

t_imp = 'from backend.lucy_core.majorana_zero_mode_gate import MajoranaZeroModeGateFabric, STAGE as STAGE_286'
r_imp = t_imp + '\nfrom backend.lucy_core.pulsar_magnetosphere_ffe import PulsarMagnetosphereFFEFabric, STAGE as STAGE_287'

t_inst = 'self.majorana_gate = MajoranaZeroModeGateFabric()'
r_inst = t_inst + '\n        # Stage 287: Pulsar Magnetosphere Relativistic FFE Engine (Era 29)\n        self.pulsar_ffe_engine = PulsarMagnetosphereFFEFabric()'

t_serv = '("majorana_gate", "core"),'
r_serv = t_serv + '\n            ("pulsar_ffe_engine", "core"),'

assert t_imp in c, 't_imp not found in lucy_runtime.py'
assert t_inst in c, 't_inst not found in lucy_runtime.py'
assert t_serv in c, 't_serv not found in lucy_runtime.py'

c = c.replace(t_imp, r_imp, 1)
c = c.replace(t_inst, r_inst, 1)
c = c.replace(t_serv, r_serv, 1)

with open(rt_path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated lucy_runtime.py for Stage 287")

# 2. Update router.py
r_path = 'backend/lucy_core/router.py'
with open(r_path, 'r', encoding='utf-8') as f:
    rc = f.read()

target_anchor = '''        if lowered.startswith("/majorana-parity") or lowered.startswith("majorana-parity") or lowered.startswith("/mzm-parity"):
            if hasattr(self.runtime, "majorana_gate"):
                res = self.runtime.majorana_gate.measure_fermion_parity()
                msg = f"Topological Fermion Parity: Eigenvalue={res['parity_eigenvalue']}, State={res['logical_state']} (Poisoning Protected)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Majorana Gate Engine not initialized.")'''

stage287_router = '''        if lowered.startswith("/majorana-parity") or lowered.startswith("majorana-parity") or lowered.startswith("/mzm-parity"):
            if hasattr(self.runtime, "majorana_gate"):
                res = self.runtime.majorana_gate.measure_fermion_parity()
                msg = f"Topological Fermion Parity: Eigenvalue={res['parity_eigenvalue']}, State={res['logical_state']} (Poisoning Protected)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Majorana Gate Engine not initialized.")

        # --- Stage 287: Pulsar Magnetosphere Relativistic Force-Free Electrodynamics (FFE) Simulator ---
        if lowered in ("/pulsar-ffe-status", "pulsar-ffe-status", "/pulsar-status", "pulsar-status"):
            if hasattr(self.runtime, "pulsar_ffe_engine"):
                tbl = self.runtime.pulsar_ffe_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.pulsar_ffe_engine.status())
            return RouterResponse("Pulsar FFE Engine not initialized.")

        if lowered.startswith("/goldreich-julian") or lowered.startswith("goldreich-julian") or lowered.startswith("/gj-density"):
            if hasattr(self.runtime, "pulsar_ffe_engine"):
                parts = text.split()
                p = float(parts[1]) if len(parts) > 1 else 0.03339
                b_g = float(parts[2]) if len(parts) > 2 else 3.8e12
                res = self.runtime.pulsar_ffe_engine.calculate_pulsar_parameters(period_s=p, b_surface_gauss=b_g)
                msg = (
                    f"Goldreich-Julian Density for P={p}s: rho_GJ={res['goldreich_julian_density_c_m3']:.2e} C/m^3, "
                    f"n_GJ={res['goldreich_julian_number_density_m3']:.2e} m^-3 (R_LC={res['light_cylinder_radius_m']:.2e} m)"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Pulsar FFE Engine not initialized.")

        if lowered.startswith("/pulsar-spindown") or lowered.startswith("pulsar-spindown"):
            if hasattr(self.runtime, "pulsar_ffe_engine"):
                parts = text.split()
                p = float(parts[1]) if len(parts) > 1 else 0.03339
                p_dot = float(parts[2]) if len(parts) > 2 else 4.21e-13
                res = self.runtime.pulsar_ffe_engine.calculate_pulsar_parameters(period_s=p, period_derivative=p_dot)
                msg = (
                    f"Pulsar Spin-Down (P={p}s, P_dot={p_dot:.2e}): E_dot={res['spindown_luminosity_watts']:.2e} W, "
                    f"Age={res['characteristic_age_years']:.1f} yrs, B_0={res['surface_b_field_tesla']:.2e} T"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Pulsar FFE Engine not initialized.")'''

if target_anchor not in rc:
    target_anchor_crlf = target_anchor.replace('\n', '\r\n')
    assert target_anchor_crlf in rc, 'target_anchor not found in router.py'
    rc = rc.replace(target_anchor_crlf, stage287_router.replace('\n', '\r\n'), 1)
else:
    rc = rc.replace(target_anchor, stage287_router, 1)

with open(r_path, 'w', encoding='utf-8') as f:
    f.write(rc)

print("Updated router.py for Stage 287")
