"""
scripts/wire_stage228.py
Wires Stage 228 HyperdimensionalComputingFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.energy_budget_governor import EnergyBudgetGovernorFabric, STAGE as STAGE_227\n'
    replacement_import = target_import + 'from backend.lucy_core.hyperdimensional_computing import HyperdimensionalComputingFabric, STAGE as STAGE_228\n'
    if 'hyperdimensional_computing' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 227: Autonomous Hardware Energy Budget Governor & Thermal-Joule Throttle Fabric (Era 23)\n        self.energy_budget_governor = EnergyBudgetGovernorFabric()\n'
    replacement_init = target_init + '        # Stage 228: High-Dimensional Hyperdimensional Computing & Vector Symbolic Architecture (Era 23)\n        self.hyperdimensional_computing = HyperdimensionalComputingFabric()\n'
    if 'self.hyperdimensional_computing' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("energy_budget_governor", "core"),\n'
    replacement_service = target_service + '            ("hyperdimensional_computing", "core"),\n'
    if '("hyperdimensional_computing", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 228 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    end_marker = '            return RouterResponse("Usage: /energy-workload <task_name> [duration_s]")\n'
    assert end_marker in text, 'End marker not found'

    insertion = """
        # Stage 228: High-Dimensional Hyperdimensional Computing & Vector Symbolic Architecture
        if lowered in {"/hdc-status", "hdc-status"}:
            if hasattr(self.runtime, "hyperdimensional_computing"):
                tbl = self.runtime.hyperdimensional_computing.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.hyperdimensional_computing.status())
            return RouterResponse("Hyperdimensional computing fabric not available.")

        if lowered.startswith("/hdc-bind ") or lowered.startswith("hdc-bind "):
            if hasattr(self.runtime, "hyperdimensional_computing"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    sa, sb = parts[1], parts[2]
                    bound = self.runtime.hyperdimensional_computing.bind_symbols(sa, sb)
                    msg = f"Bound symbols '{sa}' and '{sb}' into {bound.dimension}-D hypervector."
                    return RouterResponse(msg, data={"dim": bound.dimension, "sim_to_a": bound.cosine_similarity(self.runtime.hyperdimensional_computing.generate_symbol(sa))})
            return RouterResponse("Usage: /hdc-bind <symbol_a> <symbol_b>")

        if lowered in {"/hdc-analogy-sample", "hdc-analogy-sample"}:
            if hasattr(self.runtime, "hyperdimensional_computing"):
                self.runtime.hyperdimensional_computing.store_composite_record("usa_sample", {"currency": "dollar", "capital": "dc"})
                self.runtime.hyperdimensional_computing.store_composite_record("mexico_sample", {"currency": "peso", "capital": "cdmx"})
                best_cand, sim = self.runtime.hyperdimensional_computing.solve_relational_analogy("usa_sample", "mexico_sample", "dollar")
                msg = f"Kanerva Analogy Solver (Dollar : USA :: ? : Mexico) -> Solved: '{best_cand}' (Cosine Similarity: {sim:.4f})"
                return RouterResponse(msg, data={"analogy": "Dollar:USA :: ?:Mexico", "solution": best_cand, "similarity": sim})
            return RouterResponse("Hyperdimensional computing fabric not available.")
"""
    if 'hdc-status' not in text:
        idx = text.find(end_marker) + len(end_marker)
        text = text[:idx] + insertion + text[idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 228 into router.py')
    else:
        print('Stage 228 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
