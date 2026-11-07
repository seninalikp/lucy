# scripts/wire_stage212.py
# Wire Stage 212 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.photonic_matrix_multiplier import PhotonicMatrixMultiplierFabric, STAGE as STAGE_211\n'
imp_repl = 'from backend.lucy_core.photonic_matrix_multiplier import PhotonicMatrixMultiplierFabric, STAGE as STAGE_211\nfrom backend.lucy_core.interplanetary_dtn_routing import InterplanetaryDTNRoutingFabric, STAGE as STAGE_212\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.photonic_matrix_multiplier = PhotonicMatrixMultiplierFabric()\n'
init_repl = '        self.photonic_matrix_multiplier = PhotonicMatrixMultiplierFabric()\n        # Stage 212: Interplanetary DTN Routing (Era 22)\n        self.interplanetary_dtn = InterplanetaryDTNRoutingFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("photonic_matrix_multiplier", "core"),\n'
svc_repl = '            ("photonic_matrix_multiplier", "core"),\n            ("interplanetary_dtn", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 211: Photonic Matrix Multiplier Fabric (Era 22)\n'
dtn_router_code = '''        # Stage 212: Interplanetary DTN Routing Fabric (Era 22)
        if lowered in {"/dtn-status", "dtn-status", "/interplanetary-status", "interplanetary-status"}:
            if hasattr(self.runtime, "interplanetary_dtn"):
                tbl = self.runtime.interplanetary_dtn.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.interplanetary_dtn.status())

        if lowered.startswith("/dtn-bundle ") or lowered.startswith("dtn-bundle "):
            prefix = "/dtn-bundle " if lowered.startswith("/dtn-bundle ") else "dtn-bundle "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            if len(parts) >= 2 and hasattr(self.runtime, "interplanetary_dtn"):
                dest, payload = parts[0], parts[1]
                b = self.runtime.interplanetary_dtn.create_bundle(dest, payload)
                msg = f"[Interplanetary DTN]: Injected bundle '{b.bundle_id}' targeting '{dest}' into custody buffer."
                return RouterResponse(msg, data=b.to_dict())

        if lowered in {"/dtn-step", "dtn-step"}:
            if hasattr(self.runtime, "interplanetary_dtn"):
                forwarded = self.runtime.interplanetary_dtn.route_step()
                msg = f"[Interplanetary DTN]: Routing step executed. Forwarded bundles: {forwarded}."
                return RouterResponse(msg, data={"forwarded_bundles": forwarded})

'''
if router_hook in rc and 'interplanetary_dtn' not in rc:
    rc = rc.replace(router_hook, dtn_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 212 successfully wired into lucy_runtime.py and router.py!')
