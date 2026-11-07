"""
scripts/wire_stage235.py
Wires Stage 235 EpistemicLogicMeshFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.polyglot_bytecode_jit import PolyglotBytecodeJITFabric, STAGE as STAGE_234\n'
    replacement_import = target_import + 'from backend.lucy_core.epistemic_logic_mesh import EpistemicLogicMeshFabric, STAGE as STAGE_235\n'
    if 'epistemic_logic_mesh' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 234: Self-Synthesizing AST Bytecode JIT Compiler & Polyglot IR (Era 24)\n        self.polyglot_bytecode_jit = PolyglotBytecodeJITFabric()\n'
    replacement_init = target_init + '        # Stage 235: Decentralized Multi-Agent Epistemic Logic & Dynamic Common Knowledge Mesh (Era 24)\n        self.epistemic_logic_mesh = EpistemicLogicMeshFabric()\n'
    if 'self.epistemic_logic_mesh' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("polyglot_bytecode_jit", "core"),\n'
    replacement_service = target_service + '            ("epistemic_logic_mesh", "core"),\n'
    if '("epistemic_logic_mesh", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 235 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /bytecode-jit-compile <fn_name>")\n'
    assert target in text, 'Target end of Stage 234 block not found'

    insertion = """
        # Stage 235: Decentralized Multi-Agent Epistemic Logic & Dynamic Common Knowledge Mesh
        if lowered in {"/epistemic-status", "epistemic-status"}:
            if hasattr(self.runtime, "epistemic_logic_mesh"):
                tbl = self.runtime.epistemic_logic_mesh.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.epistemic_logic_mesh.status())
            return RouterResponse("Epistemic logic mesh not available.")

        if lowered in {"/epistemic-muddy-step", "epistemic-muddy-step"}:
            if hasattr(self.runtime, "epistemic_logic_mesh"):
                res = self.runtime.epistemic_logic_mesh.step_muddy_children_round()
                msg = f"Executed Epistemic Muddy Children Round {res['round']}. Remaining possible worlds: {res['remaining_worlds']}."
                return RouterResponse(msg, data=res)
            return RouterResponse("Epistemic logic mesh not available.")

        if lowered.startswith("/epistemic-query ") or lowered.startswith("epistemic-query "):
            if hasattr(self.runtime, "epistemic_logic_mesh"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    ag, prop = parts[1], parts[2]
                    knows = self.runtime.epistemic_logic_mesh.query_agent_knowledge(ag, prop)
                    msg = f"Agent '{ag}' knows '{prop}': {knows}."
                    return RouterResponse(msg, data={"agent": ag, "proposition": prop, "knows": knows})
            return RouterResponse("Usage: /epistemic-query <agent_id> <proposition>")

        if lowered.startswith("/epistemic-verify-common ") or lowered.startswith("epistemic-verify-common "):
            if hasattr(self.runtime, "epistemic_logic_mesh"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    prop = parts[1]
                    is_ck = self.runtime.epistemic_logic_mesh.verify_common_knowledge(prop)
                    msg = f"Proposition '{prop}' is Common Knowledge among agents: {is_ck}."
                    return RouterResponse(msg, data={"proposition": prop, "common_knowledge": is_ck})
            return RouterResponse("Usage: /epistemic-verify-common <proposition>")
"""
    if 'epistemic-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 235 into router.py')
    else:
        print('Stage 235 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
