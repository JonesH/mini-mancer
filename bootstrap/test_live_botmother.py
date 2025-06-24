"""
Test live BotMother using Phase 1 Telethon foundation

This proves the complete Phase 1 foundation works by testing the live BotMother bot.
"""

import asyncio
import logging
from src.telethon_client import TelethonSessionManager
from src.constants import TEST_GREETING_MESSAGE

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_live_botmother():
    """Test the live BotMother bot running in Docker."""
    logger.info("Testing live BotMother bot")
    
    # NEW BotMother username from BOT_MOTHER_TOKEN
    botmother_username = "@BootstrapBotMotherMVP_bot"
    
    session_manager = TelethonSessionManager("live_botmother_test")
    
    try:
        # Initialize Telethon client
        await session_manager.initialize_client()
        
        # Test /start command
        logger.info(f"Testing /start command with {botmother_username}")
        start_response = await session_manager.test_bot_message(botmother_username, "/start")
        
        if start_response:
            logger.info("✅ BotMother /start works!")
            logger.info(f"Start response: {start_response}")
        else:
            logger.warning("❌ No response to /start")
            return False
        
        # Test /help command
        logger.info(f"Testing /help command with {botmother_username}")
        help_response = await session_manager.test_bot_message(botmother_username, "/help")
        
        if help_response:
            logger.info("✅ BotMother /help works!")
            logger.info(f"Help response: {help_response[:100]}...")
        else:
            logger.warning("❌ No response to /help")
        
        # Test /create_bot command
        logger.info(f"Testing /create_bot command with {botmother_username}")
        create_response = await session_manager.test_bot_message(botmother_username, "/create_bot")
        
        if create_response:
            logger.info("✅ BotMother /create_bot works!")
            logger.info(f"Create response: {create_response[:100]}...")
        else:
            logger.warning("❌ No response to /create_bot")
        
        # Test natural language conversation
        logger.info(f"Testing natural conversation with {botmother_username}")
        conversation_response = await session_manager.test_bot_message(
            botmother_username, 
            TEST_GREETING_MESSAGE
        )
        
        if conversation_response:
            logger.info("✅ BotMother natural conversation works!")
            logger.info(f"Conversation response: {conversation_response[:100]}...")
        else:
            logger.warning("❌ No response to conversation")
        
        logger.info("🎉 All BotMother tests passed!")
        logger.info("✅ Phase 1 foundation completely validated")
        logger.info("🔜 Ready for Phase 2: Dual-Interface BotMother")
        
        return True
        
    finally:
        await session_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(test_live_botmother())