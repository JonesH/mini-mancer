#!/usr/bin/env python3
"""
Test echo bot functionality using Telethon
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from src.bot_spawner import BotSpawner

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

async def test_echo_bot():
    """Test that echo bot actually echoes messages."""
    print("🧪 Testing echo bot functionality...")
    
    # Create and start echo bot
    spawner = BotSpawner()
    await spawner.initialize()
    
    # Create echo bot
    result = await spawner.create_echo_bot("LiveTestBot", "telethon_test")
    
    if not result["success"]:
        print(f"❌ Failed to create bot: {result['error']}")
        return
    
    bot_username = result["username"]
    print(f"✅ Created echo bot: {bot_username}")
    
    # Start the bot
    start_result = await spawner.start_bot("LiveTestBot", "telethon_test")
    
    if not start_result["success"]:
        print(f"❌ Failed to start bot: {start_result['error']}")
        return
    
    print(f"✅ Started echo bot: {bot_username}")
    
    # Wait for bot to be ready
    await asyncio.sleep(3)
    
    try:
        # Connect with Telethon
        client = TelegramClient('user_test_session', API_ID, API_HASH)
        await client.start()
        
        print(f"📤 Sending test message to {bot_username}...")
        
        # Send test messages
        test_messages = [
            "Hello echo bot!",
            "/start",
            "/help",
            "This is a test message"
        ]
        
        for msg in test_messages:
            await client.send_message(bot_username, msg)
            print(f"   Sent: {msg}")
            await asyncio.sleep(2)
            
            # Get response
            messages = await client.get_messages(bot_username, limit=1)
            if messages:
                response = messages[0].text
                print(f"   Got: {response[:50]}...")
            else:
                print("   No response")
            
            await asyncio.sleep(1)
        
        await client.disconnect()
        print("✅ Telethon testing completed")
        
    except Exception as e:
        print(f"❌ Telethon error: {e}")
    
    finally:
        # Stop the bot
        print("⏹️  Stopping echo bot...")
        stop_result = await spawner.stop_bot("LiveTestBot", "telethon_test")
        
        if stop_result["success"]:
            print(f"✅ Bot stopped: {stop_result['username']}")
        
        await spawner.shutdown()

if __name__ == "__main__":
    asyncio.run(test_echo_bot())