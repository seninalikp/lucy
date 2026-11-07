"""
scripts/wire_stage262.py
Wires Stage 262 AdSCFTEntanglementWedgeFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.yang_mills_gauge_holonomy import YangMillsGaugeHolonomyFabric, STAGE as STAGE_261\n'
    replacement_import = target_import + 'from backend.lucy_core.ads_cft_entanglement_wedge import AdSCFTEntanglementWedgeFabric, STAGE as STAGE_262\n'
    if 'ads_cft_entanglement_wedge' not in text:
        assert target_import in text, 'Target import for Stage 261 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 261: Non-Abelian SU(N) Yang-Mills Gauge Connection (Era 27)\n        self.yang_mills_engine = YangMillsGaugeHolonomyFabric()\n'
    replacement_init = target_init + '        # Stage 262: Holographic AdS/CFT Ryu-Takayanagi Wedge (Era 27)\n        self.entanglement_wedge_fabric = AdSCFTEntanglementWedgeFabric()\n'
    if 'self.entanglement_wedge_fabric' not in text:
        assert target_init in text, 'Target init for Stage 261 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("yang_mills_engine", "core"),\n'
    replacement_service = target_service + '            ("entanglement_wedge_fabric", "core"),\n'
    if '("entanglement_wedge_fabric", "core")' not in text:
        assert target_service in text, 'Target service for Stage 261 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 262 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /gauge-audit <ax1> <ax2> <ax3> <ay1> <ay2> <ay3>")\n'
    assert target in text, 'Target end of Stage 261 block not found'

    insertion = """
        # Stage 262: Holographic AdS/CFT Conformal Boundary-to-Bulk Dictionary & Ryu-Takayanagi Entanglement Wedge
        if lowered in {"/ads-cft-status", "ads-cft-status", "/holographic-status", "holographic-status"}:
            if hasattr(self.runtime, "entanglement_wedge_fabric"):
                tbl = self.runtime.entanglement_wedge_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.entanglement_wedge_fabric.get_metrics())
            return RouterResponse("Entanglement wedge fabric not available.")

        if lowered.startswith("/rt-entropy ") or lowered.startswith("rt-entropy "):
            if hasattr(self.runtime, "entanglement_wedge_fabric"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    l_val = float(parts[1])
                    eps = float(parts[2]) if len(parts) >= 3 else 1e-3
                    res = self.runtime.entanglement_wedge_fabric.compute_ryu_takayanagi_entropy(l_val, eps)
                    msg = (
                        f"Ryu-Takayanagi Entanglement Entropy (l={l_val}, c={res['central_charge']}): "
                        f"S_A = {res['entanglement_entropy']:.4f} (Geodesic length: {res['geodesic_length']:.4f}, z_max={res['max_bulk_penetration_z']})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /rt-entropy <subsystem_length> [uv_cutoff]")

        if lowered.startswith("/entanglement-wedge-check ") or lowered.startswith("entanglement-wedge-check "):
            if hasattr(self.runtime, "entanglement_wedge_fabric"):
                parts = raw_text.strip().split()
                if len(parts) >= 5:
                    x, z = float(parts[1]), float(parts[2])
                    x_start, x_end = float(parts[3]), float(parts[4])
                    inside = self.runtime.entanglement_wedge_fabric.is_in_entanglement_wedge(x, z, x_start, x_end)
                    msg = f"Bulk point ({x}, {z}) inside Entanglement Wedge [{x_start}, {x_end}]: {inside}."
                    return RouterResponse(msg, data={"x": x, "z": z, "inside_wedge": inside})
            return RouterResponse("Usage: /entanglement-wedge-check <x> <z> <x_start> <x_end>")

        if lowered.startswith("/holographic-mutual-info ") or lowered.startswith("holographic-mutual-info "):
            if hasattr(self.runtime, "entanglement_wedge_fabric"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    la, lb, d = float(parts[1]), float(parts[2]), float(parts[3])
                    res = self.runtime.entanglement_wedge_fabric.compute_holographic_mutual_information(la, lb, d)
                    msg = (
                        f"Holographic Mutual Information I(A:B) = {res['mutual_information']:.4f} "
                        f"(Phase: {res['holographic_phase']}, S_A={res['entropy_a']:.2f}, S_B={res['entropy_b']:.2f})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /holographic-mutual-info <length_a> <length_b> <separation_d>")
"""
    if 'ads-cft-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 262 into router.py')
    else:
        print('Stage 262 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
