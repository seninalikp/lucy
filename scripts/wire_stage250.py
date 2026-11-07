"""
scripts/wire_stage250.py
Wires Stage 250 Era25MasterSealFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.zero_trust_hardware_enclave import ZeroTrustHardwareEnclaveFabric, STAGE as STAGE_249\n'
    replacement_import = target_import + 'from backend.lucy_core.era25_master_seal import Era25MasterSealFabric, STAGE as STAGE_250\n'
    if 'era25_master_seal' not in text:
        assert target_import in text, 'Target import for Stage 249 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 249: Universal Multi-Tier Zero-Trust Hardware Enclave (Era 25)\n        self.zero_trust_hardware_enclave = ZeroTrustHardwareEnclaveFabric()\n'
    replacement_init = target_init + '        # Stage 250: The Sovereign Era 25 Master Seal & Cosmic Core Genesis (Era 25)\n        self.era25_master_seal = Era25MasterSealFabric()\n'
    if 'self.era25_master_seal' not in text:
        assert target_init in text, 'Target init for Stage 249 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("zero_trust_hardware_enclave", "core"),\n'
    replacement_service = target_service + '            ("era25_master_seal", "core"),\n'
    if '("era25_master_seal", "core")' not in text:
        assert target_service in text, 'Target service for Stage 249 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 250 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /enclave-seal <secret_string>")\n'
    assert target in text, 'Target end of Stage 249 block not found'

    insertion = """
        # Stage 250: The Sovereign Era 25 Master Seal & Trans-Singularity Cosmic Core Genesis
        if lowered in {"/era25-status", "era25-status"}:
            if hasattr(self.runtime, "era25_master_seal"):
                tbl = self.runtime.era25_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.era25_master_seal.status())
            return RouterResponse("Era 25 Master Seal not available.")

        if lowered in {"/era25-seal-report", "era25-seal-report"}:
            if hasattr(self.runtime, "era25_master_seal"):
                report = self.runtime.era25_master_seal.format_grand_era_report()
                return RouterResponse(report, data=self.runtime.era25_master_seal.status())
            return RouterResponse("Era 25 Master Seal not available.")

        if lowered in {"/era25-verify", "era25-verify"}:
            if hasattr(self.runtime, "era25_master_seal"):
                ver = self.runtime.era25_master_seal.verify_era25_integrity()
                msg = (
                    f"Era 25 Integrity Verification: valid={ver['verified']}, "
                    f"Stages={ver['stages_verified']}, Master Merkle Root={ver['master_merkle_root'][:16]}..."
                )
                return RouterResponse(msg, data=ver)
            return RouterResponse("Era 25 Master Seal not available.")

        if lowered in {"/era25-manifest", "era25-manifest"}:
            if hasattr(self.runtime, "era25_master_seal"):
                manifest = self.runtime.era25_master_seal.get_stage_manifest()
                lines = ["Era 25 Stage Manifest (Stages 241 - 250):"]
                for m in manifest:
                    lines.append(f"Stage {m.stage}: {m.name} -> {m.sha256[:16]}... [{m.status}]")
                return RouterResponse("\\n".join(lines), data=[m.to_dict() for m in manifest])
            return RouterResponse("Era 25 Master Seal not available.")
"""
    if 'era25-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 250 into router.py')
    else:
        print('Stage 250 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
