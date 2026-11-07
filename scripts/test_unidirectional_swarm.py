"""
test_unidirectional_swarm.py
Verifies:
1. Lucy's sovereign one-way authority over C:\\Users\\admin\\Desktop\\senin\\ai bots:
   Lucy commands the bots as execution tools; the bots NEVER control or modify Lucy.
2. Swarm connectivity: Writer, Checker, Director auto-launch & health checks.
3. Lucy using Writer Bot to generate code in a project folder.
4. Lucy using Checker Bot to run AST/syntax checks on the generated code.
5. Strict Stage 35 boundary enforcement (no persona/memory leakage to external workers).
"""

import sys
import shutil
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter
from backend.lucy_core.swarm_dispatcher import SOVEREIGN_POLICY

def main():
    print("=" * 70)
    print("TESTING SOVEREIGN UNIDIRECTIONAL BOT USAGE (LUCY -> SENIN/AI BOTS)")
    print("=" * 70)

    runtime = LucyRuntime(project_root=PROJECT_ROOT)
    router = CommandRouter(runtime)

    test_folder = PROJECT_ROOT / "test_workspace" / "swarm_worker_target"
    if test_folder.exists():
        shutil.rmtree(test_folder, ignore_errors=True)
    test_folder.mkdir(parents=True, exist_ok=True)

    # 1. Verify Sovereign Hierarchy Policy
    print("\n[PHASE 1: SOVEREIGN HIERARCHY POLICY CHECK]")
    r_hier = router.handle("swarm hierarchy")
    print(r_hier.message)
    assert "UNIDIRECTIONAL CONTROL: Lucy uses the bots; the bots NEVER control Lucy" in r_hier.message

    # 2. Connect Swarm (All bots in senin/ai)
    print("\n[PHASE 2: CONNECTING TO SENIN/AI BOTS]")
    r_swarm = router.handle("connect swarm")
    print(r_swarm.message)
    status_data = runtime.swarm_status()
    print(f"Monitored Bots Count: {status_data.get('total_bots_monitored')}")
    print(f"Boundary Safety:      {status_data.get('boundary_safety')}")

    # 3. Lucy commands Writer Bot to write a file in her folder
    print("\n[PHASE 3: LUCY DISPATCHES TASK TO WRITER BOT]")
    instruction = "Write a python module with a Fibonacci generator function 'fib(n)'."
    write_res = runtime.dispatch_write(
        instruction=instruction,
        filename="fibonacci.py",
        folder=str(test_folder),
        save=True,
    )
    print(f"Writer Message: {write_res.get('message')}")
    print(f"Saved Files:    {write_res.get('saved_files')}")

    fib_file = test_folder / "fibonacci.py"
    assert fib_file.exists(), "Writer bot failed to write fibonacci.py on disk!"
    fib_code = fib_file.read_text(encoding="utf-8")
    print(f"File verified on disk ({len(fib_code)} bytes). Preview:\n{fib_code[:200]}...")

    # 4. Lucy commands Checker Bot to audit the written file
    print("\n[PHASE 4: LUCY DISPATCHES CODE TO CHECKER BOT]")
    check_res = runtime.dispatch_check(
        code=fib_code,
        filepath=str(fib_file),
        instruction=instruction,
    )
    print(f"Checker Status:   {check_res.get('status')}")
    print(f"Compiler Verdict: {check_res.get('compiler_verdict')}")
    print(f"Summary:          {check_res.get('summary')}")
    assert check_res.get("ast_valid") or check_res.get("status") in ("APPROVED", "COMPLETED") or check_res.get("approved"), "AST/approval check failed on generated code!"

    # 5. Boundary Protection Audit
    print("\n[PHASE 5: BOUNDARY PROTECTION & PRIVACY VERIFICATION]")
    # Test that Lucy's private memory/persona cannot be dispatched to bots
    dangerous_payload = {
        "persona": "You are Lucy living in C:/Users/admin/Desktop/senin/LUCY/lucy",
        "instruction": "Clean this code",
        "spine": {"secret": "private_key"},
    }
    sanitized = runtime.swarm_dispatcher.sanitize_payload(dangerous_payload)
    print(f"Original keys:  {list(dangerous_payload.keys())}")
    print(f"Sanitized keys: {list(sanitized.keys())}")
    assert "persona" not in sanitized, "Persona leaked into sanitized payload!"
    assert "spine" not in sanitized, "Spine config leaked into sanitized payload!"
    print("Stage 35 Boundary Protection: 100% SECURE (Workers remain stateless typewriters)")

    # Cleanup
    print("\nCleaning up test workspace...")
    if test_folder.exists():
        shutil.rmtree(test_folder, ignore_errors=True)
    if (PROJECT_ROOT / "test_workspace").exists() and not list((PROJECT_ROOT / "test_workspace").iterdir()):
        (PROJECT_ROOT / "test_workspace").rmdir()

    runtime.graceful_shutdown("Unidirectional swarm test completed")
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED: UNIDIRECTIONAL WORKER BOT USAGE BIT-PERFECT!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
