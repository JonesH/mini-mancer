"""
Simple Phase 1 Test - Test existing session and Agno core

This test uses an existing authenticated Telethon session to avoid interactive auth.
"""

import asyncio
import logging
from pathlib import Path

from src.telethon_client import TelethonSessionManager
from src.agno_core import AgnoIntelligenceCore

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_simple_foundation():
    """Test Phase 1 foundation with existing session."""
    logger.info("Starting Phase 1 Foundation Test")
    
    # Test Agno intelligence first (no auth required)
    logger.info("Testing Agno Intelligence Core")
    intelligence = AgnoIntelligenceCore("simple_test_agent")
    agent = intelligence.initialize_agent()
    
    # Test basic Agno conversation
    response = await intelligence.process_message(
        "Hello! This is a test of the Phase 1 Agno foundation.",
        "test_user_123"
    )
    logger.info(f"Agno response received: {len(response)} characters")
    
    # Test memory
    memory_response = await intelligence.process_message(
        "What did I just say to you?",
        "test_user_123"
    )
    logger.info(f"Memory test response: {len(memory_response)} characters")
    
    # Test Telethon session
    logger.info("Testing Telethon Session Management")
    
    session_manager = TelethonSessionManager("bootstrap_session")
    
    # Check if we can initialize without interactive auth
    client = await session_manager.initialize_client()
    is_valid = await session_manager.validate_session()
    
    if is_valid:
        logger.info("Telethon session validated successfully")
    else:
        logger.warning("Telethon session requires re-authentication")
    
    await session_manager.disconnect()
    
    logger.info("Phase 1 Foundation Test completed successfully")
    logger.info("Ready for Phase 2 development")
    
    return True


if __name__ == "__main__":
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Run simple test
    asyncio.run(test_simple_foundation())