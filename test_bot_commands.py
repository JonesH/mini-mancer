#!/usr/bin/env python3
"""
Test Bot Commands Script - Impersonate User to Test Bot Responses

This script uses Telethon to connect as a real user and send commands to 
@BotTemplateCreationTestBot to verify all commands work properly.
"""

import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_bot_commands():
    """Test all bot commands by sending them as a real user"""
    
    # Get API credentials from environment
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        print("❌ Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in environment")
        print("   Please set these in your .env file")
        return
    
    # Bot username from Docker logs
    bot_username = '@BotTemplateCreationTestBot'
    
    print(f"🤖 Testing bot commands for {bot_username}")
    print(f"🔑 Using API ID: {api_id}")
    print()
    
    # Create user client
    client = TelegramClient('test_session', int(api_id), api_hash)
    
    try:
        await client.start()
        print("✅ Connected to Telegram as user")
        
        # Commands to test
        commands = [
            '/start',
            '/examples', 
            '/create_quick',
            '/list_personalities', 
            '/create_bot',
            '/help'
        ]
        
        for command in commands:
            print(f"\n📤 Testing command: {command}")
            print("-" * 50)
            
            try:
                # Send command to bot
                message = await client.send_message(bot_username, command)
                print(f"✅ Sent: {command}")
                
                # Wait a moment for bot response
                await asyncio.sleep(2)
                
                # Get bot's response (look for messages after our command)
                async for response in client.iter_messages(bot_username, limit=5):
                    # Skip our own message
                    if response.id <= message.id:
                        continue
                        
                    # Found bot's response
                    if response.text:
                        print(f"📥 Bot Response:")
                        print(f"   Length: {len(response.text)} characters")
                        print(f"   Content: {response.text[:200]}...")
                        if len(response.text) > 200:
                            print(f"   [Response truncated - full length: {len(response.text)}]")
                        print("✅ Command succeeded")
                    else:
                        print("📥 Bot Response: [No text content]")
                    break
                else:
                    print("❌ No response received from bot")
                    
            except Exception as e:
                print(f"❌ Error testing {command}: {e}")
                
            # Wait between commands
            await asyncio.sleep(1)
            
        print("\n🏁 Bot command testing completed!")
        
    except Exception as e:
        print(f"❌ Failed to connect or test: {e}")
    finally:
        await client.disconnect()
        print("🔌 Disconnected from Telegram")

if __name__ == "__main__":
    print("🧪 Starting Bot Command Test Script")
    print("=" * 60)
    asyncio.run(test_bot_commands())