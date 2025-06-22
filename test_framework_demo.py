#!/usr/bin/env python3
"""
Demo script to showcase the Mini-Mancer automated testing framework

This script demonstrates the testing framework capabilities without
requiring real bot tokens or network access.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            cwd=Path(__file__).parent,
            capture_output=True, 
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"   ✅ Success")
            return True
        else:
            print(f"   ❌ Failed (exit code: {result.returncode})")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ⏱️ Timeout after 30s")
        return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False


def main():
    """Demonstrate the testing framework"""
    print("🧪 Mini-Mancer Testing Framework Demo")
    print("=" * 50)
    
    # Set environment for demo
    env_prefix = ["env", "PYTHONPATH=."]
    
    tests = [
        {
            "cmd": env_prefix + ["uv", "run", "pytest", "--version"],
            "desc": "Check pytest installation"
        },
        {
            "cmd": env_prefix + ["uv", "run", "pytest", "tests/", "--collect-only", "-q"],
            "desc": "Collect all test cases (49 tests expected)"
        },
        {
            "cmd": env_prefix + ["uv", "run", "pytest", "tests/test_factory_bot.py::TestFactoryBotIntegration", "-v"],
            "desc": "Run integration tests (no network required)"
        },
        {
            "cmd": env_prefix + ["uv", "run", "pytest", "tests/test_integration.py::TestAPIIntegration", "-v"],
            "desc": "Run API integration tests (mocked)"
        },
        {
            "cmd": env_prefix + ["uv", "run", "pytest", "-m", "not network", "-q", "--tb=no"],
            "desc": "Run all non-network tests"
        },
        {
            "cmd": env_prefix + ["uv", "run", "pytest", "tests/", "--markers"],
            "desc": "Show available test markers"
        }
    ]
    
    results = []
    
    for test in tests:
        success = run_command(test["cmd"], test["desc"])
        results.append(success)
    
    # Summary
    print("\n📊 Demo Results Summary")
    print("=" * 30)
    
    passed = sum(results)
    total = len(results)
    
    for i, test in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"   {status} - {test['desc']}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 Testing framework is working perfectly!")
        print("\n🚀 Next steps:")
        print("   1. Set BOT_TOKEN and BOT_TOKEN_1 environment variables")
        print("   2. Set TEST_CHAT_ID and TEST_USER_ID for your test chat") 
        print("   3. Run: PYTHONPATH=. uv run pytest -m network")
        print("   4. For full testing: PYTHONPATH=. uv run pytest")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())