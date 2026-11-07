"""
scripts/wire_stage238.py
Wires Stage 238 ByzantineSwarmConsensusFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.photonic_optical_switch import PhotonicOpticalSwitchFabric, STAGE as STAGE_237\n'
    replacement_import = target_import + 'from backend.lucy_core.byzantine_swarm_consensus import ByzantineSwarmConsensusFabric, STAGE as STAGE_238\n'
    if 'byzantine_swarm_consensus' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 237: Autonomous Photonic Optical Neural Interconnect & Ultra-Low-Latency Switch Fabric (Era 24)\n        self.photonic_optical_switch = PhotonicOpticalSwitchFabric()\n'
    replacement_init = target_init + '        # Stage 238: Self-Healing Chaos Immunity & Byzantine Swarm Consensus Auto-Recovery (Era 24)\n        self.byzantine_swarm_consensus = ByzantineSwarmConsensusFabric()\n'
    if 'self.byzantine_swarm_consensus' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("photonic_optical_switch", "core"),\n'
    replacement_service = target_service + '            ("byzantine_swarm_consensus", "core"),\n'
    if '("byzantine_swarm_consensus", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 238 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Photonic optical switch fabric not available.")\n'
    assert target in text, 'Target end of Stage 237 block not found'

    insertion = """
        # Stage 238: Self-Healing Chaos Immunity & Byzantine Swarm Consensus Auto-Recovery
        if lowered in {"/byzantine-swarm-status", "byzantine-swarm-status"}:
            if hasattr(self.runtime, "byzantine_swarm_consensus"):
                tbl = self.runtime.byzantine_swarm_consensus.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.byzantine_swarm_consensus.status())
            return RouterResponse("Byzantine swarm consensus fabric not available.")

        if lowered.startswith("/byzantine-propose ") or lowered.startswith("byzantine-propose "):
            if hasattr(self.runtime, "byzantine_swarm_consensus"):
                parts = raw_text.strip().split(maxsplit=1)
                if len(parts) >= 2:
                    import json
                    try:
                        data = json.loads(parts[1]) if parts[1].startswith("{") else {"data": parts[1]}
                        res = self.runtime.byzantine_swarm_consensus.propose_and_reach_consensus(data)
                        msg = f"Consensus round: {res.get('status', 'FAILED')} (Seq: {res.get('sequence')}, View: {res.get('view')})."
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"Consensus proposal failed: {e}")
            return RouterResponse("Usage: /byzantine-propose <payload_json_or_text>")

        if lowered.startswith("/byzantine-crash ") or lowered.startswith("byzantine-crash "):
            if hasattr(self.runtime, "byzantine_swarm_consensus"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nid = parts[1]
                    self.runtime.byzantine_swarm_consensus.inject_chaos_node_crash(nid)
                    msg = f"Chaos injected: Node '{nid}' crashed to offline state."
                    return RouterResponse(msg, data={"node": nid, "offline": True})
            return RouterResponse("Usage: /byzantine-crash <node_id>")

        if lowered.startswith("/byzantine-recover ") or lowered.startswith("byzantine-recover "):
            if hasattr(self.runtime, "byzantine_swarm_consensus"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    nid = parts[1]
                    self.runtime.byzantine_swarm_consensus.inject_chaos_node_recovery(nid)
                    msg = f"Chaos auto-recovery: Node '{nid}' restored and synchronized with quorum."
                    return RouterResponse(msg, data={"node": nid, "offline": False})
            return RouterResponse("Usage: /byzantine-recover <node_id>")
"""
    if 'byzantine-swarm-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 238 into router.py')
    else:
        print('Stage 238 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
