"""
Modern Regression Test Runner for LUCY
Runs tests for test_stageXX.py from stage start to stage end.
"""
import sys
import os
import unittest
import time

# Ensure workspace root is in sys.path
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

def run_regression(start_stage=91, end_stage=146, verbosity=1):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_dir = os.path.join(workspace_root, "tests")
    test_files = sorted([f for f in os.listdir(test_dir) if f.startswith("test_stage") and f.endswith(".py")])

    target_files = []
    for f in test_files:
        parts = f.split("_")
        if len(parts) >= 2:
            num_str = "".join([c for c in parts[1] if c.isdigit()])
            if num_str:
                num = int(num_str)
                if start_stage <= num <= end_stage:
                    target_files.append((num, f))

    target_files.sort(key=lambda x: x[0])
    
    print(f"=== LUCY MODERN REGRESSION SUITE (Stages {start_stage} -> {end_stage}) ===")
    print(f"Found {len(target_files)} target test suites.")

    for num, f in target_files:
        mod_name = f"tests.{f[:-3]}"
        try:
            mod_suite = loader.loadTestsFromName(mod_name)
            suite.addTests(mod_suite)
        except Exception as e:
            print(f"FAILED TO LOAD {mod_name}: {e}")

    runner = unittest.TextTestRunner(verbosity=verbosity)
    start_time = time.time()
    result = runner.run(suite)
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print(f"SUMMARY: Ran {result.testsRun} tests across {len(target_files)} suites in {elapsed:.3f}s")
    print(f"Errors: {len(result.errors)}, Failures: {len(result.failures)}, Skipped: {len(result.skipped)}")
    if result.wasSuccessful():
        print("STATUS: ALL TESTS PASSED SUCCESSFULLY.")
    else:
        print("STATUS: REGRESSION FAILURES DETECTED!")
    print("=" * 70)
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 91
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 146
    sys.exit(run_regression(start, end))
