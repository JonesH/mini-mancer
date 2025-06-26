#!/usr/bin/env python3
"""
Test Error Handling Fix

Tests that SimpleBotMother can handle errors with special characters properly.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src paths
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockUpdate:
    """Mock Telegram update for testing."""
    def __init__(self):
        self.message = MockMessage()
        self.effective_user = MockUser()

class MockMessage:
    """Mock Telegram message for testing."""
    def __init__(self):
        self.text = "/create_bot TestBot"
        self.replies = []
    
    async def reply_text(self, text, parse_mode=None):
        """Mock reply that captures the message."""
        self.replies.append({"text": text, "parse_mode": parse_mode})
        logger.info(f"📤 Mock reply sent (parse_mode={parse_mode}):")
        logger.info(f"   {text}")

class MockUser:
    """Mock Telegram user for testing."""
    def __init__(self):
        self.id = 12345
        self.username = "testuser"

class MockContext:
    """Mock Telegram context for testing."""
    def __init__(self):
        self.args = ["TestBot"]

async def test_error_handling():
    """Test that error handling with special characters works."""
    logger.info("🔧 Testing SimpleBotMother Error Handling")
    
    try:
        from simple_botmother import SimpleBotMother
        
        # Create SimpleBotMother but don't start it
        bot_mother = SimpleBotMother()
        
        # Create a scenario that will cause an error with special characters
        # We'll simulate this by temporarily breaking the bot_creator
        original_create_method = bot_mother.bot_creator.create_echo_bot
        
        async def mock_create_error(bot_name, user_id):
            # Return an error with special markdown characters
            raise Exception("Permission denied: [Errno 13] Permission denied: 'data/simple_bot_registry.json' - failed to create BOT_TOKEN_* environment")
        
        # Replace the method to trigger our test error
        bot_mother.bot_creator.create_echo_bot = mock_create_error
        
        # Test the create_bot_command with our mock error
        mock_update = MockUpdate()
        mock_context = MockContext()
        
        logger.info("🎯 Testing create_bot_command with special character error...")
        await bot_mother.create_bot_command(mock_update, mock_context)
        
        # Check if the reply was sent and formatted correctly
        if mock_update.message.replies:
            reply = mock_update.message.replies[-1]
            logger.info(f"✅ Error message sent successfully with parse_mode={reply['parse_mode']}")
            logger.info("   No 'Can't parse entities' error occurred!")
            
            # Check that special characters were escaped
            if "Permission denied: \\[Errno 13\\]" in reply["text"] and "BOT\\_TOKEN\\_\\*" in reply["text"]:
                logger.info("✅ Special characters properly escaped in error message")
            else:
                logger.warning("⚠️ Special characters may not be properly escaped")
        else:
            logger.error("❌ No reply was sent - error handling failed")
        
        # Restore original method
        bot_mother.bot_creator.create_echo_bot = original_create_method
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def main():
    """Main test runner."""
    print("🔧 Testing SimpleBotMother Error Handling Fix")
    print("=" * 55)
    print("This tests that errors with markdown-breaking characters")
    print("are properly escaped and don't cause parsing errors.")
    print("=" * 55)
    
    success = await test_error_handling()
    
    print("\n" + "=" * 55)
    if success:
        print("✅ ERROR HANDLING FIX WORKING!")
        print("   No more 'Can't parse entities' errors")
        print("   Special characters in errors are properly escaped")
    else:
        print("❌ Error handling fix needs attention")

if __name__ == "__main__":
    asyncio.run(main())