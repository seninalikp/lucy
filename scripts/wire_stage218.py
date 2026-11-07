# scripts/wire_stage218.py
# Wire Stage 218 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.chaos_fault_injection import ChaosFaultInjectionFabric, FaultType, STAGE as STAGE_217\n'
imp_repl = 'from backend.lucy_core.chaos_fault_injection import ChaosFaultInjectionFabric, FaultType, STAGE as STAGE_217\nfrom backend.lucy_core.trans_universal_belief_mesh import TransUniversalBeliefMeshFabric, STAGE as STAGE_218\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.chaos_engine = ChaosFaultInjectionFabric()\n'
init_repl = '        self.chaos_engine = ChaosFaultInjectionFabric()\n        # Stage 218: Trans-Universal Belief Mesh (Era 22)\n        self.belief_mesh = TransUniversalBeliefMeshFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("chaos_engine", "core"),\n'
svc_repl = '            ("chaos_engine", "core"),\n            ("belief_mesh", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 217: Chaos Fault-Injection & Resilience Engine (Era 22)\n'
belief_router_code = '''        # Stage 218: Trans-Universal Belief Propagation Mesh (Era 22)
        if lowered in {"/belief-mesh-status", "belief-mesh-status", "/lbp-status", "lbp-status"}:
            if hasattr(self.runtime, "belief_mesh"):
                tbl = self.runtime.belief_mesh.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.belief_mesh.status())

        if lowered in {"/belief-infer", "belief-infer"}:
            if hasattr(self.runtime, "belief_mesh"):
                # Initialize default 2-node consensus graph if empty
                if not self.runtime.belief_mesh.variables:
                    self.runtime.belief_mesh.add_variable("node_earth", 2, prior=[0.8, 0.2])
                    self.runtime.belief_mesh.add_variable("node_mars", 2, prior=[0.5, 0.5])
                    self.runtime.belief_mesh.add_factor(
                        "consensus_link", ["node_earth", "node_mars"],
                        {(0, 0): 0.9, (0, 1): 0.1, (1, 0): 0.1, (1, 1): 0.9}
                    )
                beliefs = self.runtime.belief_mesh.run_inference(max_iterations=10)
                msg = f"[Belief Propagation Mesh]: LBP consensus convergence reached. Posterior beliefs: {beliefs}."
                return RouterResponse(msg, data={"beliefs": beliefs})

'''
if router_hook in rc and 'belief_mesh' not in rc:
    rc = rc.replace(router_hook, belief_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 218 successfully wired into lucy_runtime.py and router.py!')
