"""
Test real bot interaction using Phase 1 foundation

This proves the Telethon foundation works by testing the actual bot from BOT_TOKEN_1.
"""

import asyncio
import logging
import os
from src.telethon_client import TelethonSessionManager
from src.constants import TEST_SIMPLE_MESSAGE
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def get_bot_username():
    """Get the username of BOT_TOKEN_1 bot using Bot API."""
    import httpx
    
    bot_token = os.getenv("BOT_TOKEN_1")
    if not bot_token:
        raise ValueError("BOT_TOKEN_1 not found in .env")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        data = response.json()
        
        if data["ok"]:
            username = data["result"]["username"]
            logger.info(f"Found bot username: @{username}")
            return f"@{username}"
        else:
            raise Exception(f"Bot API error: {data}")


async def test_real_new_bot():
    """Test the actual bot from BOT_TOKEN_1 using our Phase 1 Telethon foundation."""
    logger.info("Testing real bot from BOT_TOKEN_1")
    
    # Get bot username
    bot_username = await get_bot_username()
    
    session_manager = TelethonSessionManager("real_bot_test")
    
    # Initialize Telethon client
    await session_manager.initialize_client()
    
    # Test basic interaction
    logger.info(f"Sending /start command to {bot_username}")
    response = await session_manager.test_bot_message(bot_username, "/start")
    
    if response:
        logger.info("✅ Bot responded successfully")
        logger.info(f"Response: {response}")
    else:
        logger.warning("❌ No response from bot")
    
    # Test another message
    logger.info(f"Sending '{TEST_SIMPLE_MESSAGE}' to {bot_username}")
    hello_response = await session_manager.test_bot_message(bot_username, TEST_SIMPLE_MESSAGE)
    
    if hello_response:
        logger.info("✅ Bot responds to messages")
        logger.info(f"Hello response: {hello_response[:100]}...")
    else:
        logger.warning("❌ No response to hello message")
    
    await session_manager.disconnect()
    
    logger.info("Real bot test completed")
    return response is not None


if __name__ == "__main__":
    asyncio.run(test_real_new_bot())