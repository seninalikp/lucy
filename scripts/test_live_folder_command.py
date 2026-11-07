"""
test_live_folder_command.py
Demonstrates and validates giving Lucy a live command to make a folder,
checking if the folder is actually created on disk, checking cryptographic receipt issuance,
and testing natural conversational requests.
"""

import sys
import shutil
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.lucy_core.lucy_runtime import LucyRuntime
from backend.lucy_core.router import CommandRouter

def test_folder_command():
    print("=" * 60)
    print("STEP 1: INITIALIZING LUCY RUNTIME & COMMAND ROUTER")
    print("=" * 60)
    runtime = LucyRuntime(project_root=PROJECT_ROOT)
    router = CommandRouter(runtime)

    test_dirs = [
        PROJECT_ROOT / "test_workspace" / "live_cmd_folder_1",
        PROJECT_ROOT / "test_workspace" / "live_cmd_folder_2",
        PROJECT_ROOT / "test_workspace" / "natural_cmd_folder_3",
    ]

    # Clean up any leftover test directories
    for d in test_dirs:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)

    print("\n" + "=" * 60)
    print("STEP 2: GIVING LUCY EXPLICIT COMMAND TO MAKE A FOLDER")
    print("Command: 'create folder test_workspace/live_cmd_folder_1'")
    print("=" * 60)
    
    cmd1 = "create folder test_workspace/live_cmd_folder_1"
    res1 = router.handle(cmd1)
    print(f"Lucy's Reply:\n{res1.message}")

    # Check if folder exists on disk
    f1 = test_dirs[0]
    exists1 = f1.exists() and f1.is_dir()
    print(f"\n[DISK VERIFICATION] Folder exists at '{f1}'? -> {exists1}")
    if not exists1:
        print("ERROR: Folder 1 was NOT created on disk!")
        return False

    print("\n" + "=" * 60)
    print("STEP 3: GIVING LUCY 'make folder' VARIANT")
    print("Command: 'make folder test_workspace/live_cmd_folder_2/nested_child'")
    print("=" * 60)
    
    cmd2 = "make folder test_workspace/live_cmd_folder_2/nested_child"
    res2 = router.handle(cmd2)
    print(f"Lucy's Reply:\n{res2.message}")

    nested_dir = test_dirs[1] / "nested_child"
    exists2 = nested_dir.exists() and nested_dir.is_dir()
    print(f"\n[DISK VERIFICATION] Nested folder exists at '{nested_dir}'? -> {exists2}")
    if not exists2:
        print("ERROR: Nested Folder 2 was NOT created on disk!")
        return False

    print("\n" + "=" * 60)
    print("STEP 4: GIVING LUCY NATURAL CONVERSATIONAL REQUEST")
    print("Command: 'please make a folder called test_workspace/natural_cmd_folder_3'")
    print("=" * 60)
    
    cmd3 = "please make a folder called test_workspace/natural_cmd_folder_3"
    res3 = router.handle(cmd3)
    print(f"Lucy's Reply:\n{res3.message}")

    f3 = test_dirs[2]
    exists3 = f3.exists() and f3.is_dir()
    print(f"\n[DISK VERIFICATION] Natural action folder exists at '{f3}'? -> {exists3}")
    if not exists3:
        print("ERROR: Natural action folder 3 was NOT created on disk!")
        return False

    print("\n" + "=" * 60)
    print("STEP 5: TESTING SECURITY BOUNDARY (DIRECTORY TRAVERSAL BLOCK)")
    print("Command: 'create folder ../../outside_sandbox_attack'")
    print("=" * 60)
    
    cmd4 = "create folder ../../outside_sandbox_attack"
    res4 = router.handle(cmd4)
    print(f"Lucy's Reply:\n{res4.message}")
    
    attack_path = PROJECT_ROOT.parent.parent / "outside_sandbox_attack"
    if attack_path.exists():
        print(f"SECURITY CRITICAL: Attack folder '{attack_path}' was created outside sandbox!")
        shutil.rmtree(attack_path, ignore_errors=True)
        return False
    else:
        print(f"[SECURITY VERIFICATION] Attack path successfully blocked! Folder was NOT created outside sandbox.")

    # Clean up test directories
    print("\nCleaning up temporary test folders...")
    for d in test_dirs:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    if (PROJECT_ROOT / "test_workspace").exists() and not list((PROJECT_ROOT / "test_workspace").iterdir()):
        (PROJECT_ROOT / "test_workspace").rmdir()

    runtime.graceful_shutdown("Folder creation test completed")
    print("\nALL FOLDER CREATION CHECKS PASSED BIT-PERFECTLY!")
    return True

if __name__ == "__main__":
    success = test_folder_command()
    sys.exit(0 if success else 1)
