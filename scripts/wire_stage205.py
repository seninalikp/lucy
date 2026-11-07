# scripts/wire_stage205.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.neuromorphic_spike_mesh import NeuromorphicSpikeMeshFabric, STAGE as STAGE_204\n'
imp_repl = 'from backend.lucy_core.neuromorphic_spike_mesh import NeuromorphicSpikeMeshFabric, STAGE as STAGE_204\nfrom backend.lucy_core.knowledge_distillation_pruner import KnowledgeDistillationPrunerFabric, STAGE as STAGE_205\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.neuromorphic_spike_mesh = NeuromorphicSpikeMeshFabric()\n'
init_repl = '        self.neuromorphic_spike_mesh = NeuromorphicSpikeMeshFabric()\n        # Stage 205: Knowledge Distillation & Model Pruner (Era 21)\n        self.knowledge_distillation_pruner = KnowledgeDistillationPrunerFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("neuromorphic_spike_mesh", "core"),\n'
svc_repl = '            ("neuromorphic_spike_mesh", "core"),\n            ("knowledge_distillation_pruner", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
pruner_router_code = '''        # Stage 205: Knowledge Distillation & Model Pruner (Era 21)
        if lowered in {"/pruner-status", "pruner-status", "/distillation-status", "distillation-status"}:
            if hasattr(self.runtime, "knowledge_distillation_pruner"):
                tbl = self.runtime.knowledge_distillation_pruner.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.knowledge_distillation_pruner.status())

        if lowered.startswith("/prune-matrix ") or lowered.startswith("prune-matrix "):
            prefix = "/prune-matrix " if lowered.startswith("/prune-matrix ") else "prune-matrix "
            sp_str = text[len(prefix):].strip()
            try:
                sp_val = float(sp_str)
            except ValueError:
                sp_val = 0.5
            if hasattr(self.runtime, "knowledge_distillation_pruner"):
                sample = [[1.0, 2.0], [3.0, 4.0]]
                _, csr, act = self.runtime.knowledge_distillation_pruner.prune_unstructured(sample, target_sparsity=sp_val)
                msg = f"[Model Pruner]: Matrix pruned to {act*100:.1f}% sparsity. Non-zero elements: {len(csr.values)}."
                return RouterResponse(msg, data={"actual_sparsity": act, "csr": csr.to_dict()})

'''
if router_hook in rc and 'knowledge_distillation_pruner' not in rc:
    rc = rc.replace(router_hook, pruner_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 205 successfully wired into lucy_runtime.py and router.py!')
