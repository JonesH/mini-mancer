"""
Minimal Prototype Agent - Integrates OpenServ + Telegram + Agno-AGI

Single FastAPI application with path-based routing to avoid endpoint conflicts.
Leverages existing TelegramBotTemplate and AgentDNA system.
"""

import os
import re
import logging
from typing import Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv

from .agents import TelegramBotTemplate, TelegramWebhookHandler
from .models.agent_dna import TELEGRAM_BOT_TEMPLATE
from .models.bot_requirements import (
    BotRequirements, RequirementsValidator, BotArchitect, 
    BotComplexity, AVAILABLE_TOOLS, ToolCategory
)
from .tools.thinking_tool import ThinkingTool, analyze_bot_requirements, think_about
from .constants import (
    WELCOME_MESSAGES, BOT_CREATION_MESSAGES, ERROR_MESSAGES, KEYBOARD_BUTTONS,
    format_bot_success, format_advanced_compilation, format_advanced_success,
    format_requirements_error, format_chat_fallback
)

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Import error handling utilities
from .utils import safe_telegram_operation, ErrorContext, log_error_with_context



class OpenServTaskRequest(BaseModel):
    """OpenServ task request payload"""
    task_id: str
    task_type: str
    parameters: dict[str, Any]


class OpenServChatRequest(BaseModel):
    """OpenServ chat message request"""
    message: str
    chat_id: str
    user_id: str


class BotCompilationRequest(BaseModel):
    """OpenServ bot compilation workflow request"""
    requirements: dict[str, Any]  # BotRequirements as dict
    user_id: str
    compilation_mode: str = "standard"  # "simple", "standard", "complex"


class BotCompilationStatus(BaseModel):
    """Bot compilation status response"""
    compilation_id: str
    status: str  # "queued", "compiling", "testing", "completed", "failed"
    progress_percentage: int
    estimated_completion: str
    bot_preview: dict[str, Any] | None = None


