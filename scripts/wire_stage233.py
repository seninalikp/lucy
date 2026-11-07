"""
scripts/wire_stage233.py
Wires Stage 233 HyperbolicGraphEmbedderFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.lattice_pqc_vault import LatticePQCVaultFabric, STAGE as STAGE_232\n'
    replacement_import = target_import + 'from backend.lucy_core.hyperbolic_graph_embedder import HyperbolicGraphEmbedderFabric, STAGE as STAGE_233\n'
    if 'hyperbolic_graph_embedder' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 232: Quantum-Resilient Lattice Post-Quantum Cryptography Vault (Era 24)\n        self.lattice_pqc_vault = LatticePQCVaultFabric()\n'
    replacement_init = target_init + '        # Stage 233: Autonomous Non-Euclidean Hyperbolic Knowledge Graph Embedding (Era 24)\n        self.hyperbolic_graph_embedder = HyperbolicGraphEmbedderFabric()\n'
    if 'self.hyperbolic_graph_embedder' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("lattice_pqc_vault", "core"),\n'
    replacement_service = target_service + '            ("hyperbolic_graph_embedder", "core"),\n'
    if '("hyperbolic_graph_embedder", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 233 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    end_marker = '            return RouterResponse("Usage: /lattice-vault-read <record_id>")\n'
    assert end_marker in text, 'End marker not found'

    insertion = """
        # Stage 233: Autonomous Non-Euclidean Hyperbolic Knowledge Graph Embedding
        if lowered in {"/hyperbolic-status", "hyperbolic-status"}:
            if hasattr(self.runtime, "hyperbolic_graph_embedder"):
                tbl = self.runtime.hyperbolic_graph_embedder.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.hyperbolic_graph_embedder.status())
            return RouterResponse("Hyperbolic graph embedder not available.")

        if lowered.startswith("/hyperbolic-dist ") or lowered.startswith("hyperbolic-dist "):
            if hasattr(self.runtime, "hyperbolic_graph_embedder"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    na, nb = parts[1], parts[2]
                    try:
                        d = self.runtime.hyperbolic_graph_embedder.compute_distance(na, nb)
                        msg = f"Poincare geodesic distance between '{na}' and '{nb}': {d:.4f}."
                        return RouterResponse(msg, data={"node_a": na, "node_b": nb, "geodesic_distance": d})
                    except Exception as e:
                        return RouterResponse(f"Hyperbolic distance computation failed: {e}")
            return RouterResponse("Usage: /hyperbolic-dist <node_a> <node_b>")

        if lowered.startswith("/hyperbolic-nn ") or lowered.startswith("hyperbolic-nn "):
            if hasattr(self.runtime, "hyperbolic_graph_embedder"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nid = parts[1]
                    try:
                        nn = self.runtime.hyperbolic_graph_embedder.find_nearest_neighbors(nid, top_k=3)
                        msg = f"Nearest hyperbolic neighbors for '{nid}': {nn}"
                        return RouterResponse(msg, data={"query_node": nid, "neighbors": nn})
                    except Exception as e:
                        return RouterResponse(f"Hyperbolic nearest neighbor query failed: {e}")
            return RouterResponse("Usage: /hyperbolic-nn <node_id>")

        if lowered in {"/hyperbolic-optimize", "hyperbolic-optimize"}:
            if hasattr(self.runtime, "hyperbolic_graph_embedder"):
                loss = self.runtime.hyperbolic_graph_embedder.optimize_embedding_step(lr=0.05)
                msg = f"Completed Riemannian gradient descent step. Mean hyperbolic loss: {loss:.4f}."
                return RouterResponse(msg, data={"loss": loss})
            return RouterResponse("Hyperbolic graph embedder not available.")
"""
    if 'hyperbolic-status' not in text:
        idx = text.find(end_marker) + len(end_marker)
        text = text[:idx] + insertion + text[idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 233 into router.py')
    else:
        print('Stage 233 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
