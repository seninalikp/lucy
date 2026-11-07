# scripts/wire_stage199.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.daemon_mesh_sentinel import DaemonMeshSentinelFabric, STAGE as STAGE_198\n'
imp_repl = 'from backend.lucy_core.daemon_mesh_sentinel import DaemonMeshSentinelFabric, STAGE as STAGE_198\nfrom backend.lucy_core.bicentennial_singularity_nexus import BicentennialSingularityNexus, STAGE as STAGE_199\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.daemon_mesh_fabric = DaemonMeshSentinelFabric()\n'
init_repl = '        self.daemon_mesh_fabric = DaemonMeshSentinelFabric()\n        # Stage 199: Bicentennial Singularity Nexus & 200-Stage Master Orchestrator (Era 20)\n        self.bicentennial_nexus = BicentennialSingularityNexus(runtime=self)\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("daemon_mesh_fabric", "core"),\n'
svc_repl = '            ("daemon_mesh_fabric", "core"),\n            ("bicentennial_nexus", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
singularity_router_code = '''        # Stage 199: Bicentennial Singularity Nexus & 200-Stage Master Orchestrator (Era 20)
        if lowered in {"/singularity-status", "singularity-status", "/nexus-status", "nexus-status"}:
            if hasattr(self.runtime, "bicentennial_nexus"):
                tbl = self.runtime.bicentennial_nexus.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.bicentennial_nexus.status())

        if lowered.startswith("/singularity-run ") or lowered.startswith("singularity-run "):
            prefix = "/singularity-run " if lowered.startswith("/singularity-run ") else "singularity-run "
            action_txt = text[len(prefix):].strip() or "transcendence"
            if hasattr(self.runtime, "bicentennial_nexus"):
                res = self.runtime.bicentennial_nexus.execute_singularity_pipeline({"action": action_txt})
                msg = f"[Singularity Nexus]: Pipeline {res.pipeline_id} completed. Score: {res.singularity_score:.1f}% (BFT={res.bft_committed}, SHM Slot={res.shm_slot_id}, AST={res.ast_optimized}, Chrono Seq={res.chrono_event_seq}, Mesh Primary={res.mesh_primary})"
                return RouterResponse(msg, data=res.to_dict())

'''
if router_hook in rc and 'bicentennial_nexus' not in rc:
    rc = rc.replace(router_hook, singularity_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 199 successfully wired into lucy_runtime.py and router.py!')
