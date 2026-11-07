"""
scripts/wire_stage253.py
Wires Stage 253 CliffordGeometricAlgebraFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.jarzynski_entropy_harvester import JarzynskiEntropyHarvesterFabric, STAGE as STAGE_252\n'
    replacement_import = target_import + 'from backend.lucy_core.clifford_geometric_algebra import CliffordGeometricAlgebraFabric, STAGE as STAGE_253\n'
    if 'clifford_geometric_algebra' not in text:
        assert target_import in text, 'Target import for Stage 252 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 252: Non-Equilibrium Fluctuation-Dissipation & Crooks Harvester (Era 26)\n        self.jarzynski_entropy_harvester = JarzynskiEntropyHarvesterFabric()\n'
    replacement_init = target_init + '        # Stage 253: Hyper-Dimensional Clifford Geometric Algebra Processor (Era 26)\n        self.clifford_processor = CliffordGeometricAlgebraFabric()\n'
    if 'self.clifford_processor' not in text:
        assert target_init in text, 'Target init for Stage 252 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("jarzynski_entropy_harvester", "core"),\n'
    replacement_service = target_service + '            ("clifford_processor", "core"),\n'
    if '("clifford_processor", "core")' not in text:
        assert target_service in text, 'Target service for Stage 252 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 253 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /entropy-harvest <work_kbt> <delta_f_kbt> [bits]")\n'
    assert target in text, 'Target end of Stage 252 block not found'

    insertion = """
        # Stage 253: Hyper-Dimensional Clifford Geometric Algebra (Cl_{p,q,r}) Multivector Wave Processor
        if lowered in {"/clifford-status", "clifford-status", "/ga-status", "ga-status"}:
            if hasattr(self.runtime, "clifford_processor"):
                tbl = self.runtime.clifford_processor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.clifford_processor.get_metrics())
            return RouterResponse("Clifford processor not available.")

        if lowered.startswith("/ga-rotate ") or lowered.startswith("ga-rotate "):
            if hasattr(self.runtime, "clifford_processor"):
                parts = raw_text.strip().split()
                if len(parts) >= 6:
                    vx, vy, vz = float(parts[1]), float(parts[2]), float(parts[3])
                    plane_b = int(parts[4])
                    deg = float(parts[5])
                    rad = math.radians(deg)
                    v = self.runtime.clifford_processor.create_vector([vx, vy, vz])
                    rotor = self.runtime.clifford_processor.create_rotor(plane_b, rad)
                    v_rot = self.runtime.clifford_processor.rotate_vector(v, rotor)
                    rx, ry, rz = v_rot.coeffs[1], v_rot.coeffs[2], v_rot.coeffs[4]
                    msg = f"Rotor Rotation ({deg} deg, plane {plane_b}): ({vx}, {vy}, {vz}) -> ({rx:.4f}, {ry:.4f}, {rz:.4f})"
                    return RouterResponse(msg, data={"original": [vx, vy, vz], "rotated": [rx, ry, rz], "norm": v_rot.norm()})
            return RouterResponse("Usage: /ga-rotate <vx> <vy> <vz> <plane_bivector_idx> <angle_deg>")

        if lowered.startswith("/ga-decompose ") or lowered.startswith("ga-decompose "):
            if hasattr(self.runtime, "clifford_processor"):
                parts = raw_text.strip().split()
                if len(parts) >= 7:
                    v1 = self.runtime.clifford_processor.create_vector([float(parts[1]), float(parts[2]), float(parts[3])])
                    v2 = self.runtime.clifford_processor.create_vector([float(parts[4]), float(parts[5]), float(parts[6])])
                    res = self.runtime.clifford_processor.verify_geometric_decomposition(v1, v2)
                    msg = (
                        f"Clifford Decomposition ab = a.b + a^b: holds={res['decomposition_holds']}, "
                        f"a.b={res['scalar_inner']:.4f}, |a^b|={res['bivector_norm']:.4f}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /ga-decompose <v1x> <v1y> <v1z> <v2x> <v2y> <v2z>")
"""
    if 'clifford-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 253 into router.py')
    else:
        print('Stage 253 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
