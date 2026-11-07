# scripts/wire_stage196.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.distributed_tensor_runtime import DistributedTensorRuntimeFabric, STAGE as STAGE_195\n'
imp_repl = 'from backend.lucy_core.distributed_tensor_runtime import DistributedTensorRuntimeFabric, STAGE as STAGE_195\nfrom backend.lucy_core.self_evolving_code_pipeline import SelfEvolvingCodePipelineFabric, STAGE as STAGE_196\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.tensor_runtime_fabric = DistributedTensorRuntimeFabric()\n'
init_repl = '        self.tensor_runtime_fabric = DistributedTensorRuntimeFabric()\n        # Stage 196: Self-Evolving Code Synthesis & AST Verification Pipeline (Era 20)\n        self.self_evolving_code_fabric = SelfEvolvingCodePipelineFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("tensor_runtime_fabric", "core"),\n'
svc_repl = '            ("tensor_runtime_fabric", "core"),\n            ("self_evolving_code_fabric", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
ast_router_code = '''        # Stage 196: Self-Evolving Code Synthesis & AST Verification Pipeline (Era 20)
        if lowered in {"/ast-status", "ast-status", "/self-evolving-code-status", "self-evolving-code-status"}:
            if hasattr(self.runtime, "self_evolving_code_fabric"):
                tbl = self.runtime.self_evolving_code_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.self_evolving_code_fabric.status())

        if lowered.startswith("/ast-audit ") or lowered.startswith("ast-audit "):
            prefix = "/ast-audit " if lowered.startswith("/ast-audit ") else "ast-audit "
            raw_code = text[len(prefix):].strip()
            if hasattr(self.runtime, "self_evolving_code_fabric"):
                is_safe, viols = self.runtime.self_evolving_code_fabric.analyze_safety(raw_code)
                msg = f"[AST Audit]: Safe={is_safe}. Violations: {viols if viols else 'None'}"
                return RouterResponse(msg, data={"safe": is_safe, "violations": viols})

'''
if router_hook in rc and 'self_evolving_code_fabric' not in rc:
    rc = rc.replace(router_hook, ast_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 196 successfully wired into lucy_runtime.py and router.py!')
