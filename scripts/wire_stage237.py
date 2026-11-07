"""
scripts/wire_stage237.py
Wires Stage 237 PhotonicOpticalSwitchFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.temporal_chrono_governor import TemporalChronoGovernorFabric, STAGE as STAGE_236\n'
    replacement_import = target_import + 'from backend.lucy_core.photonic_optical_switch import PhotonicOpticalSwitchFabric, STAGE as STAGE_237\n'
    if 'photonic_optical_switch' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 236: Autonomous Temporal Chrono-State Engine & Causality Inversion Governor (Era 24)\n        self.temporal_chrono_governor = TemporalChronoGovernorFabric()\n'
    replacement_init = target_init + '        # Stage 237: Autonomous Photonic Optical Neural Interconnect & Ultra-Low-Latency Switch Fabric (Era 24)\n        self.photonic_optical_switch = PhotonicOpticalSwitchFabric()\n'
    if 'self.photonic_optical_switch' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("temporal_chrono_governor", "core"),\n'
    replacement_service = target_service + '            ("photonic_optical_switch", "core"),\n'
    if '("photonic_optical_switch", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 237 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /temporal-rollback <timeline_id> <event_id>")\n'
    assert target in text, 'Target end of Stage 236 block not found'

    insertion = """
        # Stage 237: Autonomous Photonic Optical Neural Interconnect & Ultra-Low-Latency Switch Fabric
        if lowered in {"/optical-switch-status", "optical-switch-status"}:
            if hasattr(self.runtime, "photonic_optical_switch"):
                tbl = self.runtime.photonic_optical_switch.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.photonic_optical_switch.status())
            return RouterResponse("Photonic optical switch fabric not available.")

        if lowered.startswith("/optical-route ") or lowered.startswith("optical-route "):
            if hasattr(self.runtime, "photonic_optical_switch"):
                parts = raw_text.strip().split(maxsplit=2)
                if len(parts) >= 3:
                    try:
                        ingress = int(parts[1])
                        payload = parts[2].encode("utf-8")
                        res = self.runtime.photonic_optical_switch.route_optical_packet(ingress, payload)
                        msg = (
                            f"Optical packet routed {res['ingress_port']} -> {res['egress_port']}. "
                            f"Latency: {res['latency_ps']} ps, Loss: {res['loss_db']} dB, Output: {res['output_power_mw']} mW."
                        )
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"Optical routing failed: {e}")
            return RouterResponse("Usage: /optical-route <ingress_port> <payload>")

        if lowered.startswith("/optical-program-route ") or lowered.startswith("optical-program-route "):
            if hasattr(self.runtime, "photonic_optical_switch"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    try:
                        inp, outp = int(parts[1]), int(parts[2])
                        self.runtime.photonic_optical_switch.program_route(inp, outp)
                        msg = f"Crossbar route programmed: Ingress Port {inp} -> Egress Port {outp}."
                        return RouterResponse(msg, data={"ingress": inp, "egress": outp})
                    except Exception as e:
                        return RouterResponse(f"Optical route programming failed: {e}")
            return RouterResponse("Usage: /optical-program-route <ingress_port> <egress_port>")

        if lowered in {"/optical-calibrate", "optical-calibrate"}:
            if hasattr(self.runtime, "photonic_optical_switch"):
                corrected = self.runtime.photonic_optical_switch.calibrate_thermo_optic_phases()
                msg = f"Autonomous thermo-optic calibration completed. Corrected MZI units: {corrected}."
                return RouterResponse(msg, data={"corrected_units": corrected})
            return RouterResponse("Photonic optical switch fabric not available.")
"""
    if 'optical-switch-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 237 into router.py')
    else:
        print('Stage 237 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
