# scripts/wire_stage202.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.multi_kernel_federation import MultiKernelFederationFabric, STAGE as STAGE_201\n'
imp_repl = 'from backend.lucy_core.multi_kernel_federation import MultiKernelFederationFabric, STAGE as STAGE_201\nfrom backend.lucy_core.post_quantum_crypto import PostQuantumCryptoFabric, STAGE as STAGE_202\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.multi_kernel_federation = MultiKernelFederationFabric()\n'
init_repl = '        self.multi_kernel_federation = MultiKernelFederationFabric()\n        # Stage 202: Quantum-Resistant Lattice Cryptography (Era 21)\n        self.post_quantum_crypto = PostQuantumCryptoFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("multi_kernel_federation", "core"),\n'
svc_repl = '            ("multi_kernel_federation", "core"),\n            ("post_quantum_crypto", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
pqc_router_code = '''        # Stage 202: Quantum-Resistant Lattice Cryptography (Era 21)
        if lowered in {"/pqc-status", "pqc-status", "/quantum-crypto-status", "quantum-crypto-status"}:
            if hasattr(self.runtime, "post_quantum_crypto"):
                tbl = self.runtime.post_quantum_crypto.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.post_quantum_crypto.status())

        if lowered.startswith("/pqc-sign ") or lowered.startswith("pqc-sign "):
            prefix = "/pqc-sign " if lowered.startswith("/pqc-sign ") else "pqc-sign "
            raw_msg = text[len(prefix):].strip().encode("utf-8")
            if hasattr(self.runtime, "post_quantum_crypto"):
                sig = self.runtime.post_quantum_crypto.sign_quantum(raw_msg)
                msg = f"[ML-DSA Post-Quantum Signature]: Message Digest={sig.message_digest[:16]}... | Sig Len={len(sig.signature_bytes)}B"
                return RouterResponse(msg, data=sig.to_dict())

'''
if router_hook in rc and 'post_quantum_crypto' not in rc:
    rc = rc.replace(router_hook, pqc_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 202 successfully wired into lucy_runtime.py and router.py!')
