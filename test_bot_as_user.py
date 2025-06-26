#!/usr/bin/env python3
"""
Test Bot Commands as Real User

This script uses Telethon to connect as a real user (not a bot) and sends
commands TO @BotTemplateCreationTestBot to test if the commands work correctly.

This is the CORRECT way to test bots - by impersonating a user and sending
messages TO the bot, then seeing what responses the bot gives back.
"""

import asyncio
import os
import sys
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_bot_as_user():
    """Connect as user and test bot commands"""
    
    # Get user API credentials (NOT bot credentials)
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    print("🧪 Bot Testing Script - User API Approach")
    print("=" * 60)
    
    if not api_id or not api_hash:
        print("❌ Missing TELEGRAM_API_ID or TELEGRAM_API_HASH")
        print()
        print("To test the bot, you need user API credentials:")
        print("1. Go to https://my.telegram.org/apps")
        print("2. Create an app and get your API ID and hash")
        print("3. Add them to your .env file:")
        print("   TELEGRAM_API_ID=your_api_id")
        print("   TELEGRAM_API_HASH=your_api_hash")
        print()
        print("These are USER credentials (not bot credentials)")
        print("They allow this script to send messages AS you TO the bot")
        return False
    
    print(f"✅ User API credentials found")
    print(f"   API ID: {api_id}")
    print(f"   API Hash: {api_hash[:10]}...")
    print()
    
    # Bot to test
    bot_username = '@BotTemplateCreationTestBot'
    print(f"🎯 Target bot: {bot_username}")
    print()
    
    # Create user client (this connects as YOU, not as a bot)
    client = TelegramClient('user_test_session', int(api_id), api_hash)
    
    try:
        print("🔗 Connecting to Telegram as user...")
        print("📱 You may be prompted for:")
        print("   - Your phone number (with country code, e.g., +1234567890)")
        print("   - Verification code sent to your phone")
        print("   - 2FA password if enabled")
        print()
        
        await client.start()
        
        # Get info about the connected user
        me = await client.get_me()
        print(f"✅ Connected as: {me.first_name} (@{me.username or 'no username'})")
        print()
        
        # Commands to test
        test_commands = [
            '/start',
            '/examples', 
            '/create_quick',  # This is the problematic one
            '/list_personalities',
            '/create_bot', 
            '/help'
        ]
        
        results = {}
        
        for command in test_commands:
            print(f"📤 Testing: {command}")
            print("-" * 40)
            
            try:
                # Send command TO the bot (as a user would)
                sent_message = await client.send_message(bot_username, command)
                print(f"✅ Sent '{command}' to {bot_username}")
                
                # Wait for bot response
                print("⏳ Waiting for bot response...")
                await asyncio.sleep(3)  # Give bot time to respond
                
                # Get the latest messages from the bot
                response_found = False
                async for message in client.iter_messages(bot_username, limit=10):
                    # Skip our own message
                    if message.id <= sent_message.id:
                        continue
                    
                    # Found bot's response
                    if message.text:
                        print(f"📥 Bot Response (length: {len(message.text)}):")
                        print(f"   '{message.text[:150]}...' ")
                        print("✅ Command WORKS - bot responded successfully")
                        results[command] = "SUCCESS"
                        response_found = True
                        break
                
                if not response_found:
                    print("❌ No response from bot - command may have FAILED")
                    results[command] = "NO_RESPONSE"
                    
            except Exception as e:
                print(f"❌ Error testing {command}: {e}")
                results[command] = f"ERROR: {e}"
            
            print()
            await asyncio.sleep(1)  # Brief pause between tests
        
        # Summary
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        for command, result in results.items():
            status = "✅" if result == "SUCCESS" else "❌"
            print(f"{status} {command}: {result}")
        
        # Count failures
        failures = [cmd for cmd, result in results.items() if result != "SUCCESS"]
        if failures:
            print(f"\n❌ {len(failures)} command(s) failed: {', '.join(failures)}")
            print("These commands need to be fixed!")
        else:
            print("\n🎉 All commands working correctly!")
            
        return len(failures) == 0
        
    except Exception as e:
        print(f"❌ Failed to connect or test: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure TELEGRAM_API_ID and TELEGRAM_API_HASH are correct")
        print("2. Check that you can connect to Telegram")
        print("3. Verify the bot @BotTemplateCreationTestBot exists and is running")
        return False
        
    finally:
        await client.disconnect()
        print("\n🔌 Disconnected from Telegram")

def main():
    """Main function"""
    print("🚀 Starting Bot Test (User API)")
    success = asyncio.run(test_bot_as_user())
    
    if success:
        print("\n🎯 Result: All bot commands are working!")
        sys.exit(0)
    else:
        print("\n🚨 Result: Some bot commands are broken and need fixes!")
        sys.exit(1)

if __name__ == "__main__":
    main()