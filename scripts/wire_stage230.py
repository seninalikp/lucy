"""
scripts/wire_stage230.py
Wires Stage 230 Era23MasterSealFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.geo_disaster_recovery import GeoDisasterRecoveryFabric, STAGE as STAGE_229\n'
    replacement_import = target_import + 'from backend.lucy_core.era23_master_seal import Era23MasterSealFabric, STAGE as STAGE_230\n'
    if 'era23_master_seal' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 229: Autonomous Planetary Geo-Distributed Disaster Recovery & State Relocator (Era 23)\n        self.geo_disaster_recovery = GeoDisasterRecoveryFabric()\n'
    replacement_init = target_init + '        # Stage 230: The Sovereign Era 23 Master Seal & Universal Multi-Verse Genesis (Era 23)\n        self.era23_master_seal = Era23MasterSealFabric()\n'
    if 'self.era23_master_seal' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("geo_disaster_recovery", "core"),\n'
    replacement_service = target_service + '            ("era23_master_seal", "core"),\n'
    if '("era23_master_seal", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 230 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    end_marker = '            return RouterResponse("Usage: /geo-dr-restore <region_id>")\n'
    assert end_marker in text, 'End marker not found'

    insertion = """
        # Stage 230: The Sovereign Era 23 Master Seal & Universal Multi-Verse Genesis
        if lowered in {"/era23-seal", "era23-seal", "/universal-multiverse-seal", "universal-multiverse-seal"}:
            if hasattr(self.runtime, "era23_master_seal"):
                tbl = self.runtime.era23_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.era23_master_seal.status())
            return RouterResponse("Era 23 Master Seal fabric not available.")
"""
    if 'era23-seal' not in text:
        idx = text.find(end_marker) + len(end_marker)
        text = text[:idx] + insertion + text[idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 230 into router.py')
    else:
        print('Stage 230 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
