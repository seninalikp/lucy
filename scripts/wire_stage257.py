"""
scripts/wire_stage257.py
Wires Stage 257 JosephsonSquidMagnetometerFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.renormalization_group_flow import RenormalizationGroupFlowFabric, STAGE as STAGE_256\n'
    replacement_import = target_import + 'from backend.lucy_core.josephson_squid_magnetometer import JosephsonSquidMagnetometerFabric, STAGE as STAGE_257\n'
    if 'josephson_squid_magnetometer' not in text:
        assert target_import in text, 'Target import for Stage 256 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 256: Deep Renormalization Group Flow & Wilsonian EFT (Era 26)\n        self.rg_flow_fabric = RenormalizationGroupFlowFabric()\n'
    replacement_init = target_init + '        # Stage 257: Superconducting Josephson SQUID Magnetometer (Era 26)\n        self.squid_magnetometer = JosephsonSquidMagnetometerFabric()\n'
    if 'self.squid_magnetometer' not in text:
        assert target_init in text, 'Target init for Stage 256 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("rg_flow_fabric", "core"),\n'
    replacement_service = target_service + '            ("squid_magnetometer", "core"),\n'
    if '("squid_magnetometer", "core")' not in text:
        assert target_service in text, 'Target service for Stage 256 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 257 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /rg-spin-block [width] [height] [p_up]")\n'
    assert target in text, 'Target end of Stage 256 block not found'

    insertion = """
        # Stage 257: Quantum Superconducting Josephson Junction SQUID Flux-State Quantum Magnetometer
        if lowered in {"/squid-status", "squid-status", "/josephson-status", "josephson-status"}:
            if hasattr(self.runtime, "squid_magnetometer"):
                tbl = self.runtime.squid_magnetometer.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.squid_magnetometer.get_metrics())
            return RouterResponse("SQUID magnetometer not available.")

        if lowered.startswith("/squid-measure-b ") or lowered.startswith("squid-measure-b "):
            if hasattr(self.runtime, "squid_magnetometer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    b_val = float(parts[1])
                    res = self.runtime.squid_magnetometer.measure_external_field(b_val)
                    msg = (
                        f"SQUID Field Measurement (B={b_val:.3e} T): flux={res['flux_webers']:.3e} Wb "
                        f"({res['flux_quanta']:.4f} Phi_0), V_out={res['voltage_microvolts']:.2f} uV, Ic={res['ic_microamps']:.2f} uA."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /squid-measure-b <b_tesla>")

        if lowered.startswith("/josephson-frequency ") or lowered.startswith("josephson-frequency "):
            if hasattr(self.runtime, "squid_magnetometer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    v_val = float(parts[1])
                    f_j = self.runtime.squid_magnetometer.compute_ac_josephson_frequency(v_val)
                    msg = f"AC Josephson Frequency (V={v_val:.6f} V): f_J = {f_j*1e-9:.4f} GHz ({f_j:.3e} Hz)."
                    return RouterResponse(msg, data={"voltage_v": v_val, "frequency_hz": f_j, "frequency_ghz": f_j * 1e-9})
            return RouterResponse("Usage: /josephson-frequency <voltage_volts>")
"""
    if 'squid-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 257 into router.py')
    else:
        print('Stage 257 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
