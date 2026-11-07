# scripts/wire_stage203.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.post_quantum_crypto import PostQuantumCryptoFabric, STAGE as STAGE_202\n'
imp_repl = 'from backend.lucy_core.post_quantum_crypto import PostQuantumCryptoFabric, STAGE as STAGE_202\nfrom backend.lucy_core.sovereign_contract_engine import SovereignContractEngineFabric, STAGE as STAGE_203\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.post_quantum_crypto = PostQuantumCryptoFabric()\n'
init_repl = '        self.post_quantum_crypto = PostQuantumCryptoFabric()\n        # Stage 203: Autonomous Decentralized Sovereign Contract (Era 21)\n        self.sovereign_contract_engine = SovereignContractEngineFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("post_quantum_crypto", "core"),\n'
svc_repl = '            ("post_quantum_crypto", "core"),\n            ("sovereign_contract_engine", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
contract_router_code = '''        # Stage 203: Autonomous Decentralized Sovereign Contract (Era 21)
        if lowered in {"/contract-status", "contract-status", "/smart-contract-status", "smart-contract-status"}:
            if hasattr(self.runtime, "sovereign_contract_engine"):
                tbl = self.runtime.sovereign_contract_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.sovereign_contract_engine.status())

        if lowered.startswith("/contract-deploy ") or lowered.startswith("contract-deploy "):
            prefix = "/contract-deploy " if lowered.startswith("/contract-deploy ") else "contract-deploy "
            owner = text[len(prefix):].strip() or "Senin"
            if hasattr(self.runtime, "sovereign_contract_engine"):
                from backend.lucy_core.sovereign_contract_engine import ContractInstruction
                code = [
                    ContractInstruction("PUSH", 100),
                    ContractInstruction("PUSH", 200),
                    ContractInstruction("ADD"),
                    ContractInstruction("RETURN"),
                ]
                cid = self.runtime.sovereign_contract_engine.deploy_contract(owner, code)
                msg = f"[Sovereign Contract Engine]: Contract '{cid}' deployed by owner '{owner}'."
                return RouterResponse(msg, data={"contract_id": cid, "owner": owner})

'''
if router_hook in rc and 'sovereign_contract_engine' not in rc:
    rc = rc.replace(router_hook, contract_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 203 successfully wired into lucy_runtime.py and router.py!')
