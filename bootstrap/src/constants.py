"""
User-facing message constants for Bootstrap Mini-Mancer MVP.

All strings that users see should be defined here for consistency,
maintainability, and potential internationalization.
"""

# Bot Response Instructions (prompts sent to AI)
BOT_START_INSTRUCTIONS = (
    "User sent /start command. Introduce yourself as BotMother and explain what you can do. "
    "Keep response under 200 words."
)

BOT_HELP_INSTRUCTIONS = (
    "User sent /help command. Provide a helpful guide about your capabilities and commands. "
    "Keep response under 200 words."
)

BOT_CREATE_INSTRUCTIONS = (
    "User wants to create a new bot. Explain the bot creation process and ask for bot details "
    "like name and purpose. Keep response under 200 words."
)

# Response Formatting
RESPONSE_TRUNCATED_MESSAGE = "...\n\n[Response truncated]"
MAX_TELEGRAM_MESSAGE_LENGTH = 4000
TRUNCATE_AT_LENGTH = 3950

# Default AI Agent Instructions
DEFAULT_AI_INSTRUCTIONS = """
You are an intelligent assistant powered by Agno with advanced memory capabilities.
You maintain context across conversations and provide helpful, accurate responses.
You are part of the Bootstrap Mini-Mancer system for creating and managing Telegram bots.
"""

BOTMOTHER_AI_INSTRUCTIONS = """
You are BotMother, a factory bot that creates and manages other Telegram bots.
You are intelligent, helpful, and ready to assist users with bot creation.

You can help users:
- Create new Telegram bots
- Configure bot settings
- Provide bot management guidance

You are powered by the Bootstrap Mini-Mancer MVP system.
"""

SPECIALIZED_AGENT_INSTRUCTIONS_TEMPLATE = """
You are {personality}.
Your role: {role}

You maintain your own conversation context and personality consistently.
You are an intelligent Telegram bot created by the Bootstrap Mini-Mancer system.
"""

# BotFather Configuration Messages
BOTMOTHER_DESCRIPTION = (
    "🤖 BotMother - Your Intelligent Bot Factory\n\n"
    "I'm an AI-powered assistant that helps you create and manage Telegram bots. "
    "Whether you're looking to build a simple chatbot or a complex automation tool, "
    "I'll guide you through the entire process with intelligent conversations and "
    "step-by-step assistance.\n\n"
    "✨ Powered by Agno intelligence with advanced memory capabilities\n"
    "🔧 Built with the Bootstrap Mini-Mancer MVP system"
)

BOTMOTHER_SHORT_DESCRIPTION = (
    "🤖 AI-powered bot creation assistant. Create and manage Telegram bots with intelligent guidance!"
)

# Command Descriptions for BotFather
COMMAND_DESCRIPTIONS = [
    {"command": "start", "description": "Welcome message and introduction to BotMother"},
    {"command": "help", "description": "Get help and guidance on bot creation"},
    {"command": "create_bot", "description": "Start the process of creating a new Telegram bot"},
    {"command": "list_bots", "description": "View all bots you've created"},
    {"command": "configure_bot", "description": "Configure settings for an existing bot"},
    {"command": "bot_status", "description": "Check the status of your bots"}
]

# Authentication and Session Messages
AUTH_REQUIRED_MESSAGE = "Telethon session requires authentication"
PHONE_PROMPT = "Enter your phone number: "
VERIFICATION_CODE_PROMPT = "Enter the verification code: "
TWO_FA_PASSWORD_PROMPT = "Enter your 2FA password: "

# Bot Creation Defaults
DEFAULT_BOTMOTHER_NAME = "Bootstrap BotMother"
DEFAULT_BOTMOTHER_USERNAME = "BootstrapBotMotherMVP_bot"

# Test Messages (for development/testing)
TEST_GREETING_MESSAGE = "Hello BotMother! Can you help me understand what you can do?"
TEST_SIMPLE_MESSAGE = "Hello bot!"

# Log Messages (user-visible status updates)
LOG_TOKEN_VALIDATION = "✅ Token valid for bot: @{username}"
LOG_TOKEN_VALIDATION_FAILED = "❌ Token validation failed: {error}"
LOG_DESCRIPTION_CONFIGURED = "✅ Description configured successfully"
LOG_DESCRIPTION_FAILED = "⚠️ Description configuration may have failed: {response}"
LOG_COMMANDS_CONFIGURED = "✅ Commands configured successfully"
LOG_COMMANDS_FAILED = "⚠️ Commands configuration may have failed: {response}"
LOG_SHORT_DESCRIPTION_CONFIGURED = "✅ Short description configured successfully"
LOG_SHORT_DESCRIPTION_FAILED = "⚠️ Short description configuration may have failed: {response}"
LOG_BOTMOTHER_SETUP_SUCCESS = "🎉 BotMother configuration completed successfully!"
LOG_BOTMOTHER_SETUP_PARTIAL = "⚠️ Some BotMother configuration steps may have failed"

# Success/Error Response Indicators
SUCCESS_INDICATORS = ["success", "updated", "done"]
ERROR_INDICATORS = ["error", "invalid", "wrong"]

# Timing Constants
BOTFATHER_RESPONSE_DELAY = 2  # seconds to wait between BotFather messages
BOT_RESPONSE_TIMEOUT = 10     # seconds to wait for bot responses
