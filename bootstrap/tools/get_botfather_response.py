"""
Get the full BotFather response to extract the token manually
"""

import asyncio
import logging
from src.telethon_client import TelethonSessionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_last_botfather_message():
    """Get the last message from BotFather to see the token"""
    session_manager = TelethonSessionManager("bootstrap_session")
    
    await session_manager.initialize_client()
    
    # Get recent messages from BotFather
    messages = await session_manager.client.get_messages("BotFather", limit=5)
    
    logger.info("Recent BotFather messages:")
    for i, msg in enumerate(messages):
        if msg.text:
            logger.info(f"Message {i+1}:")
            logger.info(msg.text)
            logger.info("-" * 50)
    
    await session_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(get_last_botfather_message())