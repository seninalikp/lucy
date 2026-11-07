# scripts/wire_stage208.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.compute_governor import ComputeGovernorFabric, STAGE as STAGE_207\n'
imp_repl = 'from backend.lucy_core.compute_governor import ComputeGovernorFabric, STAGE as STAGE_207\nfrom backend.lucy_core.multimodal_symbolic_grounding import MultimodalSymbolicGroundingFabric, STAGE as STAGE_208\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.compute_governor = ComputeGovernorFabric()\n'
init_repl = '        self.compute_governor = ComputeGovernorFabric()\n        # Stage 208: Multimodal Symbolic Grounding (Era 21)\n        self.multimodal_grounding = MultimodalSymbolicGroundingFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("compute_governor", "core"),\n'
svc_repl = '            ("compute_governor", "core"),\n            ("multimodal_grounding", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
ground_router_code = '''        # Stage 208: Multi-Modal Symbolic Grounding Fabric (Era 21)
        if lowered in {"/grounding-status", "grounding-status", "/symbolic-grounding-status", "symbolic-grounding-status"}:
            if hasattr(self.runtime, "multimodal_grounding"):
                tbl = self.runtime.multimodal_grounding.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.multimodal_grounding.status())

        if lowered.startswith("/grounding-query ") or lowered.startswith("grounding-query "):
            prefix = "/grounding-query " if lowered.startswith("/grounding-query ") else "grounding-query "
            lbl = text[len(prefix):].strip()
            if hasattr(self.runtime, "multimodal_grounding"):
                matches = self.runtime.multimodal_grounding.query_grounded_symbol(lbl)
                msg = f"[Symbolic Grounding]: Resolved {len(matches)} matching grounded entities for '{lbl}'."
                return RouterResponse(msg, data={"matches_count": len(matches), "entities": [m[0].to_dict() for m in matches]})

'''
if router_hook in rc and 'multimodal_grounding' not in rc:
    rc = rc.replace(router_hook, ground_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 208 successfully wired into lucy_runtime.py and router.py!')
