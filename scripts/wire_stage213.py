# scripts/wire_stage213.py
# Wire Stage 213 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.interplanetary_dtn_routing import InterplanetaryDTNRoutingFabric, STAGE as STAGE_212\n'
imp_repl = 'from backend.lucy_core.interplanetary_dtn_routing import InterplanetaryDTNRoutingFabric, STAGE as STAGE_212\nfrom backend.lucy_core.tensor_train_engine import TensorTrainEngineFabric, STAGE as STAGE_213\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.interplanetary_dtn = InterplanetaryDTNRoutingFabric()\n'
init_repl = '        self.interplanetary_dtn = InterplanetaryDTNRoutingFabric()\n        # Stage 213: Tensor-Train Engine (Era 22)\n        self.tensor_train_engine = TensorTrainEngineFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("interplanetary_dtn", "core"),\n'
svc_repl = '            ("interplanetary_dtn", "core"),\n            ("tensor_train_engine", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 212: Interplanetary DTN Routing Fabric (Era 22)\n'
tt_router_code = '''        # Stage 213: Tensor-Train Decomposer Engine (Era 22)
        if lowered in {"/tensor-train-status", "tensor-train-status", "/mps-status", "mps-status"}:
            if hasattr(self.runtime, "tensor_train_engine"):
                tbl = self.runtime.tensor_train_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.tensor_train_engine.status())

        if lowered.startswith("/tt-create ") or lowered.startswith("tt-create "):
            prefix = "/tt-create " if lowered.startswith("/tt-create ") else "tt-create "
            raw_dims = text[len(prefix):].strip().split()
            if hasattr(self.runtime, "tensor_train_engine"):
                try:
                    dims = [int(d) for d in raw_dims] if raw_dims else [2, 2, 2]
                except ValueError:
                    dims = [2, 2, 2]
                tt = self.runtime.tensor_train_engine.create_canonical_rank1_tt(dims)
                msg = f"[Tensor-Train Engine]: Created canonical rank-1 TT with dims {dims}. Frobenius norm: {tt.frobenius_norm():.4f}."
                return RouterResponse(msg, data={"mode_dimensions": dims, "ranks": tt.ranks, "norm": tt.frobenius_norm()})

'''
if router_hook in rc and 'tensor_train_engine' not in rc:
    rc = rc.replace(router_hook, tt_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 213 successfully wired into lucy_runtime.py and router.py!')
