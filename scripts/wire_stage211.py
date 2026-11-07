# scripts/wire_stage211.py
# Wire Stage 211 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.era21_master_seal import Era21MasterSealFabric, STAGE as STAGE_210\n'
imp_repl = 'from backend.lucy_core.era21_master_seal import Era21MasterSealFabric, STAGE as STAGE_210\nfrom backend.lucy_core.photonic_matrix_multiplier import PhotonicMatrixMultiplierFabric, STAGE as STAGE_211\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.era21_master_seal = Era21MasterSealFabric()\n'
init_repl = '        self.era21_master_seal = Era21MasterSealFabric()\n        # Stage 211: Photonic Matrix Multiplier (Era 22)\n        self.photonic_matrix_multiplier = PhotonicMatrixMultiplierFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("era21_master_seal", "core"),\n'
svc_repl = '            ("era21_master_seal", "core"),\n            ("photonic_matrix_multiplier", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 210: Era 21 Sovereign Master Seal & Hyper-Federation Genesis\n'
photonic_router_code = '''        # Stage 211: Photonic Matrix Multiplier Fabric (Era 22)
        if lowered in {"/photonic-status", "photonic-status", "/mzi-status", "mzi-status"}:
            if hasattr(self.runtime, "photonic_matrix_multiplier"):
                tbl = self.runtime.photonic_matrix_multiplier.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.photonic_matrix_multiplier.status())

        if lowered.startswith("/photonic-propagate ") or lowered.startswith("photonic-propagate "):
            prefix = "/photonic-propagate " if lowered.startswith("/photonic-propagate ") else "photonic-propagate "
            raw_vals = text[len(prefix):].strip().split()
            if hasattr(self.runtime, "photonic_matrix_multiplier"):
                try:
                    vec = [float(v) for v in raw_vals]
                except ValueError:
                    vec = [1.0, 0.0]
                sig = self.runtime.photonic_matrix_multiplier.propagate_signal(vec)
                intensities = [round(i, 4) for i in sig.intensities()]
                msg = f"[Photonic Compute]: Optical propagation complete. Detected power intensities: {intensities}."
                return RouterResponse(msg, data={"intensities": intensities})

'''
if router_hook in rc and 'photonic_matrix_multiplier' not in rc:
    rc = rc.replace(router_hook, photonic_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 211 successfully wired into lucy_runtime.py and router.py!')
