#!/usr/bin/env python3
"""
Event Loop Stress Test - Expose Hidden Problems

This stress test is designed to expose hidden event loop problems by:
1. Creating multiple concurrent loads
2. Monitoring for blocking calls
3. Testing database connection limits  
4. Detecting memory leaks and task failures
"""

import asyncio
import json
import logging
import random
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import httpx
import psutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from event_loop_monitor import start_monitoring, get_health_report, global_monitor
except ImportError:
    print("❌ Event loop monitor not available")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventLoopStressTest:
    """Comprehensive event loop stress testing"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = "http://localhost:14159"
        self.test_results = []
        self.start_time = time.time()
        
    async def __aenter__(self):
        await start_monitoring("stress_test_loop")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    async def test_health_endpoint_load(self, concurrent_requests: int = 50):
        """Test health endpoint under load to detect blocking"""
        logger.info(f"🔥 Testing health endpoint with {concurrent_requests} concurrent requests")
        
        async def make_request(request_id: int):
            start_time = time.time()
            try:
                response = await self.client.get(f"{self.base_url}/health")
                duration = time.time() - start_time
                
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration,
                    "success": True
                }
            except Exception as e:
                duration = time.time() - start_time
                return {
                    "request_id": request_id,
                    "error": str(e),
                    "duration": duration,
                    "success": False
                }
        
        # Launch concurrent requests
        tasks = [make_request(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if not isinstance(r, dict)]
        
        durations = [r["duration"] for r in successful]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        result = {
            "test": "health_endpoint_load",
            "concurrent_requests": concurrent_requests,
            "successful": len(successful),
            "failed": len(failed),
            "exceptions": len(exceptions),
            "avg_duration": avg_duration,
            "max_duration": max_duration,
            "slow_requests": len([d for d in durations if d > 2.0])
        }
        
        logger.info(f"✅ Health endpoint test: {len(successful)}/{concurrent_requests} successful")
        if max_duration > 5.0:
            logger.warning(f"⚠️  Slow responses detected (max: {max_duration:.2f}s)")
        
        self.test_results.append(result)
        return result
        
    async def test_agno_call_simulation(self, concurrent_calls: int = 20):
        """Simulate concurrent Agno calls to detect blocking"""
        logger.info(f"🧠 Testing simulated Agno calls with {concurrent_calls} concurrent calls")
        
        async def simulate_agno_work(call_id: int):
            """Simulate work that might block the event loop"""
            start_time = time.time()
            
            # Simulate different types of potentially blocking work
            work_type = random.choice(["cpu_intensive", "io_wait", "mixed"])
            
            try:
                if work_type == "cpu_intensive":
                    # Simulate CPU-intensive work (should not block if done properly)
                    await asyncio.sleep(0.1)  # Simulate some async work
                    # Simulate CPU work in thread pool
                    loop = asyncio.get_running_loop()
                    with ThreadPoolExecutor() as executor:
                        await loop.run_in_executor(executor, lambda: sum(range(100000)))
                        
                elif work_type == "io_wait":
                    # Simulate I/O wait (database, API calls)
                    await asyncio.sleep(random.uniform(0.1, 1.0))
                    
                else:  # mixed
                    await asyncio.sleep(0.05)
                    # Some CPU work
                    with ThreadPoolExecutor() as executor:
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(executor, lambda: sum(range(50000)))
                    await asyncio.sleep(0.05)
                
                duration = time.time() - start_time
                return {
                    "call_id": call_id,
                    "work_type": work_type,
                    "duration": duration,
                    "success": True
                }
                
            except Exception as e:
                duration = time.time() - start_time
                return {
                    "call_id": call_id,
                    "work_type": work_type,
                    "duration": duration,
                    "error": str(e),
                    "success": False
                }
        
        # Launch concurrent simulated calls
        tasks = [simulate_agno_work(i) for i in range(concurrent_calls)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
        
        durations = [r["duration"] for r in successful]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        result = {
            "test": "agno_call_simulation",
            "concurrent_calls": concurrent_calls,
            "successful": len(successful),
            "failed": len(failed),
            "avg_duration": avg_duration,
            "max_duration": max_duration,
            "slow_calls": len([d for d in durations if d > 2.0])
        }
        
        logger.info(f"🧠 Agno simulation: {len(successful)}/{concurrent_calls} successful")
        self.test_results.append(result)
        return result
        
    async def test_memory_pressure(self, iterations: int = 100):
        """Test memory usage under pressure"""
        logger.info(f"🧠 Testing memory pressure with {iterations} iterations")
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Create some memory pressure
        data_chunks = []
        
        for i in range(iterations):
            # Create some data structures
            chunk = {
                "iteration": i,
                "data": list(range(1000)),
                "timestamp": time.time(),
                "nested": {
                    "more_data": [random.random() for _ in range(100)]
                }
            }
            data_chunks.append(chunk)
            
            if i % 10 == 0:
                await asyncio.sleep(0.01)  # Let event loop breathe
        
        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Clean up
        data_chunks.clear()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        await asyncio.sleep(0.1)
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        result = {
            "test": "memory_pressure",
            "iterations": iterations,
            "initial_memory_mb": initial_memory,
            "peak_memory_mb": peak_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": peak_memory - initial_memory,
            "memory_recovered_mb": peak_memory - final_memory
        }
        
        logger.info(f"🧠 Memory test: {initial_memory:.1f}MB → {peak_memory:.1f}MB → {final_memory:.1f}MB")
        self.test_results.append(result)
        return result
        
    async def test_task_lifecycle(self, task_count: int = 100):
        """Test async task creation and cleanup"""
        logger.info(f"⚡ Testing task lifecycle with {task_count} tasks")
        
        async def dummy_task(task_id: int):
            """Dummy task that does some work"""
            await asyncio.sleep(random.uniform(0.01, 0.1))
            if random.random() < 0.05:  # 5% chance of failure
                raise Exception(f"Task {task_id} simulated failure")
            return f"Task {task_id} completed"
        
        # Get initial task count
        initial_tasks = len(asyncio.all_tasks())
        
        # Create and run tasks
        tasks = [asyncio.create_task(dummy_task(i)) for i in range(task_count)]
        
        peak_tasks = len(asyncio.all_tasks())
        
        # Wait for completion
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful = len([r for r in results if isinstance(r, str)])
        failed = len([r for r in results if isinstance(r, Exception)])
        
        # Check final task count
        await asyncio.sleep(0.1)  # Let cleanup happen
        final_tasks = len(asyncio.all_tasks())
        
        result = {
            "test": "task_lifecycle",
            "task_count": task_count,
            "initial_tasks": initial_tasks,
            "peak_tasks": peak_tasks,
            "final_tasks": final_tasks,
            "successful": successful,
            "failed": failed,
            "task_cleanup": peak_tasks - final_tasks
        }
        
        logger.info(f"⚡ Task test: {successful}/{task_count} successful, {failed} failed")
        if final_tasks > initial_tasks + 5:  # Allow some tolerance
            logger.warning(f"⚠️  Potential task leak: {final_tasks - initial_tasks} extra tasks")
        
        self.test_results.append(result)
        return result
        
    async def run_comprehensive_stress_test(self):
        """Run all stress tests"""
        logger.info("🔥 Starting comprehensive event loop stress test")
        logger.info("=" * 60)
        
        # Test 1: Health endpoint load
        await self.test_health_endpoint_load(concurrent_requests=30)
        await asyncio.sleep(1)
        
        # Test 2: Agno call simulation
        await self.test_agno_call_simulation(concurrent_calls=15)
        await asyncio.sleep(1)
        
        # Test 3: Memory pressure
        await self.test_memory_pressure(iterations=50)
        await asyncio.sleep(1)
        
        # Test 4: Task lifecycle
        await self.test_task_lifecycle(task_count=50)
        await asyncio.sleep(1)
        
        # Get final health report
        health_report = get_health_report()
        
        # Compile final results
        total_duration = time.time() - self.start_time
        
        summary = {
            "stress_test_summary": {
                "total_duration": total_duration,
                "tests_completed": len(self.test_results),
                "timestamp": time.time()
            },
            "test_results": self.test_results,
            "final_health_report": health_report
        }
        
        logger.info("\n📋 STRESS TEST SUMMARY")
        logger.info("-" * 40)
        logger.info(f"⏱️  Total duration: {total_duration:.2f}s")
        logger.info(f"✅ Tests completed: {len(self.test_results)}")
        
        # Check for critical issues
        issues = []
        
        # Check test results for problems
        for test in self.test_results:
            if test["test"] == "health_endpoint_load":
                if test["max_duration"] > 5.0:
                    issues.append(f"Health endpoint slow responses: {test['max_duration']:.2f}s")
                if test["failed"] > 0:
                    issues.append(f"Health endpoint failures: {test['failed']}")
                    
            elif test["test"] == "memory_pressure":
                if test["memory_increase_mb"] > 100:
                    issues.append(f"High memory increase: {test['memory_increase_mb']:.1f}MB")
                    
            elif test["test"] == "task_lifecycle":
                if test["final_tasks"] > test["initial_tasks"] + 5:
                    issues.append(f"Potential task leak: {test['final_tasks'] - test['initial_tasks']} tasks")
        
        # Check health report for event loop issues
        for loop_id, loop_health in health_report.get("event_loops", {}).items():
            if loop_health.get("is_blocked"):
                issues.append(f"Event loop {loop_id} is blocked")
            if loop_health.get("failed_tasks", 0) > 5:
                issues.append(f"Event loop {loop_id} has {loop_health['failed_tasks']} failed tasks")
        
        # Check Agno metrics
        agno_metrics = health_report.get("agno_metrics", {})
        if agno_metrics.get("blocking_calls", 0) > 0:
            issues.append(f"Detected {agno_metrics['blocking_calls']} blocking Agno calls")
        
        if issues:
            logger.error("🚨 CRITICAL ISSUES DETECTED:")
            for issue in issues:
                logger.error(f"   - {issue}")
            return False, summary
        else:
            logger.info("✅ NO CRITICAL ISSUES DETECTED")
            return True, summary


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Event Loop Stress Test")
    parser.add_argument("--output", "-o", type=str, help="Output results to JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        async with EventLoopStressTest() as stress_test:
            success, results = await stress_test.run_comprehensive_stress_test()
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                logger.info(f"📄 Results saved to {args.output}")
            
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        logger.info("\n👋 Stress test interrupted")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Stress test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())