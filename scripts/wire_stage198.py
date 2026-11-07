# scripts/wire_stage198.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.global_chrono_log import GlobalChronoLogFabric, STAGE as STAGE_197\n'
imp_repl = 'from backend.lucy_core.global_chrono_log import GlobalChronoLogFabric, STAGE as STAGE_197\nfrom backend.lucy_core.daemon_mesh_sentinel import DaemonMeshSentinelFabric, STAGE as STAGE_198\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.chrono_log_fabric = GlobalChronoLogFabric()\n'
init_repl = '        self.chrono_log_fabric = GlobalChronoLogFabric()\n        # Stage 198: Sovereign Autonomous Daemon Mesh & Heartbeat Sentinel (Era 20)\n        self.daemon_mesh_fabric = DaemonMeshSentinelFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("chrono_log_fabric", "core"),\n'
svc_repl = '            ("chrono_log_fabric", "core"),\n            ("daemon_mesh_fabric", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
mesh_router_code = '''        # Stage 198: Sovereign Autonomous Daemon Mesh & Heartbeat Sentinel (Era 20)
        if lowered in {"/mesh-status", "mesh-status", "/daemon-mesh-status", "daemon-mesh-status"}:
            if hasattr(self.runtime, "daemon_mesh_fabric"):
                tbl = self.runtime.daemon_mesh_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.daemon_mesh_fabric.status())

        if lowered.startswith("/mesh-ping ") or lowered.startswith("mesh-ping "):
            prefix = "/mesh-ping " if lowered.startswith("/mesh-ping ") else "mesh-ping "
            nid = text[len(prefix):].strip() or "peer_node"
            if hasattr(self.runtime, "daemon_mesh_fabric"):
                if nid not in self.runtime.daemon_mesh_fabric.peers:
                    self.runtime.daemon_mesh_fabric.register_peer(nid)
                self.runtime.daemon_mesh_fabric.record_heartbeat(nid)
                msg = f"[Daemon Mesh]: Heartbeat recorded for '{nid}'. State: ALIVE."
                return RouterResponse(msg, data={"node_id": nid, "state": "ALIVE"})

'''
if router_hook in rc and 'daemon_mesh_fabric' not in rc:
    rc = rc.replace(router_hook, mesh_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 198 successfully wired into lucy_runtime.py and router.py!')
