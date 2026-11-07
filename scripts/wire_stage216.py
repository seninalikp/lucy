# scripts/wire_stage216.py
# Wire Stage 216 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.async_micro_actor_mesh import AsyncMicroActorMeshFabric, STAGE as STAGE_215\n'
imp_repl = 'from backend.lucy_core.async_micro_actor_mesh import AsyncMicroActorMeshFabric, STAGE as STAGE_215\nfrom backend.lucy_core.quantum_hybrid_coprocessor import QuantumHybridCoprocessorFabric, PauliTerm, STAGE as STAGE_216\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.micro_actor_mesh = AsyncMicroActorMeshFabric()\n'
init_repl = '        self.micro_actor_mesh = AsyncMicroActorMeshFabric()\n        # Stage 216: Quantum Hybrid Coprocessor (Era 22)\n        self.quantum_coprocessor = QuantumHybridCoprocessorFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("micro_actor_mesh", "core"),\n'
svc_repl = '            ("micro_actor_mesh", "core"),\n            ("quantum_coprocessor", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 215: Async Micro-Actor Mesh Fabric (Era 22)\n'
vqe_router_code = '''        # Stage 216: Quantum Hybrid Coprocessor & VQE Engine (Era 22)
        if lowered in {"/quantum-coprocessor-status", "quantum-coprocessor-status", "/vqe-status", "vqe-status"}:
            if hasattr(self.runtime, "quantum_coprocessor"):
                tbl = self.runtime.quantum_coprocessor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.quantum_coprocessor.status())

        if lowered in {"/vqe-run", "vqe-run"}:
            if hasattr(self.runtime, "quantum_coprocessor"):
                from backend.lucy_core.quantum_hybrid_coprocessor import PauliTerm
                hamiltonian = [PauliTerm(coeff=-1.0, pauli_string="ZZ")]
                res = self.runtime.quantum_coprocessor.run_vqe(hamiltonian, max_iterations=10)
                msg = f"[Quantum Co-Processor]: VQE ground-state optimization complete. E0: {res.ground_state_energy:.4f} (Optimal params: {res.optimal_parameters})."
                return RouterResponse(msg, data=res.to_dict())

'''
if router_hook in rc and 'quantum_coprocessor' not in rc:
    rc = rc.replace(router_hook, vqe_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 216 successfully wired into lucy_runtime.py and router.py!')
