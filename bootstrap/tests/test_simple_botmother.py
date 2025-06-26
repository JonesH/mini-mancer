#!/usr/bin/env python3
"""
Telethon Test for SimpleBotMother - Real user interaction testing

Tests SimpleBotMother functionality by sending actual messages via Telethon
client API and verifying responses work for real users.
"""

import asyncio
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telethon credentials from environment
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

# Bot to test
BOTMOTHER_USERNAME = "BootstrapBotMotherMVP_bot"


class SimpleBotMotherTester:
    """Test SimpleBotMother using real Telethon user client."""
    
    def __init__(self):
        self.client = TelegramClient('user_test_session', API_ID, API_HASH)
        self.test_results = []
        
    async def start_session(self):
        """Start Telethon session."""
        await self.client.start()
        logger.info("✅ Telethon session started")
        
        # Get self info
        me = await self.client.get_me()
        logger.info(f"Testing as: @{me.username} ({me.first_name})")
    
    async def send_and_wait_response(self, message: str, timeout: int = 10) -> str:
        """Send message to SimpleBotMother and wait for response."""
        try:
            # Send message
            await self.client.send_message(BOTMOTHER_USERNAME, message)
            logger.info(f"📤 Sent: {message}")
            
            # Wait for response
            await asyncio.sleep(2)  # Give bot time to process
            
            # Get latest message from bot
            messages = await self.client.get_messages(BOTMOTHER_USERNAME, limit=1)
            if messages:
                response = messages[0].text
                logger.info(f"📨 Received: {response[:100]}...")
                return response
            else:
                return "No response received"
                
        except Exception as e:
            logger.error(f"Error in send_and_wait_response: {e}")
            return f"Error: {str(e)}"
    
    async def test_start_command(self):
        """Test /start command."""
        logger.info("🧪 Testing /start command...")
        
        response = await self.send_and_wait_response("/start")
        
        # Check response contains expected elements
        success = all(keyword in response.lower() for keyword in [
            "simplebotmother", "commands", "create_bot"
        ])
        
        self.test_results.append({
            "test": "/start command",
            "success": success,
            "response_length": len(response),
            "contains_commands": "create_bot" in response
        })
        
        logger.info(f"✅ /start test: {'PASS' if success else 'FAIL'}")
        return success
    
    async def test_help_command(self):
        """Test /help command."""
        logger.info("🧪 Testing /help command...")
        
        response = await self.send_and_wait_response("/help")
        
        # Check response contains help information
        success = all(keyword in response.lower() for keyword in [
            "help", "commands", "create_bot"
        ])
        
        self.test_results.append({
            "test": "/help command",
            "success": success,
            "response_length": len(response),
            "contains_help": "help" in response.lower()
        })
        
        logger.info(f"✅ /help test: {'PASS' if success else 'FAIL'}")
        return success
    
    async def test_create_bot_command(self):
        """Test /create_bot command."""
        logger.info("🧪 Testing /create_bot command...")
        
        # Test without arguments first
        response1 = await self.send_and_wait_response("/create_bot")
        
        # Should ask for bot name
        no_args_success = "provide a bot name" in response1.lower() or "usage:" in response1.lower()
        
        # Test with bot name
        test_bot_name = f"TestBot_{datetime.now().strftime('%H%M%S')}"
        response2 = await self.send_and_wait_response(f"/create_bot {test_bot_name}")
        
        # Should either create bot or show it's working on it
        with_args_success = any(keyword in response2.lower() for keyword in [
            "creating", "created", "successfully", "protomancer_supreme_bot"
        ])
        
        self.test_results.append({
            "test": "/create_bot command",
            "success": no_args_success and with_args_success,
            "no_args_response": response1[:100],
            "with_args_response": response2[:100],
            "bot_name_used": test_bot_name
        })
        
        logger.info(f"✅ /create_bot test: {'PASS' if (no_args_success and with_args_success) else 'FAIL'}")
        return no_args_success and with_args_success
    
    async def test_list_bots_command(self):
        """Test /list_bots command."""
        logger.info("🧪 Testing /list_bots command...")
        
        response = await self.send_and_wait_response("/list_bots")
        
        # Should either show bots or say no bots created
        success = any(keyword in response.lower() for keyword in [
            "bots", "created", "haven't created", "total"
        ])
        
        self.test_results.append({
            "test": "/list_bots command",
            "success": success,
            "response": response[:200]
        })
        
        logger.info(f"✅ /list_bots test: {'PASS' if success else 'FAIL'}")
        return success
    
    async def test_regular_message(self):
        """Test regular text message handling."""
        logger.info("🧪 Testing regular message handling...")
        
        response = await self.send_and_wait_response("Hello SimpleBotMother!")
        
        # Should respond with hardcoded response about commands
        success = any(keyword in response.lower() for keyword in [
            "simplebotmother", "commands", "help", "create_bot"
        ])
        
        self.test_results.append({
            "test": "Regular message",
            "success": success,
            "response": response[:200]
        })
        
        logger.info(f"✅ Regular message test: {'PASS' if success else 'FAIL'}")
        return success
    
    async def test_unknown_command(self):
        """Test unknown command handling."""
        logger.info("🧪 Testing unknown command handling...")
        
        response = await self.send_and_wait_response("/unknown_command")
        
        # Should respond normally (likely with hardcoded text response)
        success = len(response) > 10  # Any reasonable response
        
        self.test_results.append({
            "test": "Unknown command",
            "success": success,
            "response": response[:200]
        })
        
        logger.info(f"✅ Unknown command test: {'PASS' if success else 'FAIL'}")
        return success
    
    async def run_comprehensive_test(self):
        """Run all SimpleBotMother tests."""
        logger.info("🚀 Starting comprehensive SimpleBotMother testing...")
        
        # Start session
        await self.start_session()
        
        # Run all tests
        tests = [
            self.test_start_command,
            self.test_help_command,
            self.test_create_bot_command,
            self.test_list_bots_command,
            self.test_regular_message,
            self.test_unknown_command
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if await test():
                    passed += 1
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Test failed with exception: {e}")
        
        # Summary
        logger.info(f"\n🏁 TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("✅ All SimpleBotMother tests PASSED!")
        else:
            logger.warning(f"⚠️ {total - passed} tests FAILED")
        
        # Detailed results
        logger.info("\n📊 DETAILED RESULTS:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info(f"{i}. {result['test']}: {status}")
        
        await self.client.disconnect()
        
        return passed == total


async def main():
    """Main test execution."""
    print("🧪 SimpleBotMother Telethon Testing")
    print("=" * 50)
    
    tester = SimpleBotMotherTester()
    success = await tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests passed! SimpleBotMother is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check logs for details.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())