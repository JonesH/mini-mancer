"""
Comprehensive Test Runner for Mini-Mancer Testing Plan
Executes all test tiers in order of decreasing relevance with detailed reporting.

Usage:
    python tests/run_comprehensive_tests.py [options]
    
    Options:
        --tier <1-5>        Run specific tier only
        --fast              Skip slow tests (no endurance tests)
        --report            Generate detailed test report
        --stop-on-fail      Stop on first failure
        --verbose           Verbose output
"""

import asyncio
import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.test_monitor import log_test_start, log_test_end, log_error


class TestTier:
    """Represents a test tier with its metadata"""
    
    def __init__(self, tier: int, name: str, priority: str, description: str, test_file: str):
        self.tier = tier
        self.name = name
        self.priority = priority
        self.description = description
        self.test_file = test_file
        self.results: Dict[str, Any] = {}


class ComprehensiveTestRunner:
    """Main test runner for all Mini-Mancer functionality tests"""
    
    def __init__(self):
        self.test_tiers = [
            TestTier(
                tier=1,
                name="Critical Core Functionality",
                priority="MUST PASS",
                description="Bot creation, command handlers, naming, media processing",
                test_file="test_tier1_critical_functionality.py"
            ),
            TestTier(
                tier=2,
                name="Essential User Experience",
                priority="High",
                description="Inline keyboard, text creation, link accessibility, error handling",
                test_file="test_tier2_user_experience.py"
            ),
            TestTier(
                tier=3,
                name="Performance & Reliability",
                priority="Medium",
                description="Rate limiting, concurrency, load testing, memory monitoring",
                test_file="test_tier3_performance_reliability.py"
            ),
            TestTier(
                tier=4,
                name="Integration & Advanced Features",
                priority="Medium-Low",
                description="OpenServ API, compilation pipeline, WebSocket monitoring",
                test_file="test_tier4_integration_advanced.py"
            ),
            TestTier(
                tier=5,
                name="Comprehensive Coverage",
                priority="Low",
                description="Edge cases, security, end-to-end integration",
                test_file="test_tier5_comprehensive_coverage.py"
            )
        ]
        
        self.overall_results = {
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "tiers_run": [],
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "success_rate": 0.0,
            "tier_results": {}
        }

    async def run_all_tiers(self, fast_mode: bool = False, stop_on_fail: bool = False, 
                           verbose: bool = False) -> Dict[str, Any]:
        """Run all test tiers in order"""
        
        print("🔬 MINI-MANCER COMPREHENSIVE TESTING SUITE")
        print("=" * 60)
        print("Testing all functionality in order of decreasing relevance")
        print()
        
        await log_test_start("comprehensive_testing_suite")
        
        self.overall_results["start_time"] = time.time()
        
        # Run each tier
        for tier in self.test_tiers:
            print(f"🎯 TIER {tier.tier}: {tier.name}")
            print(f"   Priority: {tier.priority}")
            print(f"   Coverage: {tier.description}")
            print(f"   File: {tier.test_file}")
            print()
            
            tier_success = await self._run_tier(tier, fast_mode, verbose)
            
            self.overall_results["tiers_run"].append(tier.tier)
            self.overall_results["tier_results"][tier.tier] = tier.results
            
            # Update overall statistics
            self.overall_results["total_tests"] += tier.results.get("total", 0)
            self.overall_results["passed_tests"] += tier.results.get("passed", 0)
            self.overall_results["failed_tests"] += tier.results.get("failed", 0)
            self.overall_results["skipped_tests"] += tier.results.get("skipped", 0)
            
            if not tier_success and stop_on_fail:
                print(f"❌ STOPPING: Tier {tier.tier} failed and --stop-on-fail is enabled")
                break
            
            print("-" * 60)
        
        self.overall_results["end_time"] = time.time()
        self.overall_results["duration"] = self.overall_results["end_time"] - self.overall_results["start_time"]
        
        # Calculate success rate
        if self.overall_results["total_tests"] > 0:
            self.overall_results["success_rate"] = (
                self.overall_results["passed_tests"] / self.overall_results["total_tests"] * 100
            )
        
        await log_test_end("comprehensive_testing_suite", "COMPLETED")
        
        return self.overall_results

    async def run_specific_tier(self, tier_number: int, fast_mode: bool = False, 
                               verbose: bool = False) -> Dict[str, Any]:
        """Run a specific test tier"""
        
        tier = None
        for t in self.test_tiers:
            if t.tier == tier_number:
                tier = t
                break
        
        if not tier:
            raise ValueError(f"Invalid tier number: {tier_number}")
        
        print(f"🎯 Running Tier {tier.tier}: {tier.name}")
        print(f"   Priority: {tier.priority}")
        print(f"   Coverage: {tier.description}")
        print()
        
        await log_test_start(f"tier_{tier_number}_testing")
        
        start_time = time.time()
        tier_success = await self._run_tier(tier, fast_mode, verbose)
        duration = time.time() - start_time
        
        await log_test_end(f"tier_{tier_number}_testing", "COMPLETED")
        
        return {
            "tier": tier.tier,
            "success": tier_success,
            "duration": duration,
            "results": tier.results
        }

    async def _run_tier(self, tier: TestTier, fast_mode: bool, verbose: bool) -> bool:
        """Run tests for a specific tier"""
        
        test_file_path = Path(__file__).parent / tier.test_file
        
        if not test_file_path.exists():
            print(f"❌ Test file not found: {tier.test_file}")
            tier.results = {"error": f"Test file not found: {tier.test_file}"}
            return False
        
        # Build pytest command
        pytest_cmd = [
            "python", "-m", "pytest",
            str(test_file_path),
            f"--tb=short",
            "-v" if verbose else "-q"
        ]
        
        # Add markers for fast mode
        if fast_mode:
            pytest_cmd.extend(["-m", "not slow"])
        
        # Add tier-specific markers
        pytest_cmd.extend(["-m", f"tier{tier.tier}"])
        
        try:
            print(f"⚡ Running tests: {' '.join(pytest_cmd[3:])}")
            
            # Run pytest
            result = subprocess.run(
                pytest_cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            # Parse results
            tier.results = self._parse_pytest_output(result.stdout, result.stderr, result.returncode)
            
            # Display results
            self._display_tier_results(tier)
            
            return tier.results.get("success", False)
            
        except Exception as e:
            print(f"❌ Error running tier {tier.tier}: {e}")
            tier.results = {"error": str(e)}
            await log_error(e, f"tier_{tier.tier}_execution")
            return False

    def _parse_pytest_output(self, stdout: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse pytest output to extract test results"""
        
        results = {
            "success": return_code == 0,
            "return_code": return_code,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "warnings": 0,
            "duration": 0.0,
            "stdout": stdout,
            "stderr": stderr
        }
        
        # Parse summary line
        summary_patterns = [
            r"(\d+) passed",
            r"(\d+) failed", 
            r"(\d+) skipped",
            r"(\d+) error",
            r"(\d+) warning",
            r"in ([\d.]+)s"
        ]
        
        import re
        
        for line in stdout.split('\n'):
            if 'passed' in line or 'failed' in line or 'skipped' in line:
                # Extract numbers
                passed_match = re.search(r'(\d+) passed', line)
                if passed_match:
                    results["passed"] = int(passed_match.group(1))
                
                failed_match = re.search(r'(\d+) failed', line)
                if failed_match:
                    results["failed"] = int(failed_match.group(1))
                
                skipped_match = re.search(r'(\d+) skipped', line)
                if skipped_match:
                    results["skipped"] = int(skipped_match.group(1))
                
                error_match = re.search(r'(\d+) error', line)
                if error_match:
                    results["errors"] = int(error_match.group(1))
                
                duration_match = re.search(r'in ([\d.]+)s', line)
                if duration_match:
                    results["duration"] = float(duration_match.group(1))
        
        results["total"] = results["passed"] + results["failed"] + results["skipped"] + results["errors"]
        
        return results

    def _display_tier_results(self, tier: TestTier):
        """Display results for a tier"""
        
        results = tier.results
        
        if "error" in results:
            print(f"❌ Tier {tier.tier} ERROR: {results['error']}")
            return
        
        total = results.get("total", 0)
        passed = results.get("passed", 0)
        failed = results.get("failed", 0)
        skipped = results.get("skipped", 0)
        duration = results.get("duration", 0)
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        status_emoji = "✅" if results.get("success", False) else "❌"
        
        print(f"{status_emoji} Tier {tier.tier} Results:")
        print(f"   Tests: {total} total, {passed} passed, {failed} failed, {skipped} skipped")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Duration: {duration:.2f}s")
        
        # Show tier-specific success criteria
        tier_criteria = {
            1: 100,  # Critical - must be 100%
            2: 95,   # User Experience - 95%
            3: 90,   # Performance - 90% 
            4: 80,   # Integration - 80%
            5: 70    # Comprehensive - 70%
        }
        
        expected_rate = tier_criteria.get(tier.tier, 80)
        criteria_met = success_rate >= expected_rate
        criteria_emoji = "✅" if criteria_met else "⚠️"
        
        print(f"   {criteria_emoji} Success Criteria: {success_rate:.1f}% >= {expected_rate}% ({'MET' if criteria_met else 'NOT MET'})")
        print()

    def generate_report(self) -> str:
        """Generate detailed test report"""
        
        report_lines = [
            "# MINI-MANCER COMPREHENSIVE TEST REPORT",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            "",
            f"- **Total Duration**: {self.overall_results['duration']:.2f}s",
            f"- **Tiers Executed**: {len(self.overall_results['tiers_run'])}/5",
            f"- **Total Tests**: {self.overall_results['total_tests']}",
            f"- **Overall Success Rate**: {self.overall_results['success_rate']:.1f}%",
            "",
            "### Test Distribution",
            f"- ✅ Passed: {self.overall_results['passed_tests']}",
            f"- ❌ Failed: {self.overall_results['failed_tests']}",
            f"- ⏭️ Skipped: {self.overall_results['skipped_tests']}",
            "",
            "## Tier Results",
            ""
        ]
        
        # Add tier details
        for tier in self.test_tiers:
            if tier.tier in self.overall_results["tier_results"]:
                tier_results = self.overall_results["tier_results"][tier.tier]
                
                report_lines.extend([
                    f"### Tier {tier.tier}: {tier.name}",
                    f"**Priority**: {tier.priority}",
                    f"**Coverage**: {tier.description}",
                    "",
                    f"- Tests: {tier_results.get('total', 0)}",
                    f"- Passed: {tier_results.get('passed', 0)}",
                    f"- Failed: {tier_results.get('failed', 0)}",
                    f"- Duration: {tier_results.get('duration', 0):.2f}s",
                    f"- Success Rate: {(tier_results.get('passed', 0) / max(tier_results.get('total', 1), 1) * 100):.1f}%",
                    ""
                ])
        
        # Add recommendations
        report_lines.extend([
            "## Recommendations",
            "",
            "### Priority Actions",
        ])
        
        # Analyze failed tiers
        failed_tiers = []
        for tier_num, results in self.overall_results["tier_results"].items():
            if not results.get("success", False):
                failed_tiers.append(tier_num)
        
        if failed_tiers:
            report_lines.append(f"- **CRITICAL**: Fix failures in Tier(s) {', '.join(map(str, failed_tiers))}")
        
        if self.overall_results["success_rate"] < 90:
            report_lines.append(f"- **HIGH**: Overall success rate is {self.overall_results['success_rate']:.1f}% (target: >90%)")
        
        if not failed_tiers and self.overall_results["success_rate"] >= 90:
            report_lines.append("- ✅ **EXCELLENT**: All quality gates passed!")
        
        return "\n".join(report_lines)


async def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description="Mini-Mancer Comprehensive Test Runner")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3, 4, 5], 
                       help="Run specific tier only (1-5)")
    parser.add_argument("--fast", action="store_true", 
                       help="Skip slow tests (no endurance tests)")
    parser.add_argument("--report", action="store_true",
                       help="Generate detailed test report")
    parser.add_argument("--stop-on-fail", action="store_true",
                       help="Stop on first tier failure")
    parser.add_argument("--verbose", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    try:
        if args.tier:
            # Run specific tier
            results = await runner.run_specific_tier(
                args.tier, 
                fast_mode=args.fast,
                verbose=args.verbose
            )
            
            print(f"\n🏁 Tier {args.tier} Testing Complete")
            print(f"   Success: {'✅ YES' if results['success'] else '❌ NO'}")
            print(f"   Duration: {results['duration']:.2f}s")
            
        else:
            # Run all tiers
            results = await runner.run_all_tiers(
                fast_mode=args.fast,
                stop_on_fail=args.stop_on_fail,
                verbose=args.verbose
            )
            
            print("\n🏁 COMPREHENSIVE TESTING COMPLETE")
            print("=" * 60)
            print(f"📊 FINAL RESULTS:")
            print(f"   Total Tests: {results['total_tests']}")
            print(f"   Success Rate: {results['success_rate']:.1f}%")
            print(f"   Duration: {results['duration']:.2f}s")
            print(f"   Tiers Run: {len(results['tiers_run'])}/5")
            
            # Overall status
            if results['success_rate'] >= 90:
                print(f"🎉 OVERALL STATUS: ✅ EXCELLENT")
            elif results['success_rate'] >= 80:
                print(f"⚠️ OVERALL STATUS: 🟡 GOOD")
            else:
                print(f"❌ OVERALL STATUS: 🔴 NEEDS WORK")
        
        # Generate report if requested
        if args.report:
            report = runner.generate_report()
            report_file = Path("test_report.md")
            report_file.write_text(report)
            print(f"\n📋 Detailed report saved to: {report_file}")
    
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        await log_error(e, "comprehensive_test_runner")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())