"""
scripts/wire_stage243.py
Wires Stage 243 CellularCohomologySheafFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.exceptional_point_resonance import ExceptionalPointResonanceFabric, STAGE as STAGE_242\n'
    replacement_import = target_import + 'from backend.lucy_core.cellular_cohomology_sheaf import CellularCohomologySheafFabric, STAGE as STAGE_243\n'
    if 'cellular_cohomology_sheaf' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 242: Non-Hermitian Exceptional Point Dynamical Resonance Engine (Era 25)\n        self.exceptional_point_resonance = ExceptionalPointResonanceFabric()\n'
    replacement_init = target_init + '        # Stage 243: Deep Sheaf-Theoretic Distributed Multi-Sensor Consistency & Cellular Cohomology Engine (Era 25)\n        self.cellular_cohomology_sheaf = CellularCohomologySheafFabric()\n'
    if 'self.cellular_cohomology_sheaf' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("exceptional_point_resonance", "core"),\n'
    replacement_service = target_service + '            ("cellular_cohomology_sheaf", "core"),\n'
    if '("cellular_cohomology_sheaf", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 243 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /ep-encircle [steps] [CW|CCW]")\n'
    assert target in text, 'Target end of Stage 242 block not found'

    insertion = """
        # Stage 243: Deep Sheaf-Theoretic Distributed Multi-Sensor Consistency & Cellular Cohomology Engine
        if lowered in {"/sheaf-status", "sheaf-status"}:
            if hasattr(self.runtime, "cellular_cohomology_sheaf"):
                tbl = self.runtime.cellular_cohomology_sheaf.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.cellular_cohomology_sheaf.status())
            return RouterResponse("Cellular cohomology sheaf fabric not available.")

        if lowered in {"/sheaf-audit", "sheaf-audit"}:
            if hasattr(self.runtime, "cellular_cohomology_sheaf"):
                audit = self.runtime.cellular_cohomology_sheaf.audit_topological_obstruction()
                status_str = "CONSISTENT (H^0 Global Section)" if audit["is_global_section_h0"] else "OBSTRUCTION DETECTED (H^1 Non-Zero Residual)"
                msg = f"Sheaf Cohomology Audit: {status_str}. Energy E(x): {audit['dirichlet_energy']}."
                return RouterResponse(msg, data=audit)
            return RouterResponse("Cellular cohomology sheaf fabric not available.")

        if lowered.startswith("/sheaf-diffuse ") or lowered.startswith("sheaf-diffuse "):
            if hasattr(self.runtime, "cellular_cohomology_sheaf"):
                parts = raw_text.strip().split()
                steps = int(parts[1]) if len(parts) >= 2 else 10
                lr = float(parts[2]) if len(parts) >= 3 else 0.1
                final_energy = 0.0
                for _ in range(steps):
                    final_energy = self.runtime.cellular_cohomology_sheaf.diffuse_harmonic_consensus_step(lr)
                msg = f"Diffused Sheaf Laplacian for {steps} steps (step_size={lr}). Final Dirichlet energy: {final_energy:.6f}."
                return RouterResponse(msg, data={"steps": steps, "step_size": lr, "final_energy": final_energy})
            return RouterResponse("Usage: /sheaf-diffuse [steps] [step_size]")

        if lowered.startswith("/sheaf-set-sensor ") or lowered.startswith("sheaf-set-sensor "):
            if hasattr(self.runtime, "cellular_cohomology_sheaf"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    vid = parts[1]
                    try:
                        vals = [float(x) for x in parts[2].split(",")]
                        self.runtime.cellular_cohomology_sheaf.set_sensor_value(vid, vals)
                        msg = f"Sensor section '{vid}' updated to: {vals}."
                        return RouterResponse(msg, data={"vertex": vid, "section": vals})
                    except Exception as e:
                        return RouterResponse(f"Sensor update failed: {e}")
            return RouterResponse("Usage: /sheaf-set-sensor <vertex_id> <values_csv>")
"""
    if 'sheaf-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 243 into router.py')
    else:
        print('Stage 243 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
