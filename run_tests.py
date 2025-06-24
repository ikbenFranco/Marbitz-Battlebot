#!/usr/bin/env python
"""
Script to run tests for Marbitz Battlebot.
"""

import os
import sys
import subprocess

def run_tests():
    """Run the test suite."""
    print("Running Marbitz Battlebot tests...")
    
    # Run pytest with coverage
    result = subprocess.run(
        ["pytest", "--cov=marbitz_battlebot", "--cov-report=term-missing"],
        capture_output=True,
        text=True
    )
    
    # Print the output
    print(result.stdout)
    
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    # Return the exit code
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())