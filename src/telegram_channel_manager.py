"""
Telegram Channel Auto-Creation and Management
Simple utility for creating test logging channels
"""

import os
import logging
import asyncio
from typing import Optional, Dict, List
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class ChannelManager:
    """Simple Telegram channel management for testing"""
    
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token)
        self.created_channels: Dict[str, str] = {}  # name -> chat_id
    
    async def create_test_channel(self, channel_name: str, description: str = None) -> Optional[str]:
        """
        Create a simple test channel
        Note: This requires the bot to have appropriate permissions
        """
        try:
            # For private groups/channels, we need to create via BotFather or manually
            # This is a simplified version that works with existing channels
            logger.info(f"📢 Test channel '{channel_name}' should be created manually")
            logger.info(f"   1. Create channel '@{channel_name}' in Telegram")
            logger.info(f"   2. Add bot as admin")
            logger.info(f"   3. Set channel ID in environment as TEST_CHANNEL_ID")
            
            # Check if channel already exists in environment
            channel_id = os.getenv("TEST_CHANNEL_ID") or os.getenv("ERROR_CHANNEL_ID")
            if channel_id:
                try:
                    # Test if we can send to this channel
                    await self.bot.send_message(
                        chat_id=channel_id,
                        text=f"🧪 Test channel setup for '{channel_name}'\n\n"
                             f"Description: {description or 'Test logging channel'}\n"
                             f"Status: Ready for test monitoring"
                    )
                    self.created_channels[channel_name] = channel_id
                    logger.info(f"✅ Using existing channel {channel_id} for '{channel_name}'")
                    return channel_id
                except TelegramError as e:
                    logger.error(f"❌ Cannot access channel {channel_id}: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error setting up test channel: {e}")
            return None
    
    async def send_test_log(self, message: str, channel_name: str = "default") -> bool:
        """Send a test log message to a channel"""
        try:
            channel_id = self.created_channels.get(channel_name) or os.getenv("TEST_CHANNEL_ID")
            if not channel_id:
                logger.debug(f"No channel configured for '{channel_name}'")
                return False
            
            await self.bot.send_message(
                chat_id=channel_id,
                text=f"🧪 **Test Log**\n\n{message}",
                parse_mode='Markdown'
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending test log: {e}")
            return False
    
    def get_setup_instructions(self) -> str:
        """Get instructions for manual channel setup"""
        return """
📢 **Telegram Test Channel Setup Instructions**

1. **Create Channel**:
   - Open Telegram
   - Create new channel (e.g., @minimancer_test_logs)
   - Make it private for security

2. **Add Bot as Admin**:
   - Go to channel settings
   - Add your bot as administrator
   - Give it permission to post messages

3. **Get Channel ID**:
   - Forward a message from the channel to @userinfobot
   - Copy the chat ID (starts with -100)

4. **Configure Environment**:
   ```bash
   # Add to your .env file
   TEST_CHANNEL_ID=-1001234567890
   ERROR_CHANNEL_ID=-1001234567890  # Same or different channel
   ```

5. **Verify Setup**:
   - Run: `uv run python -c "from src.telegram_channel_manager import test_channel_setup; import asyncio; asyncio.run(test_channel_setup())"`
   - Check if test message appears in your channel

✅ **Benefits**:
- Real-time test logs in Telegram
- Error notifications during development
- Share test results with team
- Monitor bot interactions live
        """


async def test_channel_setup():
    """Test channel setup with current configuration"""
    bot_token = os.getenv("BOT_TOKEN") or os.getenv("TEST_BOT_TOKEN")
    if not bot_token:
        print("❌ No bot token found in environment")
        return
    
    manager = ChannelManager(bot_token)
    
    # Try to set up test channel
    channel_id = await manager.create_test_channel("test_logs", "Mini-Mancer test logging")
    
    if channel_id:
        # Send test message
        success = await manager.send_test_log("✅ Channel setup successful! Test monitoring is ready.")
        if success:
            print(f"✅ Test channel setup complete! Channel ID: {channel_id}")
        else:
            print("❌ Channel found but couldn't send test message")
    else:
        print("❌ Test channel setup failed")
        print("\n" + manager.get_setup_instructions())


# Global channel manager instance
_channel_manager: Optional[ChannelManager] = None


def get_channel_manager() -> Optional[ChannelManager]:
    """Get global channel manager instance"""
    global _channel_manager
    if _channel_manager is None:
        bot_token = os.getenv("BOT_TOKEN") or os.getenv("TEST_BOT_TOKEN")
        if bot_token:
            _channel_manager = ChannelManager(bot_token)
    return _channel_manager


async def log_to_test_channel(message: str) -> bool:
    """Convenience function to log to test channel"""
    manager = get_channel_manager()
    if manager:
        return await manager.send_test_log(message)
    return False


if __name__ == "__main__":
    # Run channel setup test
    asyncio.run(test_channel_setup())