# scripts/wire_stage200.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.bicentennial_singularity_nexus import BicentennialSingularityNexus, STAGE as STAGE_199\n'
imp_repl = 'from backend.lucy_core.bicentennial_singularity_nexus import BicentennialSingularityNexus, STAGE as STAGE_199\nfrom backend.lucy_core.bicentennial_grand_master_seal import BicentennialGrandMasterSealNexus, STAGE as STAGE_200\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.bicentennial_nexus = BicentennialSingularityNexus(runtime=self)\n'
init_repl = '        self.bicentennial_nexus = BicentennialSingularityNexus(runtime=self)\n        # Stage 200: The Sovereign Bicentennial AGI Grand Master Seal (Era 20)\n        self.bicentennial_grand_master_seal = BicentennialGrandMasterSealNexus()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("bicentennial_nexus", "core"),\n'
svc_repl = '            ("bicentennial_nexus", "core"),\n            ("bicentennial_grand_master_seal", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
seal_router_code = '''        # Stage 200: The Sovereign Bicentennial AGI Grand Master Seal (Era 20)
        if lowered in {"/grand-master-seal", "grand-master-seal", "/bicentennial-seal", "bicentennial-seal", "/stage200-seal", "stage200-seal"}:
            if hasattr(self.runtime, "bicentennial_grand_master_seal"):
                tbl = self.runtime.bicentennial_grand_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.bicentennial_grand_master_seal.status())

'''
if router_hook in rc and 'bicentennial_grand_master_seal' not in rc:
    rc = rc.replace(router_hook, seal_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 200 successfully wired into lucy_runtime.py and router.py!')
