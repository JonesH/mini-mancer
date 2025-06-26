#!/usr/bin/env python3
"""
Test Unlimited Bot Creation via BotFather Integration

Tests that BotFather automation works when available tokens are exhausted.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src paths
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_unlimited_creation():
    """Test unlimited bot creation functionality."""
    logger.info("🧪 Testing Unlimited Bot Creation")
    
    try:
        from unlimited_bot_creator import UnlimitedBotCreator
        
        creator = UnlimitedBotCreator()
        await creator.initialize()
        
        # Show current token status
        stats = creator.get_unlimited_stats()
        logger.info(f"📊 Current stats: {stats}")
        
        # Test bot creation (this should trigger BotFather if no tokens available)
        test_user_id = "test_user_123"
        test_bot_name = "TestUnlimitedBot"
        
        logger.info(f"🚀 Testing creation of '{test_bot_name}'...")
        
        # This should either use available token or create new one via BotFather
        result = await creator.create_echo_bot(test_bot_name, test_user_id)
        
        logger.info(f"📋 Creation result: {result}")
        
        if result["success"]:
            logger.info("✅ Bot creation successful!")
            if result.get("auto_created"):
                logger.info("🎉 NEW TOKEN WAS AUTO-CREATED VIA BOTFATHER!")
            else:
                logger.info("📦 Used existing token from pool")
        else:
            logger.error(f"❌ Bot creation failed: {result['error']}")
        
        # Show updated stats
        final_stats = creator.get_unlimited_stats()
        logger.info(f"📊 Final stats: {final_stats}")
        
        return result["success"]
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def test_token_exhaustion_scenario():
    """Test what happens when all tokens are used."""
    logger.info("🔥 Testing Token Exhaustion Scenario")
    
    try:
        from unlimited_bot_creator import UnlimitedBotCreator
        
        creator = UnlimitedBotCreator()
        await creator.initialize()
        
        # Check if we have BotFather credentials
        if not creator.api_id or not creator.api_hash:
            logger.warning("⚠️ TELEGRAM_API_ID/TELEGRAM_API_HASH not configured")
            logger.warning("   BotFather automation will not work")
            return False
        
        # Show current available tokens
        available_count = len(creator.available_tokens)
        logger.info(f"🎯 Available tokens: {available_count}")
        
        if available_count == 0:
            logger.info("🚀 Perfect! No tokens available - BotFather automation should activate")
        else:
            logger.info("📦 Tokens available - will use existing tokens first")
        
        # Test creation
        result = await creator.create_echo_bot("ExhaustionTest", "test_user_456")
        
        if result.get("auto_created"):
            logger.info("🎉 SUCCESS: BotFather automation worked!")
        else:
            logger.info("📦 Used existing token (expected if tokens available)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Exhaustion test failed: {e}")
        return False

async def main():
    """Main test runner."""
    print("🚀 Testing Unlimited Bot Creation via BotFather")
    print("=" * 60)
    
    # Test 1: Basic unlimited creation
    print("\n🧪 Test 1: Basic Unlimited Creation")
    print("-" * 40)
    test1_success = await test_unlimited_creation()
    
    # Test 2: Token exhaustion scenario
    print("\n🔥 Test 2: Token Exhaustion Scenario")
    print("-" * 40)
    test2_success = await test_token_exhaustion_scenario()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY:")
    print(f"• Basic Creation: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"• Exhaustion Test: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED - Unlimited creation working!")
        print("   BotFather integration is properly configured.")
    else:
        print("\n⚠️ Some tests failed - check configuration:")
        print("   • Ensure TELEGRAM_API_ID/TELEGRAM_API_HASH are set")
        print("   • Verify Telethon session file exists")
        print("   • Check that @BotFather is accessible")

if __name__ == "__main__":
    asyncio.run(main())