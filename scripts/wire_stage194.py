# scripts/wire_stage194.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.raft_bft_hybrid import RaftBFTHybridFabric, STAGE as STAGE_193\n'
imp_repl = 'from backend.lucy_core.raft_bft_hybrid import RaftBFTHybridFabric, STAGE as STAGE_193\nfrom backend.lucy_core.zerocopy_ipc_shm import ZeroCopyIPCShmFabric, STAGE as STAGE_194\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.raft_bft_fabric = RaftBFTHybridFabric()\n'
init_repl = '        self.raft_bft_fabric = RaftBFTHybridFabric()\n        # Stage 194: Autonomous Zero-Copy Inter-Process Shared Memory Ring (Era 20)\n        self.zerocopy_shm_fabric = ZeroCopyIPCShmFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("raft_bft_fabric", "core"),\n'
svc_repl = '            ("raft_bft_fabric", "core"),\n            ("zerocopy_shm_fabric", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
shm_router_code = '''        # Stage 194: Autonomous Zero-Copy Inter-Process Shared Memory Ring (Era 20)
        if lowered in {"/shm-status", "shm-status", "/ipc-shm-status", "ipc-shm-status"}:
            if hasattr(self.runtime, "zerocopy_shm_fabric"):
                tbl = self.runtime.zerocopy_shm_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.zerocopy_shm_fabric.status())

        if lowered.startswith("/shm-write ") or lowered.startswith("shm-write "):
            prefix = "/shm-write " if lowered.startswith("/shm-write ") else "shm-write "
            msg_txt = text[len(prefix):].strip()
            if hasattr(self.runtime, "zerocopy_shm_fabric"):
                slot_id = self.runtime.zerocopy_shm_fabric.write_direct(msg_txt.encode("utf-8"))
                msg = f"[Zero-Copy SHM]: Wrote {len(msg_txt)} bytes into slot {slot_id}."
                return RouterResponse(msg, data={"slot_id": slot_id, "bytes": len(msg_txt)})

'''
if router_hook in rc and 'zerocopy_shm_fabric' not in rc:
    rc = rc.replace(router_hook, shm_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 194 successfully wired into lucy_runtime.py and router.py!')
