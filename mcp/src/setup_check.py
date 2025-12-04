#!/usr/bin/env python3
"""
Setup verification script
Checks all dependencies and configurations before running MCP server
"""

import sys
import os
import json
from pathlib import Path


def check_python_version():
    """Check Python version."""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (need 3.8+)")
        return False


def check_dependencies():
    """Check required Python packages."""
    print("\n🔍 Checking dependencies...")
    
    required = {
        "pyspark": "3.5.0",
        "numpy": "1.24.0",
        "mcp": "0.9.0"
    }
    
    all_ok = True
    for package, min_version in required.items():
        try:
            if package == "pyspark":
                import pyspark
                version = pyspark.__version__
            elif package == "numpy":
                import numpy
                version = numpy.__version__
            elif package == "mcp":
                import mcp
                version = getattr(mcp, '__version__', 'unknown')
            
            print(f"   ✅ {package} {version}")
        except ImportError:
            print(f"   ❌ {package} not installed")
            all_ok = False
    
    return all_ok


def check_config_file():
    """Check if config file exists and is valid."""
    print("\n🔍 Checking configuration...")
    
    config_path = Path("config.json")
    if not config_path.exists():
        print("   ❌ config.json not found")
        return False
    
    try:
        with open(config_path) as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = ["paths", "models", "dataset"]
        for field in required_fields:
            if field not in config:
                print(f"   ❌ Missing field: {field}")
                return False
        
        print("   ✅ config.json valid")
        return True
        
    except json.JSONDecodeError:
        print("   ❌ config.json invalid JSON")
        return False


def check_paths():
    """Check if model and data paths exist."""
    print("\n🔍 Checking paths...")
    
    try:
        with open("config.json") as f:
            config = json.load(f)
        
        model_path = Path(config["paths"]["model_path"])
        data_path = Path(config["paths"]["data_path"])
        
        # Check model path
        if model_path.exists():
            print(f"   ✅ Model path: {model_path}")
            
            # Check for model directories
            models = config["models"]["available"]
            missing = []
            for model in models:
                model_dir = model_path / model
                if model_dir.exists():
                    print(f"      ✅ {model}")
                else:
                    print(f"      ⚠️  {model} (not found)")
                    missing.append(model)
            
            if missing:
                print(f"   ⚠️  Some models missing: {', '.join(missing)}")
        else:
            print(f"   ❌ Model path not found: {model_path}")
            print(f"      Update 'model_path' in config.json")
            return False
        
        # Check data path
        if data_path.exists():
            print(f"   ✅ Data path: {data_path}")
            
            # Check for data files
            train_file = data_path / config["dataset"]["train_file"]
            test_file = data_path / config["dataset"]["test_file"]
            
            if train_file.exists():
                print(f"      ✅ Training data")
            else:
                print(f"      ❌ Training data missing")
            
            if test_file.exists():
                print(f"      ✅ Test data")
            else:
                print(f"      ❌ Test data missing")
        else:
            print(f"   ❌ Data path not found: {data_path}")
            print(f"      Update 'data_path' in config.json")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking paths: {str(e)}")
        return False


def check_files():
    """Check if all required Python files exist."""
    print("\n🔍 Checking Python files...")
    
    required_files = [
        "mcp_server.py",
        "model_handler.py",
        "analytics_tools.py",
        "requirements.txt"
    ]
    
    all_ok = True
    for filename in required_files:
        if Path(filename).exists():
            print(f"   ✅ {filename}")
        else:
            print(f"   ❌ {filename} missing")
            all_ok = False
    
    return all_ok


def check_java():
    """Check Java installation (required for Spark)."""
    print("\n🔍 Checking Java...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True
        )
        
        # Java version is in stderr
        version_output = result.stderr.split('\n')[0]
        print(f"   ✅ {version_output}")
        return True
        
    except FileNotFoundError:
        print("   ❌ Java not found (required for Spark)")
        print("      Install Java 8 or 11")
        return False


def print_summary(checks):
    """Print summary of checks."""
    print("\n" + "=" * 60)
    print("SETUP VERIFICATION SUMMARY")
    print("=" * 60)
    
    total = len(checks)
    passed = sum(checks.values())
    
    print(f"\nPassed: {passed}/{total}")
    
    for check, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {check}")
    
    if passed == total:
        print("\n✨ All checks passed! Ready to run MCP server.")
        print("\n🚀 Start server with:")
        print("   python mcp_server.py")
    else:
        print("\n⚠️  Some checks failed. Please fix issues before running server.")
        print("\n📝 Common fixes:")
        print("   - Install dependencies: pip install -r requirements.txt")
        print("   - Update paths in config.json")
        print("   - Train models using spark_mllib_models.ipynb")
        print("   - Install Java: sudo apt install openjdk-11-jdk")


def main():
    """Run all verification checks."""
    print("🔧 MCP Server Setup Verification")
    print("Checking prerequisites for EMBER Malware Detection MCP Server\n")
    
    checks = {
        "Python version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Configuration": check_config_file(),
        "Paths": check_paths(),
        "Python files": check_files(),
        "Java (Spark)": check_java()
    }
    
    print_summary(checks)


if __name__ == "__main__":
    main()
