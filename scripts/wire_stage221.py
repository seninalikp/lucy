# scripts/wire_stage221.py
# Wire Stage 221 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.era22_master_seal import Era22MasterSealFabric, STAGE as STAGE_220\n'
imp_repl = 'from backend.lucy_core.era22_master_seal import Era22MasterSealFabric, STAGE as STAGE_220\nfrom backend.lucy_core.quantum_many_body_density import QuantumManyBodyDensityFabric, STAGE as STAGE_221\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.era22_master_seal = Era22MasterSealFabric()\n'
init_repl = '        self.era22_master_seal = Era22MasterSealFabric()\n        # Stage 221: Quantum Density Matrix Simulator (Era 23)\n        self.density_matrix_simulator = QuantumManyBodyDensityFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("era22_master_seal", "core"),\n'
svc_repl = '            ("era22_master_seal", "core"),\n            ("density_matrix_simulator", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 220: Era 22 Sovereign Master Seal & Galactic Hyper-Mesh Genesis\n'
density_router_code = '''        # Stage 221: Quantum Density Matrix & Mixed-State Dephasing Fabric (Era 23)
        if lowered in {"/density-status", "density-status", "/mixed-state-status", "mixed-state-status"}:
            if hasattr(self.runtime, "density_matrix_simulator"):
                tbl = self.runtime.density_matrix_simulator.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.density_matrix_simulator.status())

        if lowered in {"/density-pure", "density-pure"}:
            if hasattr(self.runtime, "density_matrix_simulator"):
                import math
                dm = self.runtime.density_matrix_simulator.prepare_pure_state([1.0 / math.sqrt(2), 1.0 / math.sqrt(2)])
                s = self.runtime.density_matrix_simulator.compute_von_neumann_entropy(dm)
                msg = f"[Quantum Density]: Prepared pure state |+>. Purity: {dm.purity():.4f}, Entropy: {s:.4f}."
                return RouterResponse(msg, data={"purity": dm.purity(), "entropy": s, "matrix": dm.to_real_display()})

        if lowered in {"/density-decohere", "density-decohere"}:
            if hasattr(self.runtime, "density_matrix_simulator"):
                import math
                dm = self.runtime.density_matrix_simulator.prepare_pure_state([1.0 / math.sqrt(2), 1.0 / math.sqrt(2)])
                damped = self.runtime.density_matrix_simulator.apply_phase_damping(dm, lambda_rate=0.5)
                s = self.runtime.density_matrix_simulator.compute_von_neumann_entropy(damped)
                msg = f"[Quantum Density]: Applied T2 phase damping (50%). Purity dropped to: {damped.purity():.4f}, Entropy increased to: {s:.4f}."
                return RouterResponse(msg, data={"purity": damped.purity(), "entropy": s, "matrix": damped.to_real_display()})

'''
if router_hook in rc and 'density_matrix_simulator' not in rc:
    rc = rc.replace(router_hook, density_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 221 successfully wired into lucy_runtime.py and router.py!')
