# scripts/run_modern_regression.py
import os
import re
import sys
import time
import unittest

sys.path.insert(0, os.getcwd())

def main():
    test_dir = 'tests'
    files = os.listdir(test_dir)
    stage_files = []
    for f in files:
        m = re.match(r'test_stage(\d+).*\.py$', f)
        if m:
            stg = int(m.group(1))
            if 91 <= stg <= 300:
                mod_name = f'tests.{f[:-3]}'
                stage_files.append((stg, mod_name))

    stage_files.sort()
    start_stage = stage_files[0][0]
    end_stage = stage_files[-1][0]
    total_suites = len(stage_files)

    print(f"Running regression across {total_suites} test suites (Stages {start_stage}..{end_stage}):\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for _, mod in stage_files:
        s = loader.loadTestsFromName(mod)
        suite.addTests(s)

    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    elapsed = time.time() - start_time

    status = "PASS" if result.wasSuccessful() else "FAIL"
    print("\n=======================================================")
    print(f"REGRESSION RESULT: {status}")
    print(f"Total Suites : {total_suites}")
    print(f"Total Tests  : {result.testsRun}")
    print(f"Failures     : {len(result.failures)}")
    print(f"Errors       : {len(result.errors)}")
    print(f"Elapsed Time : {elapsed:.3f}s")
    print("=======================================================\n")

    if not result.wasSuccessful():
        sys.exit(1)

if __name__ == '__main__':
    main()
