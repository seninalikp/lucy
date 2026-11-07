# scripts/wire_stage219.py
# Wire Stage 219 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.trans_universal_belief_mesh import TransUniversalBeliefMeshFabric, STAGE as STAGE_218\n'
imp_repl = 'from backend.lucy_core.trans_universal_belief_mesh import TransUniversalBeliefMeshFabric, STAGE as STAGE_218\nfrom backend.lucy_core.concept_synthesis_ontology import ConceptSynthesisOntologyFabric, STAGE as STAGE_219\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.belief_mesh = TransUniversalBeliefMeshFabric()\n'
init_repl = '        self.belief_mesh = TransUniversalBeliefMeshFabric()\n        # Stage 219: Concept Synthesis Ontology (Era 22)\n        self.ontology_engine = ConceptSynthesisOntologyFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("belief_mesh", "core"),\n'
svc_repl = '            ("belief_mesh", "core"),\n            ("ontology_engine", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 218: Trans-Universal Belief Propagation Mesh (Era 22)\n'
ontology_router_code = '''        # Stage 219: Concept Synthesis & Ontology Evolution Engine (Era 22)
        if lowered in {"/ontology-status", "ontology-status", "/concept-status", "concept-status"}:
            if hasattr(self.runtime, "ontology_engine"):
                tbl = self.runtime.ontology_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.ontology_engine.status())

        if lowered.startswith("/concept-add ") or lowered.startswith("concept-add "):
            prefix = "/concept-add " if lowered.startswith("/concept-add ") else "concept-add "
            parts = text[len(prefix):].strip().split(maxsplit=1)
            if len(parts) >= 1 and hasattr(self.runtime, "ontology_engine"):
                name = parts[0]
                cat = parts[1] if len(parts) > 1 else "entity"
                node = self.runtime.ontology_engine.add_concept(name, category=cat)
                msg = f"[Ontology Engine]: Registered concept '{name}' ({node.concept_id}) in category '{cat}'."
                return RouterResponse(msg, data=node.to_dict())

        if lowered.startswith("/concept-synthesize ") or lowered.startswith("concept-synthesize "):
            prefix = "/concept-synthesize " if lowered.startswith("/concept-synthesize ") else "concept-synthesize "
            parts = text[len(prefix):].strip().split()
            if len(parts) >= 2 and hasattr(self.runtime, "ontology_engine"):
                meta_name = parts[0]
                cluster_ids = parts[1:]
                meta_node = self.runtime.ontology_engine.synthesize_higher_order_concept(cluster_ids, meta_name)
                msg = f"[Ontology Engine]: Synthesized meta-concept '{meta_name}' ({meta_node.concept_id}) over {len(cluster_ids)} concepts."
                return RouterResponse(msg, data=meta_node.to_dict())

'''
if router_hook in rc and 'ontology_engine' not in rc:
    rc = rc.replace(router_hook, ontology_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 219 successfully wired into lucy_runtime.py and router.py!')
