"""
Bootstrap Mini-Mancer MVP - Main Entry Point

Runs SimpleBotMother for creating and managing simple echo bots.
No AI involved - pure hardcoded responses and echo bot functionality.
"""

import asyncio
import logging

from dotenv import load_dotenv

from src.simple_botmother import SimpleBotMother

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for SimpleBotMother system."""
    logger.info("Starting Bootstrap Mini-Mancer MVP with SimpleBotMother")

    try:
        # Create and run SimpleBotMother
        bot_mother = SimpleBotMother()
        await bot_mother.run()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
