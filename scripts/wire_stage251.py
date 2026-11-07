"""
scripts/wire_stage251.py
Wires Stage 251 CalabiYauMetricEngineFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.era25_master_seal import Era25MasterSealFabric, STAGE as STAGE_250\n'
    replacement_import = target_import + 'from backend.lucy_core.calabi_yau_metric_engine import CalabiYauMetricEngineFabric, STAGE as STAGE_251\n'
    if 'calabi_yau_metric_engine' not in text:
        assert target_import in text, 'Target import for Stage 250 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 250: The Sovereign Era 25 Master Seal & Cosmic Core Genesis (Era 25)\n        self.era25_master_seal = Era25MasterSealFabric()\n'
    replacement_init = target_init + '        # Stage 251: Holomorphic Modular Form & Calabi-Yau Metric Engine (Era 26)\n        self.calabi_yau_metric_engine = CalabiYauMetricEngineFabric()\n'
    if 'self.calabi_yau_metric_engine' not in text:
        assert target_init in text, 'Target init for Stage 250 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("era25_master_seal", "core"),\n'
    replacement_service = target_service + '            ("calabi_yau_metric_engine", "core"),\n'
    if '("calabi_yau_metric_engine", "core")' not in text:
        assert target_service in text, 'Target service for Stage 250 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 251 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Era 25 Master Seal not available.")\n'
    assert target in text, 'Target end of Stage 250 block not found'

    insertion = """
        # Stage 251: Holomorphic Modular Form & Calabi-Yau Compactification Metric Engine
        if lowered in {"/calabi-yau-status", "calabi-yau-status"}:
            if hasattr(self.runtime, "calabi_yau_metric_engine"):
                tbl = self.runtime.calabi_yau_metric_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.calabi_yau_metric_engine.get_metrics())
            return RouterResponse("Calabi-Yau metric engine not available.")

        if lowered.startswith("/modular-j ") or lowered.startswith("modular-j "):
            if hasattr(self.runtime, "calabi_yau_metric_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    re_val = float(parts[1])
                    im_val = float(parts[2])
                    tau = complex(re_val, im_val)
                    j_val = self.runtime.calabi_yau_metric_engine.compute_klein_j_invariant(tau)
                    msg = f"Klein j-Invariant j({tau}) = {j_val.real:.4f} + {j_val.imag:.4f}i"
                    return RouterResponse(msg, data={"tau": str(tau), "j_real": j_val.real, "j_imag": j_val.imag})
            return RouterResponse("Usage: /modular-j <re_tau> <im_tau>")

        if lowered.startswith("/modular-eisenstein ") or lowered.startswith("modular-eisenstein "):
            if hasattr(self.runtime, "calabi_yau_metric_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    weight = int(parts[1])
                    re_val = float(parts[2])
                    im_val = float(parts[3])
                    tau = complex(re_val, im_val)
                    if weight == 4:
                        res = self.runtime.calabi_yau_metric_engine.compute_eisenstein_e4(tau)
                    elif weight == 6:
                        res = self.runtime.calabi_yau_metric_engine.compute_eisenstein_e6(tau)
                    else:
                        return RouterResponse("Only weights 4 and 6 are supported for Eisenstein series.")
                    msg = f"Eisenstein Series E_{weight}({tau}) = {res.real:.6f} + {res.imag:.6f}i"
                    return RouterResponse(msg, data={"weight": weight, "tau": str(tau), "res_real": res.real, "res_imag": res.imag})
            return RouterResponse("Usage: /modular-eisenstein <4|6> <re_tau> <im_tau>")

        if lowered.startswith("/calabi-yau-ricci ") or lowered.startswith("calabi-yau-ricci "):
            if hasattr(self.runtime, "calabi_yau_metric_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    coords = []
                    for i in range(1, len(parts), 2):
                        if i + 1 < len(parts):
                            coords.append(complex(float(parts[i]), float(parts[i+1])))
                    res = self.runtime.calabi_yau_metric_engine.verify_ricci_flatness(coords)
                    msg = (
                        f"Calabi-Yau Ricci Flatness Audit (dim={res['dim']}): "
                        f"det={res['det_metric']:.4f}, residual={res['ricci_scalar_residual']:.6f}. Status: {res['status']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /calabi-yau-ricci <z1_re> <z1_im> [z2_re z2_im ...]")
"""
    if 'calabi-yau-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 251 into router.py')
    else:
        print('Stage 251 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
