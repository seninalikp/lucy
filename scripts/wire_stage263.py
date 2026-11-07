"""
scripts/wire_stage263.py
Wires Stage 263 OptomechanicalCavityTransceiverFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.ads_cft_entanglement_wedge import AdSCFTEntanglementWedgeFabric, STAGE as STAGE_262\n'
    replacement_import = target_import + 'from backend.lucy_core.optomechanical_cavity_transceiver import OptomechanicalCavityTransceiverFabric, STAGE as STAGE_263\n'
    if 'optomechanical_cavity_transceiver' not in text:
        assert target_import in text, 'Target import for Stage 262 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 262: Holographic AdS/CFT Ryu-Takayanagi Wedge (Era 27)\n        self.entanglement_wedge_fabric = AdSCFTEntanglementWedgeFabric()\n'
    replacement_init = target_init + '        # Stage 263: Optomechanical Cavity Radiation Pressure Transceiver (Era 27)\n        self.optomechanical_transceiver = OptomechanicalCavityTransceiverFabric()\n'
    if 'self.optomechanical_transceiver' not in text:
        assert target_init in text, 'Target init for Stage 262 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("entanglement_wedge_fabric", "core"),\n'
    replacement_service = target_service + '            ("optomechanical_transceiver", "core"),\n'
    if '("optomechanical_transceiver", "core")' not in text:
        assert target_service in text, 'Target service for Stage 262 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 263 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /holographic-mutual-info <length_a> <length_b> <separation_d>")\n'
    assert target in text, 'Target end of Stage 262 block not found'

    insertion = """
        # Stage 263: Superconducting Optomechanical Cavity Radiation Pressure & Phonon-Photon Squeezing Transceiver
        if lowered in {"/optomechanics-status", "optomechanics-status", "/cavity-status", "cavity-status"}:
            if hasattr(self.runtime, "optomechanical_transceiver"):
                tbl = self.runtime.optomechanical_transceiver.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.optomechanical_transceiver.get_metrics())
            return RouterResponse("Optomechanical transceiver not available.")

        if lowered.startswith("/opto-cool ") or lowered.startswith("opto-cool "):
            if hasattr(self.runtime, "optomechanical_transceiver"):
                parts = raw_text.strip().split()
                p_mw = float(parts[1]) if len(parts) >= 2 else 0.1
                t_k = float(parts[2]) if len(parts) >= 3 else 0.1
                res = self.runtime.optomechanical_transceiver.evaluate_ground_state_cooling(p_mw * 1e-3, t_k)
                msg = (
                    f"Optomechanical Backaction Cooling (P={p_mw} mW, T={t_k} K): "
                    f"n_eff={res['final_cooled_occupancy']:.4f} phonons (Ground state: {res['is_quantum_ground_state']}). "
                    f"Cooling rate: {res['optomechanical_cooling_rate_s']:.1f} s^-1."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /opto-cool [laser_power_mw] [bath_temp_k]")

        if lowered.startswith("/opto-squeeze ") or lowered.startswith("opto-squeeze "):
            if hasattr(self.runtime, "optomechanical_transceiver"):
                parts = raw_text.strip().split()
                p_mw = float(parts[1]) if len(parts) >= 2 else 1.0
                det_ratio = float(parts[2]) if len(parts) >= 3 else 0.5
                res = self.runtime.optomechanical_transceiver.compute_ponderomotive_squeezing(p_mw * 1e-3, det_ratio)
                msg = (
                    f"Ponderomotive Optical Squeezing (P={p_mw} mW): {res['squeezing_db']:.2f} dB below SQL "
                    f"(Variance: {res['noise_variance_ratio']:.4f}, Cooperativity: {res['cooperativity_C']:.2f})."
                )
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /opto-squeeze [laser_power_mw] [detuning_ratio]")
"""
    if 'optomechanics-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 263 into router.py')
    else:
        print('Stage 263 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
