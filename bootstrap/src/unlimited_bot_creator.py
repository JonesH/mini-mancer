"""
Unlimited Bot Creator - Integrates BotFather automation with SimpleBotMother

Extends BotSpawner with automatic token creation via BotFather when pool is exhausted.
"""

import asyncio
import logging
import os
import random
import string
from datetime import datetime
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from telethon import TelegramClient

from bot_spawner import BotSpawner

load_dotenv()

logger = logging.getLogger(__name__)


class UnlimitedBotCreator(BotSpawner):
    """
    Extended BotSpawner that automatically creates new bot tokens via BotFather
    when the token pool is exhausted.
    """
    
    def __init__(self):
        super().__init__()
        
        # BotFather automation setup
        self.api_id = int(os.getenv('TELEGRAM_API_ID')) if os.getenv('TELEGRAM_API_ID') else None
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone_number = os.getenv('TELEGRAM_PHONE_NUMBER')
        self.session_file = 'user_test_session'
        
        # Track auto-created bots to avoid conflicts
        self.auto_created_count = 0
        
        # Track BotFather automation availability
        self.botfather_available = False
        
        logger.info("UnlimitedBotCreator initialized with BotFather automation")
    
    async def _get_client(self) -> TelegramClient:
        """Get authenticated Telethon client for BotFather automation."""
        client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        await client.start(phone=self.phone_number)
        return client
    
    async def _validate_telethon_session(self) -> bool:
        """Check if Telethon authentication works without interaction."""
        if not all([self.api_id, self.api_hash, self.phone_number]):
            logger.warning("⚠️ Missing Telethon credentials - BotFather automation disabled")
            return False
            
        try:
            client = await self._get_client()
            # Test authentication by getting our own info
            me = await client.get_me()
            await client.disconnect()
            logger.info(f"✅ Telethon authentication validated: @{me.username or 'No username'}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Telethon authentication failed: {e}")
            logger.warning("   BotFather automation will be disabled")
            return False
    
    async def initialize(self):
        """Initialize UnlimitedBotCreator with session validation."""
        # Initialize parent class first
        await super().initialize()
        
        # Validate Telethon session for BotFather automation
        self.botfather_available = await self._validate_telethon_session()
        
        if self.botfather_available:
            logger.info("🚀 BotFather automation enabled and validated")
        else:
            logger.warning("⚠️ BotFather automation disabled - will use available tokens only")
    
    def _generate_bot_name(self, user_request: str) -> str:
        """Generate a unique bot name for BotFather."""
        # Sanitize user request
        safe_name = ''.join(c for c in user_request if c.isalnum() or c in ' -_')
        safe_name = safe_name.strip()[:20]  # Limit length
        
        if not safe_name:
            safe_name = "GeneratedBot"
        
        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%m%d_%H%M")
        
        return f"{safe_name} {timestamp}"
    
    def _generate_bot_username(self, user_request: str) -> str:
        """Generate a unique bot username for BotFather."""
        # Sanitize user request
        safe_base = ''.join(c for c in user_request if c.isalnum())
        safe_base = safe_base.lower()[:15]  # Limit length
        
        if not safe_base:
            safe_base = "generated"
        
        # Add random suffix for uniqueness
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        return f"{safe_base}_{random_suffix}_bot"
    
    async def _create_new_bot_via_botfather(self, bot_name: str) -> Dict[str, Any]:
        """
        Create a new bot via @BotFather using Telethon automation.
        
        Args:
            bot_name: Display name for the new bot
            
        Returns:
            Dict with creation result and token
        """
        client = None
        try:
            logger.info(f"🤖 Creating new bot via @BotFather: {bot_name}")
            
            client = await self._get_client()
            
            # Generate unique username
            bot_username = self._generate_bot_username(bot_name)
            display_name = self._generate_bot_name(bot_name)
            
            logger.info(f"   Name: {display_name}")
            logger.info(f"   Username: {bot_username}")
            
            # Step 1: Start new bot creation
            await client.send_message('BotFather', '/newbot')
            await asyncio.sleep(2)
            
            # Step 2: Send bot display name
            await client.send_message('BotFather', display_name)
            await asyncio.sleep(2)
            
            # Step 3: Send bot username
            await client.send_message('BotFather', bot_username)
            await asyncio.sleep(3)  # Give more time for response
            
            # Step 4: Check for token in response
            messages = await client.get_messages('BotFather', limit=3)
            
            for message in messages:
                if message.text:
                    text = message.text
                    
                    # Look for token pattern (numbers:letters)
                    import re
                    token_pattern = r'(\d+:[A-Za-z0-9_-]+)'
                    token_match = re.search(token_pattern, text)
                    
                    if token_match:
                        token = token_match.group(1)
                        logger.info(f"✅ Bot created successfully! Token: {token[:10]}...")
                        
                        return {
                            "success": True,
                            "token": token,
                            "username": bot_username,
                            "display_name": display_name,
                            "created_via": "botfather_automation"
                        }
                    
                    # Check for error messages
                    error_indicators = ['sorry', 'invalid', 'taken', 'error', 'bad']
                    if any(indicator in text.lower() for indicator in error_indicators):
                        logger.warning(f"❌ BotFather error: {text}")
                        return {
                            "success": False,
                            "error": f"BotFather rejected: {text}",
                            "error_code": "BOTFATHER_ERROR"
                        }
            
            # If we get here, no clear success or error
            logger.warning("⚠️ Ambiguous response from BotFather")
            return {
                "success": False,
                "error": "Unclear response from BotFather",
                "error_code": "AMBIGUOUS_RESPONSE"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create bot via BotFather: {e}")
            return {
                "success": False,
                "error": f"BotFather automation failed: {str(e)}",
                "error_code": "CLIENT_ERROR"
            }
        finally:
            if client:
                await client.disconnect()
    
    async def _validate_and_add_new_token(self, token: str, username: str) -> bool:
        """
        Validate new token and add it to available tokens pool.
        
        Args:
            token: Bot token from BotFather
            username: Bot username
            
        Returns:
            True if token is valid and added successfully
        """
        try:
            # Import the validation method from parent class
            validation = await super()._validate_bot_token(token)
            
            if validation["valid"]:
                # Add to available tokens
                new_token_info = {
                    "env_var": f"AUTO_BOT_TOKEN_{self.auto_created_count + 1}",
                    "token": token,
                    "username": validation["username"],
                    "name": validation["first_name"],
                    "bot_id": validation["id"],
                    "auto_created": True,
                    "created_at": datetime.now().isoformat()
                }
                
                self.available_tokens.append(new_token_info)
                self.auto_created_count += 1
                
                logger.info(f"✅ New token validated and added: @{validation['username']}")
                return True
            else:
                logger.error(f"❌ New token validation failed: {validation['error']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error validating new token: {e}")
            return False
    
    async def _setup_new_bot_commands(self, token: str) -> bool:
        """
        Setup commands for a newly created bot using BotFather integration.
        
        Args:
            token: Bot token for the new bot
            
        Returns:
            True if commands were set up successfully
        """
        try:
            # Import BotFather integration
            import sys
            from pathlib import Path
            main_src_path = Path(__file__).parent.parent.parent / "src"
            sys.path.insert(0, str(main_src_path))
            
            from botfather_integration import BotFatherIntegration
            
            botfather = BotFatherIntegration()
            commands = botfather.get_default_commands()
            
            logger.info(f"⚙️ Setting up {len(commands)} commands for new bot...")
            
            result = await botfather.configure_bot_commands(token, commands)
            
            if result["success"]:
                logger.info("✅ Commands configured for new bot")
                return True
            else:
                logger.warning(f"⚠️ Command setup failed: {result['error']}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Could not setup commands for new bot: {e}")
            return False
    
    async def create_echo_bot(self, bot_name: str, user_id: str) -> Dict[str, Any]:
        """
        Create a new SimpleEchoBot with unlimited token creation.
        
        If no tokens are available, automatically creates a new one via BotFather.
        """
        logger.info(f"Creating unlimited echo bot '{bot_name}' for user {user_id}")
        
        # First try normal token acquisition
        token_info = self._get_available_token()
        
        # If no tokens available, create a new one
        if not token_info:
            if not self.botfather_available:
                logger.warning("❌ No tokens available and BotFather automation disabled")
                return {
                    "success": False,
                    "error": "No available bot tokens and BotFather automation unavailable. Please add more BOT_TOKEN_* environment variables or fix Telethon authentication."
                }
            
            logger.info("💡 No available tokens - creating new bot via BotFather...")
            
            # Attempt to create new bot
            creation_result = await self._create_new_bot_via_botfather(bot_name)
            
            if creation_result["success"]:
                # Validate and add the new token
                token_added = await self._validate_and_add_new_token(
                    creation_result["token"],
                    creation_result["username"]
                )
                
                if token_added:
                    # Configure commands for the new bot
                    await self._setup_new_bot_commands(creation_result["token"])
                    
                    # Try again with the new token
                    token_info = self._get_available_token()
                    logger.info(f"🚀 New token created and ready: @{creation_result['username']}")
                else:
                    return {
                        "success": False,
                        "error": "Created new bot but token validation failed"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create new bot: {creation_result['error']}"
                }
        
        # If we still don't have a token, something went wrong
        if not token_info:
            return {
                "success": False,
                "error": "Unable to acquire bot token even after creation attempt"
            }
        
        # Proceed with normal bot creation using the token
        result = await super().create_echo_bot(bot_name, user_id)
        
        # Add unlimited creation info to result
        if result["success"] and token_info.get("auto_created"):
            result["auto_created"] = True
            result["message"] += " (New bot token created automatically)"
            logger.info("✨ Successfully created bot using auto-generated token!")
        
        return result
    
    def get_unlimited_stats(self) -> Dict[str, Any]:
        """Get statistics including unlimited creation capability."""
        base_stats = self.get_spawner_stats()
        
        auto_created_tokens = sum(1 for token in self.available_tokens 
                                  if token.get("auto_created", False))
        
        base_stats.update({
            "unlimited_creation": self.botfather_available,
            "auto_created_tokens": auto_created_tokens,
            "total_auto_created": self.auto_created_count,
            "botfather_automation": "enabled" if self.botfather_available else "disabled"
        })
        
        return base_stats


async def test_unlimited_creator():
    """Test UnlimitedBotCreator functionality."""
    print("🚀 Testing UnlimitedBotCreator...")
    
    creator = UnlimitedBotCreator()
    await creator.initialize()
    
    # Test stats
    stats = creator.get_unlimited_stats()
    print(f"Unlimited creator stats: {stats}")
    
    print("✅ UnlimitedBotCreator test completed")


if __name__ == "__main__":
    asyncio.run(test_unlimited_creator())