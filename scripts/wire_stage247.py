"""
scripts/wire_stage247.py
Wires Stage 247 AntiFragileStressInverterFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.adiabatic_reversible_governor import AdiabaticReversibleGovernorFabric, STAGE as STAGE_246\n'
    replacement_import = target_import + 'from backend.lucy_core.antifragile_stress_inverter import AntiFragileStressInverterFabric, STAGE as STAGE_247\n'
    if 'antifragile_stress_inverter' not in text:
        assert target_import in text, 'Target import for Stage 246 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 246: Thermodynamically Reversible Landauer-Zero Computation & Adiabatic Governor (Era 25)\n        self.adiabatic_reversible_governor = AdiabaticReversibleGovernorFabric()\n'
    replacement_init = target_init + '        # Stage 247: Sovereign Anti-Fragile Black-Swan Catastrophe Immunity & Stress Inverter (Era 25)\n        self.antifragile_stress_inverter = AntiFragileStressInverterFabric()\n'
    if 'self.antifragile_stress_inverter' not in text:
        assert target_init in text, 'Target init for Stage 246 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("adiabatic_reversible_governor", "core"),\n'
    replacement_service = target_service + '            ("antifragile_stress_inverter", "core"),\n'
    if '("antifragile_stress_inverter", "core")' not in text:
        assert target_service in text, 'Target service for Stage 246 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 247 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /adiabatic-dissipation [ramp_ns] [voltage_v]")\n'
    assert target in text, 'Target end of Stage 246 block not found'

    insertion = """
        # Stage 247: Sovereign Anti-Fragile Black-Swan Catastrophe Immunity & Systemic Stress Inversion Engine
        if lowered in {"/antifragile-status", "antifragile-status"}:
            if hasattr(self.runtime, "antifragile_stress_inverter"):
                tbl = self.runtime.antifragile_stress_inverter.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.antifragile_stress_inverter.get_metrics())
            return RouterResponse("Anti-fragile stress inverter not available.")

        if lowered.startswith("/antifragile-shock ") or lowered.startswith("antifragile-shock "):
            if hasattr(self.runtime, "antifragile_stress_inverter"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    stype = parts[1]
                    mag = float(parts[2])
                    res = self.runtime.antifragile_stress_inverter.inject_stress(stype, mag)
                    msg = (
                        f"Absorbed stress '{stype}' (mag={mag:.2f}) -> Convex Gain: +{res['convex_gain']:.4f}. "
                        f"New Capacity: {res['new_capacity']:.4f} ({res['regime']})."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /antifragile-shock <stressor_type> <magnitude>")

        if lowered.startswith("/antifragile-barbell ") or lowered.startswith("antifragile-barbell "):
            if hasattr(self.runtime, "antifragile_stress_inverter"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    res_val = float(parts[1])
                    alloc = self.runtime.antifragile_stress_inverter.apply_barbell_allocation(res_val)
                    msg = (
                        f"Taleb Barbell Allocation (Total={alloc.total_resources:.2f}): "
                        f"Core={alloc.conservative_core:.2f} ({alloc.conservative_ratio*100:.0f}%), "
                        f"Exploratory={alloc.exploratory_convex_periphery:.2f} ({alloc.periphery_ratio*100:.0f}%)."
                    )
                    return RouterResponse(msg, data={
                        "total": alloc.total_resources,
                        "core": alloc.conservative_core,
                        "exploratory": alloc.exploratory_convex_periphery,
                    })
            return RouterResponse("Usage: /antifragile-barbell <total_resources>")

        if lowered.startswith("/antifragile-transmute ") or lowered.startswith("antifragile-transmute "):
            if hasattr(self.runtime, "antifragile_stress_inverter"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    sev = float(parts[1])
                    dom = parts[2]
                    res = self.runtime.antifragile_stress_inverter.transmute_catastrophe(sev, dom)
                    msg = (
                        f"Transmuted Catastrophe in domain '{dom}' (Severity={sev}): "
                        f"Amplification={res['amplification_factor']:.2f}x, Gain=+{res['transmutation_gain']:.4f}. Status: {res['status']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /antifragile-transmute <severity> <domain>")
"""
    if 'antifragile-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 247 into router.py')
    else:
        print('Stage 247 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
