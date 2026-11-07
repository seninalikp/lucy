"""
scripts/wire_stage222.py
Wires Stage 222 HolographicSwarmMeshFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.quantum_many_body_density import QuantumManyBodyDensityFabric, STAGE as STAGE_221\n'
    replacement_import = target_import + 'from backend.lucy_core.holographic_swarm_mesh import HolographicSwarmMeshFabric, STAGE as STAGE_222\n'
    if 'holographic_swarm_mesh' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 221: Quantum Density Matrix Simulator (Era 23)\n        self.density_matrix_simulator = QuantumManyBodyDensityFabric()\n'
    replacement_init = target_init + '        # Stage 222: Sovereign Holographic Swarm Coordination & Flocking Mesh (Era 23)\n        self.holographic_swarm = HolographicSwarmMeshFabric()\n'
    if 'self.holographic_swarm' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("density_matrix_simulator", "core"),\n'
    replacement_service = target_service + '            ("holographic_swarm", "core"),\n'
    if '("holographic_swarm", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 222 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '        if lowered in {"/density-decohere", "density-decohere"}:'
    assert target in text, 'Target in router not found'

    # Find the end of density-decohere block
    end_marker = '                return RouterResponse(msg, data={"purity": damped.purity(), "entropy": s, "matrix": damped.to_real_display()})\n'
    assert end_marker in text, 'End marker not found'
    
    insertion = """
        # Stage 222: Holographic Swarm Coordination & Flocking Consensus
        if lowered in {"/swarm-status", "swarm-status"}:
            if hasattr(self.runtime, "holographic_swarm"):
                tbl = self.runtime.holographic_swarm.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.holographic_swarm.status())
            return RouterResponse("Holographic swarm fabric not available.")

        if lowered in {"/swarm-step", "swarm-step"}:
            if hasattr(self.runtime, "holographic_swarm"):
                self.runtime.holographic_swarm.step_swarm(dt=0.1)
                tbl = self.runtime.holographic_swarm.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.holographic_swarm.status())
            return RouterResponse("Holographic swarm fabric not available.")

        if lowered.startswith("/swarm-goal ") or lowered.startswith("swarm-goal "):
            if hasattr(self.runtime, "holographic_swarm"):
                parts = command.strip().split()
                if len(parts) >= 3:
                    try:
                        gx, gy = float(parts[1]), float(parts[2])
                        from backend.lucy_core.holographic_swarm_mesh import Vector2D
                        self.runtime.holographic_swarm.set_goal(Vector2D(gx, gy))
                        return RouterResponse(f"Swarm goal set to ({gx}, {gy})")
                    except ValueError:
                        return RouterResponse("Invalid coordinates for swarm goal. Usage: /swarm-goal <x> <y>")
            return RouterResponse("Holographic swarm fabric not available.")
"""
    if 'swarm-status' not in text:
        idx = text.find(end_marker) + len(end_marker)
        text = text[:idx] + insertion + text[idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 222 into router.py')
    else:
        print('Stage 222 already in router.py')

if __name__ == '__main__':
    wire_runtime()
    wire_router()
