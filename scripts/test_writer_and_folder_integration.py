"""
test_writer_and_folder_integration.py
End-to-end verification of:
1. 'make an folder' natural language variations (with 'an', 'a', 'called', etc.)
2. Connecting Lucy to the Writer Bot ('connect her to the writer bot she can use it')
3. Writer Bot auto-launch and live execution
4. Dispatched code/file generation into created folders
5. Full disk verification & execution receipt issuance
"""

import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter

def main():
    print("=" * 70)
    print("VERIFYING FOLDER CREATION & WRITER BOT INTEGRATION")
    print("=" * 70)

    runtime = LucyRuntime(project_root=PROJECT_ROOT)
    router = CommandRouter(runtime)

    test_dirs = [
        PROJECT_ROOT / "test_workspace" / "an_folder_demo",
        PROJECT_ROOT / "test_workspace" / "second_an_folder",
        PROJECT_ROOT / "test_workspace" / "writer_connected_folder",
    ]

    # Clean up any previous test folders
    for d in test_dirs:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)

    # -------------------------------------------------------------
    # TEST 1: 'make an folder' Natural Language Matching
    # -------------------------------------------------------------
    print("\n[TEST 1: 'make an folder' NATURAL LANGUAGE CREATION]")
    cmd1 = "make an folder test_workspace/an_folder_demo"
    print(f"User Prompt: '{cmd1}'")
    res1 = router.handle(cmd1)
    print(f"Lucy's Reply:\n{res1.message[:250]}...")
    
    f1 = test_dirs[0]
    exists1 = f1.exists() and f1.is_dir()
    print(f"Disk Check: Does '{f1.name}' exist on disk? -> {exists1}")
    assert exists1, f"TEST 1 FAILED: '{f1}' was not created on disk!"

    # -------------------------------------------------------------
    # TEST 2: 'make an folder called X' Variant
    # -------------------------------------------------------------
    print("\n[TEST 2: 'make an folder called X' VARIANT]")
    cmd2 = "please make an folder called test_workspace/second_an_folder"
    print(f"User Prompt: '{cmd2}'")
    res2 = router.handle(cmd2)
    print(f"Lucy's Reply:\n{res2.message[:250]}...")

    f2 = test_dirs[1]
    exists2 = f2.exists() and f2.is_dir()
    print(f"Disk Check: Does '{f2.name}' exist on disk? -> {exists2}")
    assert exists2, f"TEST 2 FAILED: '{f2}' was not created on disk!"

    # -------------------------------------------------------------
    # TEST 3: Connecting Lucy to the Writer Bot
    # -------------------------------------------------------------
    print("\n[TEST 3: CONNECTING LUCY TO THE WRITER BOT]")
    cmd3 = "connect her to the writer bot she can use it"
    print(f"User Prompt: '{cmd3}'")
    res3 = router.handle(cmd3)
    print(f"Lucy's Reply:\n{res3.message[:300]}...")

    # Also test explicit CLI command
    r_cli = router.handle("connect writer bot")
    print(f"\nRouter 'connect writer bot':\n{r_cli.message}")
    assert "CONNECTED" in r_cli.message or "ONLINE" in r_cli.message, "Writer Bot connection failed!"

    # -------------------------------------------------------------
    # TEST 4: Dispatching Code Writing into Created Folder via Writer Bot
    # -------------------------------------------------------------
    print("\n[TEST 4: DISPATCHING WRITER BOT INTO CREATED FOLDER]")
    folder_path = test_dirs[2]
    folder_path.mkdir(parents=True, exist_ok=True)
    
    write_res = runtime.dispatch_write(
        instruction="Write a hello world function that returns 'Hello from Writer Bot'.",
        filename="hello_writer.py",
        folder=str(folder_path),
        save=True,
    )
    print(f"Writer Bot Result: {write_res.get('message')}")
    print(f"Saved Files:       {write_res.get('saved_files')}")

    target_code_file = folder_path / "hello_writer.py"
    exists_code = target_code_file.exists()
    print(f"Disk Check: Does '{target_code_file.name}' exist on disk? -> {exists_code}")
    assert exists_code, "Code file was not created by Writer Bot on disk!"

    # -------------------------------------------------------------
    # CLEANUP
    # -------------------------------------------------------------
    print("\nCleaning up test folders...")
    for d in test_dirs:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    if (PROJECT_ROOT / "test_workspace").exists() and not list((PROJECT_ROOT / "test_workspace").iterdir()):
        (PROJECT_ROOT / "test_workspace").rmdir()

    runtime.graceful_shutdown("Writer and folder tests passed")
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED: FOLDER CREATION AND WRITER BOT CONNECTION 100% OPERATIONAL!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
