"""
Token Pool Manager for Mini-Mancer

Manages a pool of bot tokens for concurrent bot deployment.
Provides token allocation, deallocation, and persistence.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel


logger = logging.getLogger(__name__)


class BotInstance(BaseModel):
    """Represents an active bot instance"""
    token: str
    name: str
    username: str | None = None
    status: str = "starting"  # starting, running, stopping, stopped, error
    created_at: datetime
    user_id: str | None = None
    personality_type: str | None = None


class TokenPoolManager:
    """Manages a pool of bot tokens for concurrent bot deployment"""

    def __init__(self, pool_file: Path = Path("bot_token_pool.json")):
        self.pool_file = pool_file
        self.active_bots: dict[str, BotInstance] = {}
        self.available_tokens: list[str] = []
        self.allocated_tokens: set[str] = set()
        
        self._load_pool()

    def _load_pool(self) -> None:
        """Load token pool and active bots from persistence file"""
        try:
            if self.pool_file.exists():
                with open(self.pool_file, 'r') as f:
                    data = json.load(f)
                
                # Load available tokens
                self.available_tokens = data.get("available_tokens", [])
                
                # Load active bots
                active_bots_data = data.get("active_bots", {})
                for token, bot_data in active_bots_data.items():
                    # Parse datetime
                    bot_data["created_at"] = datetime.fromisoformat(bot_data["created_at"])
                    self.active_bots[token] = BotInstance(**bot_data)
                    self.allocated_tokens.add(token)
                
                logger.info(f"Loaded token pool: {len(self.available_tokens)} available, {len(self.active_bots)} active bots")
            else:
                logger.info("No token pool file found, initializing empty pool")
                self._initialize_from_environment()
                
        except Exception as e:
            logger.error(f"Failed to load token pool: {e}")
            self._initialize_from_environment()

    def _initialize_from_environment(self) -> None:
        """Initialize token pool from environment variables"""
        import os
        
        # Check for BOT_TOKEN_POOL (JSON array)
        pool_env = os.getenv("BOT_TOKEN_POOL")
        if pool_env:
            try:
                self.available_tokens = json.loads(pool_env)
                logger.info(f"Initialized {len(self.available_tokens)} tokens from BOT_TOKEN_POOL")
                return
            except json.JSONDecodeError:
                logger.warning("BOT_TOKEN_POOL is not valid JSON, falling back to individual tokens")
        
        # Fallback to individual BOT_TOKEN_X variables
        token_index = 1
        while True:
            token = os.getenv(f"BOT_TOKEN_{token_index}")
            if not token:
                break
            self.available_tokens.append(token)
            token_index += 1
        
        logger.info(f"Initialized {len(self.available_tokens)} tokens from BOT_TOKEN_X variables")

    def _save_pool(self) -> None:
        """Save token pool and active bots to persistence file"""
        try:
            data = {
                "available_tokens": self.available_tokens,
                "active_bots": {}
            }
            
            # Serialize active bots
            for token, bot in self.active_bots.items():
                bot_data = bot.model_dump()
                bot_data["created_at"] = bot.created_at.isoformat()
                data["active_bots"][token] = bot_data
            
            with open(self.pool_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"Saved token pool to {self.pool_file}")
            
        except Exception as e:
            logger.error(f"Failed to save token pool: {e}")

    def get_available_token(self) -> str | None:
        """Get an available token from the pool"""
        available = [token for token in self.available_tokens if token not in self.allocated_tokens]
        
        if not available:
            logger.warning("No available tokens in pool")
            return None
            
        token = available[0]
        self.allocated_tokens.add(token)
        logger.info(f"Allocated token: {token[:10]}...")
        return token

    def allocate_token(self, token: str, bot_name: str, user_id: str | None = None, 
                      personality_type: str | None = None) -> BotInstance:
        """Allocate a token to a new bot instance"""
        if token in self.active_bots:
            raise ValueError(f"Token already allocated to bot: {self.active_bots[token].name}")
        
        bot_instance = BotInstance(
            token=token,
            name=bot_name,
            created_at=datetime.now(),
            user_id=user_id,
            personality_type=personality_type
        )
        
        self.active_bots[token] = bot_instance
        self.allocated_tokens.add(token)
        self._save_pool()
        
        logger.info(f"Allocated token to bot '{bot_name}' for user {user_id}")
        return bot_instance

    def deallocate_token(self, token: str) -> bool:
        """Deallocate a token and remove bot instance"""
        if token not in self.active_bots:
            logger.warning(f"Token not found in active bots: {token[:10]}...")
            return False
        
        bot_name = self.active_bots[token].name
        del self.active_bots[token]
        self.allocated_tokens.discard(token)
        self._save_pool()
        
        logger.info(f"Deallocated token from bot '{bot_name}'")
        return True

    def update_bot_status(self, token: str, status: str, username: str | None = None) -> bool:
        """Update bot status and optionally username"""
        if token not in self.active_bots:
            logger.warning(f"Cannot update status for unknown token: {token[:10]}...")
            return False
        
        self.active_bots[token].status = status
        if username:
            self.active_bots[token].username = username
        
        self._save_pool()
        logger.debug(f"Updated bot '{self.active_bots[token].name}' status to '{status}'")
        return True

    def get_active_bots(self) -> list[BotInstance]:
        """Get list of all active bot instances"""
        return list(self.active_bots.values())

    def get_bot_by_name(self, name: str) -> BotInstance | None:
        """Find bot by name"""
        for bot in self.active_bots.values():
            if bot.name.lower() == name.lower():
                return bot
        return None

    def get_running_bots(self) -> list[BotInstance]:
        """Get list of running bot instances"""
        return [bot for bot in self.active_bots.values() if bot.status == "running"]

    def stop_all_bots(self) -> None:
        """Mark all bots as stopping (actual bot stopping handled elsewhere)"""
        for bot in self.active_bots.values():
            if bot.status == "running":
                bot.status = "stopping"
        self._save_pool()
        logger.info(f"Marked {len(self.active_bots)} bots as stopping")

    def get_pool_stats(self) -> dict[str, Any]:
        """Get statistics about the token pool"""
        total_tokens = len(self.available_tokens)
        allocated_count = len(self.allocated_tokens)
        available_count = total_tokens - allocated_count
        
        status_counts = {}
        for bot in self.active_bots.values():
            status_counts[bot.status] = status_counts.get(bot.status, 0) + 1
        
        return {
            "total_tokens": total_tokens,
            "available_tokens": available_count,
            "allocated_tokens": allocated_count,
            "active_bots": len(self.active_bots),
            "status_breakdown": status_counts
        }

    def cleanup_stopped_bots(self) -> int:
        """Remove bots with 'stopped' or 'error' status from active list"""
        stopped_tokens = []
        for token, bot in self.active_bots.items():
            if bot.status in ["stopped", "error"]:
                stopped_tokens.append(token)
        
        for token in stopped_tokens:
            self.deallocate_token(token)
        
        logger.info(f"Cleaned up {len(stopped_tokens)} stopped bots")
        return len(stopped_tokens)

    def add_token(self, token: str) -> bool:
        """Add a new token to the available pool"""
        # Validate token format
        if not self._is_valid_token_format(token):
            logger.error(f"Invalid token format: {token[:10]}...")
            return False
        
        # Check if token already exists
        if token in self.available_tokens:
            logger.warning(f"Token already in pool: {token[:10]}...")
            return False
        
        # Check if token is currently allocated
        if token in self.allocated_tokens:
            logger.warning(f"Token already allocated: {token[:10]}...")
            return False
        
        # Add to available tokens
        self.available_tokens.append(token)
        self._save_pool()
        
        logger.info(f"Added new token to pool: {token[:10]}...")
        return True
    
    def remove_token(self, token: str) -> bool:
        """Remove a token from the pool (only if not allocated)"""
        if token in self.allocated_tokens:
            logger.error(f"Cannot remove allocated token: {token[:10]}...")
            return False
        
        if token in self.available_tokens:
            self.available_tokens.remove(token)
            self._save_pool()
            logger.info(f"Removed token from pool: {token[:10]}...")
            return True
        
        logger.warning(f"Token not found in pool: {token[:10]}...")
        return False
    
    def _is_valid_token_format(self, token: str) -> bool:
        """Validate basic token format (bot_id:token_hash)"""
        if not token or len(token) < 10:
            return False
        parts = token.split(":")
        if len(parts) != 2:
            return False
        # First part should be numeric (bot ID)
        if not parts[0].isdigit():
            return False
        # Second part should be the token hash (at least 5 chars)
        if len(parts[1]) < 5:
            return False
        return True