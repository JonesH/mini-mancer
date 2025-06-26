#!/usr/bin/env python3
"""
Update Bot Commands Registration

Updates the BotFather command registration for existing bots
to match the actually implemented commands.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Add main src to path
main_src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(main_src_path))

from dotenv import load_dotenv
from botfather_integration import BotFatherIntegration

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def update_botmother_commands():
    """Update BotMother command registration"""
    logger.info("🤖 Updating BotMother commands...")
    
    bot_mother_token = os.getenv('BOT_MOTHER_TOKEN')
    if not bot_mother_token:
        logger.error("❌ BOT_MOTHER_TOKEN not found")
        return False
    
    try:
        botfather = BotFatherIntegration()
        
        # Get BotMother commands
        commands = botfather.get_botmother_commands()
        logger.info(f"📋 Setting {len(commands)} commands for BotMother...")
        
        # Configure commands
        result = await botfather.configure_bot_commands(bot_mother_token, commands)
        
        if result["success"]:
            logger.info("✅ BotMother commands updated successfully!")
            return True
        else:
            logger.error(f"❌ Failed to update BotMother commands: {result['error']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating BotMother commands: {e}")
        return False

async def update_echo_bot_commands():
    """Update echo bot command registration"""
    logger.info("🔄 Updating echo bot commands...")
    
    # Read bot registry to find echo bots
    import json
    registry_file = Path("data/simple_bot_registry.json")
    
    if not registry_file.exists():
        logger.warning("⚠️ No bot registry found")
        return True
    
    try:
        with open(registry_file, 'r') as f:
            registry = json.load(f)
        
        botfather = BotFatherIntegration()
        echo_commands = botfather.get_default_commands()
        
        success_count = 0
        total_count = 0
        
        for bot_id, bot_data in registry.items():
            token = bot_data.get('token')
            username = bot_data.get('username')
            
            if not token or not username:
                continue
                
            total_count += 1
            logger.info(f"📋 Updating commands for @{username}...")
            
            result = await botfather.configure_bot_commands(token, echo_commands)
            
            if result["success"]:
                logger.info(f"✅ Commands updated for @{username}")
                success_count += 1
            else:
                logger.error(f"❌ Failed to update @{username}: {result['error']}")
        
        logger.info(f"🎯 Echo bot updates: {success_count}/{total_count} successful")
        return success_count == total_count
        
    except Exception as e:
        logger.error(f"❌ Error updating echo bot commands: {e}")
        return False

async def main():
    """Main update process"""
    logger.info("🚀 Updating Bot Command Registrations")
    logger.info("=" * 50)
    
    # Update BotMother commands
    botmother_ok = await update_botmother_commands()
    
    # Update echo bot commands  
    echo_bots_ok = await update_echo_bot_commands()
    
    # Summary
    logger.info("=" * 50)
    if botmother_ok and echo_bots_ok:
        logger.info("🎉 All command registrations updated successfully!")
        print("\n✅ Command registration update completed!")
        print("Users will now see correct commands in Telegram UI.")
    else:
        logger.error("⚠️ Some updates failed - check logs above")
        print("\n❌ Some command updates failed - see logs for details")

if __name__ == "__main__":
    asyncio.run(main())