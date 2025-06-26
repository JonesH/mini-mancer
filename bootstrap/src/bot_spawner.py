"""
BotSpawner - Concurrent management of multiple SimpleEchoBots

Handles token management, bot creation, starting/stopping, and registry
for multiple SimpleEchoBots running simultaneously.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import httpx
from dotenv import load_dotenv

from simple_echo_bot import SimpleEchoBot

load_dotenv()

logger = logging.getLogger(__name__)


class BotSpawner:
    """Manages creation and concurrent execution of multiple SimpleEchoBots."""
    
    def __init__(self):
        # Token pool management
        self.available_tokens: List[Dict[str, str]] = []
        self.bot_registry_file = Path("data/simple_bot_registry.json")
        
        # Running bots
        self.running_bots: Dict[str, SimpleEchoBot] = {}
        self.bot_tasks: Dict[str, asyncio.Task] = {}
        
        # Ensure data directory exists
        self.bot_registry_file.parent.mkdir(exist_ok=True)
        
        logger.info("BotSpawner initialized")
    
    async def initialize(self):
        """Initialize bot spawner - discover tokens and load registry."""
        logger.info("Initializing BotSpawner...")
        
        # Discover available tokens
        await self._discover_available_tokens()
        
        # Load existing bot registry
        self._load_bot_registry()
        
        logger.info(f"BotSpawner ready - {len(self.available_tokens)} tokens available")
    
    async def _discover_available_tokens(self):
        """Discover and validate available bot tokens from environment."""
        self.available_tokens = []
        
        # Find all BOT_TOKEN_* environment variables
        bot_tokens = {}
        for key, value in os.environ.items():
            if key.startswith('BOT_TOKEN_') and value:
                bot_tokens[key] = value
        
        logger.info(f"Found {len(bot_tokens)} potential bot tokens")
        
        # Validate each token
        for env_var, token in bot_tokens.items():
            try:
                validation = await self._validate_bot_token(token)
                if validation["valid"]:
                    self.available_tokens.append({
                        "env_var": env_var,
                        "token": token,
                        "username": validation["username"],
                        "name": validation["first_name"],
                        "bot_id": validation["id"]
                    })
                    logger.info(f"✅ Token valid: @{validation['username']}")
                else:
                    logger.warning(f"❌ Invalid token {env_var}: {validation['error']}")
            except Exception as e:
                logger.error(f"Error validating {env_var}: {e}")
        
        logger.info(f"✅ {len(self.available_tokens)} valid tokens available for echo bots")
    
    async def _validate_bot_token(self, token: str) -> Dict[str, Any]:
        """Validate a bot token using Telegram Bot API."""
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        bot_info = data["result"]
                        return {
                            "valid": True,
                            "id": bot_info["id"],
                            "first_name": bot_info["first_name"],
                            "username": bot_info["username"]
                        }
                
                return {"valid": False, "error": "Invalid API response"}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _load_bot_registry(self):
        """Load bot registry from JSON file."""
        if self.bot_registry_file.exists():
            try:
                with open(self.bot_registry_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded {len(data)} bots from registry")
                return data
            except Exception as e:
                logger.error(f"Failed to load bot registry: {e}")
        return {}
    
    def _save_bot_registry(self, registry_data: Dict[str, Any]):
        """Save bot registry to JSON file."""
        try:
            with open(self.bot_registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2, default=str)
            logger.debug("Bot registry saved")
        except Exception as e:
            logger.error(f"Failed to save bot registry: {e}")
    
    def _get_available_token(self) -> Optional[Dict[str, str]]:
        """Get next available token for bot creation."""
        # Load current registry to check which tokens are in use
        registry = self._load_bot_registry()
        used_tokens = {bot_data.get('token') for bot_data in registry.values()}
        
        # Find first unused token
        for token_info in self.available_tokens:
            if token_info['token'] not in used_tokens:
                return token_info
        
        return None
    
    async def create_echo_bot(self, bot_name: str, user_id: str) -> Dict[str, Any]:
        """Create a new SimpleEchoBot."""
        logger.info(f"Creating echo bot '{bot_name}' for user {user_id}")
        
        try:
            # Get available token
            token_info = self._get_available_token()
            if not token_info:
                return {
                    "success": False,
                    "error": "No available bot tokens. All tokens are in use."
                }
            
            # Create unique bot ID
            bot_id = f"{user_id}_{bot_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create SimpleEchoBot instance
            echo_bot = SimpleEchoBot(
                name=bot_name,
                username=token_info["username"],
                token=token_info["token"],
                created_by=user_id
            )
            
            # Save to registry
            registry = self._load_bot_registry()
            registry[bot_id] = {
                "bot_id": bot_id,
                "name": bot_name,
                "username": token_info["username"],
                "token": token_info["token"],
                "created_by": user_id,
                "created_at": datetime.now().isoformat(),
                "status": "created",
                "env_var": token_info["env_var"],
                "telegram_bot_id": token_info["bot_id"]
            }
            self._save_bot_registry(registry)
            
            logger.info(f"✅ Echo bot '{bot_name}' created successfully (@{token_info['username']})")
            
            return {
                "success": True,
                "bot_id": bot_id,
                "name": bot_name,
                "username": f"@{token_info['username']}",
                "status": "created",
                "telegram_link": f"https://t.me/{token_info['username']}",
                "message": f"Echo bot '{bot_name}' created successfully!"
            }
            
        except Exception as e:
            logger.error(f"Failed to create echo bot '{bot_name}': {e}")
            return {
                "success": False,
                "error": f"Bot creation failed: {str(e)}"
            }
    
    async def start_bot(self, bot_name: str, user_id: str) -> Dict[str, Any]:
        """Start a specific echo bot."""
        try:
            # Find bot in registry
            registry = self._load_bot_registry()
            bot_data = None
            bot_id = None
            
            for bid, data in registry.items():
                if data.get("name") == bot_name and data.get("created_by") == user_id:
                    bot_data = data
                    bot_id = bid
                    break
            
            if not bot_data:
                return {
                    "success": False,
                    "error": f"Bot '{bot_name}' not found in your bot list"
                }
            
            # Check if already running
            if bot_id in self.running_bots:
                return {
                    "success": True,
                    "message": f"Bot '{bot_name}' is already running",
                    "username": f"@{bot_data['username']}",
                    "status": "running"
                }
            
            # Create and start echo bot
            echo_bot = SimpleEchoBot(
                name=bot_data["name"],
                username=bot_data["username"],
                token=bot_data["token"],
                created_by=bot_data["created_by"]
            )
            
            start_result = await echo_bot.start()
            
            if start_result["success"]:
                # Track running bot
                self.running_bots[bot_id] = echo_bot
                
                # Update registry status
                registry[bot_id]["status"] = "running"
                registry[bot_id]["last_started"] = datetime.now().isoformat()
                self._save_bot_registry(registry)
                
                logger.info(f"✅ Started echo bot '{bot_name}' (@{bot_data['username']})")
                
                return {
                    "success": True,
                    "message": f"Bot '{bot_name}' started successfully",
                    "username": f"@{bot_data['username']}",
                    "status": "running",
                    "telegram_link": f"https://t.me/{bot_data['username']}"
                }
            else:
                return {
                    "success": False,
                    "error": start_result.get("error", "Failed to start bot")
                }
            
        except Exception as e:
            logger.error(f"Failed to start bot '{bot_name}': {e}")
            return {
                "success": False,
                "error": f"Failed to start bot: {str(e)}"
            }
    
    async def stop_bot(self, bot_name: str, user_id: str) -> Dict[str, Any]:
        """Stop a specific echo bot."""
        try:
            # Find bot in registry
            registry = self._load_bot_registry()
            bot_data = None
            bot_id = None
            
            for bid, data in registry.items():
                if data.get("name") == bot_name and data.get("created_by") == user_id:
                    bot_data = data
                    bot_id = bid
                    break
            
            if not bot_data:
                return {
                    "success": False,
                    "error": f"Bot '{bot_name}' not found in your bot list"
                }
            
            # Check if running
            if bot_id not in self.running_bots:
                return {
                    "success": True,
                    "message": f"Bot '{bot_name}' is already stopped",
                    "username": f"@{bot_data['username']}",
                    "status": "stopped"
                }
            
            # Stop the bot
            echo_bot = self.running_bots[bot_id]
            stop_result = await echo_bot.stop()
            
            if stop_result["success"]:
                # Remove from running bots
                del self.running_bots[bot_id]
                
                # Update registry status
                registry[bot_id]["status"] = "stopped"
                registry[bot_id]["last_stopped"] = datetime.now().isoformat()
                self._save_bot_registry(registry)
                
                logger.info(f"✅ Stopped echo bot '{bot_name}' (@{bot_data['username']})")
                
                return {
                    "success": True,
                    "message": f"Bot '{bot_name}' stopped successfully",
                    "username": f"@{bot_data['username']}",
                    "status": "stopped"
                }
            else:
                return {
                    "success": False,
                    "error": stop_result.get("error", "Failed to stop bot")
                }
            
        except Exception as e:
            logger.error(f"Failed to stop bot '{bot_name}': {e}")
            return {
                "success": False,
                "error": f"Failed to stop bot: {str(e)}"
            }
    
    async def list_user_bots(self, user_id: str) -> List[Dict[str, Any]]:
        """List all bots created by a specific user."""
        registry = self._load_bot_registry()
        user_bots = []
        
        for bot_id, bot_data in registry.items():
            if bot_data.get("created_by") == user_id:
                # Check if currently running
                is_running = bot_id in self.running_bots
                current_status = "running" if is_running else "stopped"
                
                user_bots.append({
                    "bot_id": bot_id,
                    "name": bot_data["name"],
                    "username": f"@{bot_data['username']}",
                    "status": current_status,
                    "created": bot_data.get("created_at", "Unknown"),
                    "telegram_link": f"https://t.me/{bot_data['username']}"
                })
        
        # Sort by creation date (newest first)
        user_bots.sort(key=lambda x: x["created"], reverse=True)
        
        return user_bots
    
    async def get_bot_status(self, bot_name: str, user_id: str) -> Dict[str, Any]:
        """Get detailed status of a specific bot."""
        registry = self._load_bot_registry()
        
        for bot_id, bot_data in registry.items():
            if bot_data.get("name") == bot_name and bot_data.get("created_by") == user_id:
                is_running = bot_id in self.running_bots
                current_status = "running" if is_running else "stopped"
                
                # Get live stats if running
                live_stats = {}
                if is_running:
                    echo_bot = self.running_bots[bot_id]
                    live_stats = echo_bot.get_status()
                
                return {
                    "found": True,
                    "bot_id": bot_id,
                    "name": bot_data["name"],
                    "username": f"@{bot_data['username']}",
                    "status": current_status,
                    "created": bot_data.get("created_at", "Unknown"),
                    "telegram_link": f"https://t.me/{bot_data['username']}",
                    "live_stats": live_stats
                }
        
        return {"found": False}
    
    async def shutdown(self):
        """Shutdown all running bots."""
        logger.info("Shutting down BotSpawner...")
        
        # Stop all running bots
        stop_tasks = []
        for bot_id, echo_bot in self.running_bots.items():
            stop_tasks.append(echo_bot.stop())
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        self.running_bots.clear()
        self.bot_tasks.clear()
        
        logger.info("✅ BotSpawner shutdown complete")
    
    def get_spawner_stats(self) -> Dict[str, Any]:
        """Get overall spawner statistics."""
        registry = self._load_bot_registry()
        
        return {
            "available_tokens": len(self.available_tokens),
            "total_bots_created": len(registry),
            "currently_running": len(self.running_bots),
            "registry_file": str(self.bot_registry_file),
            "tokens_in_use": len(registry),
            "tokens_available": len(self.available_tokens) - len(registry)
        }


async def test_bot_spawner():
    """Test BotSpawner functionality."""
    print("🚀 Testing BotSpawner...")
    
    spawner = BotSpawner()
    await spawner.initialize()
    
    # Test stats
    stats = spawner.get_spawner_stats()
    print(f"Spawner stats: {stats}")
    
    # Test bot creation (won't actually work without valid tokens)
    print("✅ BotSpawner test completed")


if __name__ == "__main__":
    asyncio.run(test_bot_spawner())