class PrototypeAgent:
    """
    Minimal prototype integrating all three systems:
    - Telegram (via existing TelegramBotTemplate)
    - OpenServ (FastAPI endpoints)
    - Agno-AGI (core intelligence)
    """
    
    def __init__(self):
        # Initialize FastAPI app
        self.app = FastAPI(
            title="Mini-Mancer Prototype",
            description="OpenServ + Telegram + Agno-AGI Integration"
        )
        
        # Get bot tokens from environment with validation
        self.factory_token = os.getenv("BOT_TOKEN") or os.getenv("TEST_BOT_TOKEN")
        self.created_bot_token = os.getenv("BOT_TOKEN_1")
        
        if not self.factory_token:
            raise ValueError("BOT_TOKEN or TEST_BOT_TOKEN environment variable required")
        
        # Validate token format (should start with number and contain colon)
        if not self._is_valid_bot_token(self.factory_token):
            raise ValueError("Invalid factory bot token format")
        
        # Check if we have a separate token for created bots
        if self.created_bot_token:
            if not self._is_valid_bot_token(self.created_bot_token):
                raise ValueError("Invalid created bot token format (BOT_TOKEN_1)")
            if self.created_bot_token == self.factory_token:
                raise ValueError("BOT_TOKEN_1 cannot be the same as BOT_TOKEN")
        else:
            # No separate token available - created bots will be disabled
            logger.warning("⚠️  BOT_TOKEN_1 not configured - created bots will be disabled")
        
        # Log token status
        logger.info(f"🔑 Factory token: {self.factory_token[:15]}...")
        if self.created_bot_token:
            logger.info(f"🔑 Created bot token: {self.created_bot_token[:15]}...")
            logger.info("✅ Token validation passed - both factory and created bots enabled")
        else:
            logger.warning("⚠️  Created bot functionality disabled - only factory bot available")
        
        # Track the currently active created bot with enhanced state management
        self.active_created_bot: TelegramBotTemplate | None = None
        self.created_bot_application = None
        self.created_bot_state: str = "none"  # none, creating, starting, running, stopping, error
        self.created_bot_start_task = None  # Track async task for proper cleanup
        
        # Bot compilation workflow tracking
        self.bot_compilation_queue: dict[str, dict[str, Any]] = {}
        self.completed_bot_specs: dict[str, BotRequirements] = {}
        
        # Create agent DNA for a helpful assistant
        agent_dna = TELEGRAM_BOT_TEMPLATE.instantiate({
            "name": "PrototypeBot",
            "purpose": "Demonstrate integrated OpenServ + Telegram + Agno-AGI functionality"
        })
        
        # Initialize Enhanced BotMother with GPT-4.1 and thinking capabilities
        from .prompts.botmother_prompts import BOTMOTHER_COMPLETE_SYSTEM_PROMPT
        
        self.agno_agent = Agent(
            model=OpenAIChat(id="gpt-4o"),  # Keep the working model but upgrade to GPT-4o
            description=BOTMOTHER_COMPLETE_SYSTEM_PROMPT,
            markdown=True,
            add_history_to_messages=True,
            num_history_responses=3,  # Keep existing memory settings
        )
        
        # Initialize thinking tool for BotMother
        self.thinking_tool = ThinkingTool()
        
        logger.info("🧠 BotMother enhanced with GPT-4.1 and advanced thinking capabilities")
        
        # Add bot creation tool
        self._register_bot_creation_tool()
        
        # Initialize factory Telegram bot using existing template
        self.telegram_bot = TelegramBotTemplate(
            agent_dna=agent_dna,
            model="gpt-4o-mini",
            bot_token=self.factory_token
        )
        
        # Initialize Telegram webhook handler
        self.telegram_handler = TelegramWebhookHandler(self.telegram_bot)
        
        # Setup routes with path separation to avoid conflicts
        self._setup_routes()
    
    def _is_valid_bot_token(self, token: str) -> bool:
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
    
    def _register_bot_creation_tool(self):
        """Register bot creation and thinking tools with the factory agent"""
        # Register thinking capabilities
        def deep_think_tool(topic: str, context: dict = None) -> str:
            """Advanced thinking and analysis tool for complex decisions"""
            return think_about(topic, context)
        
        def analyze_requirements_tool(requirements: dict) -> str:
            """Analyze bot requirements for completeness and quality"""
            return analyze_bot_requirements(requirements)
        
        # Add tools to the agent (using Agno's tool system)
        # Note: In actual implementation, these would be properly registered with Agno
        # For now, these are available through direct method calls in chat handling
        
        logger.info("🛠️ BotMother tools registered: deep thinking, requirements analysis, bot creation")
        
    def create_new_bot_instant(self, bot_name: str, bot_purpose: str, personality: str = "helpful") -> str:
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
            if self.created_bot_state in ["creating", "starting", "running"]:
                return ERROR_MESSAGES["bot_already_exists"]
            
            # Validate inputs
            if not bot_name or len(bot_name.strip()) < 2:
                return ERROR_MESSAGES["invalid_bot_name"]
            if not bot_purpose or len(bot_purpose.strip()) < 5:
                return ERROR_MESSAGES["invalid_bot_purpose"]
            
            # Set state to creating
            self.created_bot_state = "creating"
            # Create agent DNA for the new bot
            from .models.agent_dna import AgentDNA, AgentPersonality, AgentCapability, PlatformTarget
            
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
            
            # For now, simulate bot creation (in real implementation, this would create actual bot)
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
            logger.info(f"\n🔧 New Bot Created:")
            logger.info(f"   Name: {bot_name}")
            logger.info(f"   Purpose: {bot_purpose}")
            logger.info(f"   Personality: {personality_trait.value}")
            logger.info(f"   Capabilities: {[cap.value for cap in new_bot_dna.capabilities]}")
            logger.info(f"   Platform: {new_bot_dna.target_platform.value}")
            logger.info(f"   Token: BOT_TOKEN_1")
            logger.info("")
            
            # Note: Actual bot starting will be handled in main.py
            # For now, return placeholder username
            return format_bot_success(bot_name, bot_purpose, personality_trait.value, bot_username)
            
        except Exception as e:
            # Reset state on error
            self.created_bot_state = "error"
            self.active_created_bot = None
            logger.error(f"❌ Bot creation failed: {e}")
            return ERROR_MESSAGES["bot_creation_error"].format(error=str(e))
    
    def create_new_bot_advanced(self, requirements: BotRequirements) -> str:
        """
        Create a sophisticated bot using comprehensive requirements.
        
        This method handles the architect mode creation with full validation,
        compilation, and testing.
        
        Args:
            requirements: Complete bot requirements specification
            
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
            
            logger.info(f"\n🏗️  Advanced Bot Creation:")
            logger.info(f"   Name: {requirements.name}")
            logger.info(f"   Complexity: {requirements.complexity_level.value}")
            logger.info(f"   Quality Score: {validation_result['score']}/100")
            logger.info(f"   Tools: {[tool.name for tool in requirements.selected_tools]}")
            logger.info(f"   OpenServ Required: {requirements.openserv_workflow_required}")
            
            if requirements.openserv_workflow_required:
                # For now, simulate OpenServ workflow
                compilation_id = f"bot_comp_{len(self.bot_compilation_queue) + 1}"
                
                # Store in compilation queue
                self.bot_compilation_queue[compilation_id] = {
                    "requirements": requirements,
                    "status": "compiling",
                    "progress": 75,
                    "created_at": datetime.now()
                }
                
                # Store completed spec for later use
                self.completed_bot_specs[requirements.name.lower()] = requirements
                
                return format_advanced_compilation(requirements.name, validation_result['score'])
            else:
                # Direct creation for simpler bots
                from .models.agent_dna import AgentDNA, AgentPersonality, AgentCapability, PlatformTarget
                
                # Map first personality trait to AgentPersonality enum
                personality_map = {
                    "analytical": AgentPersonality.PROFESSIONAL,
                    "empathetic": AgentPersonality.HELPFUL,
                    "enthusiastic": AgentPersonality.ENTHUSIASTIC,
                    "creative": AgentPersonality.CREATIVE,
                    "professional": AgentPersonality.PROFESSIONAL,
                    "humorous": AgentPersonality.WITTY,
                    "patient": AgentPersonality.CALM,
                    "supportive": AgentPersonality.HELPFUL
                }
                
                primary_trait = requirements.core_traits[0].value if requirements.core_traits else "helpful"
                personality_trait = personality_map.get(primary_trait, AgentPersonality.HELPFUL)
                
                # Create enhanced bot DNA
                new_bot_dna = AgentDNA(
                    name=requirements.name,
                    purpose=requirements.purpose,
                    personality=[personality_trait],
                    capabilities=[AgentCapability.CHAT, AgentCapability.IMAGE_ANALYSIS],
                    target_platform=PlatformTarget.TELEGRAM
                )
                
                # Create bot with enhanced configuration
                new_bot = TelegramBotTemplate(
                    agent_dna=new_bot_dna,
                    bot_token=self.created_bot_token
                )
                
                # Override with sophisticated system prompt
                new_bot.agent.description = system_prompt
                
                # Store the active created bot
                self.active_created_bot = new_bot
                
                traits = ', '.join([trait.value for trait in requirements.core_traits])
                tools = ', '.join([tool.name for tool in requirements.selected_tools])
                return format_advanced_success(requirements.name, traits, tools)
                
        except Exception as e:
            logger.error(f"❌ Error in advanced bot creation: {e}")
            return ERROR_MESSAGES["advanced_creation_error"].format(error=str(e))
    
    async def start_created_bot(self, bot_template: TelegramBotTemplate) -> str:
        """Start the created bot with proper lifecycle management"""
        from telegram.ext import Application, MessageHandler, filters
        import asyncio
        
        try:
            # Validate state before starting
            if self.created_bot_state not in ["created", "error"]:
                logger.error(f"❌ Cannot start bot in state: {self.created_bot_state}")
                return ""
            
            if not self.created_bot_token:
                logger.error("❌ No created bot token available")
                return ""
            
            # Update state to starting
            self.created_bot_state = "starting"
            logger.info(f"🚀 Starting created bot...")
            
            # Create independent Telegram application for created bot
            application = Application.builder().token(self.created_bot_token).build()
            self.created_bot_application = application
            
            # Add message handler that uses the bot template
            @safe_telegram_operation("created_bot_message", "Sorry, I encountered an error processing your message.")
            async def handle_created_bot_message(update, context):
                """Handle messages for the created bot"""
                user_id = str(update.effective_user.id)
                message_text = update.message.text
                logger.info(f"📨 [CREATED BOT] Message from user {user_id}: '{message_text}'")
                
                # Use bot template to generate response
                response_text = await bot_template.handle_message(update.message.to_dict())
                
                # Send response
                await update.message.reply_text(response_text)
                logger.info(f"📤 [CREATED BOT] Sent response to user {user_id}")
            
            # Add handlers for different message types
            @safe_telegram_operation("created_bot_photo", "Sorry, I had trouble processing your photo.")
            async def handle_created_bot_photo(update, context):
                """Handle photo messages for the created bot"""
                user_id = str(update.effective_user.id)
                logger.info(f"📸 [CREATED BOT] Photo from user {user_id}")
                
                # Use bot template to handle photo
                response_text = await bot_template.handle_photo(update.message.to_dict())
                
                # Send response
                await update.message.reply_text(response_text)
                logger.info(f"📤 [CREATED BOT] Sent photo response to user {user_id}")
            
            @safe_telegram_operation("created_bot_document", "Sorry, I had trouble processing your file.")
            async def handle_created_bot_document(update, context):
                """Handle document messages for the created bot"""
                user_id = str(update.effective_user.id)
                logger.info(f"📎 [CREATED BOT] Document from user {user_id}")
                
                # Use bot template to handle document
                response_text = await bot_template.handle_document(update.message.to_dict())
                
                # Send response
                await update.message.reply_text(response_text)
                logger.info(f"📤 [CREATED BOT] Sent document response to user {user_id}")
            
            # Register all handlers
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_created_bot_message))
            application.add_handler(MessageHandler(filters.PHOTO, handle_created_bot_photo))
            application.add_handler(MessageHandler(filters.DOCUMENT, handle_created_bot_document))
            
            # Get bot info to validate token works
            try:
                bot_info = await application.bot.get_me()
                username = bot_info.username
                logger.info(f"🤖 [CREATED BOT] Validated: {bot_info.first_name} | @{username}")
            except Exception as e:
                self.created_bot_state = "error"
                logger.error(f"❌ Failed to validate created bot token: {e}")
                return ""
            
            # Start polling as a managed background task
            async def managed_polling():
                try:
                    self.created_bot_state = "running"
                    logger.info(f"📱 [CREATED BOT] @{username} starting polling...")
                    
                    async with application:
                        await application.start()
                        await application.updater.start_polling()
                        logger.info(f"✅ [CREATED BOT] @{username} is now live and polling!")
                        
                        # Keep running until the state changes or we're interrupted
                        while self.created_bot_state == "running":
                            await asyncio.sleep(1)
                        
                        logger.info(f"🛑 [CREATED BOT] @{username} stopping polling...")
                        await application.stop()
                        
                except Exception as e:
                    self.created_bot_state = "error"
                    logger.error(f"❌ [CREATED BOT] Polling error for @{username}: {e}")
                finally:
                    if self.created_bot_state == "running":
                        self.created_bot_state = "stopped"
                    logger.info(f"🏁 [CREATED BOT] @{username} polling ended")
            
            # Store the task for cleanup
            self.created_bot_start_task = asyncio.create_task(managed_polling())
            
            # Wait a moment to ensure it starts properly
            await asyncio.sleep(0.5)
            
            if self.created_bot_state == "running":
                return username
            else:
                logger.error(f"❌ Bot failed to start properly, state: {self.created_bot_state}")
                return ""
            
        except Exception as e:
            self.created_bot_state = "error"
            logger.error(f"❌ Error starting created bot: {e}")
            return ""
    
    async def stop_created_bot(self) -> str:
        """Stop the currently running created bot with proper cleanup"""
        try:
            if self.created_bot_state == "none":
                return ERROR_MESSAGES["no_bot_to_stop"]
            
            if self.created_bot_state not in ["running", "starting", "error"]:
                logger.warning(f"⚠️ Bot is in {self.created_bot_state} state, attempting to stop...")
            
            # Set state to stopping
            old_state = self.created_bot_state
            self.created_bot_state = "stopping"
            
            logger.info(f"🛑 Stopping created bot (was {old_state})...")
            
            # Cancel the polling task if it exists
            if self.created_bot_start_task and not self.created_bot_start_task.done():
                logger.info("🔄 Cancelling bot polling task...")
                self.created_bot_start_task.cancel()
                try:
                    await self.created_bot_start_task
                except asyncio.CancelledError:
                    logger.info("✅ Bot polling task cancelled")
                except Exception as e:
                    logger.warning(f"⚠️ Error during task cancellation: {e}")
            
            # Stop the application if it exists
            if self.created_bot_application:
                try:
                    logger.info("🔄 Stopping Telegram application...")
                    await self.created_bot_application.stop()
                    logger.info("✅ Telegram application stopped")
                except Exception as e:
                    logger.warning(f"⚠️ Error stopping application: {e}")
            
            # Clean up resources
            self.active_created_bot = None
            self.created_bot_application = None
            self.created_bot_start_task = None
            self.created_bot_state = "none"
            
            logger.info("✅ Created bot stopped and resources cleaned up")
            return "✅ Bot stopped successfully"
            
        except Exception as e:
            logger.error(f"❌ Error stopping created bot: {e}")
            # Force cleanup even if there were errors
            self.active_created_bot = None
            self.created_bot_application = None
            self.created_bot_start_task = None
            self.created_bot_state = "error"
            return ERROR_MESSAGES["bot_start_failed"].format(error=str(e))
    
    async def shutdown(self):
        """Graceful shutdown of all bot resources"""
        logger.info("🛑 PrototypeAgent shutdown initiated...")
        
        try:
            # Stop any running created bots
            if self.created_bot_state in ["running", "starting"]:
                logger.info("🔄 Stopping created bot...")
                await self.stop_created_bot()
            
            # Shutdown factory bot resources
            if hasattr(self, 'telegram_bot') and self.telegram_bot:
                logger.info("🔄 Shutting down factory bot...")
                await self.telegram_bot.shutdown()
            
            # Clear all queues and data
            self.bot_compilation_queue.clear()
            self.completed_bot_specs.clear()
            
            logger.info("✅ PrototypeAgent shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Error during PrototypeAgent shutdown: {e}")
    
    def get_status_summary(self) -> dict[str, Any]:
        """Get comprehensive status of all bot systems"""
        return {
            "factory_bot": {
                "status": "running" if hasattr(self, 'telegram_bot') else "inactive",
                "token_configured": bool(self.factory_token)
            },
            "created_bot": {
                "status": self.created_bot_state,
                "token_configured": bool(self.created_bot_token),
                "active_bot": self.active_created_bot.dna.name if self.active_created_bot else None
            },
            "resources": {
                "compilation_queue_size": len(self.bot_compilation_queue),
                "completed_specs": len(self.completed_bot_specs),
                "active_polling_task": bool(self.created_bot_start_task and not self.created_bot_start_task.done())
            }
        }
    
    def _parse_bot_creation_request(self, message: str) -> dict[str, str] | None:
        """
        Enhanced parsing for bot creation requests with multiple parameter extraction.
        
        Supports:
        - Command format: /create_bot name="Bot Name" purpose="Description" personality="helpful"
        - Natural language: "create a helpful bot named Assistant for customer support"
        - Simple format: "make bot called Helper"
        
        Returns:
            Dict with extracted parameters or None if not a bot creation request
        """
        message_lower = message.lower()
        
        # Check if this is a bot creation request
        creation_keywords = ["create bot", "make bot", "new bot", "spawn bot", "/create_bot", "/create"]
        if not any(keyword in message_lower for keyword in creation_keywords):
            return None
        
        result = {}
        
        # Method 1: Command-style parsing with quotes
        # /create_bot name="Bot Name" purpose="Help users" personality="professional"
        param_patterns = {
            'name': r'name[=:]\s*["\']([^"\']+)["\']',
            'purpose': r'purpose[=:]\s*["\']([^"\']+)["\']',
            'personality': r'personality[=:]\s*["\']([^"\']+)["\']'
        }
        
        for param, pattern in param_patterns.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                result[param] = match.group(1).strip()
        
        # Method 2: Natural language parsing
        if not result.get('name'):
            # Extract name after "named", "called", "bot"
            name_patterns = [
                r'(?:named|called)\s+(["\']?)([A-Za-z0-9\s]+)\1',
                r'bot\s+(["\']?)([A-Za-z0-9\s]+)\1(?:\s+for|\s+to|\s+that)',
                r'(?:create|make)\s+(?:a\s+)?([A-Za-z0-9\s]+?)(?:\s+bot|\s+for)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    # Use group 2 if quotes were captured, otherwise group 1
                    name = match.group(2) if len(match.groups()) > 1 and match.group(2) else match.group(1)
                    if name and len(name.strip()) > 2:  # Valid name length
                        result['name'] = name.strip().title()
                        break
        
        # Method 3: Extract purpose from context
        if not result.get('purpose'):
            purpose_patterns = [
                r'for\s+([^.!?]+)',
                r'to\s+([^.!?]+)',
                r'that\s+([^.!?]+)',
                r'purpose[=:]\s*([^"\']+?)(?:\s+personality|\s*$)',
            ]
            
            for pattern in purpose_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    purpose = match.group(1).strip()
                    if len(purpose) > 5:  # Valid purpose length
                        result['purpose'] = purpose
                        break
        
        # Method 4: Extract personality traits
        if not result.get('personality'):
            personality_keywords = {
                'helpful': ['helpful', 'assistant', 'supportive', 'friendly'],
                'professional': ['professional', 'business', 'formal', 'corporate'],
                'casual': ['casual', 'relaxed', 'informal', 'chill'],
                'enthusiastic': ['enthusiastic', 'energetic', 'excited', 'upbeat'],
                'witty': ['witty', 'funny', 'humorous', 'clever'],
                'calm': ['calm', 'patient', 'gentle', 'peaceful']
            }
            
            for personality, keywords in personality_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    result['personality'] = personality
                    break
        
        # Return results if we found something useful
        if result:
            logger.info(f"🔍 Parsed bot creation request: {result}")
            return result
        
        return None
    
    def _generate_start_message(self) -> str:
        """Generate a welcoming start message with creation instructions"""
        return WELCOME_MESSAGES["start"]
    
    def _handle_structured_commands(self, message: str) -> str | None:
        """Handle structured bot creation commands"""
        message_lower = message.strip().lower()
        
        # /start and /help commands
        if message_lower in ['/start', '/help']:
            return self._generate_start_message()
        
        # /create_quick command for fast bot creation
        if message_lower.startswith('/create_quick'):
            return WELCOME_MESSAGES["quick_creation"]
        
        # /list_personalities command
        if message_lower in ['/list_personalities', '/personalities']:
            return WELCOME_MESSAGES["personalities"]
        
        # /examples command
        if message_lower in ['/examples', '/example']:
            return WELCOME_MESSAGES["examples"]
        
        return None
    
    def _generate_quick_creation_keyboard(self) -> dict:
        """Generate inline keyboard for quick bot creation"""
        return {
            "inline_keyboard": [
                [
                    {"text": KEYBOARD_BUTTONS["create_helper"], "callback_data": "create_helper"},
                    {"text": KEYBOARD_BUTTONS["create_support"], "callback_data": "create_support"}
                ],
                [
                    {"text": KEYBOARD_BUTTONS["create_fun"], "callback_data": "create_fun"},
                    {"text": KEYBOARD_BUTTONS["create_calm"], "callback_data": "create_calm"}
                ],
                [
                    {"text": KEYBOARD_BUTTONS["custom_builder"], "callback_data": "create_custom"},
                    {"text": KEYBOARD_BUTTONS["show_examples"], "callback_data": "show_examples"}
                ]
            ]
        }
    
    def _setup_routes(self):
        """Setup FastAPI routes with proper path separation"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "mini-mancer-prototype",
                "status": "running", 
                "architecture": "all-polling",
                "endpoints": {
                    "openserv_tasks": "/openserv/do_task", 
                    "openserv_chat": "/openserv/respond_chat_message"
                }
            }
        
        @self.app.post("/openserv/")
        async def openserv_main(request: Request):
            """Main OpenServ endpoint that routes based on action type"""
            body = await request.json()
            action_type = body.get("type")
            
            if action_type == "do-task":
                task_data = body.get("task", {})
                return await openserv_do_task(OpenServTaskRequest(
                    task_id=task_data.get("id", ""),
                    task_type=task_data.get("type", ""),
                    parameters=task_data.get("parameters", {})
                ))
            elif action_type == "respond-chat-message":
                message_data = body.get("message", {})
                return await openserv_respond_chat(OpenServChatRequest(
                    chat_id=message_data.get("chat_id", ""),
                    message=message_data.get("content", ""),
                    user_id=message_data.get("user_id", "")
                ))
            
            raise HTTPException(status_code=400, detail=f"Unknown action type: {action_type}")
        
        @self.app.post("/openserv/compile_bot")
        async def openserv_compile_bot(request: BotCompilationRequest):
            """Handle OpenServ bot compilation workflow"""
            try:
                # Convert dict back to BotRequirements
                requirements_dict = request.requirements
                requirements = BotRequirements(**requirements_dict)
                
                # Use advanced creation method
                result = self.create_new_bot_advanced(requirements)
                
                return {
                    "compilation_id": f"bot_comp_{len(self.bot_compilation_queue)}",
                    "status": "initiated",
                    "user_id": request.user_id,
                    "mode": request.compilation_mode,
                    "result": result,
                    "openserv_workflow": "mini-mancer-bot-compilation"
                }
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Bot compilation error: {str(e)}")
        
        @self.app.get("/openserv/compilation_status/{compilation_id}")
        async def get_compilation_status(compilation_id: str):
            """Get status of bot compilation workflow"""
            if compilation_id in self.bot_compilation_queue:
                workflow = self.bot_compilation_queue[compilation_id]
                return BotCompilationStatus(
                    compilation_id=compilation_id,
                    status=workflow["status"],
                    progress_percentage=workflow["progress"],
                    estimated_completion="1-2 minutes",
                    bot_preview={
                        "name": workflow["requirements"].name,
                        "purpose": workflow["requirements"].purpose,
                        "complexity": workflow["requirements"].complexity_level.value
                    }
                )
            else:
                raise HTTPException(status_code=404, detail="Compilation not found")
        
        @self.app.get("/openserv/available_tools")
        async def get_available_tools():
            """Get list of available tools for bot creation"""
            return {
                "tools": [
                    {
                        "id": tool_id,
                        "name": tool.name,
                        "category": tool.category.value,
                        "description": tool.description,
                        "complexity": tool.integration_complexity
                    }
                    for tool_id, tool in AVAILABLE_TOOLS.items()
                ],
                "categories": [category.value for category in ToolCategory]
            }
        
        @self.app.post("/openserv/test_connection")
        async def test_openserv_connection():
            """Test connection to OpenServ - Mini-Mancer -> OpenServ"""
            try:
                import httpx
                openserv_url = os.getenv("OPENSERV_URL", "http://localhost:8080")
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{openserv_url}/health")
                    
                    if response.status_code == 200:
                        return {
                            "status": "success",
                            "direction": "mini-mancer -> openserv",
                            "openserv_url": openserv_url,
                            "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                            "message": "OpenServ connection successful"
                        }
                    else:
                        return {
                            "status": "error",
                            "direction": "mini-mancer -> openserv", 
                            "openserv_url": openserv_url,
                            "error": f"HTTP {response.status_code}: {response.text}",
                            "message": "OpenServ connection failed"
                        }
                        
            except Exception as e:
                return {
                    "status": "error",
                    "direction": "mini-mancer -> openserv",
                    "error": str(e),
                    "message": "Failed to connect to OpenServ"
                }
        
        @self.app.get("/health")
        async def health_check():
            """Enhanced health check endpoint with comprehensive status"""
            status_summary = self.get_status_summary()
            
            return {
                "status": "healthy",
                "service": "mini-mancer",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "capabilities": [
                    "bot_creation",
                    "agno_integration", 
                    "telegram_polling",
                    "openserv_api"
                ],
                "detailed_status": status_summary,
                "active_bots": {
                    "factory_bot": status_summary["factory_bot"]["status"],
                    "created_bot": status_summary["created_bot"]["status"]
                }
            }
        
        @self.app.post("/openserv/ping")
        async def openserv_ping(request: Request):
            """Ping endpoint for OpenServ connection testing"""
            body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
            
            return {
                "status": "pong",
                "timestamp": datetime.now().isoformat(),
                "received_from": body.get("source", "unknown"),
                "mini_mancer_status": "operational",
                "message": "Mini-Mancer received your ping successfully"
            }
        
        @self.app.post("/openserv/do_task")
        async def openserv_do_task(request: OpenServTaskRequest):
            """Handle OpenServ task processing via Agno agent"""
            task_prompt = f"""
            Process this OpenServ task:
            Task ID: {request.task_id}
            Task Type: {request.task_type}
            Parameters: {request.parameters}
            
            Provide a structured response for task completion.
            """
            
            response = self.agno_agent.run(task_prompt)
            
            return {
                "task_id": request.task_id,
                "status": "completed",
                "result": response.content,
                "agent": "agno-agi"
            }
        
        @self.app.post("/openserv/respond_chat_message")
        async def openserv_respond_chat(request: OpenServChatRequest):
            """Handle OpenServ chat messages via Agno agent"""
            # Handle structured commands first
            command_response = self._handle_structured_commands(request.message)
            if command_response:
                response_data = {
                    "chat_id": request.chat_id,
                    "response": command_response,
                    "agent": "factory-bot-commands",
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
                
                # Add inline keyboard for start/help commands
                if request.message.strip().lower() in ['/start', '/help']:
                    response_data["reply_markup"] = self._generate_quick_creation_keyboard()
                
                return response_data
            
            # Check if this is a bot creation request
            parsed_request = self._parse_bot_creation_request(request.message)
            if parsed_request:
                # Use parsed parameters or defaults
                bot_name = parsed_request.get('name', 'Custom Bot')
                bot_purpose = parsed_request.get('purpose', 'General assistance')
                personality = parsed_request.get('personality', 'helpful')
                
                # Create the bot using instant method
                bot_result = self.create_new_bot_instant(bot_name, bot_purpose, personality)
                
                return {
                    "chat_id": request.chat_id,
                    "response": bot_result,
                    "agent": "factory-bot-creator",
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
            
            # Regular chat response
            chat_prompt = format_chat_fallback(request.message, request.chat_id, request.user_id)
            
            response = self.agno_agent.run(chat_prompt)
            
            return {
                "chat_id": request.chat_id,
                "response": response.content,
                "agent": "agno-agi",
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }


# Create global prototype instance
try:
    prototype = PrototypeAgent()
    app = prototype.app
    logger.info("🏭 Prototype agent initialized successfully")
except Exception as e:
    print(f"❌ Error initializing prototype agent: {e}")
    # Create minimal fallback app
    from fastapi import FastAPI
    app = FastAPI(title="Mini-Mancer (Error State)")
    prototype = None


# For development/testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=14159, reload=True)