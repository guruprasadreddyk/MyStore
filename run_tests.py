#!/usr/bin/env python
"""
Simple script to run all unit tests for MyStore services.
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
        return

    # Run pytest on all test files
    test_files = [
        "tests/test_product_service.py",
        "tests/test_cart_service.py",
        "tests/test_order_service.py",
        "tests/test_payment_service.py",
        "tests/test_search_service.py"
    ]

    print("Running unit tests for MyStore services...")
    print("=" * 50)

    total_passed = 0
    total_failed = 0

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\nRunning {test_file}...")
            result = subprocess.run([sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                                  capture_output=True, text=True)

            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            # Parse results
            lines = result.stdout.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('===') and 'passed' in line and 'failed' in line:
                    # Format: "=== 3 failed, 5 passed in 1.23s ==="
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed':
                            try:
                                total_passed += int(parts[i-1])
                            except (ValueError, IndexError):
                                pass
                        elif part == 'failed':
                            try:
                                total_failed += int(parts[i-1])
                            except (ValueError, IndexError):
                                pass
                    break
                elif line.startswith('===') and 'passed' in line and 'failed' not in line:
                    # Format: "=== 5 passed in 1.44s ==="
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed':
                            try:
                                total_passed += int(parts[i-1])
                            except (ValueError, IndexError):
                                pass
                    break
        else:
            print(f"Test file {test_file} not found!")

    print("\n" + "=" * 50)
    print(f"Test Summary: {total_passed} passed, {total_failed} failed")
    print("=" * 50)

    return total_failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)