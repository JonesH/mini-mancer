#!/usr/bin/env python3
"""
Test script to verify created bots work by sending messages as a real user.
Uses Telethon client API with user credentials to test bot functionality.
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Load environment variables
load_dotenv()

# Get Telegram API credentials
API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
DEMO_USER = os.getenv('DEMO_USER')

# Session file
SESSION_FILE = 'user_test_session'

async def test_created_bot():
    """Test the created bot by sending messages as a real user"""
    
    print("🔧 Starting Telegram client test...")
    
    # Create client
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    
    try:
        await client.start()
        print("✅ Connected to Telegram as user")
        
        # Get bot username from token pool or use known username
        bot_username = "protomancer_supreme_bot"  # From earlier API call
        
        print(f"📱 Testing created bot: @{bot_username}")
        
        # Send test message to the created bot
        test_message = "Hello! Are you working? This is a test message."
        
        print(f"📤 Sending message: '{test_message}'")
        
        try:
            # Set up response handler BEFORE sending message
            response_received = False
            bot_response = ""
            
            from telethon import events
            
            async def handle_response(event):
                nonlocal response_received, bot_response
                print(f"🤖 Bot responded: '{event.message.message}'")
                bot_response = event.message.message
                response_received = True
            
            # Add event handler for messages from the specific bot
            client.add_event_handler(handle_response, events.NewMessage(from_users=bot_username))
            
            # Send message to the bot
            message = await client.send_message(bot_username, test_message)
            print(f"✅ Message sent successfully (ID: {message.id})")
            
            # Wait for response
            print("⏳ Waiting for bot response...")
            
            # Wait up to 10 seconds for a response
            start_time = asyncio.get_event_loop().time()
            while not response_received and (asyncio.get_event_loop().time() - start_time) < 10:
                await asyncio.sleep(0.1)
            
            # Remove the event handler to clean up
            client.remove_event_handler(handle_response, events.NewMessage)
            
            if response_received:
                print("✅ SUCCESS: Created bot is working and responding!")
                print(f"   Response: '{bot_response}'")
                return True
            else:
                print("❌ FAILURE: Bot did not respond within 10 seconds")
                print("   This suggests the bot is not running or not processing messages")
                return False
                
        except Exception as e:
            print(f"❌ Error sending message to bot: {e}")
            return False
            
    except SessionPasswordNeededError:
        print("❌ Two-factor authentication is enabled. Please disable 2FA temporarily for testing.")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Telegram: {e}")
        return False
    finally:
        await client.disconnect()
        print("🔌 Disconnected from Telegram")

async def main():
    """Main test function"""
    print("🧪 Testing Mini-Mancer Created Bot Functionality")
    print("=" * 60)
    
    # Check if we have the required credentials
    if not API_ID or not API_HASH:
        print("❌ Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in .env file")
        return
    
    print(f"📋 Using API ID: {API_ID}")
    print(f"📋 Using API Hash: {API_HASH[:10]}...")
    print(f"📋 Demo User: {DEMO_USER}")
    print()
    
    # Run the test
    success = await test_created_bot()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 RESULT: Created bot is functioning correctly!")
    else:
        print("💥 RESULT: Created bot test failed!")
        print("   Check container logs and bot status")

if __name__ == "__main__":
    asyncio.run(main())