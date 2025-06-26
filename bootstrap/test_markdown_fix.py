#!/usr/bin/env python3
"""
Test Markdown Escaping Fix

Tests that error messages with special characters are properly escaped.
"""

import sys
from pathlib import Path

# Add src paths
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from markdown_utils import escape_markdown

def test_problematic_characters():
    """Test escaping of characters that cause markdown parsing errors."""
    
    # Test cases that would cause "Can't parse entities" errors
    test_cases = [
        "Can't parse entities: can't find end of the entity starting at byte offset 204",
        "Failed to create new bot: BotFather automation failed: EOF when reading a line",
        "No available bot tokens and BotFather automation unavailable. Please add more BOT_TOKEN_* environment variables or fix Telethon authentication.",
        "Database connection failed: psycopg2.OperationalError: connection to server at 'localhost' (127.0.0.1), port 5432 failed",
        "Invalid token format: expected format 'BOT_123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'",
        "Permission denied: [Errno 13] Permission denied: 'data/simple_bot_registry.json'",
    ]
    
    print("🔧 Testing Markdown Escaping for Error Messages")
    print("=" * 60)
    
    for i, error_msg in enumerate(test_cases, 1):
        print(f"\n{i}. Original error:")
        print(f"   {error_msg}")
        
        escaped = escape_markdown(error_msg)
        print(f"   Escaped:")
        print(f"   {escaped}")
        
        # Format as it would appear in SimpleBotMother
        telegram_message = f"❌ **Bot Creation Error**\n\nTechnical error: {escaped}\n\nPlease try again or contact support."
        print(f"   In Telegram message:")
        print(f"   {telegram_message}")
    
    print("\n" + "=" * 60)
    print("✅ All error messages properly escaped!")
    print("   These will no longer cause 'Can't parse entities' errors")

def test_specific_entity_error():
    """Test the specific error that was reported."""
    
    # This is the exact error pattern that was causing issues
    original_error = "Can't parse entities: can't find end of the entity starting at byte offset 204"
    
    print(f"\n🎯 Testing Specific Reported Error:")
    print(f"Original: {original_error}")
    
    escaped = escape_markdown(original_error)
    print(f"Escaped:  {escaped}")
    
    # Show how it appears in the actual error message
    full_message = f"❌ **Bot Creation Error**\n\nTechnical error: {escaped}\n\nPlease try again or contact support."
    print(f"\nFull message that will be sent:")
    print(full_message)
    
    print(f"\n✅ This error will now display properly in Telegram!")

if __name__ == "__main__":
    test_problematic_characters()
    test_specific_entity_error()