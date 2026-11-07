# scripts/wire_stage209.py
# Wire Stage 209 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.multimodal_symbolic_grounding import MultimodalSymbolicGroundingFabric, STAGE as STAGE_208\n'
imp_repl = 'from backend.lucy_core.multimodal_symbolic_grounding import MultimodalSymbolicGroundingFabric, STAGE as STAGE_208\nfrom backend.lucy_core.hyperscale_mesh_synchronizer import HyperscaleMeshSynchronizerFabric, STAGE as STAGE_209\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.multimodal_grounding = MultimodalSymbolicGroundingFabric()\n'
init_repl = '        self.multimodal_grounding = MultimodalSymbolicGroundingFabric()\n        # Stage 209: Hyperscale Mesh Synchronizer (Era 21)\n        self.hyperscale_mesh = HyperscaleMeshSynchronizerFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("multimodal_grounding", "core"),\n'
svc_repl = '            ("multimodal_grounding", "core"),\n            ("hyperscale_mesh", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 208: Multi-Modal Symbolic Grounding Fabric (Era 21)\n'
mesh_router_code = '''        # Stage 209: Hyper-Scale Cluster Mesh Synchronizer (Era 21)
        if lowered in {"/cluster-mesh-status", "cluster-mesh-status", "/mesh-sync-status", "mesh-sync-status"}:
            if hasattr(self.runtime, "hyperscale_mesh"):
                tbl = self.runtime.hyperscale_mesh.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.hyperscale_mesh.status())

        if lowered.startswith("/cluster-sync ") or lowered.startswith("cluster-sync "):
            prefix = "/cluster-sync " if lowered.startswith("/cluster-sync ") else "cluster-sync "
            parts = text[len(prefix):].strip().split()
            if len(parts) >= 2 and hasattr(self.runtime, "hyperscale_mesh"):
                src, tgt = parts[0], parts[1]
                count, keys = self.runtime.hyperscale_mesh.anti_entropy_sync(src, tgt)
                msg = f"[Cluster Mesh Synchronizer]: Synchronized clusters '{src}' and '{tgt}'. Reconciled {count} keys: {keys}."
                return RouterResponse(msg, data={"reconciled_count": count, "reconciled_keys": keys})

'''
if router_hook in rc and 'hyperscale_mesh' not in rc:
    rc = rc.replace(router_hook, mesh_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 209 successfully wired into lucy_runtime.py and router.py!')
