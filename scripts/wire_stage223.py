"""
scripts/wire_stage223.py
Wires Stage 223 SubatomicPipelineGovernorFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.holographic_swarm_mesh import HolographicSwarmMeshFabric, STAGE as STAGE_222\n'
    replacement_import = target_import + 'from backend.lucy_core.subatomic_pipeline_governor import SubatomicPipelineGovernorFabric, STAGE as STAGE_223\n'
    if 'subatomic_pipeline_governor' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 222: Sovereign Holographic Swarm Coordination & Flocking Mesh (Era 23)\n        self.holographic_swarm = HolographicSwarmMeshFabric()\n'
    replacement_init = target_init + '        # Stage 223: Sub-Atomic Micro-Architecture Pipeline Emulation & Speculative Execution Governor (Era 23)\n        self.subatomic_pipeline_governor = SubatomicPipelineGovernorFabric()\n'
    if 'self.subatomic_pipeline_governor' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("holographic_swarm", "core"),\n'
    replacement_service = target_service + '            ("subatomic_pipeline_governor", "core"),\n'
    if '("subatomic_pipeline_governor", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 223 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    end_marker = '                        return RouterResponse("Invalid coordinates for swarm goal. Usage: /swarm-goal <x> <y>")\n            return RouterResponse("Holographic swarm fabric not available.")\n'
    assert end_marker in text, 'End marker not found'

    insertion = """
        # Stage 223: Sub-Atomic Micro-Architecture Pipeline Emulation & Speculative Execution Governor
        if lowered in {"/subatomic-pipeline-status", "subatomic-pipeline-status", "/subatomic-status", "subatomic-status"}:
            if hasattr(self.runtime, "subatomic_pipeline_governor"):
                tbl = self.runtime.subatomic_pipeline_governor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.subatomic_pipeline_governor.status())
            return RouterResponse("Subatomic pipeline governor not available.")

        if lowered in {"/subatomic-pipeline-step", "subatomic-pipeline-step", "/subatomic-step", "subatomic-step"}:
            if hasattr(self.runtime, "subatomic_pipeline_governor"):
                res = self.runtime.subatomic_pipeline_governor.step_cycle()
                tbl = self.runtime.subatomic_pipeline_governor.format_ascii_status()
                return RouterResponse(tbl, data=res)
            return RouterResponse("Subatomic pipeline governor not available.")

        if (
            lowered.startswith("/subatomic-pipeline-mode ")
            or lowered.startswith("subatomic-pipeline-mode ")
            or lowered.startswith("/subatomic-mode ")
            or lowered.startswith("subatomic-mode ")
        ):
            if hasattr(self.runtime, "subatomic_pipeline_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    m_str = parts[1].upper()
                    from backend.lucy_core.subatomic_pipeline_governor import GovernorMode
                    if hasattr(GovernorMode, m_str):
                        self.runtime.subatomic_pipeline_governor.set_governor_mode(GovernorMode[m_str])
                        return RouterResponse(f"Pipeline governor mode set to {m_str}")
                    return RouterResponse(f"Unknown governor mode '{m_str}'. Valid: STRICT_MITIGATION, MONITOR_ONLY, PERMISSIVE")
            return RouterResponse("Subatomic pipeline governor not available.")
"""
    if 'subatomic-pipeline-status' not in text:
        idx = text.find(end_marker) + len(end_marker)
        text = text[:idx] + insertion + text[idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 223 into router.py')
    else:
        print('Stage 223 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
