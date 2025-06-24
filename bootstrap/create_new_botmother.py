"""
Create New BotMother via BotFather

This script creates a new BotMother token via @BotFather and configures it properly.
"""

import asyncio
import logging
import os
from src.telethon_client import TelethonSessionManager
from src.constants import DEFAULT_BOTMOTHER_NAME, DEFAULT_BOTMOTHER_USERNAME
from src.botmother_manager import BotMotherManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def create_new_botmother():
    """Create a new BotMother via BotFather and configure it."""
    logger.info("🤖 Creating new BotMother via @BotFather")
    
    session_manager = TelethonSessionManager("bootstrap_session")
    
    await session_manager.initialize_client()
    
    # Step 1: Create new bot via BotFather
    logger.info("📝 Step 1: Creating new bot with @BotFather")
    
    # Send /newbot to BotFather
    await session_manager.test_bot_message("BotFather", "/newbot")
    await asyncio.sleep(3)
    
    # Send bot name
    bot_name = DEFAULT_BOTMOTHER_NAME
    logger.info(f"Setting bot name: {bot_name}")
    await session_manager.test_bot_message("BotFather", bot_name)
    await asyncio.sleep(3)
    
    # Send bot username
    bot_username = DEFAULT_BOTMOTHER_USERNAME
    logger.info(f"Setting bot username: {bot_username}")
    response = await session_manager.test_bot_message("BotFather", bot_username)
    await asyncio.sleep(3)
    
    if not response:
        logger.error("❌ No response from BotFather - bot creation may have failed")
        return None
    
    # Extract token from BotFather response
    lines = response.split('\n')
    token = None
    
    for line in lines:
        if 'HTTP API' in line or 'token' in line.lower():
            # Look for token pattern in next lines
            for next_line in lines[lines.index(line):]:
                if ':' in next_line and len(next_line.split(':')[0]) > 8:
                    potential_token = next_line.strip()
                    if len(potential_token) > 30:  # Basic token validation
                        token = potential_token
                        break
            break
    
    if token:
        logger.info(f"✅ New BotMother created with token: {token[:15]}...")
    else:
        logger.error("❌ Could not extract token from BotFather response")
        logger.info(f"BotFather response: {response}")
        return None
    
    await session_manager.disconnect()
    
    return token


async def configure_new_botmother(token: str):
    """Configure the new BotMother with proper settings."""
    logger.info("⚙️ Configuring new BotMother")
    
    # Temporarily set the token in environment for BotMotherManager
    original_token = os.getenv("BOT_MOTHER_TOKEN")
    os.environ["BOT_MOTHER_TOKEN"] = token
    
    try:
        manager = BotMotherManager()
        
        # Validate the new token
        validation = await manager.validate_bot_token()
        
        if not validation["valid"]:
            logger.error(f"❌ New token validation failed: {validation}")
            return False
        
        logger.info(f"✅ New BotMother validated: @{validation['username']}")
        
        # Configure the bot via BotFather
        logger.info("🔧 Configuring bot via BotFather...")
        setup_result = await manager.setup_botmother_configuration()
        
        if setup_result["success"]:
            logger.info("🎉 BotMother configuration completed successfully!")
            logger.info(f"Bot username: @{validation['username']}")
            logger.info(f"Bot name: {validation['first_name']}")
            logger.info(f"New token: {token}")
            return True
        else:
            logger.warning("⚠️ Some configuration steps may have failed")
            logger.info(f"Setup result: {setup_result}")
            return False
            
    finally:
        # Restore original token
        if original_token:
            os.environ["BOT_MOTHER_TOKEN"] = original_token


async def main():
    """Main function to create and configure new BotMother."""
    logger.info("🚀 Starting new BotMother creation process")
    
    # Create new bot
    new_token = await create_new_botmother()
    
    if not new_token:
        logger.error("❌ Failed to create new BotMother")
        return
    
    # Configure the new bot
    success = await configure_new_botmother(new_token)
    
    if success:
        logger.info("✅ New BotMother creation and configuration complete!")
        logger.info(f"🔑 New BOT_MOTHER_TOKEN: {new_token}")
        logger.info("💡 Update your .env file with this new token")
        logger.info("🐳 Then restart docker compose to use the new BotMother")
    else:
        logger.error("❌ BotMother configuration failed")


if __name__ == "__main__":
    asyncio.run(main())