# scripts/wire_stage204.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.sovereign_contract_engine import SovereignContractEngineFabric, STAGE as STAGE_203\n'
imp_repl = 'from backend.lucy_core.sovereign_contract_engine import SovereignContractEngineFabric, STAGE as STAGE_203\nfrom backend.lucy_core.neuromorphic_spike_mesh import NeuromorphicSpikeMeshFabric, STAGE as STAGE_204\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.sovereign_contract_engine = SovereignContractEngineFabric()\n'
init_repl = '        self.sovereign_contract_engine = SovereignContractEngineFabric()\n        # Stage 204: Neuromorphic Spike Mesh (Era 21)\n        self.neuromorphic_spike_mesh = NeuromorphicSpikeMeshFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("sovereign_contract_engine", "core"),\n'
svc_repl = '            ("sovereign_contract_engine", "core"),\n            ("neuromorphic_spike_mesh", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
spike_router_code = '''        # Stage 204: Neuromorphic Event-Driven Spike Router (Era 21)
        if lowered in {"/spike-status", "spike-status", "/neuromorphic-status", "neuromorphic-status"}:
            if hasattr(self.runtime, "neuromorphic_spike_mesh"):
                tbl = self.runtime.neuromorphic_spike_mesh.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.neuromorphic_spike_mesh.status())

        if lowered.startswith("/spike-step ") or lowered.startswith("spike-step "):
            prefix = "/spike-step " if lowered.startswith("/spike-step ") else "spike-step "
            val_str = text[len(prefix):].strip()
            try:
                curr = float(val_str)
            except ValueError:
                curr = 1.5
            if hasattr(self.runtime, "neuromorphic_spike_mesh"):
                spikes = self.runtime.neuromorphic_spike_mesh.step_simulation(external_currents={0: curr})
                msg = f"[Neuromorphic Mesh]: Step completed. Spikes emitted: {len(spikes)} (Neuron 0 current={curr})."
                return RouterResponse(msg, data={"spikes_count": len(spikes), "spikes": [s.to_dict() for s in spikes]})

'''
if router_hook in rc and 'neuromorphic_spike_mesh' not in rc:
    rc = rc.replace(router_hook, spike_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 204 successfully wired into lucy_runtime.py and router.py!')
