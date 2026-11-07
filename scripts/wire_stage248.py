"""
scripts/wire_stage248.py
Wires Stage 248 PadicUltrametricClustererFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.antifragile_stress_inverter import AntiFragileStressInverterFabric, STAGE as STAGE_247\n'
    replacement_import = target_import + 'from backend.lucy_core.padic_ultrametric_clusterer import PadicUltrametricClustererFabric, STAGE as STAGE_248\n'
    if 'padic_ultrametric_clusterer' not in text:
        assert target_import in text, 'Target import for Stage 247 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 247: Sovereign Anti-Fragile Black-Swan Catastrophe Immunity & Stress Inverter (Era 25)\n        self.antifragile_stress_inverter = AntiFragileStressInverterFabric()\n'
    replacement_init = target_init + '        # Stage 248: Non-Archimedean p-Adic Ultrametric Cognitive Clustering (Era 25)\n        self.padic_ultrametric_clusterer = PadicUltrametricClustererFabric()\n'
    if 'self.padic_ultrametric_clusterer' not in text:
        assert target_init in text, 'Target init for Stage 247 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("antifragile_stress_inverter", "core"),\n'
    replacement_service = target_service + '            ("padic_ultrametric_clusterer", "core"),\n'
    if '("padic_ultrametric_clusterer", "core")' not in text:
        assert target_service in text, 'Target service for Stage 247 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 248 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /antifragile-transmute <severity> <domain>")\n'
    assert target in text, 'Target end of Stage 247 block not found'

    insertion = """
        # Stage 248: Non-Archimedean p-Adic Ultrametric Cognitive Clustering & Hierarchical Tree Space Embedding
        if lowered in {"/padic-status", "padic-status"}:
            if hasattr(self.runtime, "padic_ultrametric_clusterer"):
                tbl = self.runtime.padic_ultrametric_clusterer.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.padic_ultrametric_clusterer.get_metrics())
            return RouterResponse("p-Adic ultrametric clusterer not available.")

        if lowered.startswith("/padic-dist ") or lowered.startswith("padic-dist "):
            if hasattr(self.runtime, "padic_ultrametric_clusterer"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    x = int(parts[1])
                    y = int(parts[2])
                    d = self.runtime.padic_ultrametric_clusterer.ultrametric_distance(x, y)
                    msg = f"p-Adic Ultrametric Distance d_{self.runtime.padic_ultrametric_clusterer.p}({x}, {y}) = {d:.6f}"
                    return RouterResponse(msg, data={"x": x, "y": y, "distance": d, "p": self.runtime.padic_ultrametric_clusterer.p})
            return RouterResponse("Usage: /padic-dist <x_int> <y_int>")

        if lowered.startswith("/padic-triangle ") or lowered.startswith("padic-triangle "):
            if hasattr(self.runtime, "padic_ultrametric_clusterer"):
                parts = raw_text.strip().split()
                if len(parts) >= 4:
                    x, y, z = int(parts[1]), int(parts[2]), int(parts[3])
                    res = self.runtime.padic_ultrametric_clusterer.verify_strong_triangle_inequality(x, y, z)
                    msg = (
                        f"Strong Triangle Test ({x}, {y}, {z}): holds={res['strong_inequality_holds']}, "
                        f"isosceles={res['is_isosceles_ultrametric']}, sides={res['sides_sorted']}."
                    )
                    return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /padic-triangle <x_int> <y_int> <z_int>")

        if lowered.startswith("/padic-concept ") or lowered.startswith("padic-concept "):
            if hasattr(self.runtime, "padic_ultrametric_clusterer"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    name = parts[1]
                    vec = [float(v) for v in parts[2:]]
                    node = self.runtime.padic_ultrametric_clusterer.register_concept(name, vec)
                    msg = f"Registered concept '{name}' -> p-adic integer {node.padic_repr} (base {self.runtime.padic_ultrametric_clusterer.p})."
                    return RouterResponse(msg, data={"name": name, "padic_repr": node.padic_repr})
            return RouterResponse("Usage: /padic-concept <name> <val1> [val2 ...]")
"""
    if 'padic-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 248 into router.py')
    else:
        print('Stage 248 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
