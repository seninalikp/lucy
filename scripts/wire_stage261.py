"""
scripts/wire_stage261.py
Wires Stage 261 YangMillsGaugeHolonomyFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.era26_master_seal import Era26MasterSealFabric, STAGE as STAGE_260\n'
    replacement_import = target_import + 'from backend.lucy_core.yang_mills_gauge_holonomy import YangMillsGaugeHolonomyFabric, STAGE as STAGE_261\n'
    if 'yang_mills_gauge_holonomy' not in text:
        assert target_import in text, 'Target import for Stage 260 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 260: The Sovereign Era 26 Master Seal & Singularity Genesis (Era 26)\n        self.era26_master_seal = Era26MasterSealFabric()\n'
    replacement_init = target_init + '        # Stage 261: Non-Abelian SU(N) Yang-Mills Gauge Connection (Era 27)\n        self.yang_mills_engine = YangMillsGaugeHolonomyFabric()\n'
    if 'self.yang_mills_engine' not in text:
        assert target_init in text, 'Target init for Stage 260 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("era26_master_seal", "core"),\n'
    replacement_service = target_service + '            ("yang_mills_engine", "core"),\n'
    if '("yang_mills_engine", "core")' not in text:
        assert target_service in text, 'Target service for Stage 260 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 261 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Era 26 Master Seal not available.")\n'
    assert target in text, 'Target end of Stage 260 block not found'

    insertion = """
        # Stage 261: Non-Abelian SU(N) Yang-Mills Gauge Connection & Wilson Loop Holonomy Engine
        if lowered in {"/yang-mills-status", "yang-mills-status", "/gauge-holonomy-status", "gauge-holonomy-status"}:
            if hasattr(self.runtime, "yang_mills_engine"):
                tbl = self.runtime.yang_mills_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.yang_mills_engine.get_metrics())
            return RouterResponse("Yang-Mills engine not available.")

        if lowered.startswith("/wilson-loop ") or lowered.startswith("wilson-loop "):
            if hasattr(self.runtime, "yang_mills_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 7:
                    ax = [float(parts[1]), float(parts[2]), float(parts[3])]
                    ay = [float(parts[4]), float(parts[5]), float(parts[6])]
                    dx = float(parts[7]) if len(parts) >= 8 else 0.1
                    dy = float(parts[8]) if len(parts) >= 9 else 0.1
                    res = self.runtime.yang_mills_engine.compute_wilson_loop(ax, ay, dx, dy)
                    msg = (
                        f"Wilson Loop Holonomy ({res['gauge_group']}): W(C) = {res['wilson_loop_value']:.6f} "
                        f"(Trace: {res['trace_real']:.4f} + {res['trace_imag']:.4f}i, Area={res['plaquette_area']})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /wilson-loop <ax1> <ax2> <ax3> <ay1> <ay2> <ay3> [dx] [dy]")

        if lowered.startswith("/gauge-audit ") or lowered.startswith("gauge-audit "):
            if hasattr(self.runtime, "yang_mills_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 7:
                    ax = [float(parts[1]), float(parts[2]), float(parts[3])]
                    ay = [float(parts[4]), float(parts[5]), float(parts[6])]
                    res = self.runtime.yang_mills_engine.verify_gauge_invariance(ax, ay)
                    msg = (
                        f"Local Gauge Invariance Audit: invariant={res['is_gauge_invariant']}, "
                        f"Tr(orig)={res['trace_original']:.6f}, Tr(gauge_rot)={res['trace_transformed']:.6f}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /gauge-audit <ax1> <ax2> <ax3> <ay1> <ay2> <ay3>")
"""
    if 'yang-mills-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 261 into router.py')
    else:
        print('Stage 261 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
