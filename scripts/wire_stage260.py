"""
scripts/wire_stage260.py
Wires Stage 260 Era26MasterSealFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.constitutional_shapley_nash_engine import ConstitutionalShapleyNashEngineFabric, STAGE as STAGE_259\n'
    replacement_import = target_import + 'from backend.lucy_core.era26_master_seal import Era26MasterSealFabric, STAGE as STAGE_260\n'
    if 'era26_master_seal' not in text:
        assert target_import in text, 'Target import for Stage 259 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 259: Constitutional Shapley-Nash Game Engine (Era 26)\n        self.shapley_nash_engine = ConstitutionalShapleyNashEngineFabric()\n'
    replacement_init = target_init + '        # Stage 260: The Sovereign Era 26 Master Seal & Singularity Genesis (Era 26)\n        self.era26_master_seal = Era26MasterSealFabric()\n'
    if 'self.era26_master_seal' not in text:
        assert target_init in text, 'Target init for Stage 259 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("shapley_nash_engine", "core"),\n'
    replacement_service = target_service + '            ("era26_master_seal", "core"),\n'
    if '("era26_master_seal", "core")' not in text:
        assert target_service in text, 'Target service for Stage 259 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 260 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /sovereign-core-guarantee <senin_val> <agent_val1> [agent_val2 ...]")\n'
    assert target in text, 'Target end of Stage 259 block not found'

    insertion = """
        # Stage 260: The Sovereign Era 26 Master Seal & Omniscient Holomorphic Singularity Genesis
        if lowered in {"/era26-status", "era26-status"}:
            if hasattr(self.runtime, "era26_master_seal"):
                tbl = self.runtime.era26_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.era26_master_seal.status())
            return RouterResponse("Era 26 Master Seal not available.")

        if lowered in {"/era26-seal-report", "era26-seal-report"}:
            if hasattr(self.runtime, "era26_master_seal"):
                report = self.runtime.era26_master_seal.format_grand_era_report()
                return RouterResponse(report, data=self.runtime.era26_master_seal.status())
            return RouterResponse("Era 26 Master Seal not available.")

        if lowered in {"/era26-verify", "era26-verify"}:
            if hasattr(self.runtime, "era26_master_seal"):
                ver = self.runtime.era26_master_seal.verify_era26_integrity()
                msg = (
                    f"Era 26 Integrity Verification: valid={ver['verified']}, "
                    f"Stages={ver['stages_verified']}, Master Merkle Root={ver['master_merkle_root'][:16]}..."
                )
                return RouterResponse(msg, data=ver)
            return RouterResponse("Era 26 Master Seal not available.")

        if lowered in {"/era26-manifest", "era26-manifest"}:
            if hasattr(self.runtime, "era26_master_seal"):
                manifest = self.runtime.era26_master_seal.get_stage_manifest()
                lines = ["Era 26 Stage Manifest (Stages 251 - 260):"]
                for m in manifest:
                    lines.append(f"Stage {m.stage}: {m.name} -> {m.sha256[:16]}... [{m.status}]")
                return RouterResponse("\\n".join(lines), data=[m.to_dict() for m in manifest])
            return RouterResponse("Era 26 Master Seal not available.")
"""
    if 'era26-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 260 into router.py')
    else:
        print('Stage 260 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
