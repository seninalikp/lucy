"""
scripts/wire_stage227.py
Wires Stage 227 EnergyBudgetGovernorFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.topological_data_analysis import TopologicalDataAnalysisFabric, STAGE as STAGE_226\n'
    replacement_import = target_import + 'from backend.lucy_core.energy_budget_governor import EnergyBudgetGovernorFabric, STAGE as STAGE_227\n'
    if 'energy_budget_governor' not in text:
        assert target_import in text, 'Target import not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 226: Self-Supervised Topological Data Analysis & Persistent Homology Engine (Era 23)\n        self.topological_data_analysis = TopologicalDataAnalysisFabric()\n'
    replacement_init = target_init + '        # Stage 227: Autonomous Hardware Energy Budget Governor & Thermal-Joule Throttle Fabric (Era 23)\n        self.energy_budget_governor = EnergyBudgetGovernorFabric()\n'
    if 'self.energy_budget_governor' not in text:
        assert target_init in text, 'Target init not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("topological_data_analysis", "core"),\n'
    replacement_service = target_service + '            ("energy_budget_governor", "core"),\n'
    if '("energy_budget_governor", "core")' not in text:
        assert target_service in text, 'Target service not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 227 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    end_marker = '            return RouterResponse("Usage: /tda-betti <cloud_id> <epsilon>")\n'
    assert end_marker in text, 'End marker not found'

    insertion = """
        # Stage 227: Autonomous Hardware Energy Budget Governor & Thermal-Joule Throttle Fabric
        if lowered in {"/energy-status", "energy-status"}:
            if hasattr(self.runtime, "energy_budget_governor"):
                tbl = self.runtime.energy_budget_governor.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.energy_budget_governor.status())
            return RouterResponse("Energy budget governor not available.")

        if lowered.startswith("/energy-profile ") or lowered.startswith("energy-profile "):
            if hasattr(self.runtime, "energy_budget_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    p_str = parts[1].upper()
                    from backend.lucy_core.energy_budget_governor import PowerProfile
                    if hasattr(PowerProfile, p_str):
                        self.runtime.energy_budget_governor.set_profile(PowerProfile[p_str])
                        return RouterResponse(f"Energy governor power profile set to {p_str}")
                    return RouterResponse(f"Unknown power profile '{p_str}'. Valid: TURBO, NOMINAL_BALANCED, CONSERVATIVE, CRITICAL_EMERGENCY")
            return RouterResponse("Usage: /energy-profile <profile_name>")

        if lowered.startswith("/energy-workload ") or lowered.startswith("energy-workload "):
            if hasattr(self.runtime, "energy_budget_governor"):
                parts = raw_text.strip().split()
                if len(parts) >= 2:
                    tname = parts[1]
                    dur = float(parts[2]) if len(parts) >= 3 else 0.2
                    receipt = self.runtime.energy_budget_governor.execute_governed_workload(tname, workload_duration_s=dur)
                    msg = f"Workload '{tname}' executed under thermal-joule governor: {receipt.joules_consumed:.2f} Joules ({receipt.average_power_w:.1f}W avg, Peak Temp: {receipt.peak_temp_c:.1f}C)."
                    return RouterResponse(msg, data=receipt.to_dict())
            return RouterResponse("Usage: /energy-workload <task_name> [duration_s]")
"""
    if 'energy-status' not in text:
        idx = text.find(end_marker) + len(end_marker)
        text = text[:idx] + insertion + text[idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 227 into router.py')
    else:
        print('Stage 227 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
