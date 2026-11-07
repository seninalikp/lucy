import sys

# 1. Update lucy_runtime.py
rt_path = 'backend/lucy_core/lucy_runtime.py'
with open(rt_path, 'r', encoding='utf-8') as f:
    c = f.read()

t_imp = 'from backend.lucy_core.quantum_many_body_scrambler import QuantumManyBodyScramblerFabric, STAGE as STAGE_283'
r_imp = t_imp + '\nfrom backend.lucy_core.cmb_multipole_power_spectrum import CMBMultipolePowerSpectrumFabric, STAGE as STAGE_284'

t_inst = 'self.quantum_scrambler = QuantumManyBodyScramblerFabric()'
r_inst = t_inst + '\n        # Stage 284: CMB Multipole Power Spectrum & Inflationary Tensor Fabric (Era 29)\n        self.cmb_power_spectrum = CMBMultipolePowerSpectrumFabric()'

t_serv = '("quantum_scrambler", "core"),'
r_serv = t_serv + '\n            ("cmb_power_spectrum", "core"),'

assert t_imp in c, 't_imp not found in lucy_runtime.py'
assert t_inst in c, 't_inst not found in lucy_runtime.py'
assert t_serv in c, 't_serv not found in lucy_runtime.py'

c = c.replace(t_imp, r_imp, 1)
c = c.replace(t_inst, r_inst, 1)
c = c.replace(t_serv, r_serv, 1)

with open(rt_path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated lucy_runtime.py for Stage 284")

# 2. Update router.py
r_path = 'backend/lucy_core/router.py'
with open(r_path, 'r', encoding='utf-8') as f:
    rc = f.read()

target_anchor = '''        if lowered.startswith("/scrambling-time") or lowered.startswith("scrambling-time"):
            if hasattr(self.runtime, "quantum_scrambler"):
                parts = text.split()
                n = int(parts[1]) if len(parts) > 1 else 100
                temp = float(parts[2]) if len(parts) > 2 else 1.0
                res = self.runtime.quantum_scrambler.compute_scrambling_time(n_qubits=n, temperature_k=temp)
                msg = (
                    f"Fast Scrambling Time t_* for N={res['n_qubits']} at T={res['temperature_k']}K: "
                    f"{res['scrambling_time_s']:.4e} s (MSS Bound={res['mss_bound_hz']:.2e} Hz)"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Scrambler Engine not initialized.")'''

stage284_router = '''        if lowered.startswith("/scrambling-time") or lowered.startswith("scrambling-time"):
            if hasattr(self.runtime, "quantum_scrambler"):
                parts = text.split()
                n = int(parts[1]) if len(parts) > 1 else 100
                temp = float(parts[2]) if len(parts) > 2 else 1.0
                res = self.runtime.quantum_scrambler.compute_scrambling_time(n_qubits=n, temperature_k=temp)
                msg = (
                    f"Fast Scrambling Time t_* for N={res['n_qubits']} at T={res['temperature_k']}K: "
                    f"{res['scrambling_time_s']:.4e} s (MSS Bound={res['mss_bound_hz']:.2e} Hz)"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Scrambler Engine not initialized.")

        # --- Stage 284: CMB Multipole Power Spectrum & Inflationary Tensor Perturbation Engine ---
        if lowered in ("/cmb-status", "cmb-status", "/cmb-spectrum-status", "cmb-spectrum-status"):
            if hasattr(self.runtime, "cmb_power_spectrum"):
                tbl = self.runtime.cmb_power_spectrum.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.cmb_power_spectrum.status())
            return RouterResponse("CMB Power Spectrum Engine not initialized.")

        if lowered.startswith("/cmb-multipole") or lowered.startswith("cmb-multipole"):
            if hasattr(self.runtime, "cmb_power_spectrum"):
                parts = text.split()
                l_val = int(parts[1]) if len(parts) > 1 else 220
                d_l = self.runtime.cmb_power_spectrum.evaluate_multipole_d_l(l_val)
                msg = f"CMB Multipole l={l_val}: D_l = {d_l:.2f} uK^2 (Concordance Lambda-CDM)"
                return RouterResponse(msg, data={"multipole_l": l_val, "d_l_uK2": d_l})
            return RouterResponse("CMB Power Spectrum Engine not initialized.")

        if lowered.startswith("/inflation-tensor-ratio") or lowered.startswith("inflation-tensor-ratio") or lowered.startswith("/tensor-ratio"):
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

if target_anchor not in rc:
    target_anchor_crlf = target_anchor.replace('\n', '\r\n')
    assert target_anchor_crlf in rc, 'target_anchor not found in router.py'
    rc = rc.replace(target_anchor_crlf, stage284_router.replace('\n', '\r\n'), 1)
else:
    rc = rc.replace(target_anchor, stage284_router, 1)

with open(r_path, 'w', encoding='utf-8') as f:
    f.write(rc)

print("Updated router.py for Stage 284")
