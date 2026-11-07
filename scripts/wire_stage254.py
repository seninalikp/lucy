"""
scripts/wire_stage254.py
Wires Stage 254 SymplecticHamiltonianIntegratorFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.clifford_geometric_algebra import CliffordGeometricAlgebraFabric, STAGE as STAGE_253\n'
    replacement_import = target_import + 'from backend.lucy_core.symplectic_hamiltonian_integrator import SymplecticHamiltonianIntegratorFabric, STAGE as STAGE_254\n'
    if 'symplectic_hamiltonian_integrator' not in text:
        assert target_import in text, 'Target import for Stage 253 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 253: Hyper-Dimensional Clifford Geometric Algebra Processor (Era 26)\n        self.clifford_processor = CliffordGeometricAlgebraFabric()\n'
    replacement_init = target_init + '        # Stage 254: Symplectic Integrator & Lie-Poisson Momentum Preserver (Era 26)\n        self.symplectic_integrator = SymplecticHamiltonianIntegratorFabric()\n'
    if 'self.symplectic_integrator' not in text:
        assert target_init in text, 'Target init for Stage 253 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("clifford_processor", "core"),\n'
    replacement_service = target_service + '            ("symplectic_integrator", "core"),\n'
    if '("symplectic_integrator", "core")' not in text:
        assert target_service in text, 'Target service for Stage 253 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 254 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /ga-decompose <v1x> <v1y> <v1z> <v2x> <v2y> <v2z>")\n'
    assert target in text, 'Target end of Stage 253 block not found'

    insertion = """
        # Stage 254: Continuous Symplectic Geometric Integrator & Lie-Poisson Hamiltonian Momentum Preserver
        if lowered in {"/symplectic-status", "symplectic-status"}:
            if hasattr(self.runtime, "symplectic_integrator"):
                tbl = self.runtime.symplectic_integrator.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.symplectic_integrator.get_metrics())
            return RouterResponse("Symplectic integrator not available.")

        if lowered.startswith("/symplectic-simulate ") or lowered.startswith("symplectic-simulate "):
            if hasattr(self.runtime, "symplectic_integrator"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    q0 = [float(parts[1])]
                    p0 = [float(parts[2])]
                    dt = float(parts[3]) if len(parts) >= 4 else 0.05
                    steps = int(parts[4]) if len(parts) >= 5 else 100
                    res = self.runtime.symplectic_integrator.simulate_harmonic_trajectory(q0, p0, dt, steps)
                    msg = (
                        f"Symplectic Orbit (steps={steps}, dt={dt}): E0={res['initial_energy']:.4f}, "
                        f"E_final={res['final_energy']:.4f}, max_drift={res['max_drift']:.6f} ({res['relative_energy_fluctuation']*100:.4f}%)."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /symplectic-simulate <q0> <p0> [dt] [steps]")

        if lowered.startswith("/symplectic-jacobian ") or lowered.startswith("symplectic-jacobian "):
            if hasattr(self.runtime, "symplectic_integrator"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    q0 = [float(parts[1])]
                    p0 = [float(parts[2])]
                    dt = float(parts[3]) if len(parts) >= 4 else 0.05
                    res = self.runtime.symplectic_integrator.verify_symplectic_jacobian(q0, p0, dt)
                    msg = f"Symplectic Jacobian: det(J)={res['det_jacobian']:.6f}, discrepancy={res['det_discrepancy']:.6f}, holds={res['is_symplectic_invariant']}."
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /symplectic-jacobian <q0> <p0> [dt]")
"""
    if 'symplectic-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 254 into router.py')
    else:
        print('Stage 254 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
