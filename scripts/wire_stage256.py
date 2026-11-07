"""
scripts/wire_stage256.py
Wires Stage 256 RenormalizationGroupFlowFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.turing_morphogenetic_synthesizer import TuringMorphogeneticSynthesizerFabric, STAGE as STAGE_255\n'
    replacement_import = target_import + 'from backend.lucy_core.renormalization_group_flow import RenormalizationGroupFlowFabric, STAGE as STAGE_256\n'
    if 'renormalization_group_flow' not in text:
        assert target_import in text, 'Target import for Stage 255 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 255: Bio-Mimetic Turing Reaction-Diffusion Synthesizer (Era 26)\n        self.turing_synthesizer = TuringMorphogeneticSynthesizerFabric()\n'
    replacement_init = target_init + '        # Stage 256: Deep Renormalization Group Flow & Wilsonian EFT (Era 26)\n        self.rg_flow_fabric = RenormalizationGroupFlowFabric()\n'
    if 'self.rg_flow_fabric' not in text:
        assert target_init in text, 'Target init for Stage 255 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("turing_synthesizer", "core"),\n'
    replacement_service = target_service + '            ("rg_flow_fabric", "core"),\n'
    if '("rg_flow_fabric", "core")' not in text:
        assert target_service in text, 'Target service for Stage 255 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 256 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /turing-instability <fu> <fv> <gu> <gv> <du> <dv>")\n'
    assert target in text, 'Target end of Stage 255 block not found'

    insertion = """
        # Stage 256: Deep Renormalization Group Flow & Wilsonian Effective Field Theory Coarse-Grainer
        if lowered in {"/rg-flow-status", "rg-flow-status", "/renormalization-status", "renormalization-status"}:
            if hasattr(self.runtime, "rg_flow_fabric"):
                tbl = self.runtime.rg_flow_fabric.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.rg_flow_fabric.get_metrics())
            return RouterResponse("RG flow fabric not available.")

        if lowered.startswith("/rg-integrate ") or lowered.startswith("rg-integrate "):
            if hasattr(self.runtime, "rg_flow_fabric"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    g0 = float(parts[1])
                    eps = float(parts[2]) if len(parts) >= 3 else 1.0
                    steps = int(parts[3]) if len(parts) >= 4 else 30
                    res = self.runtime.rg_flow_fabric.integrate_rg_flow(g0, eps, steps)
                    msg = (
                        f"RG Trajectory (steps={steps}, eps={eps}): g_init={res['initial_coupling']:.4f} -> "
                        f"g_final={res['final_coupling']:.4f} (Wilson-Fisher target: {res['wilson_fisher_target']:.4f})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /rg-integrate <g_initial> [epsilon] [steps]")

        if lowered.startswith("/rg-spin-block ") or lowered.startswith("rg-spin-block "):
            if hasattr(self.runtime, "rg_flow_fabric"):
                parts = raw_text.strip().split()
                w = int(parts[1]) if len(parts) >= 2 else 16
                h = int(parts[2]) if len(parts) >= 3 else 16
                p_up = float(parts[3]) if len(parts) >= 4 else 0.7
                lat = self.runtime.rg_flow_fabric.generate_random_ising_lattice(w, h, p_up=p_up)
                coarse = self.runtime.rg_flow_fabric.kadanoff_spin_block_2d(lat)
                stats_orig = self.runtime.rg_flow_fabric.calculate_magnetization_and_correlation(lat)
                stats_coarse = self.runtime.rg_flow_fabric.calculate_magnetization_and_correlation(coarse)
                msg = (
                    f"Kadanoff Block ({w}x{h} -> {len(coarse[0])}x{len(coarse)}): "
                    f"mag: {stats_orig['magnetization']:.2f} -> {stats_coarse['magnetization']:.2f}, "
                    f"nn_corr: {stats_orig['nn_correlation']:.2f} -> {stats_coarse['nn_correlation']:.2f}."
                )
                return RouterResponse(msg, data={"orig": stats_orig, "coarse": stats_coarse})
            return RouterResponse("Usage: /rg-spin-block [width] [height] [p_up]")
"""
    if 'rg-flow-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 256 into router.py')
    else:
        print('Stage 256 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
