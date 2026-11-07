# scripts/wire_stage220.py
# Wire Stage 220 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.concept_synthesis_ontology import ConceptSynthesisOntologyFabric, STAGE as STAGE_219\n'
imp_repl = 'from backend.lucy_core.concept_synthesis_ontology import ConceptSynthesisOntologyFabric, STAGE as STAGE_219\nfrom backend.lucy_core.era22_master_seal import Era22MasterSealFabric, STAGE as STAGE_220\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.ontology_engine = ConceptSynthesisOntologyFabric()\n'
init_repl = '        self.ontology_engine = ConceptSynthesisOntologyFabric()\n        # Stage 220: Era 22 Master Seal & Galactic Hyper-Mesh (Era 22)\n        self.era22_master_seal = Era22MasterSealFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("ontology_engine", "core"),\n'
svc_repl = '            ("ontology_engine", "core"),\n            ("era22_master_seal", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 219: Concept Synthesis & Ontology Evolution Engine (Era 22)\n'
seal_router_code = '''        # Stage 220: Era 22 Sovereign Master Seal & Galactic Hyper-Mesh Genesis
        if lowered in {"/era22-seal", "era22-seal", "/galactic-hyper-mesh-seal", "galactic-hyper-mesh-seal"}:
            if hasattr(self.runtime, "era22_master_seal"):
                tbl = self.runtime.era22_master_seal.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.era22_master_seal.status())

        if lowered in {"/era22-audit", "era22-audit", "/galactic-audit", "galactic-audit"}:
            if hasattr(self.runtime, "era22_master_seal"):
                report = self.runtime.era22_master_seal.format_grand_era_report()
                return RouterResponse(report, data=self.runtime.era22_master_seal.status())

'''
if router_hook in rc and 'era22_master_seal' not in rc:
    rc = rc.replace(router_hook, seal_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 220 successfully wired into lucy_runtime.py and router.py!')
