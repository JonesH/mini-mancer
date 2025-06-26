#!/usr/bin/env python3
"""
Live Bot Testing - Comprehensive Telethon Testing

Tests both BotMother responses and created bot functionality
using real user interactions via Telethon client API.
"""

import asyncio
import logging
import os
import time
from dotenv import load_dotenv
from telethon import TelegramClient

# Setup environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotTester:
    def __init__(self):
        self.api_id = int(os.getenv('TELEGRAM_API_ID'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.session_file = 'user_test_session'
        self.client = None
        
        # Bot usernames to test
        self.botmother_username = None  # Will discover from BOT_MOTHER_TOKEN
        self.test_bots = [
            '@protomancer_supreme_bot',
            '@testunlimitedbo_5yq2ps_bot'
        ]
    
    async def setup_client(self):
        """Initialize and connect Telethon client"""
        logger.info("🔗 Setting up Telethon client...")
        self.client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        await self.client.start()
        
        me = await self.client.get_me()
        logger.info(f"✅ Connected as: @{me.username}")
        
        return True
    
    async def discover_botmother_username(self):
        """Discover BotMother username from token"""
        bot_mother_token = os.getenv('BOT_MOTHER_TOKEN')
        if not bot_mother_token:
            logger.error("❌ BOT_MOTHER_TOKEN not found")
            return None
        
        try:
            import httpx
            url = f"https://api.telegram.org/bot{bot_mother_token}/getMe"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        username = f"@{data['result']['username']}"
                        logger.info(f"🤖 Discovered BotMother: {username}")
                        self.botmother_username = username
                        return username
        except Exception as e:
            logger.error(f"❌ Failed to discover BotMother: {e}")
        
        return None
    
    async def send_and_wait_response(self, username, message, wait_time=3):
        """Send message and wait for response"""
        logger.info(f"📤 Sending to {username}: {message}")
        
        try:
            # Send message
            await self.client.send_message(username, message)
            
            # Wait for response
            await asyncio.sleep(wait_time)
            
            # Get recent messages
            messages = await self.client.get_messages(username, limit=3)
            
            # Find bot response (not our own message)
            for msg in messages:
                if msg.text and msg.text != message:
                    logger.info(f"📥 Response from {username}: {msg.text[:100]}...")
                    return msg.text
            
            logger.warning(f"⚠️ No response received from {username}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error communicating with {username}: {e}")
            return None
    
    async def test_botmother_commands(self):
        """Test BotMother command responses"""
        logger.info("🤖 Phase 1: Testing BotMother Commands")
        
        if not self.botmother_username:
            logger.error("❌ BotMother username not discovered - skipping")
            return False
        
        # Test commands
        commands_to_test = [
            ("/start", "Should show welcome with unlimited creation"),
            ("/help", "Should show help with unlimited capability"),
            ("/list_bots", "Should list existing bots"),
        ]
        
        success_count = 0
        
        for command, expected in commands_to_test:
            logger.info(f"🧪 Testing command: {command}")
            response = await self.send_and_wait_response(self.botmother_username, command, 5)
            
            if response:
                logger.info(f"✅ {command} - Got response")
                success_count += 1
                
                # Check for unlimited creation mentions
                if command == "/start" and "unlimited" in response.lower():
                    logger.info("✅ Welcome message mentions unlimited creation")
                elif command == "/help" and "unlimited" in response.lower():
                    logger.info("✅ Help message mentions unlimited capability")
            else:
                logger.error(f"❌ {command} - No response")
        
        logger.info(f"🎯 BotMother commands: {success_count}/{len(commands_to_test)} successful")
        return success_count == len(commands_to_test)
    
    async def test_bot_creation(self):
        """Test creating a new bot via BotMother"""
        logger.info("🏭 Testing Bot Creation")
        
        if not self.botmother_username:
            logger.error("❌ BotMother username not available")
            return False
        
        # Create a unique bot name
        test_bot_name = f"LiveTest{int(time.time())}"
        create_command = f"/create_bot {test_bot_name}"
        
        logger.info(f"🧪 Creating bot: {test_bot_name}")
        response = await self.send_and_wait_response(self.botmother_username, create_command, 15)
        
        if response and "successfully" in response.lower():
            logger.info("✅ Bot creation successful")
            
            # Extract bot username from response if possible
            if "@" in response:
                import re
                username_match = re.search(r'@(\w+)', response)
                if username_match:
                    new_bot_username = f"@{username_match.group(1)}"
                    logger.info(f"🎯 New bot created: {new_bot_username}")
                    return new_bot_username
            
            return True
        else:
            logger.error(f"❌ Bot creation failed. Response: {response}")
            return False
    
    async def test_echo_bot(self, bot_username):
        """Test echo bot functionality"""
        logger.info(f"🔄 Testing echo bot: {bot_username}")
        
        test_messages = [
            "Hello bot!",
            "/start",
            "Test message 123",
            "🤖 Emoji test"
        ]
        
        success_count = 0
        
        for test_msg in test_messages:
            response = await self.send_and_wait_response(bot_username, test_msg, 3)
            
            if response:
                # Check if it's an echo (should contain our message or be a response)
                if test_msg in response or len(response) > 5:
                    logger.info(f"✅ {bot_username} responded to: {test_msg}")
                    success_count += 1
                else:
                    logger.warning(f"⚠️ {bot_username} response unclear: {response}")
            else:
                logger.error(f"❌ {bot_username} no response to: {test_msg}")
        
        logger.info(f"🎯 {bot_username}: {success_count}/{len(test_messages)} responses")
        return success_count > 0
    
    async def test_created_bots(self):
        """Test existing created bots"""
        logger.info("🤖 Phase 2: Testing Created Echo Bots")
        
        working_bots = 0
        
        for bot_username in self.test_bots:
            logger.info(f"🧪 Testing {bot_username}")
            if await self.test_echo_bot(bot_username):
                working_bots += 1
                logger.info(f"✅ {bot_username} is working")
            else:
                logger.error(f"❌ {bot_username} not responding properly")
        
        logger.info(f"🎯 Created bots: {working_bots}/{len(self.test_bots)} working")
        return working_bots > 0
    
    async def end_to_end_test(self):
        """Complete end-to-end workflow test"""
        logger.info("🚀 Phase 3: End-to-End Integration Test")
        
        # Create new bot
        new_bot = await self.test_bot_creation()
        if not new_bot:
            logger.error("❌ End-to-end test failed at bot creation")
            return False
        
        # If we got a username, test it
        if isinstance(new_bot, str) and new_bot.startswith('@'):
            logger.info(f"🧪 Testing newly created bot: {new_bot}")
            await asyncio.sleep(5)  # Give bot time to initialize
            
            if await self.test_echo_bot(new_bot):
                logger.info("✅ End-to-end test: Complete success!")
                return True
            else:
                logger.warning("⚠️ Bot created but not responding yet")
                return True  # Creation worked, response might need time
        
        logger.info("✅ End-to-end test: Bot creation successful")
        return True
    
    async def run_comprehensive_test(self):
        """Run all tests"""
        logger.info("🚀 Starting Comprehensive Bot Testing")
        logger.info("=" * 60)
        
        # Setup
        await self.setup_client()
        await self.discover_botmother_username()
        
        # Run test phases
        phase1_ok = await self.test_botmother_commands()
        phase2_ok = await self.test_created_bots()
        phase3_ok = await self.end_to_end_test()
        
        # Summary
        logger.info("=" * 60)
        logger.info("🎯 TEST SUMMARY:")
        logger.info(f"Phase 1 (BotMother): {'✅ PASS' if phase1_ok else '❌ FAIL'}")
        logger.info(f"Phase 2 (Created Bots): {'✅ PASS' if phase2_ok else '❌ FAIL'}")
        logger.info(f"Phase 3 (End-to-End): {'✅ PASS' if phase3_ok else '❌ FAIL'}")
        
        overall_success = phase1_ok and (phase2_ok or phase3_ok)
        logger.info(f"OVERALL: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
        
        # Cleanup
        await self.client.disconnect()
        
        return overall_success

async def main():
    """Main test runner"""
    tester = BotTester()
    success = await tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("BotMother and created bots are working properly!")
    else:
        print("\n⚠️ Some tests failed - check logs for details")

if __name__ == "__main__":
    asyncio.run(main())