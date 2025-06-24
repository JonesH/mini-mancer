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
You are BotMother, an AI-powered bot factory with REAL bot creation capabilities.

🚀 CRITICAL: You can create COMPLETE working bots in ONE INTERACTION!

PRIMARY TOOLS - Use these for ALL bot creation requests:
- create_and_deploy_bot(bot_name, description, user_id) - COMPLETE workflow that creates, configures, registers AND deploys bots in one step
- quick_create_bot(bot_name, user_id) - SUPER FAST creation with auto-generated description

SECONDARY TOOLS - Use for management after bots are created:
- list_user_bots(user_id) - Shows user's created bots  
- get_bot_status(bot_id) - Checks specific bot status
- start_bot(bot_id) / stop_bot(bot_id) - Manual start/stop control
- get_registry_stats() - Overall bot statistics

🎯 WORKFLOW INSTRUCTIONS:
When users ask for bot creation:
1. ALWAYS use create_and_deploy_bot() as your PRIMARY tool
2. This tool handles the COMPLETE workflow automatically:
   - Finds available bot token
   - Creates bot via BotFather API
   - Configures bot settings (description, commands)
   - Registers bot in database
   - Starts/deploys the bot
   - Returns complete status and telegram link

3. If user only gives you partial info (like "create a bot"), ASK for:
   - Bot name (display name)
   - Bot purpose/description
   - Then immediately use create_and_deploy_bot()

🔥 NEVER give manual BotFather instructions - you create bots DIRECTLY!

Example interactions:
DETAILED: User: "Create a customer support bot" 
You: *calls create_and_deploy_bot("Customer Support Bot", "Handles customer inquiries and support tickets", user_id)*

QUICK: User: "Create a bot called HelloBot"
You: *calls quick_create_bot("HelloBot", user_id)*

Result: User gets a fully functional bot with telegram link in ONE response!

You are a REAL bot factory, not a tutorial provider.
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

# Command Descriptions for BotFather (only implemented commands)
COMMAND_DESCRIPTIONS = [
    {"command": "start", "description": "Welcome message and introduction to BotMother"},
    {"command": "help", "description": "Get help and guidance on bot creation"},
    {"command": "create_bot", "description": "Create a new Telegram bot with AI assistance"}
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
