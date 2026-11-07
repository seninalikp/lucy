"""
scripts/wire_stage242.py
Wires Stage 242 ExceptionalPointResonanceFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.metamaterial_phonon_computer import MetamaterialPhononComputerFabric, STAGE as STAGE_241\n'
    replacement_import = target_import + 'from backend.lucy_core.exceptional_point_resonance import ExceptionalPointResonanceFabric, STAGE as STAGE_242\n'
    if 'exceptional_point_resonance' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 241: Programmable Metamaterial Phonon-Polariton Waveguide Computing & Analog Tensor Interconnect (Era 25)\n        self.metamaterial_phonon_computer = MetamaterialPhononComputerFabric()\n'
    replacement_init = target_init + '        # Stage 242: Non-Hermitian Exceptional Point Dynamical Resonance Engine (Era 25)\n        self.exceptional_point_resonance = ExceptionalPointResonanceFabric()\n'
    if 'self.exceptional_point_resonance' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("metamaterial_phonon_computer", "core"),\n'
    replacement_service = target_service + '            ("exceptional_point_resonance", "core"),\n'
    if '("exceptional_point_resonance", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 242 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /phonon-mac <inputs_csv> <weights_csv>")\n'
    assert target in text, 'Target end of Stage 241 block not found'

    insertion = """
        # Stage 242: Non-Hermitian Exceptional Point Dynamical Resonance Engine
        if lowered in {"/ep-status", "ep-status"}:
            if hasattr(self.runtime, "exceptional_point_resonance"):
                tbl = self.runtime.exceptional_point_resonance.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.exceptional_point_resonance.status())
            return RouterResponse("Exceptional point resonance engine not available.")

        if lowered.startswith("/ep-enhance ") or lowered.startswith("ep-enhance "):
            if hasattr(self.runtime, "exceptional_point_resonance"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    try:
                        eps = float(parts[1])
                        res = self.runtime.exceptional_point_resonance.measure_perturbation_enhancement(eps)
                        msg = (
                            f"EP Perturbation Sensitivity Boost: {res['sensitivity_enhancement_factor']}x "
                            f"(EP Splitting: {res['ep_eigenvalue_splitting']}, Linear: {res['hermitian_linear_splitting']})."
                        )
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"EP enhancement measurement failed: {e}")
            return RouterResponse("Usage: /ep-enhance <epsilon_float>")

        if lowered.startswith("/ep-encircle ") or lowered.startswith("ep-encircle "):
            if hasattr(self.runtime, "exceptional_point_resonance"):
                parts = raw_text.strip().split()
                steps = int(parts[1]) if len(parts) >= 2 else 50
                cw = (parts[2].upper() != "CCW") if len(parts) >= 3 else True
                try:
                    res = self.runtime.exceptional_point_resonance.encircle_exceptional_point(steps, cw)
                    msg = f"Parametric loop around EP ({res['direction']}, {res['steps']} steps). Mean splitting: {res['mean_splitting']}."
                    return RouterResponse(msg, data=res)
                except Exception as e:
                    return RouterResponse(f"EP loop encircling failed: {e}")
            return RouterResponse("Usage: /ep-encircle [steps] [CW|CCW]")
"""
    if 'ep-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 242 into router.py')
    else:
        print('Stage 242 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
