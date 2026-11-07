"""
scripts/wire_stage229.py
Wires Stage 229 GeoDisasterRecoveryFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.hyperdimensional_computing import HyperdimensionalComputingFabric, STAGE as STAGE_228\n'
    replacement_import = target_import + 'from backend.lucy_core.geo_disaster_recovery import GeoDisasterRecoveryFabric, STAGE as STAGE_229\n'
    if 'geo_disaster_recovery' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 228: High-Dimensional Hyperdimensional Computing & Vector Symbolic Architecture (Era 23)\n        self.hyperdimensional_computing = HyperdimensionalComputingFabric()\n'
    replacement_init = target_init + '        # Stage 229: Autonomous Planetary Geo-Distributed Disaster Recovery & State Relocator (Era 23)\n        self.geo_disaster_recovery = GeoDisasterRecoveryFabric()\n'
    if 'self.geo_disaster_recovery' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("hyperdimensional_computing", "core"),\n'
    replacement_service = target_service + '            ("geo_disaster_recovery", "core"),\n'
    if '("geo_disaster_recovery", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 229 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    end_marker = '                return RouterResponse(msg, data={"analogy": "Dollar:USA :: ?:Mexico", "solution": best_cand, "similarity": sim})\n            return RouterResponse("Hyperdimensional computing fabric not available.")\n'
    assert end_marker in text, 'End marker not found'

    insertion = """
        # Stage 229: Autonomous Planetary Geo-Distributed Disaster Recovery & State Relocator
        if lowered in {"/geo-dr-status", "geo-dr-status"}:
            if hasattr(self.runtime, "geo_disaster_recovery"):
                tbl = self.runtime.geo_disaster_recovery.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.geo_disaster_recovery.status())
            return RouterResponse("Geo-disaster recovery fabric not available.")

        if lowered.startswith("/geo-dr-replicate ") or lowered.startswith("geo-dr-replicate "):
            if hasattr(self.runtime, "geo_disaster_recovery"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    k, v = parts[1], parts[2]
                    try:
                        seq = self.runtime.geo_disaster_recovery.replicate_state({k: v})
                        msg = f"Replicated state {{{k}: {v}}} across planetary quorum at Seq #{seq}."
                        return RouterResponse(msg, data={"seq": seq, "key": k, "val": v})
                    except Exception as e:
                        return RouterResponse(f"Replication failed: {e}")
            return RouterResponse("Usage: /geo-dr-replicate <key> <val>")

        if lowered.startswith("/geo-dr-disaster ") or lowered.startswith("geo-dr-disaster "):
            if hasattr(self.runtime, "geo_disaster_recovery"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    rid = parts[1]
                    try:
                        self.runtime.geo_disaster_recovery.trigger_disaster(rid)
                        new_prim = self.runtime.geo_disaster_recovery.primary_region_id
                        msg = f"Simulated disaster on region '{rid}'. Current active primary: '{new_prim}'."
                        return RouterResponse(msg, data={"disaster_region": rid, "new_primary": new_prim})
                    except Exception as e:
                        return RouterResponse(f"Disaster simulation failed: {e}")
            return RouterResponse("Usage: /geo-dr-disaster <region_id>")

        if lowered.startswith("/geo-dr-restore ") or lowered.startswith("geo-dr-restore "):
            if hasattr(self.runtime, "geo_disaster_recovery"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    rid = parts[1]
                    try:
                        self.runtime.geo_disaster_recovery.restore_region(rid)
                        msg = f"Restored region '{rid}' and synchronized state from primary '{self.runtime.geo_disaster_recovery.primary_region_id}'."
                        return RouterResponse(msg, data={"restored_region": rid})
                    except Exception as e:
                        return RouterResponse(f"Restoration failed: {e}")
            return RouterResponse("Usage: /geo-dr-restore <region_id>")
"""
    if 'geo-dr-status' not in text:
        idx = text.find(end_marker) + len(end_marker)
        text = text[:idx] + insertion + text[idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 229 into router.py')
    else:
        print('Stage 229 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
