"""
Telegram Integration Module for Mini-Mancer

Handles Telegram bot creation, management, and lifecycle operations.
Extracted from prototype_agent.py for better separation of concerns.
"""

import asyncio
import logging

from .agents import TelegramBotTemplate
from .constants import (
    ERROR_MESSAGES,
    format_advanced_compilation,
    format_bot_success,
    format_requirements_error,
)
from .models.agent_dna import AgentCapability, AgentDNA, AgentPersonality, PlatformTarget
from .models.bot_requirements import BotArchitect, BotRequirements, RequirementsValidator
from .token_pool_manager import TokenPoolManager


logger = logging.getLogger(__name__)


class TelegramBotManager:
    """Manages Telegram bot creation and lifecycle operations using token pool"""

    def __init__(self, created_bot_token: str | None = None):
        # Initialize token pool manager
        self.token_pool = TokenPoolManager()
        
        # Legacy single bot support (for backwards compatibility)
        self.created_bot_token = created_bot_token
        self.active_created_bot: TelegramBotTemplate | None = None
        self.created_bot_state: str = "none"  # none, creating, starting, running, stopping, error
        self.created_bot_start_task = None  # Track async task for proper cleanup
        
        # Multi-bot support with token pool
        self.active_bots: dict[str, TelegramBotTemplate] = {}  # token -> bot instance
        self.bot_start_tasks: dict[str, asyncio.Task] = {}  # token -> start task
        
        # Add legacy token to pool if provided and not already there
        if created_bot_token and created_bot_token not in self.token_pool.available_tokens:
            self.token_pool.available_tokens.append(created_bot_token)
            self.token_pool._save_pool()

        pool_stats = self.token_pool.get_pool_stats()
        if pool_stats["total_tokens"] == 0:
            logger.warning("⚠️  No bot tokens configured - bot creation will be disabled")
        else:
            logger.info(f"🎯 Token pool initialized: {pool_stats['total_tokens']} tokens available")
            
        # Clean up any bots that were stopped in previous sessions
        self.token_pool.cleanup_stopped_bots()

    def is_bot_creation_available(self) -> bool:
        """Check if bot creation is available"""
        return self.token_pool.get_pool_stats()["available_tokens"] > 0

    def is_bot_active(self) -> bool:
        """Check if any bot is currently active (legacy compatibility)"""
        return self.created_bot_state in ["creating", "starting", "running"] or len(self.active_bots) > 0
    
    def get_active_bot_count(self) -> int:
        """Get number of currently active bots"""
        return len(self.active_bots)
    
    def get_running_bot_count(self) -> int:
        """Get number of currently running bots"""
        return len(self.token_pool.get_running_bots())
    
    def list_active_bots(self) -> list[dict]:
        """Get list of active bots with details"""
        bots = []
        for bot_instance in self.token_pool.get_active_bots():
            bots.append({
                "name": bot_instance.name,
                "username": bot_instance.username,
                "status": bot_instance.status,
                "created_at": bot_instance.created_at,
                "personality_type": bot_instance.personality_type,
                "user_id": bot_instance.user_id
            })
        return bots

    async def create_bot_instant(
        self, bot_name: str, bot_purpose: str, personality: str = "helpful", user_id: str | None = None
    ) -> str:
        """
        Create a new Telegram bot with the specified parameters using token pool.

        Args:
            bot_name: Name for the new bot
            bot_purpose: Purpose/description of what the bot does
            personality: Personality trait (helpful, professional, casual, etc.)
            user_id: Optional user ID for tracking who created the bot

        Returns:
            Success message with bot information and t.me link
        """
        # Check if bot creation is available
        if not self.is_bot_creation_available():
            return ERROR_MESSAGES["bot_creation_disabled"]

        # Validate inputs
        if not bot_name or len(bot_name.strip()) < 2:
            return ERROR_MESSAGES["invalid_bot_name"]
        if not bot_purpose or len(bot_purpose.strip()) < 5:
            return ERROR_MESSAGES["invalid_bot_purpose"]

        # Get available token from pool
        token = self.token_pool.get_available_token()
        if not token:
            pool_stats = self.token_pool.get_pool_stats()
            return f"❌ No available bot tokens in pool. Active bots: {pool_stats['allocated_tokens']}/{pool_stats['total_tokens']}"

        try:
            # Map personality string to enum
            personality_map = {
                "helpful": AgentPersonality.HELPFUL,
                "professional": AgentPersonality.PROFESSIONAL,
                "casual": AgentPersonality.CASUAL,
                "enthusiastic": AgentPersonality.ENTHUSIASTIC,
                "witty": AgentPersonality.WITTY,
                "calm": AgentPersonality.CALM,
                "playful": AgentPersonality.PLAYFUL,
            }

            personality_trait = personality_map.get(personality.lower(), AgentPersonality.HELPFUL)

            # Create new bot DNA
            new_bot_dna = AgentDNA(
                name=bot_name,
                purpose=bot_purpose,
                personality=[personality_trait],
                capabilities=[AgentCapability.CHAT, AgentCapability.IMAGE_ANALYSIS],
                target_platform=PlatformTarget.TELEGRAM,
            )

            # Create bot username
            bot_username = bot_name.lower().replace(" ", "_") + "_bot"

            # Allocate token in pool and create bot instance record
            bot_instance = self.token_pool.allocate_token(
                token=token,
                bot_name=bot_name,
                user_id=user_id,
                personality_type=personality_trait.value
            )

            # Create the bot instance
            new_bot = TelegramBotTemplate(agent_dna=new_bot_dna, bot_token=token)

            # Store in active bots
            self.active_bots[token] = new_bot
            
            # Update status to created
            self.token_pool.update_bot_status(token, "created", bot_username)

            # Log the new bot creation
            logger.info("\n🔧 New Bot Created:")
            logger.info(f"   Name: {bot_name}")
            logger.info(f"   Purpose: {bot_purpose}")
            logger.info(f"   Personality: {personality_trait.value}")
            logger.info(f"   Capabilities: {[cap.value for cap in new_bot_dna.capabilities]}")
            logger.info(f"   Platform: {new_bot_dna.target_platform.value}")
            logger.info(f"   Token: {token[:10]}...")
            logger.info(f"   User: {user_id}")
            logger.info("")

            # Get pool stats for status message
            pool_stats = self.token_pool.get_pool_stats()
            status_msg = f"\n\n🎯 **Token Pool Status**: {pool_stats['allocated_tokens']}/{pool_stats['total_tokens']} tokens in use"
            
            return format_bot_success(bot_name, bot_purpose, personality_trait.value, bot_username) + status_msg

        except Exception as e:
            # Deallocate token on error
            self.token_pool.deallocate_token(token)
            if token in self.active_bots:
                del self.active_bots[token]
            logger.error(f"❌ Bot creation failed: {e}")
            return ERROR_MESSAGES["bot_creation_error"].format(error=str(e))

    def create_bot_advanced(
        self, requirements: BotRequirements, bot_compilation_queue: dict
    ) -> str:
        """
        Create a sophisticated bot using comprehensive requirements.

        Args:
            requirements: Complete bot requirements specification
            bot_compilation_queue: Queue to track compilation status

        Returns:
            Status message about bot compilation process
        """
        try:
            # Validate requirements
            validation_result = RequirementsValidator.validate_requirements(requirements)

            if not validation_result["valid"]:
                issues_text = "\n".join([f"• {issue}" for issue in validation_result["issues"]])
                return format_requirements_error(issues_text)

            # Generate comprehensive system prompt
            BotArchitect.generate_system_prompt(requirements)
            BotArchitect.generate_agno_agent_config(requirements)

            logger.info("\n🏗️  Advanced Bot Creation:")
            logger.info(f"   Name: {requirements.name}")
            logger.info(f"   Complexity: {requirements.complexity_level.value}")
            logger.info(f"   Quality Score: {validation_result['score']}/100")
            logger.info(f"   Tools: {[tool.name for tool in requirements.selected_tools]}")
            logger.info(f"   OpenServ Required: {requirements.openserv_workflow_required}")

            if requirements.openserv_workflow_required:
                # For now, simulate OpenServ workflow
                compilation_id = f"bot_comp_{len(bot_compilation_queue) + 1}"

                # Store in compilation queue
                from datetime import datetime

                bot_compilation_queue[compilation_id] = {
                    "requirements": requirements,
                    "status": "compiling",
                    "progress": 75,
                    "created_at": datetime.now(),
                }

                return format_advanced_compilation(requirements.name, validation_result["score"])
            else:
                # Direct creation for simpler bots
                personality_map = {
                    "analytical": AgentPersonality.PROFESSIONAL,
                    "empathetic": AgentPersonality.HELPFUL,
                    "enthusiastic": AgentPersonality.ENTHUSIASTIC,
                    "creative": AgentPersonality.CREATIVE,
                    "professional": AgentPersonality.PROFESSIONAL,
                    "humorous": AgentPersonality.WITTY,
                }

                # Use first personality trait or default to helpful
                personality_trait = AgentPersonality.HELPFUL
                if requirements.personality_traits:
                    trait_name = requirements.personality_traits[0].lower()
                    personality_trait = personality_map.get(trait_name, AgentPersonality.HELPFUL)

                # Create bot DNA from requirements
                new_bot_dna = AgentDNA(
                    name=requirements.name,
                    purpose=requirements.purpose,
                    personality=[personality_trait],
                    capabilities=[AgentCapability.CHAT, AgentCapability.IMAGE_ANALYSIS],
                    target_platform=PlatformTarget.TELEGRAM,
                )

                # Create the bot instance
                new_bot = TelegramBotTemplate(
                    agent_dna=new_bot_dna, bot_token=self.created_bot_token
                )

                # Store the active created bot
                self.active_created_bot = new_bot
                self.created_bot_state = "created"

                return (
                    f"✅ **{requirements.name}** has been created successfully!\n\n"
                    f"**Quality Score:** {validation_result['score']}/100\n"
                    f"**Complexity:** {requirements.complexity_level.value}\n"
                    f"**Tools:** {len(requirements.selected_tools)} integrated\n\n"
                    f"Your bot is ready to use!"
                )

        except Exception as e:
            logger.error(f"❌ Advanced bot creation failed: {e}")
            return f"❌ **Bot creation failed**\n\nError: {str(e)}"

    async def start_created_bot(self, bot_template: TelegramBotTemplate) -> str:
        """Start the created bot with enhanced lifecycle management"""
        if self.created_bot_state != "created":
            return "❌ No bot ready to start"

        try:
            self.created_bot_state = "starting"

            # Get the bot token from the template
            if not bot_template.bot_token:
                self.created_bot_state = "error"
                return "❌ No bot token available for deployment"

            # Import required Telegram components
            from telegram import Bot
            from telegram.ext import Application, MessageHandler, filters

            # Create Telegram application for the new bot
            bot_application = Application.builder().token(bot_template.bot_token).build()

            # Add message handler for the bot
            async def handle_bot_message(update, context):
                """Handle messages sent to the created bot"""
                try:
                    if not update.message or not update.message.text:
                        return

                    # Prepare message data for the bot template (matching expected format)
                    message_data = {
                        "text": update.message.text,
                        "message_id": update.message.message_id,
                        "from": {
                            "id": update.effective_user.id,
                            "username": update.effective_user.username,
                        },
                        "chat": {
                            "id": update.effective_chat.id,
                        },
                    }

                    # Get response from the bot template's AI agent
                    response = await bot_template.handle_message(message_data)

                    # Send response back to user
                    await update.message.reply_text(response)

                    logger.info(f"🤖 [CREATED BOT] Processed message: {update.message.text[:50]}...")

                except Exception as e:
                    logger.error(f"❌ [CREATED BOT] Error handling message: {e}")
                    await update.message.reply_text("Sorry, I had trouble processing your message. Please try again.")

            # Register the message handler
            bot_application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_message)
            )

            # Get bot information
            bot = Bot(bot_template.bot_token)
            bot_info = await bot.get_me()
            bot_username = bot_info.username

            logger.info(f"🚀 [CREATED BOT] Starting bot: @{bot_username}")

            # Start the bot application in the background
            async def run_bot():
                """Run the created bot"""
                try:
                    async with bot_application:
                        await bot_application.start()
                        await bot_application.updater.start_polling()
                        logger.info(f"✅ [CREATED BOT] @{bot_username} is now live and responding to messages!")

                        # Keep running until cancelled
                        while self.created_bot_state == "running":
                            await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"❌ [CREATED BOT] Runtime error: {e}")
                    self.created_bot_state = "error"
                finally:
                    if bot_application.updater:
                        await bot_application.updater.stop()
                    await bot_application.stop()
                    logger.info(f"🛑 [CREATED BOT] @{bot_username} stopped")

            # Start the bot in a background task
            import asyncio
            self.created_bot_start_task = asyncio.create_task(run_bot())

            # Set state to running
            self.created_bot_state = "running"

            return bot_username

        except Exception as e:
            self.created_bot_state = "error"
            logger.error(f"❌ Failed to start created bot: {e}")
            return f"❌ Failed to start bot: {str(e)}"

    async def stop_created_bot(self) -> str:
        """Stop the currently running created bot"""
        if self.created_bot_state != "running":
            return "❌ No bot is currently running"

        try:
            self.created_bot_state = "stopping"

            # Cancel the bot's background task if it exists
            if self.created_bot_start_task:
                self.created_bot_start_task.cancel()
                try:
                    await self.created_bot_start_task
                except asyncio.CancelledError:
                    pass  # Expected when cancelling task
                self.created_bot_start_task = None

            # Clean up state
            self.created_bot_state = "none"
            self.active_created_bot = None

            logger.info("🛑 [CREATED BOT] Successfully stopped created bot")
            return "✅ Bot stopped successfully"

        except Exception as e:
            self.created_bot_state = "error"
            logger.error(f"❌ Failed to stop created bot: {e}")
            return f"❌ Failed to stop bot: {str(e)}"

    async def shutdown(self):
        """Cleanup all bot resources"""
        try:
            if self.active_created_bot:
                await self.stop_created_bot()
            if self.created_bot_start_task:
                self.created_bot_start_task.cancel()
            logger.info("🧹 Telegram bot manager shutdown complete")
        except Exception as e:
            logger.error(f"❌ Error during telegram manager shutdown: {e}")

    @staticmethod
    def is_valid_bot_token(token: str) -> bool:
        """Validate bot token format (should be like 123456:ABC-DEF...)"""
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

    # Multi-Bot Management Methods

    async def start_bot_by_token(self, token: str) -> str:
        """Start a specific bot by its token"""
        if token not in self.active_bots:
            return f"❌ No bot found with token {token[:10]}..."
        
        bot_instance = self.token_pool.active_bots.get(token)
        if not bot_instance:
            return f"❌ Bot not found in token pool"
        
        if bot_instance.status == "running":
            return f"✅ Bot '{bot_instance.name}' is already running"
        
        try:
            # Update status to starting
            self.token_pool.update_bot_status(token, "starting")
            
            # Get the bot template
            bot_template = self.active_bots[token]
            
            # Import required Telegram components
            from telegram import Bot
            from telegram.ext import Application, MessageHandler, filters

            # Create Telegram application for the bot
            bot_application = Application.builder().token(token).build()

            # Add message handler for the bot
            async def handle_bot_message(update, context):
                """Handle messages sent to the created bot"""
                try:
                    if not update.message or not update.message.text:
                        return

                    # Prepare message data for the bot template (matching expected format)
                    message_data = {
                        "text": update.message.text,
                        "message_id": update.message.message_id,
                        "from": {
                            "id": update.effective_user.id,
                            "username": update.effective_user.username,
                        },
                        "chat": {
                            "id": update.effective_chat.id,
                        },
                    }

                    # Get response from the bot template's AI agent
                    response = await bot_template.handle_message(message_data)

                    # Send response back to user
                    await update.message.reply_text(response)

                    logger.info(f"🤖 [BOT {bot_instance.name}] Processed message: {update.message.text[:50]}...")

                except Exception as e:
                    logger.error(f"❌ [BOT {bot_instance.name}] Error handling message: {e}")
                    await update.message.reply_text("Sorry, I had trouble processing your message. Please try again.")

            # Register the message handler
            bot_application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bot_message)
            )

            # Get bot information and update username
            bot = Bot(token)
            bot_info = await bot.get_me()
            bot_username = bot_info.username
            
            # Update bot instance with username
            self.token_pool.update_bot_status(token, "starting", bot_username)

            logger.info(f"🚀 [BOT {bot_instance.name}] Starting bot: @{bot_username}")

            # Start the bot application in the background
            async def run_bot():
                """Run the bot"""
                try:
                    async with bot_application:
                        await bot_application.start()
                        await bot_application.updater.start_polling()
                        
                        # Update status to running
                        self.token_pool.update_bot_status(token, "running", bot_username)
                        
                        logger.info(f"✅ [BOT {bot_instance.name}] @{bot_username} is now live and responding to messages!")

                        # Keep running until cancelled
                        while token in self.bot_start_tasks and bot_instance.status == "running":
                            await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"❌ [BOT {bot_instance.name}] Runtime error: {e}")
                    self.token_pool.update_bot_status(token, "error")
                finally:
                    if bot_application.updater:
                        await bot_application.updater.stop()
                    await bot_application.stop()
                    logger.info(f"🛑 [BOT {bot_instance.name}] @{bot_username} stopped")

            # Start the bot in a background task
            self.bot_start_tasks[token] = asyncio.create_task(run_bot())
            
            # Wait a moment for the bot to start
            await asyncio.sleep(0.5)
            
            logger.info(f"🚀 Started bot '{bot_instance.name}' with token {token[:10]}...")
            return f"🚀 Bot '{bot_instance.name}' (@{bot_username}) started successfully!"
            
        except Exception as e:
            self.token_pool.update_bot_status(token, "error")
            if token in self.bot_start_tasks:
                del self.bot_start_tasks[token]
            logger.error(f"❌ Failed to start bot '{bot_instance.name}': {e}")
            return f"❌ Failed to start bot: {e}"

    async def stop_bot_by_token(self, token: str) -> str:
        """Stop a specific bot by its token"""
        bot_instance = self.token_pool.active_bots.get(token)
        if not bot_instance:
            return f"❌ No bot found with token {token[:10]}..."
        
        try:
            # Update status to stopping
            self.token_pool.update_bot_status(token, "stopping")
            
            # Stop the bot (implementation would go here)
            if token in self.bot_start_tasks:
                task = self.bot_start_tasks[token]
                if not task.done():
                    task.cancel()
                del self.bot_start_tasks[token]
            
            # Remove from active bots and deallocate token
            if token in self.active_bots:
                del self.active_bots[token]
            
            self.token_pool.deallocate_token(token)
            
            logger.info(f"🛑 Stopped bot '{bot_instance.name}' with token {token[:10]}...")
            return f"🛑 Bot '{bot_instance.name}' stopped successfully!"
            
        except Exception as e:
            self.token_pool.update_bot_status(token, "error")
            logger.error(f"❌ Failed to stop bot '{bot_instance.name}': {e}")
            return f"❌ Failed to stop bot: {e}"

    async def stop_bot_by_name(self, bot_name: str) -> str:
        """Stop a bot by its name"""
        bot_instance = self.token_pool.get_bot_by_name(bot_name)
        if not bot_instance:
            return f"❌ No bot found with name '{bot_name}'"
        
        return await self.stop_bot_by_token(bot_instance.token)

    async def restart_bot_by_name(self, bot_name: str) -> str:
        """Restart a bot by stopping and starting it"""
        stop_result = await self.stop_bot_by_name(bot_name)
        if "❌" in stop_result:
            return stop_result
        
        # Small delay for cleanup
        await asyncio.sleep(1)
        
        # Find the bot again (it might have been recreated)
        bot_instance = self.token_pool.get_bot_by_name(bot_name)
        if not bot_instance:
            return f"❌ Bot '{bot_name}' not found after stop"
        
        return await self.start_bot_by_token(bot_instance.token)

    def get_pool_status(self) -> str:
        """Get formatted token pool status"""
        stats = self.token_pool.get_pool_stats()
        active_bots = self.token_pool.get_active_bots()
        
        if not active_bots:
            return f"🎯 **Token Pool**: {stats['available_tokens']}/{stats['total_tokens']} tokens available\n📱 **Active Bots**: None"
        
        bot_list = []
        for bot in active_bots:
            status_emoji = {"running": "🟢", "starting": "🟡", "stopping": "🟠", "error": "🔴", "created": "⚪"}.get(bot.status, "⚫")
            bot_list.append(f"   {status_emoji} **{bot.name}** (@{bot.username or 'pending'}) - {bot.status}")
        
        return f"🎯 **Token Pool**: {stats['available_tokens']}/{stats['total_tokens']} tokens available\n📱 **Active Bots**:\n" + "\n".join(bot_list)
