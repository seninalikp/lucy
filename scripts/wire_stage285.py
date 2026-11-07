import sys

# 1. Update lucy_runtime.py
rt_path = 'backend/lucy_core/lucy_runtime.py'
with open(rt_path, 'r', encoding='utf-8') as f:
    c = f.read()

t_imp = 'from backend.lucy_core.cmb_multipole_power_spectrum import CMBMultipolePowerSpectrumFabric, STAGE as STAGE_284'
r_imp = t_imp + '\nfrom backend.lucy_core.quantum_zeno_dynamic_controller import QuantumZenoDynamicControllerFabric, STAGE as STAGE_285'

t_inst = 'self.cmb_power_spectrum = CMBMultipolePowerSpectrumFabric()'
r_inst = t_inst + '\n        # Stage 285: Quantum Zeno & Anti-Zeno Dynamic Controller (Era 29)\n        self.zeno_controller = QuantumZenoDynamicControllerFabric()'

t_serv = '("cmb_power_spectrum", "core"),'
r_serv = t_serv + '\n            ("zeno_controller", "core"),'

assert t_imp in c, 't_imp not found in lucy_runtime.py'
assert t_inst in c, 't_inst not found in lucy_runtime.py'
assert t_serv in c, 't_serv not found in lucy_runtime.py'

c = c.replace(t_imp, r_imp, 1)
c = c.replace(t_inst, r_inst, 1)
c = c.replace(t_serv, r_serv, 1)

with open(rt_path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated lucy_runtime.py for Stage 285")

# 2. Update router.py
r_path = 'backend/lucy_core/router.py'
with open(r_path, 'r', encoding='utf-8') as f:
    rc = f.read()

target_anchor = '''        if lowered.startswith("/inflation-tensor-ratio") or lowered.startswith("inflation-tensor-ratio") or lowered.startswith("/tensor-ratio"):
            if hasattr(self.runtime, "cmb_power_spectrum"):
                parts = text.split()
                r_val = float(parts[1]) if len(parts) > 1 else 0.03
                res = self.runtime.cmb_power_spectrum.compute_inflation_tensor_ratio(tensor_to_scalar_r=r_val)
                msg = (
                    f"Inflationary Tensor-to-Scalar Ratio r={res['tensor_to_scalar_r']}: "
                    f"Scale={res['inflation_energy_scale_gev']:.2e} GeV, Lyth Excursion={res['lyth_bound_delta_phi_planck']:.2f} M_Pl"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("CMB Power Spectrum Engine not initialized.")'''

stage285_router = '''        if lowered.startswith("/inflation-tensor-ratio") or lowered.startswith("inflation-tensor-ratio") or lowered.startswith("/tensor-ratio"):
            if hasattr(self.runtime, "cmb_power_spectrum"):
                parts = text.split()
                r_val = float(parts[1]) if len(parts) > 1 else 0.03
                res = self.runtime.cmb_power_spectrum.compute_inflation_tensor_ratio(tensor_to_scalar_r=r_val)
                msg = (
                    f"Inflationary Tensor-to-Scalar Ratio r={res['tensor_to_scalar_r']}: "
                    f"Scale={res['inflation_energy_scale_gev']:.2e} GeV, Lyth Excursion={res['lyth_bound_delta_phi_planck']:.2f} M_Pl"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("CMB Power Spectrum Engine not initialized.")

        # --- Stage 285: Quantum Zeno & Anti-Zeno Dynamic Measurement Controller ---
        if lowered in ("/zeno-status", "zeno-status", "/zeno-controller-status", "zeno-controller-status"):
            if hasattr(self.runtime, "zeno_controller"):
                tbl = self.runtime.zeno_controller.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.zeno_controller.status())
            return RouterResponse("Quantum Zeno Controller not initialized.")

        if lowered.startswith("/zeno-inhibit") or lowered.startswith("zeno-inhibit"):
            if hasattr(self.runtime, "zeno_controller"):
                parts = text.split()
                tau = float(parts[1]) if len(parts) > 1 else 1e-11
                t_tot = float(parts[2]) if len(parts) > 2 else 1e-9
                res = self.runtime.zeno_controller.simulate_zeno_inhibition(measurement_interval_tau_s=tau, total_time_s=t_tot)
                msg = (
                    f"Quantum Zeno Inhibition (tau={res['measurement_interval_tau_s']:.1e}s, N={res['number_of_measurements']}): "
                    f"P(t)={res['survival_probability']:.4f} (Natural={res['natural_decay_probability']:.4f}, Ratio={res['decay_suppression_ratio']:.2e})"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Zeno Controller not initialized.")

        if lowered.startswith("/anti-zeno-accelerate") or lowered.startswith("anti-zeno-accelerate"):
            if hasattr(self.runtime, "zeno_controller"):
                parts = text.split()
                tau = float(parts[1]) if len(parts) > 1 else 1e-10
                res = self.runtime.zeno_controller.simulate_anti_zeno_regime(measurement_interval_tau_s=tau)
                msg = (
                    f"Quantum Anti-Zeno Acceleration (tau={res['measurement_interval_tau_s']:.1e}s): "
                    f"Regime={res['regime']}, Rate Ratio Gamma_eff/Gamma_0 = {res['decay_ratio_gamma_eff_over_gamma_0']:.2f}x"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Zeno Controller not initialized.")'''

if target_anchor not in rc:
    target_anchor_crlf = target_anchor.replace('\n', '\r\n')
    assert target_anchor_crlf in rc, 'target_anchor not found in router.py'
    rc = rc.replace(target_anchor_crlf, stage285_router.replace('\n', '\r\n'), 1)
else:
    rc = rc.replace(target_anchor, stage285_router, 1)

with open(r_path, 'w', encoding='utf-8') as f:
    f.write(rc)

print("Updated router.py for Stage 285")
