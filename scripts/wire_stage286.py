import sys

# 1. Update lucy_runtime.py
rt_path = 'backend/lucy_core/lucy_runtime.py'
with open(rt_path, 'r', encoding='utf-8') as f:
    c = f.read()

t_imp = 'from backend.lucy_core.quantum_zeno_dynamic_controller import QuantumZenoDynamicControllerFabric, STAGE as STAGE_285'
r_imp = t_imp + '\nfrom backend.lucy_core.majorana_zero_mode_gate import MajoranaZeroModeGateFabric, STAGE as STAGE_286'

t_inst = 'self.zeno_controller = QuantumZenoDynamicControllerFabric()'
r_inst = t_inst + '\n        # Stage 286: Topological Majorana Zero-Mode Braiding & Gate (Era 29)\n        self.majorana_gate = MajoranaZeroModeGateFabric()'

t_serv = '("zeno_controller", "core"),'
r_serv = t_serv + '\n            ("majorana_gate", "core"),'

assert t_imp in c, 't_imp not found in lucy_runtime.py'
assert t_inst in c, 't_inst not found in lucy_runtime.py'
assert t_serv in c, 't_serv not found in lucy_runtime.py'

c = c.replace(t_imp, r_imp, 1)
c = c.replace(t_inst, r_inst, 1)
c = c.replace(t_serv, r_serv, 1)

with open(rt_path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated lucy_runtime.py for Stage 286")

# 2. Update router.py
r_path = 'backend/lucy_core/router.py'
with open(r_path, 'r', encoding='utf-8') as f:
    rc = f.read()

target_anchor = '''        if lowered.startswith("/anti-zeno-accelerate") or lowered.startswith("anti-zeno-accelerate"):
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

stage286_router = '''        if lowered.startswith("/anti-zeno-accelerate") or lowered.startswith("anti-zeno-accelerate"):
            if hasattr(self.runtime, "zeno_controller"):
                parts = text.split()
                tau = float(parts[1]) if len(parts) > 1 else 1e-10
                res = self.runtime.zeno_controller.simulate_anti_zeno_regime(measurement_interval_tau_s=tau)
                msg = (
                    f"Quantum Anti-Zeno Acceleration (tau={res['measurement_interval_tau_s']:.1e}s): "
                    f"Regime={res['regime']}, Rate Ratio Gamma_eff/Gamma_0 = {res['decay_ratio_gamma_eff_over_gamma_0']:.2f}x"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Zeno Controller not initialized.")

        # --- Stage 286: Topological Majorana Zero-Mode Braiding & Parity-Protected Qubit Gate ---
        if lowered in ("/majorana-status", "majorana-status", "/mzm-status", "mzm-status"):
            if hasattr(self.runtime, "majorana_gate"):
                tbl = self.runtime.majorana_gate.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.majorana_gate.status())
            return RouterResponse("Majorana Gate Engine not initialized.")

        if lowered.startswith("/majorana-braid") or lowered.startswith("majorana-braid") or lowered.startswith("/mzm-braid"):
            if hasattr(self.runtime, "majorana_gate"):
                parts = text.split()
                i = int(parts[1]) if len(parts) > 1 else 0
                j = int(parts[2]) if len(parts) > 2 else 1
                res = self.runtime.majorana_gate.apply_braid(i, j)
                if "error" in res:
                    return RouterResponse(res["error"])
                msg = f"Majorana Braid {res['braid_operation']} Applied: Total Braids={res['braid_count']}, Parity={res['fermion_parity']} (Fault-Tolerant)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Majorana Gate Engine not initialized.")

        if lowered.startswith("/majorana-parity") or lowered.startswith("majorana-parity") or lowered.startswith("/mzm-parity"):
            if hasattr(self.runtime, "majorana_gate"):
                res = self.runtime.majorana_gate.measure_fermion_parity()
                msg = f"Topological Fermion Parity: Eigenvalue={res['parity_eigenvalue']}, State={res['logical_state']} (Poisoning Protected)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Majorana Gate Engine not initialized.")'''

if target_anchor not in rc:
    target_anchor_crlf = target_anchor.replace('\n', '\r\n')
    assert target_anchor_crlf in rc, 'target_anchor not found in router.py'
    rc = rc.replace(target_anchor_crlf, stage286_router.replace('\n', '\r\n'), 1)
else:
    rc = rc.replace(target_anchor, stage286_router, 1)

with open(r_path, 'w', encoding='utf-8') as f:
    f.write(rc)

print("Updated router.py for Stage 286")
