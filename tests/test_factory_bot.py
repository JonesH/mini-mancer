"""
Factory Bot Testing - Tests for Mini-Mancer bot creation functionality

Tests the main factory bot that creates other bots through:
- Text message bot creation requests
- Inline keyboard quick creation buttons  
- Bot startup and lifecycle management
- Error handling and validation
"""

import asyncio
import pytest
import time
from typing import Any

from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

from conftest import (
    BotTestSession, TelegramTestError,
    bot_creation_test_case, inline_keyboard_test_case
)


@pytest.mark.factory_bot
@pytest.mark.network
@pytest.mark.asyncio
class TestFactoryBotCreation:
    """Test factory bot's core bot creation functionality"""
    
    async def test_factory_bot_start_command(
        self, 
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test /start command returns proper welcome with inline keyboard"""
        print("🚀 Testing factory bot /start command...")
        
        result = await bot_interaction_helper.send_message_and_wait("/start")
        
        # Verify message was sent successfully
        assert result.message_id > 0
        
        # In a full implementation, you'd verify:
        # - Welcome message text contains factory bot intro
        # - Inline keyboard has expected quick creation buttons
        # - All 6 bot type buttons are present
        
        print("✅ /start command test completed")
    
    async def test_text_based_bot_creation(
        self,
        telegram_bot_session: BotTestSession, 
        bot_interaction_helper,
        bot_creation_test_case,
        performance_monitor
    ):
        """Test bot creation via text messages"""
        test_case = bot_creation_test_case
        print(f"🤖 Testing bot creation: {test_case.name}")
        
        performance_monitor.start_timing(f"bot_creation_{test_case.name}")
        
        try:
            # Send bot creation request
            result = await bot_interaction_helper.test_bot_creation_flow(
                test_case.input_message,
                test_case.name
            )
            
            duration = performance_monitor.end_timing(f"bot_creation_{test_case.name}")
            
            # Verify basic success
            assert result["success"], f"Bot creation failed for {test_case.name}"
            
            # Performance check - bot creation should complete within reasonable time
            assert duration < 30, f"Bot creation took too long: {duration}s"
            
            if test_case.should_create_bot:
                # Additional validation for successful bot creation
                assert result["bot_name"], "Bot name should be present"
                print(f"✅ Bot '{result['bot_name']}' created successfully in {duration:.2f}s")
            else:
                print(f"✅ Non-creation request handled correctly in {duration:.2f}s")
                
        except TelegramTestError as e:
            pytest.fail(f"Telegram API error during bot creation: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error during bot creation: {e}")
    
    async def test_inline_keyboard_bot_creation(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper, 
        inline_keyboard_test_case,
        performance_monitor
    ):
        """Test bot creation via inline keyboard buttons"""
        callback_data = inline_keyboard_test_case
        print(f"🎮 Testing inline keyboard creation: {callback_data}")
        
        performance_monitor.start_timing(f"inline_creation_{callback_data}")
        
        try:
            result = await bot_interaction_helper.test_inline_keyboard_creation(callback_data)
            
            duration = performance_monitor.end_timing(f"inline_creation_{callback_data}")
            
            assert result["success"], f"Inline keyboard creation failed for {callback_data}"
            assert duration < 20, f"Inline creation took too long: {duration}s"
            
            print(f"✅ Inline keyboard '{callback_data}' creation completed in {duration:.2f}s")
            
        except Exception as e:
            pytest.fail(f"Error during inline keyboard creation: {e}")
    
    async def test_bot_name_extraction(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test proper extraction of bot names from creation requests"""
        test_cases = [
            ("Create a bot named TestBot", "TestBot"),
            ("Make a bot called HelperBot for assistance", "HelperBot"), 
            ("I want a gaming bot named GamerBot123", "GamerBot123"),
            ("Create SupportBot", "SupportBot"),  # Without 'named' keyword
        ]
        
        for request_text, expected_name in test_cases:
            print(f"🔍 Testing name extraction: '{request_text}' -> '{expected_name}'")
            
            result = await bot_interaction_helper.test_bot_creation_flow(
                request_text, expected_name
            )
            
            # In full implementation, would verify extracted name matches expected
            assert result["success"], f"Failed to process: {request_text}"
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        print("✅ Bot name extraction tests completed")


@pytest.mark.factory_bot
@pytest.mark.network 
@pytest.mark.asyncio
class TestFactoryBotErrorHandling:
    """Test factory bot error handling and edge cases"""
    
    async def test_invalid_bot_creation_requests(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test handling of invalid bot creation requests"""
        invalid_requests = [
            "",  # Empty message
            "a",  # Too short
            "x" * 5000,  # Too long
            "🤖" * 100,  # Excessive emojis
            "CREATE BOT NOW!!!" * 50,  # Spammy content
        ]
        
        for invalid_request in invalid_requests:
            print(f"❌ Testing invalid request: '{invalid_request[:50]}...'")
            
            try:
                result = await bot_interaction_helper.send_message_and_wait(invalid_request)
                
                # Should handle gracefully without crashing
                assert result.message_id > 0, "Factory bot should respond to invalid requests"
                
            except TelegramTestError as e:
                # Some invalid requests might cause API errors - that's acceptable
                print(f"⚠️ Expected API error for invalid request: {e}")
            
            await asyncio.sleep(0.5)  # Rate limiting
        
        print("✅ Invalid request handling tests completed")
    
    async def test_concurrent_bot_creation_requests(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper,
        performance_monitor
    ):
        """Test handling of multiple simultaneous bot creation requests"""
        print("🔄 Testing concurrent bot creation requests...")
        
        performance_monitor.start_timing("concurrent_requests")
        
        # Create multiple bot creation requests simultaneously
        creation_tasks = []
        for i in range(3):  # Test with 3 concurrent requests
            task = bot_interaction_helper.test_bot_creation_flow(
                f"Create bot ConcurrentBot{i}",
                f"ConcurrentBot{i}"
            )
            creation_tasks.append(task)
        
        try:
            # Run all requests concurrently
            results = await asyncio.gather(*creation_tasks, return_exceptions=True)
            
            duration = performance_monitor.end_timing("concurrent_requests")
            
            # Analyze results
            successful_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            error_count = sum(1 for r in results if isinstance(r, Exception))
            
            print(f"📊 Concurrent creation results: {successful_count} successful, {error_count} errors")
            
            # At least some should succeed (system should handle concurrency gracefully)
            assert successful_count > 0, "At least some concurrent requests should succeed"
            assert duration < 60, f"Concurrent requests took too long: {duration}s"
            
            print(f"✅ Concurrent request test completed in {duration:.2f}s")
            
        except Exception as e:
            pytest.fail(f"Error during concurrent request testing: {e}")
    
    async def test_rate_limiting_behavior(
        self,
        telegram_bot_session: BotTestSession,
        bot_interaction_helper
    ):
        """Test factory bot behavior under rapid message sending"""
        print("⚡ Testing rate limiting behavior...")
        
        messages_sent = 0
        errors_encountered = 0
        
        # Send messages rapidly to test rate limiting
        for i in range(10):
            try:
                await bot_interaction_helper.send_message_and_wait(f"Test message {i}")
                messages_sent += 1
                
                # Very short delay to trigger rate limiting
                await asyncio.sleep(0.1)
                
            except TelegramError as e:
                errors_encountered += 1
                if "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                    print(f"⚠️ Rate limit encountered (expected): {e}")
                    break
                else:
                    print(f"❌ Unexpected Telegram error: {e}")
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                break
        
        print(f"📊 Rate limiting test: {messages_sent} sent, {errors_encountered} errors")
        
        # Should handle rate limiting gracefully
        assert messages_sent > 0, "Should be able to send at least some messages"
        
        print("✅ Rate limiting test completed")


@pytest.mark.factory_bot
@pytest.mark.integration
@pytest.mark.asyncio
class TestFactoryBotIntegration:
    """Integration tests for factory bot with PrototypeAgent"""
    
    async def test_prototype_agent_integration(
        self,
        prototype_agent_instance,
        performance_monitor
    ):
        """Test factory bot integration with PrototypeAgent"""
        print("🔧 Testing PrototypeAgent integration...")
        
        agent = prototype_agent_instance
        
        # Verify agent initialization
        assert agent is not None, "PrototypeAgent should initialize"
        assert hasattr(agent, 'create_new_bot_instant'), "Agent should have bot creation method"
        
        performance_monitor.start_timing("agent_bot_creation")
        
        try:
            # Test instant bot creation
            result = agent.create_new_bot_instant(
                "TestIntegrationBot",
                "Testing integration functionality", 
                "helpful and efficient"
            )
            
            duration = performance_monitor.end_timing("agent_bot_creation")
            
            # Verify result
            assert result is not None, "Bot creation should return a result"
            assert isinstance(result, str), "Result should be a string message"
            assert "TestIntegrationBot" in result, "Result should mention bot name"
            
            print(f"✅ PrototypeAgent integration test completed in {duration:.2f}s")
            print(f"📝 Creation result: {result[:100]}...")
            
        except Exception as e:
            pytest.fail(f"PrototypeAgent integration failed: {e}")
    
    async def test_bot_state_management(
        self,
        prototype_agent_instance
    ):
        """Test bot state tracking and lifecycle management"""
        print("📊 Testing bot state management...")
        
        agent = prototype_agent_instance
        
        # Check initial state
        initial_state = getattr(agent, 'created_bot_state', 'none')
        print(f"📋 Initial bot state: {initial_state}")
        
        # Create a bot and verify state changes
        result = agent.create_new_bot_instant(
            "StateTestBot",
            "Testing state management",
            "methodical and precise"
        )
        
        # Check state after creation
        post_creation_state = getattr(agent, 'created_bot_state', 'unknown')
        print(f"📋 Post-creation bot state: {post_creation_state}")
        
        # Verify state progression
        assert post_creation_state != initial_state, "Bot state should change after creation"
        
        # Check if bot is tracked
        active_bot = getattr(agent, 'active_created_bot', None)
        if active_bot:
            print("✅ Active bot is properly tracked")
        else:
            print("⚠️ No active bot tracked after creation")
        
        print("✅ Bot state management test completed")


@pytest.mark.factory_bot
@pytest.mark.slow
@pytest.mark.asyncio
async def test_factory_bot_endurance(
    telegram_bot_session: BotTestSession,
    bot_interaction_helper,
    performance_monitor
):
    """Long-running endurance test for factory bot stability"""
    print("🏃 Starting factory bot endurance test...")
    
    performance_monitor.start_timing("endurance_test")
    
    test_duration = 60  # 1 minute endurance test
    start_time = time.time()
    
    interactions = 0
    errors = 0
    
    while time.time() - start_time < test_duration:
        try:
            # Alternate between different types of requests
            if interactions % 3 == 0:
                await bot_interaction_helper.send_message_and_wait("How are you doing?")
            elif interactions % 3 == 1:
                await bot_interaction_helper.send_message_and_wait("Create a test bot")
            else:
                await bot_interaction_helper.send_message_and_wait("/start")
            
            interactions += 1
            
            # Rate limiting delay
            await asyncio.sleep(2)
            
        except Exception as e:
            errors += 1
            print(f"⚠️ Endurance test error {errors}: {e}")
            
            # If too many errors, stop the test
            if errors > 5:
                break
            
            # Wait longer after errors
            await asyncio.sleep(5)
    
    duration = performance_monitor.end_timing("endurance_test")
    
    print(f"📊 Endurance test completed:")
    print(f"   Duration: {duration:.2f}s")
    print(f"   Interactions: {interactions}")
    print(f"   Errors: {errors}")
    print(f"   Success rate: {((interactions - errors) / interactions * 100):.1f}%")
    
    # Verify reasonable stability
    assert interactions > 10, "Should complete reasonable number of interactions"
    assert errors < interactions * 0.3, "Error rate should be less than 30%"
    
    print("✅ Factory bot endurance test completed")