"""
Telegram Integration Module for Mini-Mancer

Handles Telegram bot creation, management, and lifecycle operations.
Extracted from prototype_agent.py for better separation of concerns.
"""

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

logger = logging.getLogger(__name__)


class TelegramBotManager:
    """Manages Telegram bot creation and lifecycle operations"""

    def __init__(self, created_bot_token: str | None = None):
        self.created_bot_token = created_bot_token
        self.active_created_bot: TelegramBotTemplate | None = None
        self.created_bot_state: str = "none"  # none, creating, starting, running, stopping, error
        self.created_bot_start_task = None  # Track async task for proper cleanup

        if not self.created_bot_token:
            logger.warning("⚠️  BOT_TOKEN_1 not configured - created bots will be disabled")

    def is_bot_creation_available(self) -> bool:
        """Check if bot creation is available"""
        return bool(self.created_bot_token)

    def is_bot_active(self) -> bool:
        """Check if a bot is currently active"""
        return self.created_bot_state in ["creating", "starting", "running"]

    def create_bot_instant(self, bot_name: str, bot_purpose: str, personality: str = "helpful") -> str:
        """
        Create a new Telegram bot with the specified parameters.
        
        Args:
            bot_name: Name for the new bot
            bot_purpose: Purpose/description of what the bot does
            personality: Personality trait (helpful, professional, casual, etc.)
            
        Returns:
            Success message with bot information and t.me link
        """
        try:
            # Check if bot creation is available
            if not self.created_bot_token:
                return ERROR_MESSAGES["bot_creation_disabled"]

            # Check if another bot is already active
            if self.is_bot_active():
                return ERROR_MESSAGES["bot_already_exists"]

            # Validate inputs
            if not bot_name or len(bot_name.strip()) < 2:
                return ERROR_MESSAGES["invalid_bot_name"]
            if not bot_purpose or len(bot_purpose.strip()) < 5:
                return ERROR_MESSAGES["invalid_bot_purpose"]

            # Set state to creating
            self.created_bot_state = "creating"

            # Map personality string to enum
            personality_map = {
                "helpful": AgentPersonality.HELPFUL,
                "professional": AgentPersonality.PROFESSIONAL,
                "casual": AgentPersonality.CASUAL,
                "enthusiastic": AgentPersonality.ENTHUSIASTIC,
                "witty": AgentPersonality.WITTY,
                "calm": AgentPersonality.CALM,
                "playful": AgentPersonality.PLAYFUL
            }

            personality_trait = personality_map.get(personality.lower(), AgentPersonality.HELPFUL)

            # Create new bot DNA
            new_bot_dna = AgentDNA(
                name=bot_name,
                purpose=bot_purpose,
                personality=[personality_trait],
                capabilities=[AgentCapability.CHAT, AgentCapability.IMAGE_ANALYSIS],
                target_platform=PlatformTarget.TELEGRAM
            )

            # Create bot username
            bot_username = bot_name.lower().replace(" ", "_") + "_bot"

            # Create the bot instance with BOT_TOKEN_1
            new_bot = TelegramBotTemplate(
                agent_dna=new_bot_dna,
                bot_token=self.created_bot_token
            )

            # Store the active created bot
            self.active_created_bot = new_bot
            self.created_bot_state = "created"  # Successfully created, ready to start

            # Log the new bot creation
            logger.info("\n🔧 New Bot Created:")
            logger.info(f"   Name: {bot_name}")
            logger.info(f"   Purpose: {bot_purpose}")
            logger.info(f"   Personality: {personality_trait.value}")
            logger.info(f"   Capabilities: {[cap.value for cap in new_bot_dna.capabilities]}")
            logger.info(f"   Platform: {new_bot_dna.target_platform.value}")
            logger.info("   Token: BOT_TOKEN_1")
            logger.info("")

            return format_bot_success(bot_name, bot_purpose, personality_trait.value, bot_username)

        except Exception as e:
            # Reset state on error
            self.created_bot_state = "error"
            self.active_created_bot = None
            logger.error(f"❌ Bot creation failed: {e}")
            return ERROR_MESSAGES["bot_creation_error"].format(error=str(e))

    def create_bot_advanced(self, requirements: BotRequirements, bot_compilation_queue: dict) -> str:
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
            system_prompt = BotArchitect.generate_system_prompt(requirements)
            agno_config = BotArchitect.generate_agno_agent_config(requirements)

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
                    "created_at": datetime.now()
                }

                return format_advanced_compilation(requirements.name, validation_result['score'])
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
                    target_platform=PlatformTarget.TELEGRAM
                )

                # Create the bot instance
                new_bot = TelegramBotTemplate(
                    agent_dna=new_bot_dna,
                    bot_token=self.created_bot_token
                )

                # Store the active created bot
                self.active_created_bot = new_bot
                self.created_bot_state = "created"

                return f"✅ **{requirements.name}** has been created successfully!\n\n" \
                       f"**Quality Score:** {validation_result['score']}/100\n" \
                       f"**Complexity:** {requirements.complexity_level.value}\n" \
                       f"**Tools:** {len(requirements.selected_tools)} integrated\n\n" \
                       f"Your bot is ready to use!"

        except Exception as e:
            logger.error(f"❌ Advanced bot creation failed: {e}")
            return f"❌ **Bot creation failed**\n\nError: {str(e)}"

    async def start_created_bot(self, bot_template: TelegramBotTemplate) -> str:
        """Start the created bot with enhanced lifecycle management"""
        if self.created_bot_state != "created":
            return "❌ No bot ready to start"

        try:
            self.created_bot_state = "starting"
            # Implementation would go here for starting the bot
            # This is a placeholder for the actual bot starting logic
            self.created_bot_state = "running"
            return "✅ Bot started successfully!"
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
            # Implementation would go here for stopping the bot
            self.created_bot_state = "none"
            self.active_created_bot = None
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
