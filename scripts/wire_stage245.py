"""
scripts/wire_stage245.py
Wires Stage 245 OrbitalConstellationGridFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.dna_molecular_storage import DnaMolecularStorageFabric, STAGE as STAGE_244\n'
    replacement_import = target_import + 'from backend.lucy_core.orbital_constellation_grid import OrbitalConstellationGridFabric, STAGE as STAGE_245\n'
    if 'orbital_constellation_grid' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 244: Autonomous Synthetic Biology DNA/RNA Storage Codec & Transceiver (Era 25)\n        self.dna_molecular_storage = DnaMolecularStorageFabric()\n'
    replacement_init = target_init + '        # Stage 245: Hyper-Scale Neuromorphic Astro-Grid Orbital Constellation Coordinator (Era 25)\n        self.orbital_constellation_grid = OrbitalConstellationGridFabric()\n'
    if 'self.orbital_constellation_grid' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("dna_molecular_storage", "core"),\n'
    replacement_service = target_service + '            ("orbital_constellation_grid", "core"),\n'
    if '("orbital_constellation_grid", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 245 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("DNA molecular storage fabric not available.")\n'
    assert target in text, 'Target end of Stage 244 block not found'

    insertion = """
        # Stage 245: Hyper-Scale Neuromorphic Astro-Grid Orbital Constellation Coordinator
        if lowered in {"/astro-grid-status", "astro-grid-status"}:
            if hasattr(self.runtime, "orbital_constellation_grid"):
                tbl = self.runtime.orbital_constellation_grid.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.orbital_constellation_grid.status())
            return RouterResponse("Orbital constellation grid not available.")

        if lowered.startswith("/astro-isl ") or lowered.startswith("astro-isl "):
            if hasattr(self.runtime, "orbital_constellation_grid"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    s_a, s_b = parts[1], parts[2]
                    ep = float(parts[3]) if len(parts) >= 4 else 0.0
                    try:
                        res = self.runtime.orbital_constellation_grid.check_inter_satellite_link(s_a, s_b, ep)
                        status_str = f"CLEAR (Latency: {res['optical_latency_ms']} ms)" if res['line_of_sight_clear'] else "OCCULTED BY EARTH"
                        msg = f"ISL Link {s_a} <-> {s_b}: {status_str}. Distance: {res['distance_km']} km."
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"ISL calculation failed: {e}")
            return RouterResponse("Usage: /astro-isl <sat_a> <sat_b> [epoch_seconds]")

        if lowered.startswith("/astro-route ") or lowered.startswith("astro-route "):
            if hasattr(self.runtime, "orbital_constellation_grid"):
                parts = raw_text.strip().split(maxsplit=3)
                if len(parts) >= 4:
                    s_src, s_dst, payload_txt = parts[1], parts[2], parts[3]
                    try:
                        res = self.runtime.orbital_constellation_grid.route_dtn_bundle(s_src, s_dst, {"payload": payload_txt})
                        msg = f"DTN Bundle Routing: {res['status']} along path {' -> '.join(res['route'])}."
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"DTN routing failed: {e}")
            return RouterResponse("Usage: /astro-route <source_sat> <dest_sat> <payload_text>")
"""
    if 'astro-grid-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 245 into router.py')
    else:
        print('Stage 245 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
