"""
Telethon Session Management - Phase 1 Foundation

Handles Telethon client authentication, session persistence, and core testing utilities.
This is the foundation for all bot testing in the bootstrap MVP.
"""

import os
import asyncio
import logging
from typing import Optional
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TelethonSessionManager:
    """Manages Telethon client sessions for testing bot interactions."""
    
    def __init__(self, session_name: str = "bootstrap_session"):
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.session_name = session_name
        self.client: Optional[TelegramClient] = None
        
        if not self.api_id or not self.api_hash:
            raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")
    
    async def initialize_client(self) -> TelegramClient:
        """Initialize and authenticate Telethon client."""
        if self.client and self.client.is_connected():
            return self.client
            
        session_path = Path(f"data/{self.session_name}.session")
        session_path.parent.mkdir(exist_ok=True)
        
        self.client = TelegramClient(str(session_path), self.api_id, self.api_hash)
        
        await self.client.start()
        
        if not await self.client.is_user_authorized():
            print("Telethon session requires authentication")
            phone = input("Enter your phone number: ")
            await self.client.send_code_request(phone)
            
            try:
                code = input("Enter the verification code: ")
                await self.client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = input("Enter your 2FA password: ")
                await self.client.sign_in(password=password)
        
        logger.info("Telethon session authenticated and ready")
        return self.client
    
    async def test_bot_message(self, bot_username: str, message: str, timeout: int = 10) -> str | None:
        """
        Send message to a bot and get response.
        
        This is the core testing method - sends message TO bot as real user.
        """
        if not self.client:
            await self.initialize_client()
        
        # Send message to bot
        await self.client.send_message(bot_username, message)
        logger.info(f"Sent message to {bot_username}: {message}")
        
        # Wait for response
        await asyncio.sleep(2)  # Give bot time to respond
        
        # Get latest message from bot
        messages = await self.client.get_messages(bot_username, limit=1)
        
        if messages and messages[0].text:
            response = messages[0].text
            logger.info(f"Received response from {bot_username}: {response[:50]}...")
            return response
        else:
            logger.warning(f"No response received from {bot_username}")
            return None
    
    async def validate_session(self) -> bool:
        """Check if current session is valid and connected."""
        if not self.client:
            return False
            
        me = await self.client.get_me()
        logger.info(f"Session valid for user: {me.first_name} (@{me.username})")
        return True
    
    async def disconnect(self):
        """Properly disconnect the Telethon client."""
        if self.client:
            await self.client.disconnect()
            logger.info("Telethon client disconnected")


async def test_telethon_setup():
    """Test Telethon session setup and basic functionality."""
    print("🔧 Testing Telethon session management...")
    
    session_manager = TelethonSessionManager()
    
    try:
        # Initialize client
        client = await session_manager.initialize_client()
        
        # Validate session
        is_valid = await session_manager.validate_session()
        
        if is_valid:
            print("✅ Telethon setup complete and ready for bot testing")
            return True
        else:
            print("❌ Telethon setup failed")
            return False
            
    except Exception as e:
        print(f"❌ Telethon test failed: {e}")
        return False
    
    finally:
        await session_manager.disconnect()


if __name__ == "__main__":
    # Test the Telethon setup
    asyncio.run(test_telethon_setup())