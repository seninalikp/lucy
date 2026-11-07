"""
scripts/wire_stage236.py
Wires Stage 236 TemporalChronoGovernorFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.epistemic_logic_mesh import EpistemicLogicMeshFabric, STAGE as STAGE_235\n'
    replacement_import = target_import + 'from backend.lucy_core.temporal_chrono_governor import TemporalChronoGovernorFabric, STAGE as STAGE_236\n'
    if 'temporal_chrono_governor' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 235: Decentralized Multi-Agent Epistemic Logic & Dynamic Common Knowledge Mesh (Era 24)\n        self.epistemic_logic_mesh = EpistemicLogicMeshFabric()\n'
    replacement_init = target_init + '        # Stage 236: Autonomous Temporal Chrono-State Engine & Causality Inversion Governor (Era 24)\n        self.temporal_chrono_governor = TemporalChronoGovernorFabric()\n'
    if 'self.temporal_chrono_governor' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("epistemic_logic_mesh", "core"),\n'
    replacement_service = target_service + '            ("temporal_chrono_governor", "core"),\n'
    if '("temporal_chrono_governor", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 236 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /epistemic-verify-common <proposition>")\n'
    assert target in text, 'Target end of Stage 235 block not found'

    insertion = """
        # Stage 236: Autonomous Temporal Chrono-State Engine & Causality Inversion Governor
        if lowered in {"/temporal-chrono-status", "temporal-chrono-status", "/causality-governor-status"}:
            if hasattr(self.runtime, "temporal_chrono_governor"):
                tbl = self.runtime.temporal_chrono_governor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.temporal_chrono_governor.status())
            return RouterResponse("Temporal chrono governor not available.")

        if lowered.startswith("/temporal-commit ") or lowered.startswith("temporal-commit "):
            if hasattr(self.runtime, "temporal_chrono_governor"):
                parts = raw_text.strip().split(maxsplit=2)
                if len(parts) >= 3:
                    timeline_id = parts[1]
                    kv_pair = parts[2]
                    if "=" in kv_pair:
                        k, v = kv_pair.split("=", 1)
                        try:
                            if "." in v:
                                val = float(v)
                            else:
                                val = int(v)
                        except ValueError:
                            val = v
                        try:
                            evt = self.runtime.temporal_chrono_governor.commit_event(timeline_id, {k: val})
                            msg = f"Committed Chrono Event '{evt.event_id}' to timeline '{timeline_id}' at Tick {evt.logical_tick}."
                            return RouterResponse(msg, data={"event_id": evt.event_id, "tick": evt.logical_tick, "state_delta": {k: val}})
                        except Exception as e:
                            return RouterResponse(f"Temporal commit failed: {e}")
            return RouterResponse("Usage: /temporal-commit <timeline_id> <key=value>")

        if lowered.startswith("/temporal-fork ") or lowered.startswith("temporal-fork "):
            if hasattr(self.runtime, "temporal_chrono_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    src, dst = parts[1], parts[2]
                    try:
                        self.runtime.temporal_chrono_governor.fork_timeline(src, dst)
                        msg = f"Forked timeline '{dst}' from '{src}'."
                        return RouterResponse(msg, data={"source_timeline": src, "new_timeline": dst})
                    except Exception as e:
                        return RouterResponse(f"Temporal fork failed: {e}")
            return RouterResponse("Usage: /temporal-fork <source_timeline> <new_timeline>")

        if lowered.startswith("/temporal-rollback ") or lowered.startswith("temporal-rollback "):
            if hasattr(self.runtime, "temporal_chrono_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    tl_id, target_evt = parts[1], parts[2]
                    try:
                        res = self.runtime.temporal_chrono_governor.invert_causality_and_rollback(tl_id, target_evt)
                        msg = f"Causality inverted! Timeline '{tl_id}' rolled back to '{target_evt}'. Pruned events: {res['pruned_events_count']}."
                        return RouterResponse(msg, data=res)
                    except Exception as e:
                        return RouterResponse(f"Temporal rollback failed: {e}")
            return RouterResponse("Usage: /temporal-rollback <timeline_id> <event_id>")
"""
    if 'temporal-chrono-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 236 into router.py')
    else:
        print('Stage 236 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
