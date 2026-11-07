"""
scripts/wire_stage259.py
Wires Stage 259 ConstitutionalShapleyNashEngineFabric into lucy_runtime.py and router.py
"""

def wire_runtime():
    with open('backend/lucy_core/lucy_runtime.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target_import = 'from backend.lucy_core.relativistic_chrono_synchronizer import RelativisticChronoSynchronizerFabric, STAGE as STAGE_258\n'
    replacement_import = target_import + 'from backend.lucy_core.constitutional_shapley_nash_engine import ConstitutionalShapleyNashEngineFabric, STAGE as STAGE_259\n'
    if 'constitutional_shapley_nash_engine' not in text:
        assert target_import in text, 'Target import for Stage 258 not found'
        text = text.replace(target_import, replacement_import, 1)

    target_init = '        # Stage 258: Relativistic Astro-Chronometric Synchronizer (Era 26)\n        self.chrono_synchronizer = RelativisticChronoSynchronizerFabric()\n'
    replacement_init = target_init + '        # Stage 259: Constitutional Shapley-Nash Game Engine (Era 26)\n        self.shapley_nash_engine = ConstitutionalShapleyNashEngineFabric()\n'
    if 'self.shapley_nash_engine' not in text:
        assert target_init in text, 'Target init for Stage 258 not found'
        text = text.replace(target_init, replacement_init, 1)

    target_service = '            ("chrono_synchronizer", "core"),\n'
    replacement_service = target_service + '            ("shapley_nash_engine", "core"),\n'
    if '("shapley_nash_engine", "core")' not in text:
        assert target_service in text, 'Target service for Stage 258 not found'
        text = text.replace(target_service, replacement_service, 1)

    with open('backend/lucy_core/lucy_runtime.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Successfully wired Stage 259 into lucy_runtime.py')


def wire_router():
    with open('backend/lucy_core/router.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = '            return RouterResponse("Usage: /clock-sync <raw_clock_sec> <altitude_km> <elapsed_days> [body]")\n'
    assert target in text, 'Target end of Stage 258 block not found'

    insertion = """
        # Stage 259: Autonomous Sovereign Multi-Agent Constitutional Game-Theoretic Shapley-Nash Equilibrium Engine
        if lowered in {"/shapley-nash-status", "shapley-nash-status", "/game-theory-status", "game-theory-status"}:
            if hasattr(self.runtime, "shapley_nash_engine"):
                tbl = self.runtime.shapley_nash_engine.format_ascii_status()
                return RouterResponse(tbl, data=self.runtime.shapley_nash_engine.get_metrics())
            return RouterResponse("Shapley-Nash engine not available.")

        if lowered.startswith("/shapley-majority ") or lowered.startswith("shapley-majority "):
            if hasattr(self.runtime, "shapley_nash_engine"):
                parts = raw_text.strip().split()
                agents = parts[1:] if len(parts) >= 2 else ["Senin", "Subagent_1", "Subagent_2"]
                # Majority rule game
                res = self.runtime.shapley_nash_engine.compute_shapley_values(
                    agents,
                    lambda s: 1.0 if len(s) >= (len(agents) // 2 + 1) else 0.0
                )
                msg = f"Shapley Majority Allocation ({len(agents)} agents): " + ", ".join(f"{k}={v:.4f}" for k, v in res.items())
                return RouterResponse(msg, data=res)
            return RouterResponse("Usage: /shapley-majority [agent1 agent2 ...]")

        if lowered in {"/nash-prisoners-dilemma", "nash-prisoners-dilemma"}:
            if hasattr(self.runtime, "shapley_nash_engine"):
                players = ["P1", "P2"]
                actions = {"P1": ["Cooperate", "Defect"], "P2": ["Cooperate", "Defect"]}
                payoffs = {
                    ("Cooperate", "Cooperate"): {"P1": 3.0, "P2": 3.0},
                    ("Cooperate", "Defect"): {"P1": 0.0, "P2": 5.0},
                    ("Defect", "Cooperate"): {"P1": 5.0, "P2": 0.0},
                    ("Defect", "Defect"): {"P1": 1.0, "P2": 1.0},
                }
                psne = self.runtime.shapley_nash_engine.find_pure_strategy_nash_equilibria(players, actions, payoffs)
                msg = f"Prisoner's Dilemma Nash Equilibrium: {psne[0]['strategy']} -> Payoffs: {psne[0]['payoffs']}"
                return RouterResponse(msg, data=psne)
            return RouterResponse("Shapley-Nash engine not available.")

        if lowered.startswith("/sovereign-core-guarantee ") or lowered.startswith("sovereign-core-guarantee "):
            if hasattr(self.runtime, "shapley_nash_engine"):
                parts = raw_text.strip().split()
                if len(parts) >= 3:
                    senin_val = float(parts[1])
                    alloc = {"Senin": senin_val}
                    for i, p in enumerate(parts[2:]):
                        alloc[f"Agent_{i+1}"] = float(p)
                    guaranteed = self.runtime.shapley_nash_engine.enforce_constitutional_sovereign_guarantee(alloc)
                    msg = "Constitutional Core Guarantee: " + ", ".join(f"{k}={v:.2f}" for k, v in guaranteed.items())
                    return RouterResponse(msg, data=guaranteed)
            return RouterResponse("Usage: /sovereign-core-guarantee <senin_val> <agent_val1> [agent_val2 ...]")
"""
    if 'shapley-nash-status' not in text:
        last_idx = text.rfind(target) + len(target)
        text = text[:last_idx] + insertion + text[last_idx:]
        with open('backend/lucy_core/router.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print('Successfully wired Stage 259 into router.py')
    else:
        print('Stage 259 already in router.py')


if __name__ == '__main__':
    wire_runtime()
    wire_router()
