"""
scripts/wire_stage234.py
Wires Stage 234 PolyglotBytecodeJITFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.hyperbolic_graph_embedder import HyperbolicGraphEmbedderFabric, STAGE as STAGE_233\n'
    replacement_import = target_import + 'from backend.lucy_core.polyglot_bytecode_jit import PolyglotBytecodeJITFabric, STAGE as STAGE_234\n'
    if 'polyglot_bytecode_jit' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 233: Autonomous Non-Euclidean Hyperbolic Knowledge Graph Embedding (Era 24)\n        self.hyperbolic_graph_embedder = HyperbolicGraphEmbedderFabric()\n'
    replacement_init = target_init + '        # Stage 234: Self-Synthesizing AST Bytecode JIT Compiler & Polyglot IR (Era 24)\n        self.polyglot_bytecode_jit = PolyglotBytecodeJITFabric()\n'
    if 'self.polyglot_bytecode_jit' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("hyperbolic_graph_embedder", "core"),\n'
    replacement_service = target_service + '            ("polyglot_bytecode_jit", "core"),\n'
    if '("polyglot_bytecode_jit", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 234 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Hyperbolic graph embedder not available.")\n'
    assert target in text, 'Target end of hyperbolic block not found'

    insertion = """
        # Stage 234: Self-Synthesizing AST Bytecode JIT Compiler & Polyglot Intermediate Representation
        if lowered in {"/bytecode-jit-status", "bytecode-jit-status"}:
            if hasattr(self.runtime, "polyglot_bytecode_jit"):
                tbl = self.runtime.polyglot_bytecode_jit.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.polyglot_bytecode_jit.status())
            return RouterResponse("Polyglot bytecode JIT compiler not available.")

        if lowered.startswith("/bytecode-jit-exec ") or lowered.startswith("bytecode-jit-exec "):
            if hasattr(self.runtime, "polyglot_bytecode_jit"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    fn_name = parts[1]
                    raw_args = parts[2:]
                    parsed_args = []
                    for arg in raw_args:
                        try:
                            if "." in arg:
                                parsed_args.append(float(arg))
                            else:
                                parsed_args.append(int(arg))
                        except ValueError:
                            parsed_args.append(arg)
                    try:
                        res = self.runtime.polyglot_bytecode_jit.execute_function(fn_name, *parsed_args)
                        msg = f"JIT function '{fn_name}' execution result: {res}."
                        return RouterResponse(msg, data={"function": fn_name, "args": parsed_args, "result": res})
                    except Exception as e:
                        return RouterResponse(f"JIT execution failed: {e}")
            return RouterResponse("Usage: /bytecode-jit-exec <fn_name> [args...]")

        if lowered.startswith("/bytecode-jit-compile ") or lowered.startswith("bytecode-jit-compile "):
            if hasattr(self.runtime, "polyglot_bytecode_jit"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    fn_name = parts[1]
                    try:
                        res = self.runtime.polyglot_bytecode_jit.compile_jit(fn_name)
                        msg = f"JIT compilation for '{fn_name}' succeeded. Native Tier-1 compiled."
                        return RouterResponse(msg, data={"function": fn_name, "jit_compiled": True})
                    except Exception as e:
                        return RouterResponse(f"JIT compilation failed: {e}")
            return RouterResponse("Usage: /bytecode-jit-compile <fn_name>")
"""
    if 'bytecode-jit-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 234 into router.py')
    else:
        print('Stage 234 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
