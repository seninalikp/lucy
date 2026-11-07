"""
scripts/wire_stage255.py
Wires Stage 255 TuringMorphogeneticSynthesizerFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.symplectic_hamiltonian_integrator import SymplecticHamiltonianIntegratorFabric, STAGE as STAGE_254\n'
    replacement_import = target_import + 'from backend.lucy_core.turing_morphogenetic_synthesizer import TuringMorphogeneticSynthesizerFabric, STAGE as STAGE_255\n'
    if 'turing_morphogenetic_synthesizer' not in text:
        assert target_import in text, 'Target import for Stage 254 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 254: Symplectic Integrator & Lie-Poisson Momentum Preserver (Era 26)\n        self.symplectic_integrator = SymplecticHamiltonianIntegratorFabric()\n'
    replacement_init = target_init + '        # Stage 255: Bio-Mimetic Turing Reaction-Diffusion Synthesizer (Era 26)\n        self.turing_synthesizer = TuringMorphogeneticSynthesizerFabric()\n'
    if 'self.turing_synthesizer' not in text:
        assert target_init in text, 'Target init for Stage 254 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("symplectic_integrator", "core"),\n'
    replacement_service = target_service + '            ("turing_synthesizer", "core"),\n'
    if '("turing_synthesizer", "core")' not in text:
        assert target_service in text, 'Target service for Stage 254 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 255 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /symplectic-jacobian <q0> <p0> [dt]")\n'
    assert target in text, 'Target end of Stage 254 block not found'

    insertion = """
        # Stage 255: Sovereign Bio-Mimetic Morphogenetic Reaction-Diffusion Turing Pattern Synthesizer
        if lowered in {"/turing-status", "turing-status", "/morphogenesis-status", "morphogenesis-status"}:
            if hasattr(self.runtime, "turing_synthesizer"):
                tbl = self.runtime.turing_synthesizer.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.turing_synthesizer.get_metrics())
            return RouterResponse("Turing synthesizer not available.")

        if lowered.startswith("/turing-step ") or lowered.startswith("turing-step "):
            if hasattr(self.runtime, "turing_synthesizer"):
                parts = raw_text.strip().split()
                steps = int(parts[1]) if len(parts) >= 2 else 5
                dt = float(parts[2]) if len(parts) >= 3 else 1.0
                self.runtime.turing_synthesizer.step_reaction_diffusion(steps=steps, dt=dt)
                stats = self.runtime.turing_synthesizer.compute_morphogenetic_statistics()
                msg = f"Simulated {steps} PDE steps (dt={dt}): state={stats['regime']}, var(u)={stats['variance_u']:.4f}, var(v)={stats['variance_v']:.4f}"
                return RouterResponse(msg, data=stats)
            return RouterResponse("Usage: /turing-step [steps] [dt]")

        if lowered.startswith("/turing-seed ") or lowered.startswith("turing-seed "):
            if hasattr(self.runtime, "turing_synthesizer"):
                parts = raw_text.strip().split()
                r = int(parts[1]) if len(parts) >= 2 else 4
                self.runtime.turing_synthesizer.seed_central_spot(radius=r)
                msg = f"Seeded central perturbation (radius={r}) into {self.runtime.turing_synthesizer.w}x{self.runtime.turing_synthesizer.h} grid."
                return RouterResponse(msg, data={"radius": r})
            return RouterResponse("Usage: /turing-seed [radius]")

        if lowered.startswith("/turing-instability ") or lowered.startswith("turing-instability "):
            if hasattr(self.runtime, "turing_synthesizer"):
                parts = raw_text.strip().split()
                if len(parts) >= 7:
                    fu, fv = float(parts[1]), float(parts[2])
                    gu, gv = float(parts[3]), float(parts[4])
                    du, dv = float(parts[5]), float(parts[6])
                    res = self.runtime.turing_synthesizer.evaluate_turing_instability(fu, fv, gu, gv, du, dv)
                    msg = (
                        f"Turing Instability Audit: unstable={res['is_turing_instability']}, "
                        f"kc={res['critical_wavenumber']}, wavelength={res['pattern_wavelength']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /turing-instability <fu> <fv> <gu> <gv> <du> <dv>")
"""
    if 'turing-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 255 into router.py')
    else:
        print('Stage 255 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
