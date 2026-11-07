# scripts/wire_stage193.py
import re

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.kernel_self_healing import KernelSelfHealingFabric, STAGE as STAGE_192\n'
imp_repl = 'from backend.lucy_core.kernel_self_healing import KernelSelfHealingFabric, STAGE as STAGE_192\nfrom backend.lucy_core.raft_bft_hybrid import RaftBFTHybridFabric, STAGE as STAGE_193\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.kernel_self_healing = KernelSelfHealingFabric()\n'
init_repl = '        self.kernel_self_healing = KernelSelfHealingFabric()\n        # Stage 193: Sovereign Distributed Consensus Raft-BFT Hybrid (Era 20)\n        self.raft_bft_fabric = RaftBFTHybridFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("kernel_self_healing", "core"),\n'
svc_repl = '            ("kernel_self_healing", "core"),\n            ("raft_bft_fabric", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
bft_router_code = '''        # Stage 193: Sovereign Distributed Consensus Raft-BFT Hybrid (Era 20)
        if lowered in {"/bft-status", "bft-status", "/raft-bft-status", "raft-bft-status"}:
            if hasattr(self.runtime, "raft_bft_fabric"):
                tbl = self.runtime.raft_bft_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.raft_bft_fabric.status())

        if lowered.startswith("/bft-propose ") or lowered.startswith("bft-propose "):
            prefix = "/bft-propose " if lowered.startswith("/bft-propose ") else "bft-propose "
            parts = text[len(prefix):].strip().split()
            k = parts[0] if parts else "key"
            v = parts[1] if len(parts) > 1 else "val"
            if hasattr(self.runtime, "raft_bft_fabric"):
                ok, entry = self.runtime.raft_bft_fabric.propose_command({k: v})
                msg = f"[Raft-BFT]: Proposed '{k}={v}'. Committed: {ok} (Log Index: {entry.index if entry else 'N/A'})"
                return RouterResponse(msg, data=entry.to_dict() if entry else {})

'''
if router_hook in rc and 'raft_bft_fabric' not in rc:
    rc = rc.replace(router_hook, bft_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 193 successfully wired into lucy_runtime.py and router.py!')
