#!/usr/bin/env python3
"""
Manual test for bot creation workflow - Direct SimpleBotMother testing
"""

import asyncio
from src.simple_botmother import SimpleBotMother
from src.bot_spawner import BotSpawner

async def test_bot_creation():
    """Test the bot creation workflow directly."""
    print("🧪 Testing bot creation workflow...")
    
    # Test BotSpawner directly
    spawner = BotSpawner()
    await spawner.initialize()
    
    print(f"Available tokens: {len(spawner.available_tokens)}")
    for token in spawner.available_tokens:
        print(f"  - @{token['username']} ({token['name']})")
    
    # Test creating an echo bot
    print("\n🤖 Creating test echo bot...")
    result = await spawner.create_echo_bot("TestEchoBot", "test_user_123")
    
    if result["success"]:
        print(f"✅ Bot created: {result['username']}")
        print(f"   Link: {result['telegram_link']}")
        
        # Test starting the bot
        print("\n🚀 Starting echo bot...")
        start_result = await spawner.start_bot("TestEchoBot", "test_user_123")
        
        if start_result["success"]:
            print(f"✅ Bot started: {start_result['username']}")
            
            # Let it run for a few seconds
            print("⏱️  Letting bot run for 10 seconds...")
            await asyncio.sleep(10)
            
            # Stop the bot
            print("\n⏹️  Stopping echo bot...")
            stop_result = await spawner.stop_bot("TestEchoBot", "test_user_123")
            
            if stop_result["success"]:
                print(f"✅ Bot stopped: {stop_result['username']}")
            else:
                print(f"❌ Failed to stop bot: {stop_result['error']}")
        else:
            print(f"❌ Failed to start bot: {start_result['error']}")
    else:
        print(f"❌ Failed to create bot: {result['error']}")
    
    # Clean up
    await spawner.shutdown()
    print("\n✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_bot_creation())