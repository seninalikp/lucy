# scripts/wire_stage214.py
# Wire Stage 214 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.tensor_train_engine import TensorTrainEngineFabric, STAGE as STAGE_213\n'
imp_repl = 'from backend.lucy_core.tensor_train_engine import TensorTrainEngineFabric, STAGE as STAGE_213\nfrom backend.lucy_core.holographic_associative_memory import HolographicAssociativeMemoryFabric, STAGE as STAGE_214\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.tensor_train_engine = TensorTrainEngineFabric()\n'
init_repl = '        self.tensor_train_engine = TensorTrainEngineFabric()\n        # Stage 214: Holographic Associative Memory (Era 22)\n        self.holographic_memory = HolographicAssociativeMemoryFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("tensor_train_engine", "core"),\n'
svc_repl = '            ("tensor_train_engine", "core"),\n            ("holographic_memory", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 213: Tensor-Train Decomposer Engine (Era 22)\n'
hcam_router_code = '''        # Stage 214: Holographic Associative Memory Fabric (Era 22)
        if lowered in {"/hcam-status", "hcam-status", "/holographic-status", "holographic-status"}:
            if hasattr(self.runtime, "holographic_memory"):
                tbl = self.runtime.holographic_memory.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.holographic_memory.status())

        if lowered.startswith("/hcam-store ") or lowered.startswith("hcam-store "):
            prefix = "/hcam-store " if lowered.startswith("/hcam-store ") else "hcam-store "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            if len(parts) >= 2 and hasattr(self.runtime, "holographic_memory"):
                k, v = parts[0], parts[1]
                p = self.runtime.holographic_memory.store_page(k, v)
                msg = f"[Holographic CAM]: Encoded memory '{k}' into optical interference volume (Page: {p.page_id})."
                return RouterResponse(msg, data=p.to_dict())

        if lowered.startswith("/hcam-recall ") or lowered.startswith("hcam-recall "):
            prefix = "/hcam-recall " if lowered.startswith("/hcam-recall ") else "hcam-recall "
            query = text[len(prefix):].strip()
            if hasattr(self.runtime, "holographic_memory"):
                matches = self.runtime.holographic_memory.associative_recall(query, correlation_threshold=0.5)
                res_summary = [{"key": m[0].key, "corr": m[1], "data": m[0].associated_data} for m in matches]
                msg = f"[Holographic CAM]: Associative phase correlation for '{query}' returned {len(matches)} matches: {res_summary}."
                return RouterResponse(msg, data={"matches": res_summary})

'''
if router_hook in rc and 'holographic_memory' not in rc:
    rc = rc.replace(router_hook, hcam_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 214 successfully wired into lucy_runtime.py and router.py!')
