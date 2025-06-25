#!/usr/bin/env python3
"""
Debug BotMother to see what's actually happening.
"""

import asyncio
import logging
from src.telethon_client import TelethonSessionManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_botmother_responses():
    """Debug what BotMother is actually responding."""
    print("🔍 Debugging BotMother responses...")
    
    session_manager = TelethonSessionManager("live_botmother_test")
    
    try:
        await session_manager.initialize_client()
        
        bot_username = "@BootstrapBotMotherMVP_bot"
        
        # Test /start command
        print(f"\n📤 Sending /start to {bot_username}")
        await session_manager.client.send_message(bot_username, "/start")
        await asyncio.sleep(3)  # Wait longer for response
        
        # Get the latest messages from bot
        messages = await session_manager.client.get_messages(bot_username, limit=5)
        print(f"📥 Latest messages from {bot_username}:")
        for i, msg in enumerate(messages):
            if msg.text:
                print(f"  {i+1}. {msg.date}: {msg.text[:100]}...")
        
        print(f"\n📤 Sending 'Hello' to {bot_username}")
        await session_manager.client.send_message(bot_username, "Hello")
        await asyncio.sleep(3)
        
        # Get latest messages again
        messages = await session_manager.client.get_messages(bot_username, limit=3)
        print(f"📥 Latest messages after 'Hello':")
        for i, msg in enumerate(messages):
            if msg.text:
                print(f"  {i+1}. {msg.date}: {msg.text[:100]}...")
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await session_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(debug_botmother_responses())