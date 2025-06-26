#!/usr/bin/env python3
"""
Test existing echo bot from registry
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from src.bot_spawner import BotSpawner

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

async def test_existing_echo_bot():
    """Test existing echo bot from registry."""
    print("🧪 Testing existing echo bot...")
    
    spawner = BotSpawner()
    await spawner.initialize()
    
    # Start existing bot
    print("🚀 Starting existing TestEchoBot...")
    start_result = await spawner.start_bot("TestEchoBot", "test_user_123")
    
    if not start_result["success"]:
        print(f"❌ Failed to start bot: {start_result['error']}")
        return
    
    bot_username = start_result["username"]
    print(f"✅ Started echo bot: {bot_username}")
    
    # Wait for bot to be ready
    await asyncio.sleep(3)
    
    try:
        # Connect with Telethon
        client = TelegramClient('user_test_session', API_ID, API_HASH)
        await client.start()
        
        # Strip @ from username for messaging
        clean_username = bot_username.replace('@', '')
        print(f"📤 Sending test messages to {clean_username}...")
        
        # Send test messages
        test_messages = [
            "/start",
            "Hello echo bot!",
            "/help",
            "/stats"
        ]
        
        for msg in test_messages:
            print(f"\n   📤 Sending: {msg}")
            await client.send_message(clean_username, msg)
            await asyncio.sleep(3)  # Give bot time to respond
            
            # Get latest response
            messages = await client.get_messages(clean_username, limit=1)
            if messages:
                response = messages[0].text
                print(f"   📨 Response: {response[:100]}...")
                
                # Check if it's an echo
                if msg.startswith('/'):
                    # Commands should get specific responses
                    if msg == "/start" and "hello" in response.lower():
                        print("   ✅ /start command working")
                    elif msg == "/help" and "help" in response.lower():
                        print("   ✅ /help command working")
                    elif msg == "/stats" and "statistics" in response.lower():
                        print("   ✅ /stats command working")
                    else:
                        print(f"   ❓ Unexpected response for {msg}")
                else:
                    # Regular messages should be echoed
                    if f"Echo: {msg}" in response:
                        print("   ✅ Echo functionality working")
                    else:
                        print(f"   ❓ Expected echo, got: {response[:50]}...")
            else:
                print("   ❌ No response received")
        
        await client.disconnect()
        print("\n✅ Telethon testing completed")
        
    except Exception as e:
        print(f"❌ Telethon error: {e}")
    
    finally:
        # Stop the bot
        print("\n⏹️  Stopping echo bot...")
        stop_result = await spawner.stop_bot("TestEchoBot", "test_user_123")
        
        if stop_result["success"]:
            print(f"✅ Bot stopped: {stop_result['username']}")
        
        await spawner.shutdown()

if __name__ == "__main__":
    asyncio.run(test_existing_echo_bot())