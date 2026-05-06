#!/usr/bin/env python
"""
Test runner for MyStore services.
Runs unit tests using pytest.

NOTE: This runner only runs the test files that were updated and fixed:
- test_admin_service.py (17 tests)
- test_catalog_service.py (37 tests)
- test_utils.py (19 tests)

Other test files (order_service, payment_service, user_service, validation, 
order_processor) have pre-existing issues and were not modified in this update.

To run all tests (including ones with pre-existing failures), modify the 
test_files list in the run_tests() function.
"""

import subprocess
import sys
import os

def run_tests():
    """Run all tests using pytest."""
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Warning: Virtual environment not detected. Please activate the venv first:")
        print("  .venv\\Scripts\\activate  (Windows)")
        print("  source .venv/bin/activate  (Linux/Mac)")
        print()

    # Set PYTHONPATH to include services directory
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([
        os.path.abspath("services"),
        env.get("PYTHONPATH", "")
    ])

    print("=" * 70)
    print("Running MyStore Test Suite")
    print("=" * 70)
    print()

    # Run pytest on all test files
    test_files = [
        ("Admin Service", "tests/test_admin_service.py"),
        ("Catalog Service", "tests/test_catalog_service.py"),
        ("Order Service", "tests/test_order_service.py"),
        ("Payment Service", "tests/test_payment_service.py"),
        ("User Service", "tests/test_user_service.py"),
        ("Utils", "tests/test_utils.py"),
        ("Validation", "tests/test_validation.py"),
        ("Order Processor", "tests/test_order_processor.py")
    ]

    print(f"Running {len(test_files)} test files separately to avoid caching issues...")
    print()

    all_passed = True
    total_passed = 0
    total_failed = 0
    
    for name, test_file in test_files:
        if not os.path.exists(test_file):
            print(f"WARNING: {test_file} not found, skipping...")
            continue
            
        print(f"Running {name} tests...")
        
        # Run each file separately
        cmd = [
            sys.executable, "-m", "pytest",
            test_file,
            "-v",
            "--tb=short",
            "-q"
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        output = result.stdout + result.stderr
        
        # Extract pass/fail counts from output
        passed_count = 0
        failed_count = 0
        
        for line in output.split('\n'):
            # Look for lines like "17 passed" or "14 failed, 59 passed"
            if 'passed' in line or 'failed' in line:
                # Try to extract numbers
                import re
                passed_match = re.search(r'(\d+)\s+passed', line)
                failed_match = re.search(r'(\d+)\s+failed', line)
                
                if passed_match:
                    passed_count = int(passed_match.group(1))
                if failed_match:
                    failed_count = int(failed_match.group(1))
        
        if passed_count > 0:
            total_passed += passed_count
            print(f"  PASS: {passed_count} tests passed")
        if failed_count > 0:
            total_failed += failed_count
            all_passed = False
            print(f"  FAIL: {failed_count} tests failed")
        
        if result.returncode != 0 and failed_count == 0:
            # Test run had errors but we couldn't parse them
            all_passed = False
            print(f"  ERROR: Test run failed")
        
        print()

    print("=" * 70)
    print(f"Total: {total_passed} passed, {total_failed} failed")
    print("=" * 70)
    
    if all_passed:
        print("SUCCESS: All tests passed!")
    else:
        print("FAILURE: Some tests failed!")
    print()

    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)