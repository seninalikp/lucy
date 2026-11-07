"""
scripts/wire_stage241.py
Wires Stage 241 MetamaterialPhononComputerFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.era24_master_seal import Era24MasterSealFabric, STAGE as STAGE_240\n'
    replacement_import = target_import + 'from backend.lucy_core.metamaterial_phonon_computer import MetamaterialPhononComputerFabric, STAGE as STAGE_241\n'
    if 'metamaterial_phonon_computer' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 240: The Sovereign Era 24 Master Seal & AGI Singularity Genesis (Era 24)\n        self.era24_master_seal = Era24MasterSealFabric()\n'
    replacement_init = target_init + '        # Stage 241: Programmable Metamaterial Phonon-Polariton Waveguide Computing & Analog Tensor Interconnect (Era 25)\n        self.metamaterial_phonon_computer = MetamaterialPhononComputerFabric()\n'
    if 'self.metamaterial_phonon_computer' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("era24_master_seal", "core"),\n'
    replacement_service = target_service + '            ("metamaterial_phonon_computer", "core"),\n'
    if '("metamaterial_phonon_computer", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 241 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Era 24 Master Seal not available.")\n'
    assert target in text, 'Target end of Stage 240 block not found'

    insertion = """
        # Stage 241: Programmable Metamaterial Phonon-Polariton Waveguide Computing & Analog Tensor Interconnect
        if lowered in {"/phonon-status", "phonon-status"}:
            if hasattr(self.runtime, "metamaterial_phonon_computer"):
                tbl = self.runtime.metamaterial_phonon_computer.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.metamaterial_phonon_computer.status())
            return RouterResponse("Metamaterial phonon computer not available.")

        if lowered.startswith("/phonon-route ") or lowered.startswith("phonon-route "):
            if hasattr(self.runtime, "metamaterial_phonon_computer"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    try:
                        freq = float(parts[1])
                        amp = float(parts[2]) if len(parts) >= 3 else 1.0
                        dist = float(parts[3]) if len(parts) >= 4 else 10.0
                        res = self.runtime.metamaterial_phonon_computer.propagate_phonon_wave(freq, amp, dist)
                        msg = (
                            f"Phonon Wave at {freq:.2f} GHz -> Output Amplitude: {res['output_amplitude']}, "
                            f"Mode: {res['transmission_mode']}, Delay: {res['delay_ps']} ps."
                        )
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"Phonon wave routing failed: {e}")
            return RouterResponse("Usage: /phonon-route <freq_ghz> [amplitude] [distance_um]")

        if lowered.startswith("/phonon-mac ") or lowered.startswith("phonon-mac "):
            if hasattr(self.runtime, "metamaterial_phonon_computer"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    try:
                        in_vals = [float(x) for x in parts[1].split(",")]
                        wt_vals = [float(x) for x in parts[2].split(",")]
                        res = self.runtime.metamaterial_phonon_computer.execute_analog_wave_mac(in_vals, wt_vals)
                        msg = (
                            f"Analog Wave MAC Result: {res['analog_mac_result']} "
                            f"(Theoretical: {res['theoretical_dot_product']}, Fidelity: {res['mac_fidelity']})."
                        )
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"Analog MAC failed: {e}")
            return RouterResponse("Usage: /phonon-mac <inputs_csv> <weights_csv>")
"""
    if 'phonon-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 241 into router.py')
    else:
        print('Stage 241 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
