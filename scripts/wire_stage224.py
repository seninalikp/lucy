"""
scripts/wire_stage224.py
Wires Stage 224 MultiverseStateForkerFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.subatomic_pipeline_governor import SubatomicPipelineGovernorFabric, STAGE as STAGE_223\n'
    replacement_import = target_import + 'from backend.lucy_core.multiverse_state_forker import MultiverseStateForkerFabric, STAGE as STAGE_224\n'
    if 'multiverse_state_forker' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 223: Sub-Atomic Micro-Architecture Pipeline Emulation & Speculative Execution Governor (Era 23)\n        self.subatomic_pipeline_governor = SubatomicPipelineGovernorFabric()\n'
    replacement_init = target_init + '        # Stage 224: Universal Multi-Verse Counterfactual State Forker & Timeline Brancher (Era 23)\n        self.multiverse_forker = MultiverseStateForkerFabric()\n'
    if 'self.multiverse_forker' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("subatomic_pipeline_governor", "core"),\n'
    replacement_service = target_service + '            ("multiverse_forker", "core"),\n'
    if '("multiverse_forker", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 224 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    end_marker = '                    return RouterResponse(f"Unknown governor mode \'{m_str}\'. Valid: STRICT_MITIGATION, MONITOR_ONLY, PERMISSIVE")\n            return RouterResponse("Subatomic pipeline governor not available.")\n'
    assert end_marker in text, 'End marker not found'

    insertion = """
        # Stage 224: Universal Multi-Verse Counterfactual State Forker & Timeline Brancher
        if lowered in {"/multiverse-status", "multiverse-status"}:
            if hasattr(self.runtime, "multiverse_forker"):
                tbl = self.runtime.multiverse_forker.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.multiverse_forker.status())
            return RouterResponse("Multiverse state forker not available.")

        if lowered.startswith("/multiverse-fork ") or lowered.startswith("multiverse-fork "):
            if hasattr(self.runtime, "multiverse_forker"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nb = parts[1]
                    from_b = parts[2] if len(parts) >= 3 else "canonical"
                    try:
                        self.runtime.multiverse_forker.fork_branch(nb, from_branch_id=from_b)
                        return RouterResponse(f"Forked new timeline '{nb}' from '{from_b}'.")
                    except Exception as e:
                        return RouterResponse(f"Fork failed: {e}")
            return RouterResponse("Usage: /multiverse-fork <new_branch> [from_branch]")

        if lowered.startswith("/multiverse-switch ") or lowered.startswith("multiverse-switch "):
            if hasattr(self.runtime, "multiverse_forker"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    target_b = parts[1]
                    try:
                        self.runtime.multiverse_forker.switch_active_branch(target_b)
                        return RouterResponse(f"Switched active timeline to '{target_b}'.")
                    except Exception as e:
                        return RouterResponse(f"Switch failed: {e}")
            return RouterResponse("Usage: /multiverse-switch <branch>")

        if lowered.startswith("/multiverse-divergence ") or lowered.startswith("multiverse-divergence "):
            if hasattr(self.runtime, "multiverse_forker"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    b1, b2 = parts[1], parts[2]
                    try:
                        div = self.runtime.multiverse_forker.compute_divergence(b1, b2)
                        msg = f"Divergence between '{b1}' and '{b2}': {div['total_differences']} diffs (Ratio: {div['divergence_ratio']:.2%})"
                        return RouterResponse(msg, data=div)
                    except Exception as e:
                        return RouterResponse(f"Divergence failed: {e}")
            return RouterResponse("Usage: /multiverse-divergence <branch_a> <branch_b>")
"""
    if 'multiverse-status' not in text:
        idx = text.find(end_marker) + len(end_marker)
        text = text[:idx] + insertion + text[idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 224 into router.py')
    else:
        print('Stage 224 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
