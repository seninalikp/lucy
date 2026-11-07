# scripts/wire_stage215.py
# Wire Stage 215 into lucy_runtime.py and router.py
import os, sys

# Wire lucy_runtime.py
with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
    c = f.read()

imp_target = 'from backend.lucy_core.holographic_associative_memory import HolographicAssociativeMemoryFabric, STAGE as STAGE_214\n'
imp_repl = 'from backend.lucy_core.holographic_associative_memory import HolographicAssociativeMemoryFabric, STAGE as STAGE_214\nfrom backend.lucy_core.async_micro_actor_mesh import AsyncMicroActorMeshFabric, STAGE as STAGE_215\n'
if imp_target in c:
    c = c.replace(imp_target, imp_repl, 1)

init_target = '        self.holographic_memory = HolographicAssociativeMemoryFabric()\n'
init_repl = '        self.holographic_memory = HolographicAssociativeMemoryFabric()\n        # Stage 215: Async Micro-Actor Mesh (Era 22)\n        self.micro_actor_mesh = AsyncMicroActorMeshFabric()\n'
if init_target in c:
    c = c.replace(init_target, init_repl, 1)

svc_target = '            ("holographic_memory", "core"),\n'
svc_repl = '            ("holographic_memory", "core"),\n            ("micro_actor_mesh", "core"),\n'
if svc_target in c:
    c = c.replace(svc_target, svc_repl, 1)

with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Wire router.py
with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
    rc = f.read()

router_hook = '        # Stage 214: Holographic Associative Memory Fabric (Era 22)\n'
actor_router_code = '''        # Stage 215: Async Micro-Actor Mesh Fabric (Era 22)
        if lowered in {"/actor-mesh-status", "actor-mesh-status", "/micro-actor-status", "micro-actor-status"}:
            if hasattr(self.runtime, "micro_actor_mesh"):
                tbl = self.runtime.micro_actor_mesh.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.micro_actor_mesh.status())

        if lowered.startswith("/actor-spawn ") or lowered.startswith("actor-spawn "):
            prefix = "/actor-spawn " if lowered.startswith("/actor-spawn ") else "actor-spawn "
            aid = text[len(prefix):].strip()
            if hasattr(self.runtime, "micro_actor_mesh"):
                actor = self.runtime.micro_actor_mesh.spawn_actor(aid)
                msg = f"[Micro-Actor Mesh]: Spawned autonomous actor '{aid}' with active supervision."
                return RouterResponse(msg, data={"actor_id": aid, "status": actor.status.value})

        if lowered.startswith("/actor-send ") or lowered.startswith("actor-send "):
            prefix = "/actor-send " if lowered.startswith("/actor-send ") else "actor-send "
            parts = text[len(prefix):].strip().split(maxsplit=2)
            if len(parts) >= 2 and hasattr(self.runtime, "micro_actor_mesh"):
                tgt, act = parts[0], parts[1]
                payload = parts[2] if len(parts) > 2 else {}
                m = self.runtime.micro_actor_mesh.send_message(tgt, act, payload)
                msg = f"[Micro-Actor Mesh]: Dispatched message '{m.message_id}' (Action: {act}) to target '{tgt}'."
                return RouterResponse(msg, data=m.to_dict())

        if lowered in {"/actor-step", "actor-step"}:
            if hasattr(self.runtime, "micro_actor_mesh"):
                results = self.runtime.micro_actor_mesh.step_scheduler()
                msg = f"[Micro-Actor Mesh]: Scheduler execution cycle complete. Actor outputs: {results}."
                return RouterResponse(msg, data={"results": results})

'''
if router_hook in rc and 'micro_actor_mesh' not in rc:
    rc = rc.replace(router_hook, actor_router_code + router_hook, 1)
    with open('backend/lucy_core/router.py', 'w', encoding='utf-8', newline='') as f:
        f.write(rc)

print('Stage 215 successfully wired into lucy_runtime.py and router.py!')
