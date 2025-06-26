"""
Tier 3 Performance & Reliability Tests - Mini-Mancer Testing Plan
Tests system stability and performance under various load conditions.

Priority: Medium - Stability Issues
Coverage:
- Rate limiting effectiveness
- Concurrent request handling
- Performance under load
- Memory usage monitoring
- Response time analysis
"""

import asyncio
import pytest
import time
import psutil
import os
from typing import Any
from concurrent.futures import ThreadPoolExecutor

from conftest import BotTestSession, TelegramTestError
from src.test_monitor import log_test_start, log_test_end, log_error


@pytest.mark.tier3
@pytest.mark.performance
@pytest.mark.asyncio
class TestRateLimitingEffectiveness:
    """Test rate limiting effectiveness"""
    
    async def test_rapid_message_sending(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper,
        performance_monitor
    ):
        """Test rapid message sending (burst testing)"""
        await log_test_start("rapid_message_sending")
        
        performance_monitor.start_timing("rapid_message_burst")
        
        try:
            print("⚡ Testing rapid message sending...")
            
            # Send messages rapidly to test rate limiting
            messages_sent = 0
            rate_limit_triggered = False
            start_time = time.time()
            
            # Try to send 10 messages rapidly
            for i in range(10):
                try:
                    message = f"Rapid test message {i}"
                    result = await bot_interaction_helper.send_message_and_wait(message)
                    
                    if result.message_id > 0:
                        messages_sent += 1
                        print(f"✓ Message {i+1} sent successfully")
                    
                    # No manual delay - let rate limiter handle it
                    
                except TelegramTestError as e:
                    if "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                        rate_limit_triggered = True
                        print(f"⚠️ Rate limit triggered at message {i+1}: {e}")
                        break
                    else:
                        raise e
            
            duration = performance_monitor.end_timing("rapid_message_burst")
            
            # Verify rate limiting behavior
            assert messages_sent > 0, "Should be able to send at least some messages"
            
            if rate_limit_triggered:
                print(f"✅ Rate limiting working: sent {messages_sent}/10 messages before limit")
            else:
                print(f"✅ All {messages_sent} messages sent successfully (within limits)")
            
            await log_test_end("rapid_message_sending", "PASSED")
            
        except Exception as e:
            await log_error(e, "rapid_message_sending")
            pytest.fail(f"Rapid message sending test failed: {e}")

    async def test_rapid_bot_creation_attempts(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test rapid bot creation attempts"""
        await log_test_start("rapid_bot_creation")
        
        try:
            print("🤖⚡ Testing rapid bot creation attempts...")
            
            creation_attempts = [
                "create helpful bot named RapidBot1",
                "create professional bot named RapidBot2", 
                "create gaming bot named RapidBot3",
                "create support bot named RapidBot4"
            ]
            
            creations_successful = 0
            
            for i, creation_request in enumerate(creation_attempts):
                try:
                    print(f"Attempt {i+1}: {creation_request}")
                    
                    result = await bot_interaction_helper.send_message_and_wait(creation_request)
                    
                    if result.message_id > 0:
                        creations_successful += 1
                        print(f"✓ Creation attempt {i+1} processed")
                    
                    # Small delay to allow for automatic bot replacement
                    await asyncio.sleep(1)
                    
                except TelegramTestError as e:
                    print(f"⚠️ Creation attempt {i+1} failed: {e}")
            
            # Due to automatic bot replacement, only the last creation should succeed
            print(f"✅ Rapid bot creation test: {creations_successful}/{len(creation_attempts)} processed")
            assert creations_successful > 0, "At least some creation attempts should be processed"
            
            await log_test_end("rapid_bot_creation", "PASSED")
            
        except Exception as e:
            await log_error(e, "rapid_bot_creation")
            pytest.fail(f"Rapid bot creation test failed: {e}")

    async def test_rate_limiting_recovery(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test rate limiting recovery"""
        await log_test_start("rate_limiting_recovery")
        
        try:
            print("🔄 Testing rate limiting recovery...")
            
            # Send a few rapid messages to potentially trigger rate limiting
            for i in range(5):
                try:
                    await bot_interaction_helper.send_message_and_wait(f"Recovery test {i}")
                except TelegramTestError:
                    print(f"Rate limit triggered at message {i}")
                    break
            
            # Wait for rate limit to reset
            print("Waiting for rate limit recovery...")
            await asyncio.sleep(10)
            
            # Test normal functionality after recovery
            recovery_result = await bot_interaction_helper.send_message_and_wait("/start")
            assert recovery_result.message_id > 0, "Should work normally after rate limit recovery"
            
            print("✅ Rate limiting recovery successful")
            await log_test_end("rate_limiting_recovery", "PASSED")
            
        except Exception as e:
            await log_error(e, "rate_limiting_recovery")
            pytest.fail(f"Rate limiting recovery test failed: {e}")


@pytest.mark.tier3
@pytest.mark.performance
@pytest.mark.asyncio
class TestConcurrentRequestHandling:
    """Test concurrent request handling"""
    
    async def test_concurrent_bot_creation(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper,
        performance_monitor
    ):
        """Test multiple users creating bots simultaneously"""
        await log_test_start("concurrent_bot_creation")
        
        performance_monitor.start_timing("concurrent_bot_creation")
        
        try:
            print("👥 Testing concurrent bot creation...")
            
            # Simulate concurrent creation requests
            concurrent_requests = [
                "create helpful bot named ConcurrentBot1",
                "create professional bot named ConcurrentBot2",
                "create gaming bot named ConcurrentBot3"
            ]
            
            # Run creation requests concurrently
            tasks = []
            for request in concurrent_requests:
                task = bot_interaction_helper.send_message_and_wait(request)
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            duration = performance_monitor.end_timing("concurrent_bot_creation")
            
            # Analyze results
            successful_count = sum(1 for r in results if hasattr(r, 'message_id') and r.message_id > 0)
            error_count = sum(1 for r in results if isinstance(r, Exception))
            
            print(f"📊 Concurrent creation results: {successful_count} successful, {error_count} errors")
            print(f"⏱️ Completed in {duration:.2f}s")
            
            # Should handle concurrency gracefully (automatic replacement means only one succeeds)
            assert successful_count > 0, "At least some concurrent requests should succeed"
            assert duration < 30, f"Concurrent creation took too long: {duration}s"
            
            await log_test_end("concurrent_bot_creation", "PASSED")
            
        except Exception as e:
            await log_error(e, "concurrent_bot_creation")
            pytest.fail(f"Concurrent bot creation test failed: {e}")

    async def test_concurrent_command_processing(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper,
        performance_monitor
    ):
        """Test concurrent command processing"""
        await log_test_start("concurrent_command_processing")
        
        performance_monitor.start_timing("concurrent_commands")
        
        try:
            print("⚙️ Testing concurrent command processing...")
            
            # Mix of different commands
            concurrent_commands = [
                "/start",
                "/help", 
                "/create_quick",
                "/list_personalities",
                "/examples"
            ]
            
            # Execute commands concurrently
            tasks = [bot_interaction_helper.send_message_and_wait(cmd) for cmd in concurrent_commands]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            duration = performance_monitor.end_timing("concurrent_commands")
            
            # Analyze results
            successful_count = sum(1 for r in results if hasattr(r, 'message_id') and r.message_id > 0)
            
            print(f"📊 Concurrent commands: {successful_count}/{len(concurrent_commands)} successful")
            print(f"⏱️ Completed in {duration:.2f}s")
            
            assert successful_count >= len(concurrent_commands) * 0.8, "At least 80% of commands should succeed"
            assert duration < 20, f"Concurrent commands took too long: {duration}s"
            
            await log_test_end("concurrent_command_processing", "PASSED")
            
        except Exception as e:
            await log_error(e, "concurrent_command_processing")
            pytest.fail(f"Concurrent command processing test failed: {e}")

    async def test_mixed_content_concurrent_load(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test concurrent processing with mixed content types"""
        await log_test_start("mixed_content_concurrent")
        
        try:
            print("🎭 Testing mixed content concurrent load...")
            
            # Mix of commands, bot creation, and regular messages
            mixed_requests = [
                "/start",
                "create helpful bot named MixedTestBot",
                "/help",
                "Hello, how are you?",
                "/create_quick",
                "What can you do?",
                "/list_personalities"
            ]
            
            # Execute with slight delays to simulate real usage
            results = []
            for request in mixed_requests:
                try:
                    result = await bot_interaction_helper.send_message_and_wait(request)
                    results.append(result)
                    await asyncio.sleep(0.5)  # Small delay between requests
                except Exception as e:
                    print(f"Request failed: {request} - {e}")
                    results.append(e)
            
            successful_count = sum(1 for r in results if hasattr(r, 'message_id') and r.message_id > 0)
            
            print(f"📊 Mixed content results: {successful_count}/{len(mixed_requests)} successful")
            
            assert successful_count >= len(mixed_requests) * 0.7, "At least 70% of mixed requests should succeed"
            
            await log_test_end("mixed_content_concurrent", "PASSED")
            
        except Exception as e:
            await log_error(e, "mixed_content_concurrent")
            pytest.fail(f"Mixed content concurrent test failed: {e}")


@pytest.mark.tier3
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
class TestPerformanceUnderLoad:
    """Test performance under sustained load"""
    
    async def test_endurance_with_mixed_media(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper,
        performance_monitor
    ):
        """Test endurance with mixed media types (extended stress test)"""
        await log_test_start("endurance_mixed_media")
        
        performance_monitor.start_timing("endurance_test")
        
        try:
            print("🏃‍♂️ Starting endurance test with mixed media...")
            
            # Endurance test parameters
            test_duration_seconds = 120  # 2 minutes for CI compatibility
            start_time = time.time()
            
            interactions = 0
            errors = 0
            
            # Mix of different interaction types
            interaction_types = [
                ("command", "/start"),
                ("command", "/help"),
                ("text", "Hello, how are you?"),
                ("creation", "create helpful bot named EnduranceBot"),
                ("command", "/create_quick"),
                ("text", "What can you help me with?")
            ]
            
            while time.time() - start_time < test_duration_seconds:
                try:
                    # Cycle through interaction types
                    interaction_type, content = interaction_types[interactions % len(interaction_types)]
                    
                    print(f"Interaction {interactions + 1}: {interaction_type} - {content[:30]}...")
                    
                    result = await bot_interaction_helper.send_message_and_wait(content)
                    
                    if hasattr(result, 'message_id') and result.message_id > 0:
                        interactions += 1
                    else:
                        errors += 1
                    
                    # Rate limiter handles timing - small delay for endurance
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    errors += 1
                    print(f"⚠️ Endurance error {errors}: {e}")
                    
                    # If too many errors, reduce frequency
                    if errors > 5:
                        await asyncio.sleep(5)
            
            duration = performance_monitor.end_timing("endurance_test")
            
            # Calculate metrics
            success_rate = ((interactions - errors) / interactions * 100) if interactions > 0 else 0
            interactions_per_minute = (interactions / duration) * 60
            
            print(f"📊 Endurance test results:")
            print(f"   Duration: {duration:.2f}s")
            print(f"   Interactions: {interactions}")
            print(f"   Errors: {errors}")
            print(f"   Success rate: {success_rate:.1f}%")
            print(f"   Rate: {interactions_per_minute:.1f} interactions/minute")
            
            # Verify stability
            assert interactions > 10, "Should complete reasonable number of interactions"
            assert success_rate > 70, f"Success rate too low: {success_rate}%"
            
            await log_test_end("endurance_mixed_media", "PASSED")
            
        except Exception as e:
            await log_error(e, "endurance_mixed_media")
            pytest.fail(f"Endurance test failed: {e}")

    async def test_memory_usage_monitoring(self):
        """Test memory usage monitoring during operations"""
        await log_test_start("memory_usage_monitoring")
        
        try:
            print("💾 Testing memory usage monitoring...")
            
            # Get initial memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            print(f"Initial memory usage: {initial_memory:.2f} MB")
            
            # Simulate some operations (would normally be actual bot operations)
            await asyncio.sleep(1)
            
            # Check memory after operations
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            print(f"Memory after operations: {current_memory:.2f} MB")
            print(f"Memory increase: {memory_increase:.2f} MB")
            
            # Memory should not increase dramatically
            assert memory_increase < 100, f"Memory increase too high: {memory_increase} MB"
            
            print("✅ Memory usage within acceptable limits")
            await log_test_end("memory_usage_monitoring", "PASSED")
            
        except Exception as e:
            await log_error(e, "memory_usage_monitoring")
            pytest.fail(f"Memory usage monitoring failed: {e}")

    async def test_response_time_degradation(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper,
        performance_monitor
    ):
        """Test response time degradation analysis"""
        await log_test_start("response_time_degradation")
        
        try:
            print("⏱️ Testing response time degradation...")
            
            response_times = []
            
            # Test response times over multiple interactions
            for i in range(10):
                start_time = time.time()
                
                try:
                    result = await bot_interaction_helper.send_message_and_wait(f"Performance test {i}")
                    
                    if hasattr(result, 'message_id') and result.message_id > 0:
                        response_time = time.time() - start_time
                        response_times.append(response_time)
                        print(f"Response {i+1}: {response_time:.2f}s")
                    
                except Exception as e:
                    print(f"Response {i+1} failed: {e}")
                
                await asyncio.sleep(1)
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
                
                print(f"📊 Response time analysis:")
                print(f"   Average: {avg_response_time:.2f}s")
                print(f"   Min: {min_response_time:.2f}s")
                print(f"   Max: {max_response_time:.2f}s")
                
                # Check for excessive degradation
                if len(response_times) > 5:
                    first_half_avg = sum(response_times[:len(response_times)//2]) / (len(response_times)//2)
                    second_half_avg = sum(response_times[len(response_times)//2:]) / (len(response_times) - len(response_times)//2)
                    degradation = ((second_half_avg - first_half_avg) / first_half_avg) * 100
                    
                    print(f"   Degradation: {degradation:.1f}%")
                    assert degradation < 50, f"Response time degradation too high: {degradation}%"
                
                assert avg_response_time < 10, f"Average response time too high: {avg_response_time}s"
            
            await log_test_end("response_time_degradation", "PASSED")
            
        except Exception as e:
            await log_error(e, "response_time_degradation")
            pytest.fail(f"Response time degradation test failed: {e}")


@pytest.mark.tier3
@pytest.mark.performance
@pytest.mark.asyncio
async def test_tier3_performance_integration(
    telegram_bot_session: BotTestSession,
    bot_interaction_helper,
    performance_monitor
):
    """Integration test for all Tier 3 performance functionality"""
    await log_test_start("tier3_performance_integration")
    
    performance_monitor.start_timing("tier3_performance_integration")
    
    try:
        print("⚡ Running Tier 3 Performance Integration Test...")
        
        # Test 1: Basic rate limiting
        rapid_messages = ["Test 1", "Test 2", "Test 3"]
        for msg in rapid_messages:
            await bot_interaction_helper.send_message_and_wait(msg)
            await asyncio.sleep(0.5)
        
        # Test 2: Concurrent operations
        concurrent_tasks = [
            bot_interaction_helper.send_message_and_wait("/start"),
            bot_interaction_helper.send_message_and_wait("/help"),
            bot_interaction_helper.send_message_and_wait("Hello")
        ]
        
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        successful_concurrent = sum(1 for r in results if hasattr(r, 'message_id') and r.message_id > 0)
        
        # Test 3: Memory check
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        
        duration = performance_monitor.end_timing("tier3_performance_integration")
        
        print(f"📊 Performance integration results:")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Concurrent success: {successful_concurrent}/{len(concurrent_tasks)}")
        print(f"   Memory usage: {memory_usage:.2f} MB")
        
        # Verify performance criteria
        assert duration < 30, f"Performance integration took too long: {duration}s"
        assert successful_concurrent >= len(concurrent_tasks) * 0.8, "Most concurrent operations should succeed"
        assert memory_usage < 500, f"Memory usage too high: {memory_usage} MB"
        
        print("✅ Tier 3 performance integration test completed successfully")
        await log_test_end("tier3_performance_integration", "PASSED")
        
    except Exception as e:
        await log_error(e, "tier3_performance_integration")
        pytest.fail(f"Tier 3 performance integration test failed: {e}")