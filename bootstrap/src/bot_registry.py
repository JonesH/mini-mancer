"""
PostgreSQL Bot Registry - Track created bots in database storage.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import Column, String, DateTime, Integer, JSON, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

Base = declarative_base()


class BotRecord(Base):
    """SQLAlchemy model for bot registry."""
    __tablename__ = 'bot_registry'
    
    bot_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    username = Column(String, nullable=False)
    token = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    description = Column(String)
    bot_data = Column(JSON)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class BotRegistry:
    """PostgreSQL-based bot registry for tracking created bots with task management."""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "postgresql+psycopg://ai:ai@localhost:5532/ai")
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._ensure_tables_exist()
        
        # Child bot task management
        self._running_bots: dict[str, asyncio.Task] = {}
        self._bot_applications: dict[str, Any] = {}
    
    def _ensure_tables_exist(self):
        """Create tables if they don't exist."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Bot registry tables ensured")
        except Exception as e:
            logger.error(f"Failed to create bot registry tables: {e}")
    
    def _get_session(self):
        """Get database session."""
        return self.SessionLocal()
    
    def add_bot(self, bot_id: str, bot_data: dict[str, Any]) -> bool:
        """Add a new bot to the registry."""
        try:
            with self._get_session() as session:
                bot_record = BotRecord(
                    bot_id=bot_id,
                    name=bot_data.get("name", "Unknown Bot"),
                    username=bot_data.get("username", "unknown_bot"),
                    token=bot_data.get("token", ""),
                    created_by=bot_data.get("created_by", "unknown"),
                    description=bot_data.get("description", ""),
                    bot_data=bot_data,
                    status="active"
                )
                session.add(bot_record)
                session.commit()
                
            logger.info(f"Added bot {bot_id} to registry")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add bot {bot_id}: {e}")
            return False
    
    def get_bot(self, bot_id: str) -> dict[str, Any] | None:
        """Get bot data by ID."""
        try:
            with self._get_session() as session:
                bot_record = session.query(BotRecord).filter_by(bot_id=bot_id).first()
                if bot_record:
                    return {
                        "bot_id": bot_record.bot_id,
                        "name": bot_record.name,
                        "username": bot_record.username,
                        "token": bot_record.token,
                        "created_by": bot_record.created_by,
                        "description": bot_record.description,
                        "status": bot_record.status,
                        "created_at": bot_record.created_at.isoformat(),
                        "last_updated": bot_record.last_updated.isoformat(),
                        **bot_record.bot_data
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get bot {bot_id}: {e}")
            return None
    
    def list_bots(self, user_id: str = None) -> list[dict[str, Any]]:
        """List all bots, optionally filtered by user."""
        try:
            with self._get_session() as session:
                query = session.query(BotRecord)
                if user_id:
                    query = query.filter_by(created_by=user_id)
                
                bots = []
                for bot_record in query.order_by(BotRecord.created_at.desc()).all():
                    bots.append({
                        "bot_id": bot_record.bot_id,
                        "name": bot_record.name,
                        "username": bot_record.username,
                        "created_by": bot_record.created_by,
                        "description": bot_record.description,
                        "status": bot_record.status,
                        "created_at": bot_record.created_at.isoformat(),
                        "last_updated": bot_record.last_updated.isoformat()
                    })
                
                return bots
        except Exception as e:
            logger.error(f"Failed to list bots: {e}")
            return []
    
    def update_bot_status(self, bot_id: str, status: str) -> bool:
        """Update bot status (active, stopped, error)."""
        try:
            with self._get_session() as session:
                bot_record = session.query(BotRecord).filter_by(bot_id=bot_id).first()
                if bot_record:
                    bot_record.status = status
                    bot_record.last_updated = datetime.now()
                    session.commit()
                    logger.info(f"Updated bot {bot_id} status to {status}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to update bot {bot_id} status: {e}")
            return False
    
    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        try:
            with self._get_session() as session:
                total_created = session.query(BotRecord).count()
                active_bots = session.query(BotRecord).filter_by(status="active").count()
                
                return {
                    "total_created": total_created,
                    "active_bots": active_bots
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"total_created": 0, "active_bots": 0}
    
    def get_available_token(self) -> str | None:
        """Get next available bot token from environment."""
        try:
            # Check for available bot tokens in environment
            for i in range(1, 6):  # Check BOT_TOKEN_1 through BOT_TOKEN_5
                token_key = f"BOT_TOKEN_{i}"
                token = os.getenv(token_key)
                
                if token:
                    # Check if this token is already in use
                    with self._get_session() as session:
                        existing_bot = session.query(BotRecord).filter_by(token=token).first()
                        if not existing_bot:
                            logger.info(f"Found available token: {token_key}")
                            return token
            
            logger.warning("No available bot tokens found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to check available tokens: {e}")
            return None
    
    async def start_child_bot(self, bot_id: str, bot_application) -> bool:
        """Start a child bot as async task."""
        try:
            if bot_id in self._running_bots:
                logger.warning(f"Bot {bot_id} is already running")
                return False
            
            # Create async task for the bot
            async def run_bot():
                try:
                    await bot_application.initialize()
                    await bot_application.start()
                    await bot_application.updater.start_polling()
                    
                    # Keep running
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    logger.info(f"Bot {bot_id} task cancelled")
                except Exception as e:
                    logger.error(f"Bot {bot_id} error: {e}")
                finally:
                    # Cleanup
                    try:
                        await bot_application.updater.stop()
                        await bot_application.stop()
                        await bot_application.shutdown()
                    except Exception as cleanup_error:
                        logger.error(f"Bot {bot_id} cleanup error: {cleanup_error}")
            
            # Start the bot task
            task = asyncio.create_task(run_bot())
            self._running_bots[bot_id] = task
            self._bot_applications[bot_id] = bot_application
            
            # Update status in database
            self.update_bot_status(bot_id, "running")
            
            logger.info(f"Started child bot {bot_id} as async task")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start bot {bot_id}: {e}")
            return False
    
    async def stop_child_bot(self, bot_id: str) -> bool:
        """Stop a running child bot."""
        try:
            if bot_id not in self._running_bots:
                logger.warning(f"Bot {bot_id} is not running")
                return False
            
            # Cancel the task
            task = self._running_bots[bot_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            # Cleanup
            del self._running_bots[bot_id]
            if bot_id in self._bot_applications:
                del self._bot_applications[bot_id]
            
            # Update status in database
            self.update_bot_status(bot_id, "stopped")
            
            logger.info(f"Stopped child bot {bot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop bot {bot_id}: {e}")
            return False
    
    def get_running_bots(self) -> list[str]:
        """Get list of currently running bot IDs."""
        return list(self._running_bots.keys())
    
    async def stop_all_child_bots(self):
        """Stop all running child bots."""
        logger.info(f"Stopping {len(self._running_bots)} child bots...")
        
        # Cancel all tasks
        for bot_id, task in self._running_bots.items():
            task.cancel()
        
        # Wait for all to complete
        if self._running_bots:
            await asyncio.gather(*self._running_bots.values(), return_exceptions=True)
        
        # Clear all tracking
        self._running_bots.clear()
        self._bot_applications.clear()
        
        logger.info("All child bots stopped")


async def test_bot_registry():
    """Test bot registry functionality with task management."""
    print("📊 Testing PostgreSQL bot registry with task management...")
    
    registry = BotRegistry()
    
    # Test adding a bot
    bot_data = {
        "name": "Test Bot",
        "username": "test_bot",
        "token": "123456:TEST_TOKEN",
        "created_by": "user123",
        "description": "A test bot"
    }
    
    success = registry.add_bot("test_bot_1", bot_data)
    print(f"Add bot result: {success}")
    
    # Test getting bot
    retrieved = registry.get_bot("test_bot_1")
    print(f"Retrieved bot: {retrieved}")
    
    # Test listing bots
    bots = registry.list_bots()
    print(f"All bots: {len(bots)}")
    
    # Test stats
    stats = registry.get_stats()
    print(f"Stats: {stats}")
    
    # Test available token
    token = registry.get_available_token()
    print(f"Available token: {token[:20] if token else 'None'}...")
    
    # Test task management
    running_bots = registry.get_running_bots()
    print(f"Running bots: {running_bots}")
    
    print("✅ Bot registry test completed")


if __name__ == "__main__":
    asyncio.run(test_bot_registry())