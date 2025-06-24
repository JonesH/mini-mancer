"""
BotMother Manager - Configuration and BotFather Integration

Manages BotMother's token validation, description, commands, and BotFather configuration.
Uses Telethon client API to interact with @BotFather for bot configuration.
"""

import asyncio
import logging
import os
import httpx
from typing import Any, Optional

from src.telethon_client import TelethonSessionManager
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class BotMotherManager:
    """Manages BotMother configuration and BotFather integration."""
    
    def __init__(self):
        self.token = os.getenv("BOT_MOTHER_TOKEN")
        if not self.token:
            raise ValueError("BOT_MOTHER_TOKEN must be set in environment")
        
        self.session_manager = TelethonSessionManager("botmother_manager")
        self.bot_info: dict | None = None
    
    async def validate_bot_token(self) -> dict[str, Any]:
        """Validate BotMother token using Telegram Bot API."""
        logger.info(f"Validating BotMother token: {self.token[:10]}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{self.token}/getMe"
            )
            
            data = response.json()
            
            if data["ok"]:
                self.bot_info = data["result"]
                logger.info(f"✅ Token valid for bot: @{self.bot_info['username']}")
                return {
                    "valid": True,
                    "username": self.bot_info["username"],
                    "first_name": self.bot_info["first_name"],
                    "id": self.bot_info["id"]
                }
            else:
                logger.error(f"❌ Token validation failed: {data}")
                return {"valid": False, "error": data.get("description", "Unknown error")}
    
    async def configure_bot_description(self, description: str) -> bool:
        """Configure BotMother's description via BotFather."""
        if not self.bot_info:
            await self.validate_bot_token()
        
        bot_username = f"@{self.bot_info['username']}"
        logger.info(f"Configuring description for {bot_username}")
        
        await self.session_manager.initialize_client()
        
        # Send /setdescription to BotFather
        await self.session_manager.test_bot_message("BotFather", "/setdescription")
        await asyncio.sleep(2)
        
        # Send bot username
        await self.session_manager.test_bot_message("BotFather", bot_username)
        await asyncio.sleep(2)
        
        # Send description
        response = await self.session_manager.test_bot_message("BotFather", description)
        
        await self.session_manager.disconnect()
        
        if response and ("success" in response.lower() or "updated" in response.lower()):
            logger.info("✅ Description configured successfully")
            return True
        else:
            logger.warning(f"⚠️ Description configuration may have failed: {response}")
            return False
    
    async def configure_bot_commands(self, commands: list[dict[str, str]]) -> bool:
        """Configure BotMother's command list via BotFather."""
        if not self.bot_info:
            await self.validate_bot_token()
        
        bot_username = f"@{self.bot_info['username']}"
        logger.info(f"Configuring commands for {bot_username}")
        
        # Format commands for BotFather
        command_text = "\n".join([
            f"{cmd['command']} - {cmd['description']}" 
            for cmd in commands
        ])
        
        await self.session_manager.initialize_client()
        
        # Send /setcommands to BotFather
        await self.session_manager.test_bot_message("BotFather", "/setcommands")
        await asyncio.sleep(2)
        
        # Send bot username
        await self.session_manager.test_bot_message("BotFather", bot_username)
        await asyncio.sleep(2)
        
        # Send command list
        response = await self.session_manager.test_bot_message("BotFather", command_text)
        
        await self.session_manager.disconnect()
        
        if response and ("success" in response.lower() or "updated" in response.lower()):
            logger.info("✅ Commands configured successfully")
            return True
        else:
            logger.warning(f"⚠️ Commands configuration may have failed: {response}")
            return False
    
    async def configure_bot_short_description(self, short_description: str) -> bool:
        """Configure BotMother's short description via BotFather."""
        if not self.bot_info:
            await self.validate_bot_token()
        
        bot_username = f"@{self.bot_info['username']}"
        logger.info(f"Configuring short description for {bot_username}")
        
        await self.session_manager.initialize_client()
        
        # Send /setabouttext to BotFather  
        await self.session_manager.test_bot_message("BotFather", "/setabouttext")
        await asyncio.sleep(2)
        
        # Send bot username
        await self.session_manager.test_bot_message("BotFather", bot_username)
        await asyncio.sleep(2)
        
        # Send short description
        response = await self.session_manager.test_bot_message("BotFather", short_description)
        
        await self.session_manager.disconnect()
        
        if response and ("success" in response.lower() or "updated" in response.lower()):
            logger.info("✅ Short description configured successfully")
            return True
        else:
            logger.warning(f"⚠️ Short description configuration may have failed: {response}")
            return False
    
    async def setup_botmother_configuration(self) -> dict[str, Any]:
        """Complete BotMother setup with description and commands."""
        logger.info("Setting up complete BotMother configuration")
        
        # Validate token first
        validation = await self.validate_bot_token()
        if not validation["valid"]:
            return {"success": False, "error": "Token validation failed"}
        
        # Configure description
        description = (
            "🤖 BotMother - Your Intelligent Bot Factory\n\n"
            "I'm an AI-powered assistant that helps you create and manage Telegram bots. "
            "Whether you're looking to build a simple chatbot or a complex automation tool, "
            "I'll guide you through the entire process with intelligent conversations and "
            "step-by-step assistance.\n\n"
            "✨ Powered by Agno intelligence with advanced memory capabilities\n"
            "🔧 Built with the Bootstrap Mini-Mancer MVP system"
        )
        
        desc_result = await self.configure_bot_description(description)
        
        # Configure short description
        short_desc = "🤖 AI-powered bot creation assistant. Create and manage Telegram bots with intelligent guidance!"
        short_desc_result = await self.configure_bot_short_description(short_desc)
        
        # Configure commands
        commands = [
            {"command": "start", "description": "Welcome message and introduction to BotMother"},
            {"command": "help", "description": "Get help and guidance on bot creation"},
            {"command": "create_bot", "description": "Start the process of creating a new Telegram bot"},
            {"command": "list_bots", "description": "View all bots you've created"},
            {"command": "configure_bot", "description": "Configure settings for an existing bot"},
            {"command": "bot_status", "description": "Check the status of your bots"}
        ]
        
        commands_result = await self.configure_bot_commands(commands)
        
        result = {
            "success": all([desc_result, short_desc_result, commands_result]),
            "token_valid": validation["valid"],
            "bot_username": validation["username"],
            "description_configured": desc_result,
            "short_description_configured": short_desc_result,
            "commands_configured": commands_result
        }
        
        if result["success"]:
            logger.info("🎉 BotMother configuration completed successfully!")
        else:
            logger.warning("⚠️ Some BotMother configuration steps may have failed")
        
        return result
    
    def get_bot_info(self) -> dict | None:
        """Get cached bot information."""
        return self.bot_info
    
    def get_bot_username(self) -> str | None:
        """Get bot username with @ prefix."""
        if self.bot_info:
            return f"@{self.bot_info['username']}"
        return None


async def test_botmother_manager():
    """Test BotMotherManager functionality."""
    logger.info("Testing BotMotherManager")
    
    manager = BotMotherManager()
    
    # Test token validation
    validation = await manager.validate_bot_token()
    logger.info(f"Token validation: {validation}")
    
    if validation["valid"]:
        # Test complete setup
        setup_result = await manager.setup_botmother_configuration()
        logger.info(f"Setup result: {setup_result}")
        
        # Show bot info
        bot_info = manager.get_bot_info()
        bot_username = manager.get_bot_username()
        logger.info(f"Bot info: {bot_info}")
        logger.info(f"Bot username: {bot_username}")
        
        return setup_result["success"]
    
    return False


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Test the BotMotherManager
    asyncio.run(test_botmother_manager())