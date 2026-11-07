# scripts/wire_stage201.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.bicentennial_grand_master_seal import BicentennialGrandMasterSealNexus, STAGE as STAGE_200\n'
imp_repl = 'from backend.lucy_core.bicentennial_grand_master_seal import BicentennialGrandMasterSealNexus, STAGE as STAGE_200\nfrom backend.lucy_core.multi_kernel_federation import MultiKernelFederationFabric, STAGE as STAGE_201\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.bicentennial_grand_master_seal = BicentennialGrandMasterSealNexus()\n'
init_repl = '        self.bicentennial_grand_master_seal = BicentennialGrandMasterSealNexus()\n        # Stage 201: Autonomous Multi-Kernel Federation Bus (Era 21)\n        self.multi_kernel_federation = MultiKernelFederationFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("bicentennial_grand_master_seal", "core"),\n'
svc_repl = '            ("bicentennial_grand_master_seal", "core"),\n            ("multi_kernel_federation", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
fed_router_code = '''        # Stage 201: Autonomous Multi-Kernel Federation Bus & Cross-Kernel RPC (Era 21)
        if lowered in {"/federation-status", "federation-status", "/multi-kernel-status", "multi-kernel-status"}:
            if hasattr(self.runtime, "multi_kernel_federation"):
                tbl = self.runtime.multi_kernel_federation.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.multi_kernel_federation.status())

        if lowered.startswith("/federation-peer ") or lowered.startswith("federation-peer "):
            prefix = "/federation-peer " if lowered.startswith("/federation-peer ") else "federation-peer "
            parts = text[len(prefix):].strip().split()
            kid = parts[0] if parts else "satellite_kernel_1"
            kname = parts[1] if len(parts) > 1 else "Satellite"
            kendpoint = parts[2] if len(parts) > 2 else "ipc://satellite"
            if hasattr(self.runtime, "multi_kernel_federation"):
                peer = self.runtime.multi_kernel_federation.register_remote_kernel(kid, kname, kendpoint, ["compute", "memory"])
                msg = f"[Kernel Federation]: Peered remote kernel '{peer.kernel_id}' ({peer.name}) at '{peer.endpoint}'."
                return RouterResponse(msg, data=peer.to_dict())

'''
if router_hook in rc and 'multi_kernel_federation' not in rc:
    rc = rc.replace(router_hook, fed_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 201 successfully wired into lucy_runtime.py and router.py!')
