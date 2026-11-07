"""
scripts/wire_stage231.py
Wires Stage 231 NeuromorphicSpikingFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.era23_master_seal import Era23MasterSealFabric, STAGE as STAGE_230\n'
    replacement_import = target_import + 'from backend.lucy_core.neuromorphic_spiking_fabric import NeuromorphicSpikingFabric, STAGE as STAGE_231\n'
    if 'neuromorphic_spiking_fabric' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 230: The Sovereign Era 23 Master Seal & Universal Multi-Verse Genesis (Era 23)\n        self.era23_master_seal = Era23MasterSealFabric()\n'
    replacement_init = target_init + '        # Stage 231: Neuromorphic Spiking Neural Network & LIF Synaptic Fabric (Era 24)\n        self.neuromorphic_spiking = NeuromorphicSpikingFabric()\n'
    if 'self.neuromorphic_spiking' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("era23_master_seal", "core"),\n'
    replacement_service = target_service + '            ("neuromorphic_spiking", "core"),\n'
    if '("neuromorphic_spiking", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 231 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    end_marker = '            return RouterResponse("Era 23 Master Seal fabric not available.")\n'
    assert end_marker in text, 'End marker not found'

    insertion = """
        # Stage 231: Neuromorphic Spiking Neural Network & LIF Synaptic Fabric
        if lowered in {"/snn-status", "snn-status", "/lif-status", "lif-status"}:
            if hasattr(self.runtime, "neuromorphic_spiking"):
                tbl = self.runtime.neuromorphic_spiking.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.neuromorphic_spiking.status())
            return RouterResponse("Neuromorphic spiking fabric not available.")

        if lowered in {"/snn-step", "snn-step", "/lif-step", "lif-step"}:
            if hasattr(self.runtime, "neuromorphic_spiking"):
                spikes = self.runtime.neuromorphic_spiking.step(input_currents={"in_0": 35.0})
                msg = f"Stepped neuromorphic clock (+1.0ms). Spikes fired: {spikes if spikes else 'None'}."
                return RouterResponse(msg, data={"spikes": spikes, "time_ms": self.runtime.neuromorphic_spiking.current_time_ms})
            return RouterResponse("Neuromorphic spiking fabric not available.")

        if (
            lowered.startswith("/snn-sim ")
            or lowered.startswith("snn-sim ")
            or lowered.startswith("/lif-sim ")
            or lowered.startswith("lif-sim ")
        ):
            if hasattr(self.runtime, "neuromorphic_spiking"):
                parts = raw_text.strip().split()
                dur = float(parts[1]) if len(parts) >= 2 else 20.0
                res = self.runtime.neuromorphic_spiking.run_simulation(duration_ms=dur, input_schedule={"in_0": 30.0, "in_1": 25.0})
                msg = f"Simulated {res['duration_ms']:.1f}ms: Fired {res['spikes_fired_count']} spikes across {len(res['active_neurons'])} neurons ({res['firing_rate_hz']:.1f} Hz)."
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /snn-sim <duration_ms>")
"""
    if 'snn-status' not in text:
        idx = text.find(end_marker) + len(end_marker)
        text = text[:idx] + insertion + text[idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 231 into router.py')
    else:
        print('Stage 231 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
