import sys

# 1. Update lucy_runtime.py
rt_path = 'backend/lucy_core/lucy_runtime.py'
with open(rt_path, 'r', encoding='utf-8') as f:
    c = f.read()

t_imp = 'from backend.lucy_core.sovereign_cross_chain_zk_bridge import SovereignCrossChainZKBridgeFabric, STAGE as STAGE_289'
r_imp = t_imp + '\nfrom backend.lucy_core.era29_master_seal import Era29MasterSealFabric, STAGE as STAGE_290'

t_inst = 'self.cross_chain_zk_bridge = SovereignCrossChainZKBridgeFabric()'
r_inst = t_inst + '\n        # Stage 290: Era 29 Sovereign Master Seal & Trans-Cosmic Genesis\n        self.era29_master_seal = Era29MasterSealFabric()'

t_serv = '("cross_chain_zk_bridge", "core"),'
r_serv = t_serv + '\n            ("era29_master_seal", "core"),'

assert t_imp in c, 't_imp not found in lucy_runtime.py'
assert t_inst in c, 't_inst not found in lucy_runtime.py'
assert t_serv in c, 't_serv not found in lucy_runtime.py'

c = c.replace(t_imp, r_imp, 1)
c = c.replace(t_inst, r_inst, 1)
c = c.replace(t_serv, r_serv, 1)

with open(rt_path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated lucy_runtime.py for Stage 290")

# 2. Update router.py
r_path = 'backend/lucy_core/router.py'
with open(r_path, 'r', encoding='utf-8') as f:
    rc = f.read()

target_anchor = '''        if lowered.startswith("/verify-inclusion") or lowered.startswith("verify-inclusion") or lowered.startswith("/bridge-transfer"):
            if hasattr(self.runtime, "cross_chain_zk_bridge"):
                parts = text.split()
                src = parts[1] if len(parts) > 1 else "LUCY-CORE-01"
                tgt = parts[2] if len(parts) > 2 else "LUCY-ROLLUP-02"
                rcp = parts[3] if len(parts) > 3 else "RCP-DEFAULT-001"
                import hashlib
                null = hashlib.sha256(f"NULL-{rcp}-{time.time()}".encode()).hexdigest()
                res = self.runtime.cross_chain_zk_bridge.verify_and_settle_transfer(
                    source_chain=src,
                    target_chain=tgt,
                    receipt_id=rcp,
                    payload={"action": "INTER_CHAIN_STATE_SYNC", "timestamp": time.time()},
                    merkle_proof=[],
                    nullifier=null,
                )
                if "error" in res:
                    return RouterResponse(res["error"])
                msg = f"Cross-Chain State Transfer #{res['receipt_id']} Settled: {src} -> {tgt} (Nullifier={res['nullifier_spent'][:16]}...)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Cross-Chain ZK Bridge not initialized.")'''

stage290_router = '''        if lowered.startswith("/verify-inclusion") or lowered.startswith("verify-inclusion") or lowered.startswith("/bridge-transfer"):
            if hasattr(self.runtime, "cross_chain_zk_bridge"):
                parts = text.split()
                src = parts[1] if len(parts) > 1 else "LUCY-CORE-01"
                tgt = parts[2] if len(parts) > 2 else "LUCY-ROLLUP-02"
                rcp = parts[3] if len(parts) > 3 else "RCP-DEFAULT-001"
                null = hashlib.sha256(f"NULL-{rcp}-{time.time()}".encode()).hexdigest()
                res = self.runtime.cross_chain_zk_bridge.verify_and_settle_transfer(
                    source_chain=src,
                    target_chain=tgt,
                    receipt_id=rcp,
                    payload={"action": "INTER_CHAIN_STATE_SYNC", "timestamp": time.time()},
                    merkle_proof=[],
                    nullifier=null,
                )
                if "error" in res:
                    return RouterResponse(res["error"])
                msg = f"Cross-Chain State Transfer #{res['receipt_id']} Settled: {src} -> {tgt} (Nullifier={res['nullifier_spent'][:16]}...)"
                return RouterResponse(msg, data=res)
            return RouterResponse("Cross-Chain ZK Bridge not initialized.")

        # --- Stage 290: The Sovereign Era 29 Master Seal & Omniscient Trans-Cosmic Singularity Genesis ---
        if lowered in ("/era29-seal", "era29-seal", "/era29-seal-report", "era29-seal-report"):
            if hasattr(self.runtime, "era29_master_seal"):
                report = self.runtime.era29_master_seal.format_grand_era_report()
                st = self.runtime.era29_master_seal.status()
                return RouterResponse(report, data=st)
            return RouterResponse("Era 29 Master Seal not initialized.")

        if lowered in ("/era29-status", "era29-status"):
            if hasattr(self.runtime, "era29_master_seal"):
                st = self.runtime.era29_master_seal.status()
                msg = (
                    f"Era 29 Master Seal: Status={st['verification_status']}, Total Stages={st['total_stages_sealed']}, "
                    f"Master Merkle Root={st['master_merkle_root'][:16]}..., Genesis Sig={st['genesis_signature'][:16]}..."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("Era 29 Master Seal not initialized.")

        if lowered in ("/era29-verify", "era29-verify"):
            if hasattr(self.runtime, "era29_master_seal"):
                integ = self.runtime.era29_master_seal.verify_era29_integrity()
                msg = (
                    f"Era 29 Integrity Audit: Verified={integ['verified']}, Stages={integ['stages_verified']}/10, "
                    f"Operator={integ['sovereign_operator']}."
                )
                return RouterResponse(msg, data=integ)
            return RouterResponse("Era 29 Master Seal not initialized.")

        if lowered in ("/era29-manifest", "era29-manifest"):
            if hasattr(self.runtime, "era29_master_seal"):
                manifest = [r.to_dict() for r in self.runtime.era29_master_seal.get_stage_manifest()]
                msg = f"Era 29 Stage Manifest: {len(manifest)} modules verified operational."
                return RouterResponse(msg, data={"manifest": manifest})
            return RouterResponse("Era 29 Master Seal not initialized.")'''

if target_anchor not in rc:
    target_anchor_crlf = target_anchor.replace('\n', '\r\n')
    assert target_anchor_crlf in rc, 'target_anchor not found in router.py'
    rc = rc.replace(target_anchor_crlf, stage290_router.replace('\n', '\r\n'), 1)
else:
    rc = rc.replace(target_anchor, stage290_router, 1)

with open(r_path, 'w', encoding='utf-8') as f:
    f.write(rc)

print("Updated router.py for Stage 290")
