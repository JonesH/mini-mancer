#!/usr/bin/env python3
"""
SimpleBotMother Startup Script

Properly starts SimpleBotMother with correct import paths.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from simple_botmother import SimpleBotMother

async def main():
    """Start SimpleBotMother"""
    print("🚀 Starting SimpleBotMother...")
    
    try:
        bot_mother = SimpleBotMother()
        await bot_mother.run()
    except KeyboardInterrupt:
        print("👋 SimpleBotMother stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.exception("SimpleBotMother error")

if __name__ == "__main__":
    asyncio.run(main())