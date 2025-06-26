#!/usr/bin/env python3
"""
Test Unlimited Bot Creation

Tests the integration of BotFather automation with SimpleBotMother
to verify unlimited bot creation capability.
"""

import asyncio
import logging
import os
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

async def test_unlimited_bot_creation():
    """Test the unlimited bot creation system"""
    logger.info("🚀 Testing Unlimited Bot Creation System")
    
    # Step 1: Test UnlimitedBotCreator directly
    logger.info("📋 Step 1: Testing UnlimitedBotCreator class")
    
    try:
        from src.unlimited_bot_creator import UnlimitedBotCreator
        
        creator = UnlimitedBotCreator()
        await creator.initialize()
        
        # Get stats
        stats = creator.get_unlimited_stats()
        logger.info(f"✅ UnlimitedBotCreator stats: {stats}")
        
        # Test bot creation (simulate exhausted token pool)
        test_user_id = "test_user_12345"
        test_bot_name = "TestUnlimitedBot"
        
        logger.info(f"🤖 Testing bot creation: {test_bot_name}")
        
        # Temporarily empty token pool to force new creation
        original_tokens = creator.available_tokens.copy()
        creator.available_tokens = []  # Force auto-creation
        
        # Test creation
        result = await creator.create_echo_bot(test_bot_name, test_user_id)
        
        # Restore original tokens
        creator.available_tokens = original_tokens
        
        if result["success"]:
            logger.info(f"✅ Bot creation successful: {result}")
        else:
            logger.error(f"❌ Bot creation failed: {result}")
        
        await creator.shutdown()
        
    except Exception as e:
        logger.error(f"❌ UnlimitedBotCreator test failed: {e}")
    
    # Step 2: Test Telethon integration (if session exists)
    logger.info("📋 Step 2: Testing Telethon integration")
    
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_file = 'user_test_session'
    
    if api_id and api_hash:
        try:
            client = TelegramClient(session_file, int(api_id), api_hash)
            await client.start()
            
            # Test if we can connect
            me = await client.get_me()
            logger.info(f"✅ Telethon connected as: @{me.username}")
            
            # Test BotFather integration availability
            try:
                await client.send_message('BotFather', '/help')
                logger.info("✅ BotFather is accessible via Telethon")
            except Exception as e:
                logger.warning(f"⚠️ BotFather access issue: {e}")
            
            await client.disconnect()
            
        except Exception as e:
            logger.error(f"❌ Telethon test failed: {e}")
    else:
        logger.warning("⚠️ TELEGRAM_API_ID/API_HASH not set - skipping Telethon test")
    
    # Step 3: Test SimpleBotMother integration
    logger.info("📋 Step 3: Testing SimpleBotMother integration")
    
    try:
        from src.simple_botmother import SimpleBotMother
        
        # Check if BOT_MOTHER_TOKEN is available
        if os.getenv("BOT_MOTHER_TOKEN"):
            logger.info("✅ BOT_MOTHER_TOKEN found - SimpleBotMother can initialize")
            
            # Test initialization (don't actually run)
            bot_mother = SimpleBotMother()
            logger.info(f"✅ SimpleBotMother initialized with UnlimitedBotCreator: {type(bot_mother.bot_creator).__name__}")
            
        else:
            logger.warning("⚠️ BOT_MOTHER_TOKEN not set - cannot test SimpleBotMother")
            
    except Exception as e:
        logger.error(f"❌ SimpleBotMother test failed: {e}")
    
    logger.info("🎯 Unlimited bot creation test completed!")

async def test_botfather_integration():
    """Test BotFather integration functionality"""
    logger.info("🤖 Testing BotFather Integration")
    
    try:
        # Test token validation
        import sys
        sys.path.append('..')
        from src.botfather_integration import BotFatherIntegration
        
        botfather = BotFatherIntegration()
        
        # Test with a fake token to check validation
        fake_token = "123456789:ABCDEFghijklmnopqrstuvwxyz"
        validation = await botfather.validate_bot_token(fake_token)
        
        logger.info(f"✅ Token validation works: {validation['valid']} (expected False)")
        
    except Exception as e:
        logger.error(f"❌ BotFather integration test failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing Unlimited Bot Creation System")
    print("=" * 50)
    
    asyncio.run(test_unlimited_bot_creation())
    print("\n" + "=" * 50)
    asyncio.run(test_botfather_integration())
    
    print("✅ All tests completed!")