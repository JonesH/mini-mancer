"""
Test BotMotherManager functionality

Tests token validation and basic functionality without requiring BotFather interaction.
"""

import asyncio
import logging
from src.botmother_manager import BotMotherManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_basic_functionality():
    """Test basic BotMotherManager functionality."""
    logger.info("Testing BotMotherManager basic functionality")
    
    manager = BotMotherManager()
    
    # Test token validation
    logger.info("Testing token validation...")
    validation = await manager.validate_bot_token()
    
    if not validation["valid"]:
        logger.error(f"❌ Token validation failed: {validation}")
        return False
    
    logger.info("✅ Token validation successful")
    logger.info(f"Bot username: {validation['username']}")
    logger.info(f"Bot name: {validation['first_name']}")
    logger.info(f"Bot ID: {validation['id']}")
    
    # Test getter methods
    bot_info = manager.get_bot_info()
    bot_username = manager.get_bot_username()
    
    logger.info(f"Bot info: {bot_info}")
    logger.info(f"Bot username with @: {bot_username}")
    
    # Prepare commands that would be configured
    commands = [
        {"command": "start", "description": "Welcome message and introduction to BotMother"},
        {"command": "help", "description": "Get help and guidance on bot creation"},
        {"command": "create_bot", "description": "Start the process of creating a new Telegram bot"},
        {"command": "list_bots", "description": "View all bots you've created"},
        {"command": "configure_bot", "description": "Configure settings for an existing bot"},
        {"command": "bot_status", "description": "Check the status of your bots"}
    ]
    
    logger.info("📋 Commands that would be configured:")
    for cmd in commands:
        logger.info(f"  /{cmd['command']} - {cmd['description']}")
    
    logger.info("✅ BotMotherManager basic functionality working")
    return True


if __name__ == "__main__":
    # Test basic functionality
    success = asyncio.run(test_basic_functionality())
    
    if success:
        logger.info("🎉 BotMotherManager ready for BotFather configuration")
        logger.info("💡 To configure via BotFather, run the full setup_botmother_configuration() method")
    else:
        logger.error("❌ BotMotherManager test failed")