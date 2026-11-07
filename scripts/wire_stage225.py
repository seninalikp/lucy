"""
scripts/wire_stage225.py
Wires Stage 225 RecursiveSNARKAggregatorFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.multiverse_state_forker import MultiverseStateForkerFabric, STAGE as STAGE_224\n'
    replacement_import = target_import + 'from backend.lucy_core.recursive_snark_aggregator import RecursiveSNARKAggregatorFabric, STAGE as STAGE_225\n'
    if 'recursive_snark_aggregator' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 224: Universal Multi-Verse Counterfactual State Forker & Timeline Brancher (Era 23)\n        self.multiverse_forker = MultiverseStateForkerFabric()\n'
    replacement_init = target_init + '        # Stage 225: Autonomous Zero-Knowledge Proof Aggregator & Recursive SNARK Verifier (Era 23)\n        self.recursive_snark_aggregator = RecursiveSNARKAggregatorFabric()\n'
    if 'self.recursive_snark_aggregator' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("multiverse_forker", "core"),\n'
    replacement_service = target_service + '            ("recursive_snark_aggregator", "core"),\n'
    if '("recursive_snark_aggregator", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 225 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    end_marker = '            return RouterResponse("Usage: /multiverse-divergence <branch_a> <branch_b>")\n'
    assert end_marker in text, 'End marker not found'

    insertion = """
        # Stage 225: Autonomous Zero-Knowledge Proof Aggregator & Recursive SNARK Verifier
        if lowered in {"/snark-status", "snark-status"}:
            if hasattr(self.runtime, "recursive_snark_aggregator"):
                tbl = self.runtime.recursive_snark_aggregator.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.recursive_snark_aggregator.status())
            return RouterResponse("Recursive SNARK aggregator not available.")

        if lowered in {"/snark-prove-sample", "snark-prove-sample"}:
            if hasattr(self.runtime, "recursive_snark_aggregator"):
                p = self.runtime.recursive_snark_aggregator.prove_circuit("multiplier", witness=[1, 7, 6, 42], public_inputs=[42])
                ok = self.runtime.recursive_snark_aggregator.verify_proof(p)
                return RouterResponse(f"Generated and verified proof {p.proof_id} for circuit '{p.circuit_name}': {'VALID' if ok else 'INVALID'}", data=p.to_dict())
            return RouterResponse("Recursive SNARK aggregator not available.")

        if lowered in {"/snark-aggregate-sample", "snark-aggregate-sample"}:
            if hasattr(self.runtime, "recursive_snark_aggregator"):
                p1 = self.runtime.recursive_snark_aggregator.prove_circuit("multiplier", witness=[1, 3, 5, 15], public_inputs=[15])
                p2 = self.runtime.recursive_snark_aggregator.prove_circuit("multiplier", witness=[1, 4, 10, 40], public_inputs=[40])
                agg = self.runtime.recursive_snark_aggregator.aggregate_proofs([p1, p2])
                ok = self.runtime.recursive_snark_aggregator.verify_proof(agg)
                return RouterResponse(f"Synthesized Recursive SNARK {agg.proof_id} folding 2 proofs: {'VALID' if ok else 'INVALID'} (Depth: {agg.recursion_depth})", data=agg.to_dict())
            return RouterResponse("Recursive SNARK aggregator not available.")
"""
    if 'snark-status' not in text:
        idx = text.find(end_marker) + len(end_marker)
        text = text[:idx] + insertion + text[idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 225 into router.py')
    else:
        print('Stage 225 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
