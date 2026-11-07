"""
Wiring script for Stage 279: Sovereign Decentralized Autonomous Zero-Knowledge Rollup & Verifiable State Compressor
Author: Senin (Senin Ali K P)
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Import
    target_imp = "from backend.lucy_core.casimir_polder_vacuum_engine import CasimirPolderVacuumEngineFabric, STAGE as STAGE_278"
    repl_imp = target_imp + "\nfrom backend.lucy_core.sovereign_zk_rollup_compressor import SovereignZKRollupCompressorFabric, STAGE as STAGE_279"
    if target_imp in text and repl_imp not in text:
        text = text.replace(target_imp, repl_imp, 1)

    # Init
    target_init = "self.casimir_vacuum_engine = CasimirPolderVacuumEngineFabric()"
    repl_init = target_init + "\n        # Stage 279: Sovereign ZK-Rollup & Verifiable State Compressor (Era 28)\n        self.zk_rollup_compressor = SovereignZKRollupCompressorFabric()"
    if target_init in text and repl_init not in text:
        text = text.replace(target_init, repl_init, 1)

    # Supervisor services
    target_svc = '("casimir_vacuum_engine", "core"),'
    repl_svc = target_svc + '\n            ("zk_rollup_compressor", "core"),'
    if target_svc in text and repl_svc not in text:
        text = text.replace(target_svc, repl_svc, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully wired Stage 279 into lucy_runtime.py")


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = 'return RouterResponse("Usage: /casimir-levitate <eps1> <eps_medium> <eps2> [separation_nm]")'
    insertion = """

        # --- Stage 279: Sovereign Decentralized Autonomous Zero-Knowledge Rollup & Verifiable State Compressor ---
        if lowered in ("/rollup-status", "rollup-status"):
            if hasattr(self.runtime, "zk_rollup_compressor"):
                st = self.runtime.zk_rollup_compressor.get_status()
                msg = (
                    f"ZK Rollup Compressor: Accounts={st['accounts_count']}, Supply={st['total_circulating_balance']:.2f}, "
                    f"State Root={st['current_state_root'][:16]}..., Batches Settled={st['total_batches_settled']}."
                )
                return RouterResponse(msg, data=st)
            return RouterResponse("ZK Rollup Compressor not initialized.")

        if lowered.startswith("/rollup-compress ") or lowered.startswith("rollup-compress "):
            if hasattr(self.runtime, "zk_rollup_compressor"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    f_id, t_id, amt = int(parts[1]), int(parts[2]), float(parts[3])
                    txs = [{"from": f_id, "to": t_id, "amount": amt, "nonce": 0}]
                    res = self.runtime.zk_rollup_compressor.compress_transaction_batch(txs)
                    msg = (
                        f"Rollup Compression: {res['uncompressed_bytes']}B -> {res['compressed_bytes']}B "
                        f"({res['compression_ratio']:.2f}x reduction), Hex: {res['compressed_payload_hex']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /rollup-compress <from_id> <to_id> <amount>")

        if lowered.startswith("/rollup-settle ") or lowered.startswith("rollup-settle "):
            if hasattr(self.runtime, "zk_rollup_compressor"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    f_id, t_id, amt = int(parts[1]), int(parts[2]), float(parts[3])
                    txs = [{"from": f_id, "to": t_id, "amount": amt, "nonce": 0}]
                    res = self.runtime.zk_rollup_compressor.process_and_verify_rollup_batch(txs)
                    msg = (
                        f"Rollup Batch #{res['batch_id']} Settled: Valid={res['valid_transactions']}, "
                        f"Post-Root={res['post_state_root'][:16]}..., Proof={res['succinct_validity_proof'][:16]}... ({res['status']})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /rollup-settle <from_id> <to_id> <amount>")

        if lowered in ("/rollup-root", "rollup-root"):
            if hasattr(self.runtime, "zk_rollup_compressor"):
                st = self.runtime.zk_rollup_compressor.get_status()
                msg = f"Current Sovereign Rollup State Root: {st['current_state_root']}."
                return RouterResponse(msg, data={"state_root": st['current_state_root']})
            return RouterResponse("ZK Rollup Compressor not initialized.")"""

    if "rollup-status" not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Successfully wired Stage 279 into router.py")
    else:
        print("Stage 279 already wired in router.py")


if __name__ == '__main__':
    wire_runtime()
    wire_router()
