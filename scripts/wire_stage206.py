# scripts/wire_stage206.py
# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.knowledge_distillation_pruner import KnowledgeDistillationPrunerFabric, STAGE as STAGE_205\n'
imp_repl = 'from backend.lucy_core.knowledge_distillation_pruner import KnowledgeDistillationPrunerFabric, STAGE as STAGE_205\nfrom backend.lucy_core.zk_invariant_prover import ZKInvariantProverFabric, STAGE as STAGE_206\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.knowledge_distillation_pruner = KnowledgeDistillationPrunerFabric()\n'
init_repl = '        self.knowledge_distillation_pruner = KnowledgeDistillationPrunerFabric()\n        # Stage 206: ZK Invariant Prover (Era 21)\n        self.zk_invariant_prover = ZKInvariantProverFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("knowledge_distillation_pruner", "core"),\n'
svc_repl = '            ("knowledge_distillation_pruner", "core"),\n            ("zk_invariant_prover", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 106: Offline Multi-Modal Voice Fabric\n'
zk_router_code = '''        # Stage 206: Autonomous Zero-Knowledge Proof Invariant Generator (Era 21)
        if lowered in {"/zk-status", "zk-status", "/zk-prover-status", "zk-prover-status"}:
            if hasattr(self.runtime, "zk_invariant_prover"):
                tbl = self.runtime.zk_invariant_prover.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.zk_invariant_prover.status())

        if lowered.startswith("/zk-prove-multiplier ") or lowered.startswith("zk-prove-multiplier "):
            prefix = "/zk-prove-multiplier " if lowered.startswith("/zk-prove-multiplier ") else "zk-prove-multiplier "
            parts = text[len(prefix):].strip().split()
            try:
                wa = int(parts[0]) if parts else 7
                wb = int(parts[1]) if len(parts) > 1 else 11
            except ValueError:
                wa, wb = 7, 11
            if hasattr(self.runtime, "zk_invariant_prover"):
                prod = wa * wb
                proof = self.runtime.zk_invariant_prover.prove_statement(
                    "circuit_multiplier",
                    witness={"w_a": wa, "w_b": wb},
                    public_inputs={"public_c": prod},
                )
                msg = f"[ZK-SNARK Prover]: Generated proof '{proof.proof_id}' for public_c={prod}. Private witness hidden."
                return RouterResponse(msg, data=proof.to_dict())

'''
if router_hook in rc and 'zk_invariant_prover' not in rc:
    rc = rc.replace(router_hook, zk_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 206 successfully wired into lucy_runtime.py and router.py!')
