"""
Performance and Stress Testing - Tests for Mini-Mancer system performance

Tests system performance under various conditions:
- Concurrent bot creation and management
- Memory usage and resource cleanup
- API rate limiting and throttling
- System recovery and resilience
- Load testing scenarios
"""

import asyncio
import pytest
import time
import psutil
import gc
from typing import List, Dict, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from telegram import Bot
from telegram.error import TelegramError
from telegram.ext import Application

from conftest import BotTestSession, TelegramTestError


@dataclass
class PerformanceMetrics:
    """Container for performance test metrics"""
    start_time: float = 0
    end_time: float = 0
    peak_memory_mb: float = 0
    avg_response_time: float = 0
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    cpu_usage_percent: float = 0
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def success_rate(self) -> float:
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100
    
    @property
    def operations_per_second(self) -> float:
        if self.duration == 0:
            return 0.0
        return self.total_operations / self.duration


class SystemMonitor:
    """Monitor system resources during testing"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.initial_memory
        self.cpu_measurements = []
        self.monitoring = False
        self.monitor_task = None
    
    async def start_monitoring(self):
        """Start continuous monitoring"""
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """Stop monitoring and return metrics"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        return {
            "initial_memory_mb": self.initial_memory,
            "peak_memory_mb": self.peak_memory,
            "memory_increase_mb": self.peak_memory - self.initial_memory,
            "avg_cpu_percent": sum(self.cpu_measurements) / len(self.cpu_measurements) if self.cpu_measurements else 0
        }
    
    async def _monitor_loop(self):
        """Continuous monitoring loop"""
        while self.monitoring:
            try:
                # Memory monitoring
                current_memory = self.process.memory_info().rss / 1024 / 1024
                self.peak_memory = max(self.peak_memory, current_memory)
                
                # CPU monitoring
                cpu_percent = self.process.cpu_percent()
                self.cpu_measurements.append(cpu_percent)
                
                await asyncio.sleep(1)  # Monitor every second
            except Exception:
                pass  # Continue monitoring even if individual measurements fail


@pytest.mark.performance
@pytest.mark.network
@pytest.mark.asyncio
class TestConcurrentBotOperations:
    """Test concurrent bot creation and management"""
    
    async def test_concurrent_bot_creation_stress(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Stress test with multiple concurrent bot creation requests"""
        print("⚡ Starting concurrent bot creation stress test...")
        
        monitor = SystemMonitor()
        await monitor.start_monitoring()
        
        metrics = PerformanceMetrics()
        metrics.start_time = time.time()
        
        # Create many concurrent bot creation requests
        concurrent_requests = 10
        creation_tasks = []
        
        for i in range(concurrent_requests):
            task = bot_interaction_helper.test_bot_creation_flow(
                f"Create bot StressBot{i}",
                f"StressBot{i}"
            )
            creation_tasks.append(task)
        
        try:
            # Execute all requests concurrently
            results = await asyncio.gather(*creation_tasks, return_exceptions=True)
            
            metrics.end_time = time.time()
            
            # Analyze results
            for result in results:
                metrics.total_operations += 1
                if isinstance(result, dict) and result.get("success"):
                    metrics.successful_operations += 1
                else:
                    metrics.failed_operations += 1
            
            monitoring_results = await monitor.stop_monitoring()
            
            print(f"📊 Concurrent Bot Creation Stress Test Results:")
            print(f"   Duration: {metrics.duration:.2f}s")
            print(f"   Concurrent requests: {concurrent_requests}")
            print(f"   Success rate: {metrics.success_rate:.1f}%")
            print(f"   Operations/second: {metrics.operations_per_second:.2f}")
            print(f"   Peak memory: {monitoring_results['peak_memory_mb']:.1f}MB")
            print(f"   Memory increase: {monitoring_results['memory_increase_mb']:.1f}MB")
            print(f"   Average CPU: {monitoring_results['avg_cpu_percent']:.1f}%")
            
            # Performance assertions
            assert metrics.success_rate >= 50, f"Success rate too low: {metrics.success_rate}%"
            assert metrics.duration <= 60, f"Test took too long: {metrics.duration}s"
            assert monitoring_results['memory_increase_mb'] <= 500, "Memory usage too high"
            
            print("✅ Concurrent bot creation stress test completed")
            
        except Exception as e:
            await monitor.stop_monitoring()
            pytest.fail(f"Concurrent stress test failed: {e}")


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
async def test_system_endurance_basic(
    telegram_bot_session: BotTestSession,
    bot_interaction_helper
):
    """Basic endurance test for system stability"""
    print("🏃‍♂️ Starting basic system endurance test...")
    
    test_duration = 60  # 1 minute basic test
    start_time = time.time()
    
    operations = 0
    errors = 0
    
    while time.time() - start_time < test_duration:
        try:
            # Simple operations
            await bot_interaction_helper.send_message_and_wait("Test message")
            operations += 1
            await asyncio.sleep(3)
            
        except Exception as e:
            errors += 1
            print(f"⚠️ Endurance test error: {e}")
            await asyncio.sleep(5)
    
    duration = time.time() - start_time
    success_rate = ((operations - errors) / operations * 100) if operations > 0 else 0
    
    print(f"📊 Basic Endurance Test Results:")
    print(f"   Duration: {duration:.2f}s")
    print(f"   Operations: {operations}")
    print(f"   Errors: {errors}")
    print(f"   Success rate: {success_rate:.1f}%")
    
    assert operations >= 10, "Should complete reasonable number of operations"
    assert success_rate >= 70, f"Success rate too low: {success_rate}%"
    
    print("✅ Basic endurance test completed")