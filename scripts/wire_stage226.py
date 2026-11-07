"""
scripts/wire_stage226.py
Wires Stage 226 TopologicalDataAnalysisFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.recursive_snark_aggregator import RecursiveSNARKAggregatorFabric, STAGE as STAGE_225\n'
    replacement_import = target_import + 'from backend.lucy_core.topological_data_analysis import TopologicalDataAnalysisFabric, STAGE as STAGE_226\n'
    if 'topological_data_analysis' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 225: Autonomous Zero-Knowledge Proof Aggregator & Recursive SNARK Verifier (Era 23)\n        self.recursive_snark_aggregator = RecursiveSNARKAggregatorFabric()\n'
    replacement_init = target_init + '        # Stage 226: Self-Supervised Topological Data Analysis & Persistent Homology Engine (Era 23)\n        self.topological_data_analysis = TopologicalDataAnalysisFabric()\n'
    if 'self.topological_data_analysis' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("recursive_snark_aggregator", "core"),\n'
    replacement_service = target_service + '            ("topological_data_analysis", "core"),\n'
    if '("topological_data_analysis", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 226 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    end_marker = '                return RouterResponse(f"Synthesized Recursive SNARK {agg.proof_id} folding 2 proofs: {\'VALID\' if ok else \'INVALID\'} (Depth: {agg.recursion_depth})", data=agg.to_dict())\n            return RouterResponse("Recursive SNARK aggregator not available.")\n'
    assert end_marker in text, 'End marker not found'

    insertion = """
        # Stage 226: Self-Supervised Topological Data Analysis & Persistent Homology Engine
        if lowered in {"/tda-status", "tda-status"}:
            if hasattr(self.runtime, "topological_data_analysis"):
                tbl = self.runtime.topological_data_analysis.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.topological_data_analysis.status())
            return RouterResponse("Topological data analysis fabric not available.")

        if lowered in {"/tda-circle-sample", "tda-circle-sample"}:
            if hasattr(self.runtime, "topological_data_analysis"):
                self.runtime.topological_data_analysis.generate_circle_sample("demo_circle", num_points=16, radius=1.0)
                intervals = self.runtime.topological_data_analysis.compute_vietoris_rips_homology("demo_circle")
                h1_count = sum(1 for it in intervals if it.dimension == 1)
                msg = f"Generated circle point cloud 'demo_circle'. Discovered {len(intervals)} persistence intervals ({h1_count} topological 1-cycles / H1 loops)."
                return RouterResponse(msg, data={"intervals": [it.to_dict() for it in intervals]})
            return RouterResponse("Topological data analysis fabric not available.")

        if lowered.startswith("/tda-betti ") or lowered.startswith("tda-betti "):
            if hasattr(self.runtime, "topological_data_analysis"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    cid, eps_str = parts[1], parts[2]
                    try:
                        eps = float(eps_str)
                        b = self.runtime.topological_data_analysis.compute_betti_numbers(cid, epsilon=eps)
                        msg = f"Betti numbers for '{cid}' at epsilon={eps:.2f}: beta_0={b['beta_0']} (components), beta_1={b['beta_1']} (1-holes)"
                        return RouterResponse(msg, data=b)
                    except Exception as e:
                        return RouterResponse(f"TDA Betti computation failed: {e}")
            return RouterResponse("Usage: /tda-betti <cloud_id> <epsilon>")
"""
    if 'tda-status' not in text:
        idx = text.find(end_marker) + len(end_marker)
        text = text[:idx] + insertion + text[idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 226 into router.py')
    else:
        print('Stage 226 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
