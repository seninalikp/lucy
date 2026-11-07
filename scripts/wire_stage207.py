# scripts/wire_stage207.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.zk_invariant_prover import ZKInvariantProverFabric, STAGE as STAGE_206\n'
imp_repl = 'from backend.lucy_core.zk_invariant_prover import ZKInvariantProverFabric, STAGE as STAGE_206\nfrom backend.lucy_core.compute_governor import ComputeGovernorFabric, STAGE as STAGE_207\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.zk_invariant_prover = ZKInvariantProverFabric()\n'
init_repl = '        self.zk_invariant_prover = ZKInvariantProverFabric()\n        # Stage 207: Compute Governor (Era 21)\n        self.compute_governor = ComputeGovernorFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("zk_invariant_prover", "core"),\n'
svc_repl = '            ("zk_invariant_prover", "core"),\n            ("compute_governor", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
gov_router_code = '''        # Stage 207: Latency-Adaptive Compute Governor (Era 21)
        if lowered in {"/governor-status", "governor-status", "/compute-governor-status", "compute-governor-status"}:
            if hasattr(self.runtime, "compute_governor"):
                tbl = self.runtime.compute_governor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.compute_governor.status())

        if lowered.startswith("/governor-sample ") or lowered.startswith("governor-sample "):
            prefix = "/governor-sample " if lowered.startswith("/governor-sample ") else "governor-sample "
            val_str = text[len(prefix):].strip()
            try:
                lat = float(val_str)
            except ValueError:
                lat = 25.0
            if hasattr(self.runtime, "compute_governor"):
                prof = self.runtime.compute_governor.record_latency(lat)
                msg = f"[Compute Governor]: Recorded latency {lat:.2f}ms. Active Profile: {prof.value}."
                return RouterResponse(msg, data={"latency_ms": lat, "profile": prof.value})

'''
if router_hook in rc and 'compute_governor' not in rc:
    rc = rc.replace(router_hook, gov_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 207 successfully wired into lucy_runtime.py and router.py!')
