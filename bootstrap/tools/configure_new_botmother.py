"""
Configure the new BotMother with commands via BotFather
"""

import asyncio
import logging
from src.botmother_manager import BotMotherManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def configure_new_botmother():
    """Configure the new BotMother via BotFather"""
    logger.info("🔧 Configuring new BotMother via BotFather")
    
    manager = BotMotherManager()
    
    # First validate the new token
    validation = await manager.validate_bot_token()
    
    if not validation["valid"]:
        logger.error(f"❌ Token validation failed: {validation}")
        return False
    
    logger.info(f"✅ New BotMother validated: @{validation['username']}")
    logger.info(f"Bot name: {validation['first_name']}")
    logger.info(f"Bot ID: {validation['id']}")
    
    # Configure via BotFather  
    logger.info("🔧 Configuring commands and description via BotFather...")
    setup_result = await manager.setup_botmother_configuration()
    
    if setup_result["success"]:
        logger.info("🎉 BotMother configuration completed successfully!")
        logger.info(f"✅ Description configured: {setup_result['description_configured']}")
        logger.info(f"✅ Short description configured: {setup_result['short_description_configured']}")
        logger.info(f"✅ Commands configured: {setup_result['commands_configured']}")
        return True
    else:
        logger.warning("⚠️ Some configuration steps may have failed")
        logger.info(f"Setup result: {setup_result}")
        return False

if __name__ == "__main__":
    success = asyncio.run(configure_new_botmother())
    
    if success:
        logger.info("🚀 New BotMother is ready! Starting docker compose...")
    else:
        logger.error("❌ Configuration failed")