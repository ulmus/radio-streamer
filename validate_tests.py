#!/usr/bin/env python3
"""
Simple test validation script that checks test structure without running pytest
"""

import os
import sys
import ast
import importlib.util
from pathlib import Path


def check_test_file_structure(file_path):
    """Check if a test file has proper structure"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        
        # Check for test classes and functions
        test_classes = []
        test_functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                test_classes.append(node.name)
            elif isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                test_functions.append(node.name)
        
        return {
            'file': file_path,
            'test_classes': test_classes,
            'test_functions': test_functions,
            'valid': len(test_classes) > 0 or len(test_functions) > 0
        }
    
    except Exception as e:
        return {
            'file': file_path,
            'error': str(e),
            'valid': False
        }


def check_imports(file_path):
    """Check if imports in test file are valid"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        return imports
    
    except Exception as e:
        return [f"Error parsing imports: {e}"]


def validate_test_structure():
    """Validate the overall test structure"""
    test_dir = Path('tests')
    
    if not test_dir.exists():
        print("❌ tests/ directory not found")
        return False
    
    print("✅ tests/ directory exists")
    
    # Check for required files
    required_files = ['__init__.py', 'conftest.py']
    for file in required_files:
        file_path = test_dir / file
        if file_path.exists():
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
    
    # Check test files
    test_files = list(test_dir.glob('test_*.py'))
    print(f"\n📁 Found {len(test_files)} test files:")
    
    total_tests = 0
    valid_files = 0
    
    for test_file in test_files:
        result = check_test_file_structure(test_file)
        
        if result['valid']:
            valid_files += 1
            class_count = len(result['test_classes'])
            func_count = len(result['test_functions'])
            total_tests += class_count + func_count
            
            print(f"  ✅ {test_file.name}: {class_count} classes, {func_count} functions")
            
            # Show test classes
            for cls in result['test_classes']:
                print(f"    📋 {cls}")
        else:
            print(f"  ❌ {test_file.name}: {result.get('error', 'No tests found')}")
    
    print(f"\n📊 Summary:")
    print(f"  Valid test files: {valid_files}/{len(test_files)}")
    print(f"  Total test items: {total_tests}")
    
    return valid_files == len(test_files) and total_tests > 0


def check_pytest_config():
    """Check pytest configuration"""
    config_files = ['pytest.ini', 'pyproject.toml', 'setup.cfg']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ Found pytest config: {config_file}")
            return True
    
    print("❌ No pytest configuration found")
    return False


def check_test_dependencies():
    """Check if test dependencies are properly configured"""
    pyproject_path = Path('pyproject.toml')
    
    if not pyproject_path.exists():
        print("❌ pyproject.toml not found")
        return False
    
    try:
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        if 'test' in content and 'pytest' in content:
            print("✅ Test dependencies configured in pyproject.toml")
            return True
        else:
            print("❌ Test dependencies not properly configured")
            return False
    
    except Exception as e:
        print(f"❌ Error reading pyproject.toml: {e}")
        return False


def main():
    """Main validation function"""
    print("🧪 Radio Streamer Test Suite Validation")
    print("=" * 50)
    
    checks = [
        ("Test Structure", validate_test_structure),
        ("Pytest Config", check_pytest_config),
        ("Test Dependencies", check_test_dependencies),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n🔍 Checking {check_name}...")
        if check_func():
            passed += 1
        else:
            print(f"❌ {check_name} check failed")
    
    print(f"\n📋 Validation Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 Test suite structure is valid!")
        print("\nNext steps:")
        print("1. Install test dependencies: pip install -e .[test]")
        print("2. Run tests: python run_tests.py")
        print("3. Generate coverage: python run_tests.py --coverage")
        return True
    else:
        print("❌ Test suite needs fixes before running")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)