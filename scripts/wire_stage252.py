"""
scripts/wire_stage252.py
Wires Stage 252 JarzynskiEntropyHarvesterFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.calabi_yau_metric_engine import CalabiYauMetricEngineFabric, STAGE as STAGE_251\n'
    replacement_import = target_import + 'from backend.lucy_core.jarzynski_entropy_harvester import JarzynskiEntropyHarvesterFabric, STAGE as STAGE_252\n'
    if 'jarzynski_entropy_harvester' not in text:
        assert target_import in text, 'Target import for Stage 251 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 251: Holomorphic Modular Form & Calabi-Yau Metric Engine (Era 26)\n        self.calabi_yau_metric_engine = CalabiYauMetricEngineFabric()\n'
    replacement_init = target_init + '        # Stage 252: Non-Equilibrium Fluctuation-Dissipation & Crooks Harvester (Era 26)\n        self.jarzynski_entropy_harvester = JarzynskiEntropyHarvesterFabric()\n'
    if 'self.jarzynski_entropy_harvester' not in text:
        assert target_init in text, 'Target init for Stage 251 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("calabi_yau_metric_engine", "core"),\n'
    replacement_service = target_service + '            ("jarzynski_entropy_harvester", "core"),\n'
    if '("jarzynski_entropy_harvester", "core")' not in text:
        assert target_service in text, 'Target service for Stage 251 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 252 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /calabi-yau-ricci <z1_re> <z1_im> [z2_re z2_im ...]")\n'
    assert target in text, 'Target end of Stage 251 block not found'

    insertion = """
        # Stage 252: Non-Equilibrium Fluctuation-Dissipation & Crooks Jarzynski Entropy Harvester
        if lowered in {"/entropy-harvester-status", "entropy-harvester-status", "/jarzynski-status", "jarzynski-status"}:
            if hasattr(self.runtime, "jarzynski_entropy_harvester"):
                tbl = self.runtime.jarzynski_entropy_harvester.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.jarzynski_entropy_harvester.get_metrics())
            return RouterResponse("Jarzynski entropy harvester not available.")

        if lowered.startswith("/jarzynski-free-energy ") or lowered.startswith("jarzynski-free-energy "):
            if hasattr(self.runtime, "jarzynski_entropy_harvester"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    samples = [float(p) for p in parts[1:]]
                    res = self.runtime.jarzynski_entropy_harvester.compute_jarzynski_free_energy(samples)
                    msg = (
                        f"Jarzynski Free Energy (N={res['ensemble_size']}): "
                        f"Delta F = {res['delta_f_kbt']:.4f} kBT ({res['delta_f_joules']:.3e} J), "
                        f"Dissipation = {res['dissipated_work_kbt']:.4f} kBT ({res['dissipated_work_joules']:.3e} J)."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /jarzynski-free-energy <w1_kbt> [w2_kbt ...]")

        if lowered.startswith("/entropy-harvest ") or lowered.startswith("entropy-harvest "):
            if hasattr(self.runtime, "jarzynski_entropy_harvester"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    w = float(parts[1])
                    df = float(parts[2])
                    bits = float(parts[3]) if len(parts) >= 4 else 1.0
                    res = self.runtime.jarzynski_entropy_harvester.harvest_stochastic_fluctuation(w, df, bits)
                    msg = (
                        f"Harvested {res['harvested_joules']:.3e} J from fluctuation (w={w} kBT, df={df} kBT). "
                        f"Total Harvested: {res['total_joules_harvested']:.3e} J."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /entropy-harvest <work_kbt> <delta_f_kbt> [bits]")
"""
    if 'entropy-harvester-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 252 into router.py')
    else:
        print('Stage 252 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
