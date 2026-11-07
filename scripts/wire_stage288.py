import sys

# 1. Update lucy_runtime.py
rt_path = 'backend/lucy_core/lucy_runtime.py'
with open(rt_path, 'r', encoding='utf-8') as f:
    c = f.read()

t_imp = 'from backend.lucy_core.pulsar_magnetosphere_ffe import PulsarMagnetosphereFFEFabric, STAGE as STAGE_287'
r_imp = t_imp + '\nfrom backend.lucy_core.quantum_fisher_phase_estimator import QuantumFisherPhaseEstimatorFabric, STAGE as STAGE_288'

t_inst = 'self.pulsar_ffe_engine = PulsarMagnetosphereFFEFabric()'
r_inst = t_inst + '\n        # Stage 288: Quantum Optic Phase Estimator & Fisher Information (Era 29)\n        self.fisher_phase_estimator = QuantumFisherPhaseEstimatorFabric()'

t_serv = '("pulsar_ffe_engine", "core"),'
r_serv = t_serv + '\n            ("fisher_phase_estimator", "core"),'

assert t_imp in c, 't_imp not found in lucy_runtime.py'
assert t_inst in c, 't_inst not found in lucy_runtime.py'
assert t_serv in c, 't_serv not found in lucy_runtime.py'

c = c.replace(t_imp, r_imp, 1)
c = c.replace(t_inst, r_inst, 1)
c = c.replace(t_serv, r_serv, 1)

with open(rt_path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated lucy_runtime.py for Stage 288")

# 2. Update router.py
r_path = 'backend/lucy_core/router.py'
with open(r_path, 'r', encoding='utf-8') as f:
    rc = f.read()

target_anchor = '''        if lowered.startswith("/pulsar-spindown") or lowered.startswith("pulsar-spindown"):
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

stage288_router = '''        if lowered.startswith("/pulsar-spindown") or lowered.startswith("pulsar-spindown"):
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
            return RouterResponse("Pulsar FFE Engine not initialized.")

        # --- Stage 288: Quantum Optic Phase Estimator & Quantum Fisher Information Engine ---
        if lowered in ("/fisher-status", "fisher-status", "/qfi-status", "qfi-status"):
            if hasattr(self.runtime, "fisher_phase_estimator"):
                tbl = self.runtime.fisher_phase_estimator.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.fisher_phase_estimator.status())
            return RouterResponse("Quantum Fisher Phase Estimator not initialized.")

        if lowered.startswith("/heisenberg-limit") or lowered.startswith("heisenberg-limit") or lowered.startswith("/hl-eval"):
            if hasattr(self.runtime, "fisher_phase_estimator"):
                parts = text.split()
                photons = float(parts[1]) if len(parts) > 1 else 100.0
                st_type = parts[2] if len(parts) > 2 else "N00N"
                res = self.runtime.fisher_phase_estimator.calculate_quantum_fisher_info(mean_photons=photons, state_type=st_type)
                msg = (
                    f"QFI Metrology ({res['state_type']}, N={res['mean_photon_number']}): "
                    f"Delta_phi={res['cramer_rao_bound_radians']:.4e} rad, F_Q={res['quantum_fisher_info']:.2e}, "
                    f"Advantage={res['quantum_advantage_ratio']:.2f}x over SQL"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Fisher Phase Estimator not initialized.")

        if lowered.startswith("/noon-phase-eval") or lowered.startswith("noon-phase-eval") or lowered.startswith("/noon-fringes"):
            if hasattr(self.runtime, "fisher_phase_estimator"):
                parts = text.split()
                phi = float(parts[1]) if len(parts) > 1 else 0.5
                n = int(parts[2]) if len(parts) > 2 else 8
                res = self.runtime.fisher_phase_estimator.simulate_mach_zehnder_fringes(true_phase_rad=phi, n_photons=n, state_type="N00N")
                msg = (
                    f"N00N State Super-Resolution (N={res['photon_number_n']}): "
                    f"Transmission at phi={phi:.3f} rad is {res['transmission_at_true_phase']:.4f} (Finesse Multiplier={res['fringe_finesse_multiplier']:.1f}x)"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Fisher Phase Estimator not initialized.")'''

if target_anchor not in rc:
    target_anchor_crlf = target_anchor.replace('\n', '\r\n')
    assert target_anchor_crlf in rc, 'target_anchor not found in router.py'
    rc = rc.replace(target_anchor_crlf, stage288_router.replace('\n', '\r\n'), 1)
else:
    rc = rc.replace(target_anchor, stage288_router, 1)

with open(r_path, 'w', encoding='utf-8') as f:
    f.write(rc)

print("Updated router.py for Stage 288")
