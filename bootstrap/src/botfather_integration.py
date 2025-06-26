"""
BotFather Integration Module for Mini-Mancer

Handles validation and configuration of Telegram bots using Telethon client API.
Automates conversations with @BotFather just like a human user would.
"""

import asyncio
import logging
import os
import re
from typing import Any

from dotenv import load_dotenv
from telethon import TelegramClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class BotFatherIntegration:
    """Integration with @BotFather using Telethon client API"""
    
    def __init__(self):
        self.api_id = int(os.getenv('TELEGRAM_API_ID'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.session_file = 'user_test_session'  # Use existing authenticated session
    
    async def _get_client(self) -> TelegramClient:
        """Get authenticated Telethon client"""
        client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        await client.start()
        return client
    
    async def validate_bot_token(self, token: str) -> dict[str, Any]:
        """
        Validate bot token using Telegram Bot API
        
        Args:
            token: Bot token from BotFather
            
        Returns:
            Dict with validation result and bot info
        """
        import httpx
        
        try:
            logger.info(f"🔍 Validating token via Bot API: {token[:10]}...")
            
            # Use Bot API getMe method to validate token and get bot info
            url = f"https://api.telegram.org/bot{token}/getMe"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("ok"):
                        bot_info = data.get("result", {})
                        return {
                            "valid": True,
                            "bot_info": bot_info,
                            "bot_id": bot_info.get("id"),
                            "username": bot_info.get("username"),
                            "first_name": bot_info.get("first_name"),
                            "can_join_groups": bot_info.get("can_join_groups", True),
                            "can_read_all_group_messages": bot_info.get("can_read_all_group_messages", False),
                            "supports_inline_queries": bot_info.get("supports_inline_queries", False)
                        }
                    else:
                        return {
                            "valid": False,
                            "error": data.get("description", "Bot API returned error"),
                            "error_code": "BOT_API_ERROR"
                        }
                elif response.status_code == 401:
                    return {
                        "valid": False,
                        "error": "Unauthorized - Invalid bot token",
                        "error_code": "INVALID_TOKEN"
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"Bot API returned status {response.status_code}",
                        "error_code": "HTTP_ERROR"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error validating token: {e}")
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}",
                "error_code": "CLIENT_ERROR"
            }
    
    def _parse_bot_info(self, text: str) -> dict[str, Any]:
        """Parse bot information from BotFather's response"""
        bot_info = {}
        
        # Try to extract username (format: @username)
        username_match = re.search(r'@(\w+)', text)
        if username_match:
            bot_info['username'] = username_match.group(1)
        
        # Try to extract bot name from various formats
        name_patterns = [
            r'Bot name:\s*(.+)',
            r'Name:\s*(.+)',
            r'This is\s*(.+)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bot_info['first_name'] = match.group(1).strip()
                break
        
        # Generate a placeholder ID (BotFather doesn't give us the actual ID)
        if 'username' in bot_info:
            bot_info['id'] = hash(bot_info['username']) % (10**9)
        
        return bot_info
    
    async def configure_bot_commands(self, token: str, commands: list[dict]) -> dict[str, Any]:
        """
        Configure bot commands by messaging @BotFather
        
        Args:
            token: Bot token
            commands: List of command dicts with 'command' and 'description'
            
        Returns:
            Result of operation
        """
        client = None
        try:
            client = await self._get_client()
            
            # First get bot info to find the username
            bot_info_result = await self.validate_bot_token(token)
            if not bot_info_result["valid"]:
                return {
                    "success": False,
                    "error": "Invalid token - cannot configure commands"
                }
            
            bot_username = f"@{bot_info_result['username']}"
            logger.info(f"⚙️ Setting commands for {bot_username} via @BotFather")
            
            # Start the setcommands process
            await client.send_message('BotFather', '/setcommands')
            await asyncio.sleep(2)
            
            # Send the bot username (not token)
            await client.send_message('BotFather', bot_username)
            await asyncio.sleep(2)
            
            # Format commands for BotFather
            command_text = ""
            for cmd in commands:
                command_text += f"{cmd['command']} - {cmd['description']}\n"
            
            # Send the commands
            await client.send_message('BotFather', command_text.strip())
            await asyncio.sleep(2)
            
            # Check for success response
            messages = await client.get_messages('BotFather', limit=3)
            
            for message in messages:
                if message.text:
                    text = message.text.lower()
                    if any(success in text for success in ['success', 'updated', 'done']):
                        return {
                            "success": True,
                            "error": None
                        }
                    elif any(error in text for error in ['error', 'invalid', 'wrong']):
                        return {
                            "success": False,
                            "error": f"BotFather rejected command configuration: {message.text}"
                        }
            
            return {
                "success": True,  # Assume success if no error
                "error": None
            }
                    
        except Exception as e:
            logger.error(f"❌ Error setting commands: {e}")
            return {
                "success": False,
                "error": f"Failed to set commands: {str(e)}"
            }
        finally:
            if client:
                await client.disconnect()
    
    async def configure_bot_description(self, token: str, description: str) -> dict[str, Any]:
        """
        Configure bot description by messaging @BotFather
        
        Args:
            token: Bot token
            description: Bot description text
            
        Returns:
            Result of operation
        """
        client = None
        try:
            client = await self._get_client()
            
            # First get bot info to find the username
            bot_info_result = await self.validate_bot_token(token)
            if not bot_info_result["valid"]:
                return {
                    "success": False,
                    "error": "Invalid token - cannot configure description"
                }
            
            bot_username = f"@{bot_info_result['username']}"
            logger.info(f"📝 Setting description for {bot_username} via @BotFather")
            
            # Start the setdescription process
            await client.send_message('BotFather', '/setdescription')
            await asyncio.sleep(2)
            
            # Send the bot username (not token)
            await client.send_message('BotFather', bot_username)
            await asyncio.sleep(2)
            
            # Send the description
            await client.send_message('BotFather', description)
            await asyncio.sleep(2)
            
            # Check for success response
            messages = await client.get_messages('BotFather', limit=3)
            
            for message in messages:
                if message.text:
                    text = message.text.lower()
                    if any(success in text for success in ['success', 'updated', 'done']):
                        return {
                            "success": True,
                            "error": None
                        }
                    elif any(error in text for error in ['error', 'invalid', 'wrong']):
                        return {
                            "success": False,
                            "error": f"BotFather rejected description: {message.text}"
                        }
            
            return {
                "success": True,  # Assume success if no error
                "error": None
            }
                    
        except Exception as e:
            logger.error(f"❌ Error setting description: {e}")
            return {
                "success": False,
                "error": f"Failed to set description: {str(e)}"
            }
        finally:
            if client:
                await client.disconnect()
    
    async def configure_bot_short_description(self, token: str, short_description: str) -> dict[str, Any]:
        """
        Configure bot short description by messaging @BotFather
        
        Args:
            token: Bot token
            short_description: Short description text
            
        Returns:
            Result of operation
        """
        client = None
        try:
            client = await self._get_client()
            
            # First get bot info to find the username
            bot_info_result = await self.validate_bot_token(token)
            if not bot_info_result["valid"]:
                return {
                    "success": False,
                    "error": "Invalid token - cannot configure short description"
                }
            
            bot_username = f"@{bot_info_result['username']}"
            logger.info(f"📋 Setting short description for {bot_username} via @BotFather")
            
            # Start the setabouttext process (BotFather's command for short description)
            await client.send_message('BotFather', '/setabouttext')
            await asyncio.sleep(2)
            
            # Send the bot username (not token)
            await client.send_message('BotFather', bot_username)
            await asyncio.sleep(2)
            
            # Send the short description
            await client.send_message('BotFather', short_description)
            await asyncio.sleep(2)
            
            # Check for success response
            messages = await client.get_messages('BotFather', limit=3)
            
            for message in messages:
                if message.text:
                    text = message.text.lower()
                    if any(success in text for success in ['success', 'updated', 'done']):
                        return {
                            "success": True,
                            "error": None
                        }
                    elif any(error in text for error in ['error', 'invalid', 'wrong']):
                        return {
                            "success": False,
                            "error": f"BotFather rejected short description: {message.text}"
                        }
            
            return {
                "success": True,  # Assume success if no error
                "error": None
            }
                    
        except Exception as e:
            logger.error(f"❌ Error setting short description: {e}")
            return {
                "success": False,
                "error": f"Failed to set short description: {str(e)}"
            }
        finally:
            if client:
                await client.disconnect()
    
    @staticmethod
    def get_default_commands() -> list[dict]:
        """Get default command set for created echo bots"""
        return [
            {"command": "start", "description": "Start interaction with the bot"},
            {"command": "help", "description": "Show help message and available commands"},
            {"command": "stats", "description": "Show bot statistics and status"},
        ]
    
    @staticmethod
    def get_botmother_commands() -> list[dict]:
        """Get command set for SimpleBotMother factory bot"""
        return [
            {"command": "start", "description": "Welcome message and bot overview"},
            {"command": "help", "description": "Show help and available commands"},
            {"command": "create_bot", "description": "Create a new echo bot"},
            {"command": "list_bots", "description": "List all your created bots"},
            {"command": "start_bot", "description": "Start a specific bot"},
            {"command": "stop_bot", "description": "Stop a specific bot"},
            {"command": "bot_status", "description": "Check status of a specific bot"},
        ]
    
    async def full_bot_setup(self, token: str, bot_name: str, bot_purpose: str, 
                           custom_commands: list[dict] | None = None) -> dict[str, Any]:
        """
        Complete bot setup with validation, commands, and descriptions
        
        Args:
            token: Bot token from BotFather
            bot_name: Name for the bot
            bot_purpose: Purpose/description of the bot
            custom_commands: Optional custom commands (uses defaults if None)
            
        Returns:
            Comprehensive setup result
        """
        results = {
            "token_valid": False,
            "bot_info": None,
            "commands_set": False,
            "description_set": False,
            "short_description_set": False,
            "errors": []
        }
        
        # Step 1: Validate token
        logger.info(f"🔍 Validating bot token: {token[:10]}...")
        validation_result = await self.validate_bot_token(token)
        
        if not validation_result["valid"]:
            results["errors"].append(f"Token validation failed: {validation_result['error']}")
            return results
        
        results["token_valid"] = True
        results["bot_info"] = validation_result["bot_info"]
        bot_username = validation_result.get("username", "unknown")
        
        logger.info(f"✅ Token valid for bot: @{bot_username}")
        
        # Step 2: Set commands
        commands = custom_commands or self.get_default_commands()
        logger.info(f"⚙️ Setting {len(commands)} commands...")
        
        commands_result = await self.configure_bot_commands(token, commands)
        if commands_result["success"]:
            results["commands_set"] = True
            logger.info("✅ Commands configured successfully")
        else:
            results["errors"].append(f"Failed to set commands: {commands_result['error']}")
        
        # Step 3: Set description
        description = f"{bot_name} - {bot_purpose}"
        logger.info(f"📝 Setting description: {description[:50]}...")
        
        desc_result = await self.configure_bot_description(token, description)
        if desc_result["success"]:
            results["description_set"] = True
            logger.info("✅ Description configured successfully")
        else:
            results["errors"].append(f"Failed to set description: {desc_result['error']}")
        
        # Step 4: Set short description
        short_desc = bot_purpose[:120]  # Telegram limit
        logger.info(f"📋 Setting short description: {short_desc[:30]}...")
        
        short_desc_result = await self.configure_bot_short_description(token, short_desc)
        if short_desc_result["success"]:
            results["short_description_set"] = True
            logger.info("✅ Short description configured successfully")
        else:
            results["errors"].append(f"Failed to set short description: {short_desc_result['error']}")
        
        logger.info(f"🎯 Bot setup complete for @{bot_username}")
        return results