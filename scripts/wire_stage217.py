# scripts/wire_stage217.py
# Wire Stage 217 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.quantum_hybrid_coprocessor import QuantumHybridCoprocessorFabric, PauliTerm, STAGE as STAGE_216\n'
imp_repl = 'from backend.lucy_core.quantum_hybrid_coprocessor import QuantumHybridCoprocessorFabric, PauliTerm, STAGE as STAGE_216\nfrom backend.lucy_core.chaos_fault_injection import ChaosFaultInjectionFabric, FaultType, STAGE as STAGE_217\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.quantum_coprocessor = QuantumHybridCoprocessorFabric()\n'
init_repl = '        self.quantum_coprocessor = QuantumHybridCoprocessorFabric()\n        # Stage 217: Chaos Fault Injection (Era 22)\n        self.chaos_engine = ChaosFaultInjectionFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("quantum_coprocessor", "core"),\n'
svc_repl = '            ("quantum_coprocessor", "core"),\n            ("chaos_engine", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 216: Quantum Hybrid Coprocessor & VQE Engine (Era 22)\n'
chaos_router_code = '''        # Stage 217: Chaos Fault-Injection & Resilience Engine (Era 22)
        if lowered in {"/chaos-status", "chaos-status", "/fault-status", "fault-status"}:
            if hasattr(self.runtime, "chaos_engine"):
                tbl = self.runtime.chaos_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.chaos_engine.status())

        if lowered in {"/chaos-campaign", "chaos-campaign"}:
            if hasattr(self.runtime, "chaos_engine"):
                res = self.runtime.chaos_engine.run_chaos_campaign(["kernel_bus", "quantum_coprocessor", "dtn_router"])
                msg = f"[Chaos Engine]: Campaign complete. Resilience Score: {res['resilience_score']} ({res['total_experiments']} tests run)."
                return RouterResponse(msg, data=res)

        if lowered.startswith("/chaos-inject ") or lowered.startswith("chaos-inject "):
            prefix = "/chaos-inject " if lowered.startswith("/chaos-inject ") else "chaos-inject "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            if len(parts) >= 2 and hasattr(self.runtime, "chaos_engine"):
                ft_str, tgt = parts[0].upper(), parts[1]
                from backend.lucy_core.chaos_fault_injection import FaultType
                ft = getattr(FaultType, ft_str, FaultType.LATENCY_SPIKE)
                exp = self.runtime.chaos_engine.inject_fault(ft, tgt)
                msg = f"[Chaos Engine]: Injected fault '{ft.value}' into target '{tgt}' (ID: {exp.experiment_id})."
                return RouterResponse(msg, data=exp.to_dict())

'''
if router_hook in rc and 'chaos_engine' not in rc:
    rc = rc.replace(router_hook, chaos_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 217 successfully wired into lucy_runtime.py and router.py!')
