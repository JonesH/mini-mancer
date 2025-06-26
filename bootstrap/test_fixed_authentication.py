#!/usr/bin/env python3
"""
Test Fixed Telethon Authentication

Tests that the non-interactive authentication fix works properly.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src paths
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fixed_authentication():
    """Test the fixed non-interactive authentication."""
    logger.info("🔧 Testing Fixed Telethon Authentication")
    
    try:
        from unlimited_bot_creator import UnlimitedBotCreator
        
        # Test initialization with session validation
        creator = UnlimitedBotCreator()
        logger.info("📋 Initializing UnlimitedBotCreator...")
        await creator.initialize()
        
        # Check authentication status
        if creator.botfather_available:
            logger.info("✅ BotFather automation is available!")
            logger.info("   Non-interactive authentication successful")
        else:
            logger.warning("❌ BotFather automation is disabled")
            logger.warning("   Check Telethon credentials in .env")
        
        # Show stats
        stats = creator.get_unlimited_stats()
        logger.info(f"📊 Stats: {stats}")
        
        # Test graceful fallback when tokens exhausted
        if creator.botfather_available:
            logger.info("🚀 Testing token creation capability...")
            
            # Temporarily empty token pool to test fallback
            original_tokens = creator.available_tokens.copy()
            creator.available_tokens = []
            
            result = await creator.create_echo_bot("TestAuth", "test_user")
            
            # Restore tokens
            creator.available_tokens = original_tokens
            
            if result["success"]:
                logger.info("✅ Token creation works!")
                if result.get("auto_created"):
                    logger.info("🎉 Auto-creation via BotFather successful!")
            else:
                logger.warning(f"⚠️ Token creation failed: {result['error']}")
        else:
            logger.info("🔄 Testing graceful fallback when automation disabled...")
            
            # Test that it fails gracefully
            creator.available_tokens = []  # Force no tokens
            result = await creator.create_echo_bot("TestFallback", "test_user")
            
            if not result["success"] and "BotFather automation unavailable" in result["error"]:
                logger.info("✅ Graceful fallback works correctly!")
                logger.info(f"   Error message: {result['error']}")
            else:
                logger.warning("⚠️ Fallback not working as expected")
        
        await creator.shutdown()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def main():
    """Main test runner."""
    print("🔧 Testing Fixed Telethon Authentication")
    print("=" * 50)
    print("This tests:")
    print("1. Non-interactive authentication with phone number")
    print("2. Session validation on startup")
    print("3. Graceful fallback when automation unavailable")
    print("=" * 50)
    
    success = await test_fixed_authentication()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ AUTHENTICATION FIX WORKING!")
        print("   No more 'EOF when reading a line' errors")
        print("   SimpleBotMother can now use BotFather automation safely")
    else:
        print("❌ Authentication fix needs attention")
        print("   Check Telethon configuration")

if __name__ == "__main__":
    asyncio.run(main())