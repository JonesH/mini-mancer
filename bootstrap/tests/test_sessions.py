"""Test which session files are working"""

import asyncio
import logging
from src.telethon_client import TelethonSessionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_session(session_name):
    """Test if a session works"""
    try:
        logger.info(f"Testing session: {session_name}")
        session_manager = TelethonSessionManager(session_name)
        await session_manager.initialize_client()
        is_valid = await session_manager.validate_session()
        await session_manager.disconnect()
        
        if is_valid:
            logger.info(f"✅ {session_name} - WORKING")
            return True
        else:
            logger.info(f"❌ {session_name} - INVALID")
            return False
    except Exception as e:
        logger.info(f"❌ {session_name} - ERROR: {e}")
        return False

async def test_all_sessions():
    sessions = [
        "bootstrap_session",
        "botmother_manager", 
        "live_botmother_test",
        "phase1_test_session"
    ]
    
    working_sessions = []
    for session in sessions:
        if await test_session(session):
            working_sessions.append(session)
    
    logger.info(f"Working sessions: {working_sessions}")
    return working_sessions

if __name__ == "__main__":
    asyncio.run(test_all_sessions())