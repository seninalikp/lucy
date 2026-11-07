"""
scripts/wire_stage246.py
Wires Stage 246 AdiabaticReversibleGovernorFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.orbital_constellation_grid import OrbitalConstellationGridFabric, STAGE as STAGE_245\n'
    replacement_import = target_import + 'from backend.lucy_core.adiabatic_reversible_governor import AdiabaticReversibleGovernorFabric, STAGE as STAGE_246\n'
    if 'adiabatic_reversible_governor' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 245: Hyper-Scale Neuromorphic Astro-Grid Orbital Constellation Coordinator (Era 25)\n        self.orbital_constellation_grid = OrbitalConstellationGridFabric()\n'
    replacement_init = target_init + '        # Stage 246: Thermodynamically Reversible Landauer-Zero Computation & Adiabatic Governor (Era 25)\n        self.adiabatic_reversible_governor = AdiabaticReversibleGovernorFabric()\n'
    if 'self.adiabatic_reversible_governor' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("orbital_constellation_grid", "core"),\n'
    replacement_service = target_service + '            ("adiabatic_reversible_governor", "core"),\n'
    if '("adiabatic_reversible_governor", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 246 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /astro-route <source_sat> <dest_sat> <payload_text>")\n'
    assert target in text, 'Target end of Stage 245 block not found'

    insertion = """
        # Stage 246: Thermodynamically Reversible Landauer-Zero Computation & Adiabatic Switching Governor
        if lowered in {"/reversible-status", "reversible-status", "/adiabatic-status"}:
            if hasattr(self.runtime, "adiabatic_reversible_governor"):
                tbl = self.runtime.adiabatic_reversible_governor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.adiabatic_reversible_governor.status())
            return RouterResponse("Adiabatic reversible governor not available.")

        if lowered.startswith("/reversible-cnot ") or lowered.startswith("reversible-cnot "):
            if hasattr(self.runtime, "adiabatic_reversible_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    c, t = int(parts[1]), int(parts[2])
                    c_out, t_out = self.runtime.adiabatic_reversible_governor.execute_feynman_cnot(c, t)
                    msg = f"Feynman CNOT: ({c}, {t}) -> ({c_out}, {t_out}). Zero information loss."
                    return RouterResponse(msg, data={"in": [c, t], "out": [c_out, t_out]})
            return RouterResponse("Usage: /reversible-cnot <control_bit> <target_bit>")

        if lowered.startswith("/reversible-cswap ") or lowered.startswith("reversible-cswap "):
            if hasattr(self.runtime, "adiabatic_reversible_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    c, a, b = int(parts[1]), int(parts[2]), int(parts[3])
                    c_o, a_o, b_o = self.runtime.adiabatic_reversible_governor.execute_fredkin_cswap(c, a, b)
                    msg = f"Fredkin CSWAP: ({c}, {a}, {b}) -> ({c_o}, {a_o}, {b_o}). Bit weight conserved."
                    return RouterResponse(msg, data={"in": [c, a, b], "out": [c_o, a_o, b_o]})
            return RouterResponse("Usage: /reversible-cswap <control_bit> <a_bit> <b_bit>")

        if lowered.startswith("/adiabatic-dissipation ") or lowered.startswith("adiabatic-dissipation "):
            if hasattr(self.runtime, "adiabatic_reversible_governor"):
                parts = raw_text.strip().split()
                ramp_ns = float(parts[1]) if len(parts) >= 2 else 10.0
                v = float(parts[2]) if len(parts) >= 3 else 0.8
                res = self.runtime.adiabatic_reversible_governor.compute_adiabatic_switching_dissipation(
                    voltage_v=v,
                    ramp_time_seconds=ramp_ns * 1e-9
                )
                msg = (
                    f"Adiabatic Charging (T_ramp={ramp_ns} ns, V={v} V): "
                    f"Dissipated {res['adiabatic_dissipated_energy_joules']:.3e} J ({res['energy_reduction_factor']}x savings vs CMOS)."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /adiabatic-dissipation [ramp_ns] [voltage_v]")
"""
    if 'reversible-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 246 into router.py')
    else:
        print('Stage 246 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
