"""
scripts/wire_stage240.py
Wires Stage 240 Era24MasterSealFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.planetary_resource_exchange import PlanetaryResourceExchangeFabric, STAGE as STAGE_239\n'
    replacement_import = target_import + 'from backend.lucy_core.era24_master_seal import Era24MasterSealFabric, STAGE as STAGE_240\n'
    if 'era24_master_seal' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 239: Planetary Sovereign Autonomous Resource Exchange & Zero-Sum Tokenless Ledger (Era 24)\n        self.planetary_resource_exchange = PlanetaryResourceExchangeFabric()\n'
    replacement_init = target_init + '        # Stage 240: The Sovereign Era 24 Master Seal & AGI Singularity Genesis (Era 24)\n        self.era24_master_seal = Era24MasterSealFabric()\n'
    if 'self.era24_master_seal' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("planetary_resource_exchange", "core"),\n'
    replacement_service = target_service + '            ("era24_master_seal", "core"),\n'
    if '("era24_master_seal", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 240 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /resource-balance <node_id>")\n'
    assert target in text, 'Target end of Stage 239 block not found'

    insertion = """
        # Stage 240: The Sovereign Era 24 Master Seal & AGI Singularity Genesis
        if lowered in {"/era24-status", "era24-status", "/era24-seal-status"}:
            if hasattr(self.runtime, "era24_master_seal"):
                tbl = self.runtime.era24_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.era24_master_seal.status())
            return RouterResponse("Era 24 Master Seal not available.")

        if lowered in {"/era24-seal-report", "era24-seal-report", "/era24-report"}:
            if hasattr(self.runtime, "era24_master_seal"):
                rep = self.runtime.era24_master_seal.format_grand_era_report()
                return RouterResponse(rep, data=self.runtime.era24_master_seal.certificate.to_dict())
            return RouterResponse("Era 24 Master Seal not available.")

        if lowered in {"/era24-verify", "era24-verify"}:
            if hasattr(self.runtime, "era24_master_seal"):
                integ = self.runtime.era24_master_seal.verify_era24_integrity()
                status_str = "PASSED (LOCKED AND VERIFIED)" if integ["verified"] else "FAILED (INTEGRITY BREACH)"
                msg = f"Era 24 Cryptographic Verification: {status_str}. Master Merkle Root: {integ['master_merkle_root'][:16]}..."
                return RouterResponse(msg, data=integ)
            return RouterResponse("Era 24 Master Seal not available.")

        if lowered in {"/era24-manifest", "era24-manifest"}:
            if hasattr(self.runtime, "era24_master_seal"):
                manifest = self.runtime.era24_master_seal.get_stage_manifest()
                items = [f"Stage {m.stage:03d}: {m.name} [{m.sha256[:12]}...]" for m in manifest]
                msg = "\\n".join(["[Era 24 Stage Manifest: 10 Stages]"] + items)
                return RouterResponse(msg, data={"manifest": [m.to_dict() for m in manifest]})
            return RouterResponse("Era 24 Master Seal not available.")
"""
    if 'era24-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 240 into router.py')
    else:
        print('Stage 240 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
