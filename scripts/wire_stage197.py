# scripts/wire_stage197.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.self_evolving_code_pipeline import SelfEvolvingCodePipelineFabric, STAGE as STAGE_196\n'
imp_repl = 'from backend.lucy_core.self_evolving_code_pipeline import SelfEvolvingCodePipelineFabric, STAGE as STAGE_196\nfrom backend.lucy_core.global_chrono_log import GlobalChronoLogFabric, STAGE as STAGE_197\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.self_evolving_code_fabric = SelfEvolvingCodePipelineFabric()\n'
init_repl = '        self.self_evolving_code_fabric = SelfEvolvingCodePipelineFabric()\n        # Stage 197: Autonomous Global Chrono-Log & Event Sourcing Fabric (Era 20)\n        self.chrono_log_fabric = GlobalChronoLogFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("self_evolving_code_fabric", "core"),\n'
svc_repl = '            ("self_evolving_code_fabric", "core"),\n            ("chrono_log_fabric", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
chrono_router_code = '''        # Stage 197: Autonomous Global Chrono-Log & Event Sourcing Fabric (Era 20)
        if lowered in {"/chrono-status", "chrono-status", "/chrono-log-status", "chrono-log-status"}:
            if hasattr(self.runtime, "chrono_log_fabric"):
                tbl = self.runtime.chrono_log_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.chrono_log_fabric.status())

        if lowered.startswith("/chrono-append ") or lowered.startswith("chrono-append "):
            prefix = "/chrono-append " if lowered.startswith("/chrono-append ") else "chrono-append "
            parts = text[len(prefix):].strip().split()
            s_id = parts[0] if parts else "default_stream"
            e_type = parts[1] if len(parts) > 1 else "SET"
            k = parts[2] if len(parts) > 2 else "key"
            v = parts[3] if len(parts) > 3 else "val"
            if hasattr(self.runtime, "chrono_log_fabric"):
                ev = self.runtime.chrono_log_fabric.append_event(s_id, e_type, {k: v})
                msg = f"[Chrono-Log]: Appended Event Seq {ev.global_seq} to '{s_id}' (HLC: {ev.hlc.to_string()})"
                return RouterResponse(msg, data=ev.to_dict())

'''
if router_hook in rc and 'chrono_log_fabric' not in rc:
    rc = rc.replace(router_hook, chrono_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 197 successfully wired into lucy_runtime.py and router.py!')
