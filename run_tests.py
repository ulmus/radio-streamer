#!/usr/bin/env python3
"""
Test runner for radio-streamer project

This script runs the test suite with different configurations and options.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def install_test_dependencies():
    """Install test dependencies"""
    print("Installing test dependencies...")
    cmd = [sys.executable, "-m", "pip", "install", "-e", ".[test]"]
    return run_command(cmd, "Installing test dependencies")


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests"""
    cmd = [sys.executable, "-m", "pytest", "tests/", "-m", "unit"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing"])
    
    return run_command(cmd, "Running unit tests")


def run_integration_tests(verbose=False):
    """Run integration tests"""
    cmd = [sys.executable, "-m", "pytest", "tests/", "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running integration tests")


def run_api_tests(verbose=False):
    """Run API tests"""
    cmd = [sys.executable, "-m", "pytest", "tests/test_api.py"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running API tests")


def run_streamdeck_tests(verbose=False, hardware=False):
    """Run StreamDeck tests"""
    cmd = [sys.executable, "-m", "pytest", "tests/test_streamdeck.py"]
    
    if verbose:
        cmd.append("-v")
    
    if not hardware:
        cmd.extend(["-m", "not hardware"])
    
    return run_command(cmd, "Running StreamDeck tests")


def run_all_tests(verbose=False, coverage=False, include_hardware=False):
    """Run all tests"""
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=html"])
    
    if not include_hardware:
        cmd.extend(["-m", "not hardware"])
    
    return run_command(cmd, "Running all tests")


def run_fast_tests(verbose=False):
    """Run fast tests only (exclude slow and hardware tests)"""
    cmd = [sys.executable, "-m", "pytest", "tests/", "-m", "not slow and not hardware"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running fast tests")


def run_legacy_tests():
    """Run legacy standalone test scripts for comparison"""
    print("\n" + "="*60)
    print("Running legacy test scripts for comparison")
    print("="*60)
    
    legacy_scripts = [
        "test_spotify_integration.py",
        "test_streamdeck_modular.py",
        "test_api.py"
    ]
    
    results = []
    for script in legacy_scripts:
        if os.path.exists(script):
            print(f"\nRunning legacy script: {script}")
            result = subprocess.run([sys.executable, script], capture_output=True, text=True)
            results.append((script, result.returncode == 0))
            
            if result.stdout:
                print("STDOUT:", result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr)
    
    print(f"\nLegacy test results:")
    for script, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {script}: {status}")
    
    return all(success for _, success in results)


def check_test_coverage():
    """Generate and display test coverage report"""
    cmd = [sys.executable, "-m", "pytest", "tests/", "--cov=.", "--cov-report=html", "--cov-report=term"]
    return run_command(cmd, "Generating coverage report")


def lint_tests():
    """Run linting on test files"""
    try:
        # Try to run flake8 if available
        cmd = [sys.executable, "-m", "flake8", "tests/", "--max-line-length=100"]
        return run_command(cmd, "Linting test files")
    except FileNotFoundError:
        print("flake8 not available, skipping linting")
        return True


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run radio-streamer tests")
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--streamdeck", action="store_true", help="Run StreamDeck tests only")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only")
    parser.add_argument("--legacy", action="store_true", help="Run legacy test scripts")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--lint", action="store_true", help="Lint test files")
    parser.add_argument("--hardware", action="store_true", help="Include hardware tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    success = True
    
    if args.install_deps:
        success &= install_test_dependencies()
    
    if args.unit:
        success &= run_unit_tests(args.verbose, args.coverage)
    elif args.integration:
        success &= run_integration_tests(args.verbose)
    elif args.api:
        success &= run_api_tests(args.verbose)
    elif args.streamdeck:
        success &= run_streamdeck_tests(args.verbose, args.hardware)
    elif args.fast:
        success &= run_fast_tests(args.verbose)
    elif args.legacy:
        success &= run_legacy_tests()
    elif args.coverage:
        success &= check_test_coverage()
    elif args.lint:
        success &= lint_tests()
    elif args.all or len(sys.argv) == 1:  # Default to all tests
        success &= run_all_tests(args.verbose, args.coverage, args.hardware)
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()