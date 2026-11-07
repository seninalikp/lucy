# scripts/wire_stage210.py
# Wire Stage 210 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.hyperscale_mesh_synchronizer import HyperscaleMeshSynchronizerFabric, STAGE as STAGE_209\n'
imp_repl = 'from backend.lucy_core.hyperscale_mesh_synchronizer import HyperscaleMeshSynchronizerFabric, STAGE as STAGE_209\nfrom backend.lucy_core.era21_master_seal import Era21MasterSealFabric, STAGE as STAGE_210\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.hyperscale_mesh = HyperscaleMeshSynchronizerFabric()\n'
init_repl = '        self.hyperscale_mesh = HyperscaleMeshSynchronizerFabric()\n        # Stage 210: Era 21 Master Seal & Hyper-Federation Genesis\n        self.era21_master_seal = Era21MasterSealFabric(workspace_root=self.project_path)\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("hyperscale_mesh", "core"),\n'
svc_repl = '            ("hyperscale_mesh", "core"),\n            ("era21_master_seal", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 209: Hyper-Scale Cluster Mesh Synchronizer (Era 21)\n'
seal_router_code = '''        # Stage 210: Era 21 Sovereign Master Seal & Hyper-Federation Genesis
        if lowered in {"/era21-seal", "era21-seal", "/hyper-federation-seal", "hyper-federation-seal"}:
            if hasattr(self.runtime, "era21_master_seal"):
                tbl = self.runtime.era21_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.era21_master_seal.status())

        if lowered in {"/era21-audit", "era21-audit", "/hyper-federation-audit", "hyper-federation-audit"}:
            if hasattr(self.runtime, "era21_master_seal"):
                report = self.runtime.era21_master_seal.format_grand_era_report()
                return RouterResponse(report, data=self.runtime.era21_master_seal.status())

'''
if router_hook in rc and 'era21_master_seal' not in rc:
    rc = rc.replace(router_hook, seal_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 210 successfully wired into lucy_runtime.py and router.py!')
