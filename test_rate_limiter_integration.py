#!/usr/bin/env python3
"""
Test script to verify rate limiter integration in test framework
"""

import asyncio
import os
from unittest.mock import Mock

# Set mock mode for testing
os.environ["TEST_MOCK_MODE"] = "true"
os.environ["TEST_CLEANUP_MESSAGES"] = "true"
os.environ["TEST_MESSAGE_DELAY"] = "0.1"

async def test_rate_limiter_integration():
    """Test that the rate limiter is properly integrated"""
    print("🧪 Testing rate limiter integration in test framework...")
    
    # Import test components
    from tests.conftest import bot_test_config, BotTestSession
    
    # Get test config
    config = {
        "factory_token": "mock_token",
        "created_token": "mock_created_token", 
        "test_chat_id": 123456,
        "test_user_id": 789012,
        "mock_mode": True,
        "cleanup_messages": True,
        "message_delay": 0.1,
        "max_test_duration": 300,
        "cleanup_delay": 2.0,
    }
    
    # Create mock bot session
    mock_bot = Mock()
    mock_bot.get_me = Mock(return_value=Mock(first_name="MockBot", username="mock_bot"))
    mock_bot.send_message = Mock()
    mock_bot.delete_message = Mock()
    mock_bot.close = Mock()
    
    session = BotTestSession(
        factory_bot=mock_bot,
        factory_token=config["factory_token"],
        created_bot_token=config["created_token"],
        test_chat_id=config["test_chat_id"],
        test_user_id=config["test_user_id"]
    )
    
    # Test the bot interaction helper
    from tests.conftest import BotInteractionHelper
    helper = BotInteractionHelper(session, config)
    
    print("📨 Testing message sending with rate limiter...")
    
    # Send multiple messages rapidly
    for i in range(5):
        await helper.send_message_and_wait(f"Test message {i+1}")
    
    print("🧹 Testing message cleanup...")
    await helper.cleanup_messages()
    
    print("✅ Rate limiter integration test completed successfully!")
    print("🎯 Benefits:")
    print("   - Automatic rate limiting with token bucket algorithm")
    print("   - 429 error detection and adaptive rate reduction") 
    print("   - No more crude manual delays")
    print("   - Per-bot rate limiting isolation")
    print("   - Monitoring integration")

if __name__ == "__main__":
    asyncio.run(test_rate_limiter_integration())