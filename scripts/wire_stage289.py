import sys

# 1. Update lucy_runtime.py
rt_path = 'backend/lucy_core/lucy_runtime.py'
with open(rt_path, 'r', encoding='utf-8') as f:
    c = f.read()

t_imp = 'from backend.lucy_core.quantum_fisher_phase_estimator import QuantumFisherPhaseEstimatorFabric, STAGE as STAGE_288'
r_imp = t_imp + '\nfrom backend.lucy_core.sovereign_cross_chain_zk_bridge import SovereignCrossChainZKBridgeFabric, STAGE as STAGE_289'

t_inst = 'self.fisher_phase_estimator = QuantumFisherPhaseEstimatorFabric()'
r_inst = t_inst + '\n        # Stage 289: Sovereign Cross-Chain State Relayer & ZK Merkle Bridge (Era 29)\n        self.cross_chain_zk_bridge = SovereignCrossChainZKBridgeFabric()'

t_serv = '("fisher_phase_estimator", "core"),'
r_serv = t_serv + '\n            ("cross_chain_zk_bridge", "core"),'

assert t_imp in c, 't_imp not found in lucy_runtime.py'
assert t_inst in c, 't_inst not found in lucy_runtime.py'
assert t_serv in c, 't_serv not found in lucy_runtime.py'

c = c.replace(t_imp, r_imp, 1)
c = c.replace(t_inst, r_inst, 1)
c = c.replace(t_serv, r_serv, 1)

with open(rt_path, 'w', encoding='utf-8') as f:
    f.write(c)

print("Updated lucy_runtime.py for Stage 289")

# 2. Update router.py
r_path = 'backend/lucy_core/router.py'
with open(r_path, 'r', encoding='utf-8') as f:
    rc = f.read()

target_anchor = '''        if lowered.startswith("/noon-phase-eval") or lowered.startswith("noon-phase-eval") or lowered.startswith("/noon-fringes"):
            if hasattr(self.runtime, "fisher_phase_estimator"):
                parts = text.split()
                phi = float(parts[1]) if len(parts) > 1 else 0.5
                n = int(parts[2]) if len(parts) > 2 else 8
                res = self.runtime.fisher_phase_estimator.simulate_mach_zehnder_fringes(true_phase_rad=phi, n_photons=n, state_type="N00N")
                msg = (
                    f"N00N State Super-Resolution (N={res['photon_number_n']}): "
                    f"Transmission at phi={phi:.3f} rad is {res['transmission_at_true_phase']:.4f} (Finesse Multiplier={res['fringe_finesse_multiplier']:.1f}x)"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Fisher Phase Estimator not initialized.")'''

stage289_router = '''        if lowered.startswith("/noon-phase-eval") or lowered.startswith("noon-phase-eval") or lowered.startswith("/noon-fringes"):
            if hasattr(self.runtime, "fisher_phase_estimator"):
                parts = text.split()
                phi = float(parts[1]) if len(parts) > 1 else 0.5
                n = int(parts[2]) if len(parts) > 2 else 8
                res = self.runtime.fisher_phase_estimator.simulate_mach_zehnder_fringes(true_phase_rad=phi, n_photons=n, state_type="N00N")
                msg = (
                    f"N00N State Super-Resolution (N={res['photon_number_n']}): "
                    f"Transmission at phi={phi:.3f} rad is {res['transmission_at_true_phase']:.4f} (Finesse Multiplier={res['fringe_finesse_multiplier']:.1f}x)"
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Quantum Fisher Phase Estimator not initialized.")

        # --- Stage 289: Sovereign Cross-Chain State Relayer & ZK Merkle Bridge ---
        if lowered in ("/zk-bridge-status", "zk-bridge-status", "/cross-chain-status", "cross-chain-status"):
            if hasattr(self.runtime, "cross_chain_zk_bridge"):
                tbl = self.runtime.cross_chain_zk_bridge.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.cross_chain_zk_bridge.status())
            return RouterResponse("Cross-Chain ZK Bridge not initialized.")

        if lowered.startswith("/relay-header") or lowered.startswith("relay-header"):
            if hasattr(self.runtime, "cross_chain_zk_bridge"):
                parts = text.split()
                if len(parts) < 5:
                    return RouterResponse("Usage: /relay-header <chain_id> <height> <prev_hash> <state_root>")
                cid = parts[1]
                h = int(parts[2])
                p_hash = parts[3]
                s_root = parts[4]
                res = self.runtime.cross_chain_zk_bridge.relay_header(chain_id=cid, height=h, prev_hash=p_hash, state_root=s_root)
                if "error" in res:
                    return RouterResponse(res["error"])
                msg = f"Header Relayed for {res['chain_id']} at height {res['height']}: Block Hash={res['block_hash'][:16]}..."
                return RouterResponse(msg, data=res)
            return RouterResponse("Cross-Chain ZK Bridge not initialized.")

        if lowered.startswith("/verify-inclusion") or lowered.startswith("verify-inclusion") or lowered.startswith("/bridge-transfer"):
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

if target_anchor not in rc:
    target_anchor_crlf = target_anchor.replace('\n', '\r\n')
    assert target_anchor_crlf in rc, 'target_anchor not found in router.py'
    rc = rc.replace(target_anchor_crlf, stage289_router.replace('\n', '\r\n'), 1)
else:
    rc = rc.replace(target_anchor, stage289_router, 1)

with open(r_path, 'w', encoding='utf-8') as f:
    f.write(rc)

print("Updated router.py for Stage 289")
