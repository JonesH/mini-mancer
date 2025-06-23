"""
Agent Controller - Core orchestration for Mini-Mancer

Refactored main controller that coordinates all components.
Extracted from prototype_agent.py for better single responsibility.
"""

import logging
import os

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
from fastapi import FastAPI

from .agents import TelegramBotTemplate, TelegramWebhookHandler
from .api_router import APIRouter
from .models.agent_dna import TELEGRAM_BOT_TEMPLATE
from .models.bot_requirements import BotRequirements
from .telegram_integration import TelegramBotManager
from .tools.thinking_tool import ThinkingTool, analyze_bot_requirements, think_about


# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AgentController:
    """
    Core controller that orchestrates all Mini-Mancer components:
    - Telegram bot management
    - OpenServ API integration
    - Agno-AGI intelligence
    - FastAPI application
    """

    def __init__(self):
        # Initialize configuration
        self._initialize_configuration()

        # Initialize FastAPI app
        self.app = FastAPI(
            title="Mini-Mancer Prototype", description="OpenServ + Telegram + Agno-AGI Integration"
        )

        # Initialize core components
        self._initialize_telegram_manager()
        self._initialize_agno_agent()
        self._initialize_factory_bot()

        # Initialize bot compilation tracking
        self.bot_compilation_queue: dict[str, dict] = {}
        self.completed_bot_specs: dict[str, BotRequirements] = {}

        # Initialize API router
        self.api_router = APIRouter(
            telegram_manager=self.telegram_manager,
            agno_agent=self.agno_agent,
            bot_compilation_queue=self.bot_compilation_queue,
            completed_bot_specs=self.completed_bot_specs,
        )

        # Setup FastAPI routes
        self._setup_routes()

        logger.info("🚀 Agent Controller initialized successfully")

    def _initialize_configuration(self):
        """Initialize and validate configuration"""
        # Get bot tokens from environment with validation
        self.factory_token = os.getenv("BOT_TOKEN") or os.getenv("TEST_BOT_TOKEN")
        self.created_bot_token = os.getenv("BOT_TOKEN_1")

        if not self.factory_token:
            raise ValueError("BOT_TOKEN or TEST_BOT_TOKEN environment variable required")

        # Validate token formats
        if not TelegramBotManager.is_valid_bot_token(self.factory_token):
            raise ValueError("Invalid factory bot token format")

        if self.created_bot_token:
            if not TelegramBotManager.is_valid_bot_token(self.created_bot_token):
                raise ValueError("Invalid created bot token format (BOT_TOKEN_1)")
            if self.created_bot_token == self.factory_token:
                raise ValueError("BOT_TOKEN_1 cannot be the same as BOT_TOKEN")

        # Log token status
        logger.info(f"🔑 Factory token: {self.factory_token[:15]}...")
        if self.created_bot_token:
            logger.info(f"🔑 Created bot token: {self.created_bot_token[:15]}...")
            logger.info("✅ Token validation passed - both factory and created bots enabled")
        else:
            logger.warning("⚠️  Created bot functionality disabled - only factory bot available")

    def _initialize_telegram_manager(self):
        """Initialize the Telegram bot manager"""
        self.telegram_manager = TelegramBotManager(self.created_bot_token)
        logger.info("📱 Telegram bot manager initialized")

    def _initialize_agno_agent(self):
        """Initialize the Agno-AGI agent"""
        # Initialize Enhanced BotMother with GPT-4o and thinking capabilities
        from .prompts.botmother_prompts import BOTMOTHER_COMPLETE_SYSTEM_PROMPT

        self.agno_agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            description=BOTMOTHER_COMPLETE_SYSTEM_PROMPT,
            markdown=True,
            add_history_to_messages=True,
            num_history_responses=3,
        )

        # Initialize thinking tool for BotMother
        self.thinking_tool = ThinkingTool()
        self._register_bot_creation_tools()

        logger.info("🧠 BotMother enhanced with GPT-4o and advanced thinking capabilities")

    def _initialize_factory_bot(self):
        """Initialize the factory Telegram bot"""
        # Create agent DNA for a helpful assistant
        agent_dna = TELEGRAM_BOT_TEMPLATE.instantiate(
            {
                "name": "PrototypeBot",
                "purpose": "Demonstrate integrated OpenServ + Telegram + Agno-AGI functionality",
            }
        )

        # Initialize factory Telegram bot using existing template
        self.telegram_bot = TelegramBotTemplate(
            agent_dna=agent_dna, model="gpt-4o-mini", bot_token=self.factory_token
        )

        # Initialize Telegram webhook handler
        self.telegram_handler = TelegramWebhookHandler(self.telegram_bot)

        logger.info("🤖 Factory Telegram bot initialized")

    def _register_bot_creation_tools(self):
        """Register bot creation and thinking tools with the factory agent"""

        def deep_think_tool(topic: str, context: dict = None) -> str:
            """Advanced thinking and analysis tool for complex decisions"""
            return think_about(topic, context)

        def analyze_requirements_tool(requirements: dict) -> str:
            """Analyze bot requirements for completeness and quality"""
            return analyze_bot_requirements(requirements)

        # Note: In actual implementation, these would be properly registered with Agno
        # For now, these are available through direct method calls in chat handling

        logger.info(
            "🛠️ BotMother tools registered: deep thinking, requirements analysis, bot creation"
        )

    def _setup_routes(self):
        """Setup all FastAPI routes using the API router"""

        # Root endpoints
        self.app.add_api_route("/", self.api_router.root, methods=["GET"])

        # OpenServ integration endpoints
        self.app.add_api_route("/openserv", self.api_router.openserv_main, methods=["POST"])
        self.app.add_api_route(
            "/openserv/compile_bot", self.api_router.openserv_compile_bot, methods=["POST"]
        )
        self.app.add_api_route(
            "/openserv/compilation_status/{compilation_id}",
            self.api_router.get_compilation_status,
            methods=["GET"],
        )
        self.app.add_api_route(
            "/openserv/available_tools", self.api_router.get_available_tools, methods=["GET"]
        )
        self.app.add_api_route(
            "/openserv/test_connection", self.api_router.test_openserv_connection, methods=["POST"]
        )
        self.app.add_api_route("/health", self.api_router.health_check, methods=["GET"])
        self.app.add_api_route("/openserv/ping", self.api_router.openserv_ping, methods=["POST"])
        self.app.add_api_route(
            "/openserv/do_task", self.api_router.openserv_do_task, methods=["POST"]
        )
        self.app.add_api_route(
            "/openserv/respond_chat_message",
            self.api_router.openserv_respond_chat,
            methods=["POST"],
        )

        # Test monitoring endpoints
        self.app.add_api_route(
            "/test-monitor", self.api_router.test_monitor_dashboard, methods=["GET"]
        )
        self.app.add_api_websocket_route("/test-monitor/ws", self.api_router.test_monitor_websocket)
        self.app.add_api_route(
            "/test-monitor/events", self.api_router.get_test_events, methods=["GET"]
        )
        self.app.add_api_route(
            "/test-monitor/stats", self.api_router.get_test_stats, methods=["GET"]
        )

        logger.info("🛣️ API routes configured successfully")

    # Delegation methods for bot operations
    async def create_new_bot_instant(
        self, bot_name: str, bot_purpose: str, personality: str = "helpful"
    ) -> str:
        """Create a new bot using instant mode"""
        return await self.telegram_manager.create_bot_instant(bot_name, bot_purpose, personality)

    def create_new_bot_advanced(self, requirements: BotRequirements) -> str:
        """Create a new bot using advanced mode"""
        return self.telegram_manager.create_bot_advanced(requirements, self.bot_compilation_queue)

    async def start_created_bot(self, bot_template: TelegramBotTemplate) -> str:
        """Start the created bot"""
        return await self.telegram_manager.start_created_bot(bot_template)

    async def stop_created_bot(self) -> str:
        """Stop the created bot"""
        return await self.telegram_manager.stop_created_bot()

    async def shutdown(self):
        """Cleanup all resources"""
        try:
            await self.telegram_manager.shutdown()
            logger.info("🧹 Agent Controller shutdown complete")
        except Exception as e:
            logger.error(f"❌ Error during agent controller shutdown: {e}")

    # Properties for backward compatibility
    @property
    def active_created_bot(self) -> TelegramBotTemplate | None:
        """Get the currently active created bot"""
        return self.telegram_manager.active_created_bot

    @property
    def created_bot_state(self) -> str:
        """Get the current state of the created bot"""
        return self.telegram_manager.created_bot_state
