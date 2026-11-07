import sys

# 1. Update lucy_runtime.py
rt_path = 'backend/lucy_core/lucy_runtime.py'
with open(rt_path, 'r', encoding='utf-8') as f:
    c = f.read()

t_imp = 'from backend.lucy_core.non_hermitian_pt_symmetric_engine import NonHermitianPTSymmetricFabric, STAGE as STAGE_282'
r_imp = t_imp + '\nfrom backend.lucy_core.quantum_many_body_scrambler import QuantumManyBodyScramblerFabric, STAGE as STAGE_283'

t_inst = 'self.pt_symmetric_engine = NonHermitianPTSymmetricFabric()'
r_inst = t_inst + '\n        # Stage 283: Quantum Many-Body Scrambler & OTOC Engine (Era 29)\n        self.quantum_scrambler = QuantumManyBodyScramblerFabric()'

t_serv = '("pt_symmetric_engine", "core"),'
r_serv = t_serv + '\n            ("quantum_scrambler", "core"),'

assert t_imp in c, 't_imp not found in lucy_runtime.py'
assert t_inst in c, 't_inst not found in lucy_runtime.py'
assert t_serv in c, 't_serv not found in lucy_runtime.py'

c = c.replace(t_imp, r_imp, 1)
c = c.replace(t_inst, r_inst, 1)
c = c.replace(t_serv, r_serv, 1)

with open(rt_path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated lucy_runtime.py for Stage 283")

# 2. Update router.py
r_path = 'backend/lucy_core/router.py'
with open(r_path, 'r', encoding='utf-8') as f:
    rc = f.read()

target_anchor = '''        if lowered.startswith("/exceptional-point-detect") or lowered.startswith("exceptional-point-detect") or lowered.startswith("/ep-detect"):
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

stage283_router = '''        if lowered.startswith("/exceptional-point-detect") or lowered.startswith("exceptional-point-detect") or lowered.startswith("/ep-detect"):
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
            return RouterResponse("PT-Symmetric Quantum Engine not initialized.")

        # --- Stage 283: Quantum Many-Body Scrambler & OTOC Fast Scrambler ---
        if lowered in ("/otoc-status", "otoc-status", "/scrambler-status", "scrambler-status"):
            if hasattr(self.runtime, "quantum_scrambler"):
                tbl = self.runtime.quantum_scrambler.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.quantum_scrambler.status())
            return RouterResponse("Quantum Scrambler Engine not initialized.")

        if lowered.startswith("/otoc-correlator") or lowered.startswith("otoc-correlator"):
            if hasattr(self.runtime, "quantum_scrambler"):
                parts = text.split()
                n = int(parts[1]) if len(parts) > 1 else 64
                temp = float(parts[2]) if len(parts) > 2 else 1.0
                res = self.runtime.quantum_scrambler.calculate_otoc_evolution(n_qubits=n, temperature_k=temp, steps=20)
                msg = (
                    f"OTOC Evolution (N={res['n_qubits']}, T={res['temperature_k']}K): "
                    f"Lyapunov={res['lyapunov_exponent']:.2e} Hz, t_*={res['scrambling_time_s']:.2e} s, Steps={res['total_steps']}"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Scrambler Engine not initialized.")

        if lowered.startswith("/scrambling-time") or lowered.startswith("scrambling-time"):
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

if target_anchor not in rc:
    target_anchor_crlf = target_anchor.replace('\n', '\r\n')
    assert target_anchor_crlf in rc, 'target_anchor not found in router.py'
    rc = rc.replace(target_anchor_crlf, stage283_router.replace('\n', '\r\n'), 1)
else:
    rc = rc.replace(target_anchor, stage283_router, 1)

with open(r_path, 'w', encoding='utf-8') as f:
    f.write(rc)

print("Updated router.py for Stage 283")
