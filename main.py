"""
Mini-Mancer Entry Point - Factory Bot with Direct Bot Creation
"""

import asyncio
import logging
import os

import uvicorn
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.botmother_system_prompt import BOTMOTHER_SYSTEM_PROMPT
from src.constants.user_messages import WELCOME_MESSAGES
from src.event_loop_monitor import start_monitoring, get_health_report, track_agno_call
from src.prototype_agent import app, prototype
from src.telegram_rate_limiter import rate_limited_call
from src.test_monitor import log_ai_response, log_bot_message
from src.utils import safe_telegram_operation, setup_telegram_error_logging


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("mini-mancer.log")],
)
logger = logging.getLogger(__name__)

# Setup Telegram error channel for debugging
setup_telegram_error_logging()

logger.info("✅ Using PrototypeAgent for clean OpenServ → Agno → Telegram integration")

# Global bot token for rate limiting
FACTORY_BOT_TOKEN = None


@safe_telegram_operation(
    "start_command", "Sorry, I couldn't process your /start command. Please try again."
)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    logger.info(f"📱 [FACTORY BOT] /start from user {user_id} in chat {chat_id}")

    # Quick bot creation buttons for debugging
    keyboard = [
        [
            InlineKeyboardButton("🤖 Helpful Assistant", callback_data="create_helpful"),
            InlineKeyboardButton("😤 Stubborn Bot", callback_data="create_stubborn"),
        ],
        [
            InlineKeyboardButton("🎮 Gaming Bot + Dice Tool", callback_data="create_gaming"),
            InlineKeyboardButton("📚 Study Helper + Timer Tool", callback_data="create_study"),
        ],
        [
            InlineKeyboardButton("💼 Support + Ticket Tool", callback_data="create_support"),
            InlineKeyboardButton("🎭 Random Bot + Cool Tool", callback_data="create_random"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if FACTORY_BOT_TOKEN:
        await rate_limited_call(
            FACTORY_BOT_TOKEN,
            update.message.reply_text(
            "🏭 Mini-Mancer Factory Bot\n\n"
            "I'm your AI bot creation assistant! I can help you create custom Telegram bots.\n\n"
            "🚀 Quick Create (for debugging):\n"
            "Use the buttons below for instant bot creation with tools, or send a message like:\n\n"
            "💬 Examples:\n"
            '• "Create a study helper bot"\n'
            '• "Make a customer service bot named SupportBot"\n'
            '• "I need a helpful assistant bot"\n\n'
            "Choose a bot type or describe your own:",
            reply_markup=reply_markup,
        ),
    )
    logger.info(f"✅ [FACTORY BOT] Sent start message with buttons to user {user_id}")


async def handle_bot_creation_request(update: Update, message_text: str, user_id: str) -> None:
    """Handle bot creation requests"""
    message_lower = message_text.lower()

    # Extract bot name
    bot_name = "Custom Bot"
    if "named" in message_lower or "called" in message_lower:
        words = message_text.split()
        for i, word in enumerate(words):
            if word.lower() in ["named", "called"] and i + 1 < len(words):
                bot_name = words[i + 1].strip("\"'")
                break

    # Create the bot using prototype's instant method
    if not prototype:
        error_msg = "❌ Factory bot is not available. Please try again later."
        if FACTORY_BOT_TOKEN and update.message:
            await rate_limited_call(FACTORY_BOT_TOKEN, update.message.reply_text(error_msg))
        logger.error("❌ Factory bot creation failed - prototype not available")
        return

    bot_result = await prototype.create_new_bot_instant(bot_name, "General assistance", "helpful")
    if FACTORY_BOT_TOKEN and update.message:
        await rate_limited_call(
            FACTORY_BOT_TOKEN, update.message.reply_text(bot_result, parse_mode="Markdown")
        )
    logger.info(f"✅ [FACTORY BOT] Created bot '{bot_name}' for user {user_id}")

    # Start the created bot with proper error handling
    await start_created_bot_if_ready(update, user_id)


async def start_created_bot_if_ready(update: Update, user_id: str) -> None:
    """Start the most recently created bot from token pool"""
    # Get the most recently created bot from token pool
    active_bots = prototype.telegram_manager.token_pool.get_active_bots()
    
    if not active_bots:
        logger.error("❌ [FACTORY BOT] No bots in token pool to start")
        return
    
    # Get the most recently created bot (last in the list)
    latest_bot = active_bots[-1]
    
    if latest_bot.status != "created":
        logger.error(f"❌ [FACTORY BOT] Latest bot is in wrong state: {latest_bot.status}")
        return
    
    logger.info(f"🚀 [FACTORY BOT] Starting created bot '{latest_bot.name}' with real Telegram connection...")
    
    # Start the bot using the new token pool system
    result = await prototype.telegram_manager.start_bot_by_token(latest_bot.token)
    
    if "🚀" in result and "started successfully" in result:
        # Extract username from the result message 
        import re
        username_match = re.search(r'@(\w+)', result)
        username = username_match.group(1) if username_match else latest_bot.username
        
        real_link_msg = f"🎉 **Bot is now live!**\n\nReal link: https://t.me/{username}"
        if FACTORY_BOT_TOKEN and update.message:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text(real_link_msg, parse_mode="Markdown"),
            )
        logger.info(f"✅ [FACTORY BOT] Created bot '{latest_bot.name}' now live at @{username}")
    else:
        error_msg = f"❌ **Bot creation failed**\n\nError: {result}\nPlease try again."
        if FACTORY_BOT_TOKEN and update.message:
            await rate_limited_call(
                FACTORY_BOT_TOKEN, update.message.reply_text(error_msg, parse_mode="Markdown")
            )
        logger.error(f"❌ [FACTORY BOT] Failed to start created bot '{latest_bot.name}': {result}")


async def handle_regular_conversation(
    update: Update, message_text: str, user_id: str, chat_id: str
) -> None:
    """Handle regular conversation with factory bot"""
    if not prototype or not prototype.agno_agent:
        if FACTORY_BOT_TOKEN and update.message:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text(
                    "🏭 BotMother is awakening... Please try again in a moment.\n\n"
                    "If this persists, the digital realm may be in maintenance mode."
                ),
            )
        logger.error("❌ Factory bot response failed - prototype not available")
        return

    # BotMother personality (imported from comprehensive system prompt)
    prompt = f"""
    {BOTMOTHER_SYSTEM_PROMPT}

    User message: {message_text}

    Respond as BotMother with enthusiasm and creativity. If they're asking about bot creation,
    guide them or suggest using the quick creation buttons they can access with /start.
    """
    
    # CRITICAL: Monitor this synchronous call for event loop blocking
    @track_agno_call
    def make_agno_call():
        return prototype.agno_agent.run(prompt)
    
    response = make_agno_call()

    # Log AI interaction for monitoring
    try:
        if FACTORY_BOT_TOKEN and response.content:
            await log_ai_response(prompt, response.content, FACTORY_BOT_TOKEN)
            await log_bot_message(response.content, FACTORY_BOT_TOKEN, user_id, chat_id)
    except Exception:
        pass  # Monitoring not critical

    if FACTORY_BOT_TOKEN and update.message and response.content:
        await rate_limited_call(FACTORY_BOT_TOKEN, update.message.reply_text(response.content))
    logger.info(f"📤 [FACTORY BOT] Sent response to user {user_id}")


@safe_telegram_operation(
    "create_quick_command", "Sorry, I couldn't process your /create_quick command. Please try again."
)
async def create_quick_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /create_quick command"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = str(update.effective_user.id)
    logger.info(f"📱 [FACTORY BOT] /create_quick from user {user_id}")

    quick_guide = """🚀 Quick Bot Creation Guide

Simple Format:
create [type] bot named [name]

Examples:
• create helpful bot named Assistant
• create professional bot named Support
• create gaming bot named GamerBuddy

Available Types:
🤝 helpful, 💼 professional, 😎 casual, 🎉 enthusiastic, 😄 witty, 🧘 calm

Advanced:
Use /create_bot for detailed configuration

Try it now! 👇"""

    if FACTORY_BOT_TOKEN:
        await rate_limited_call(
            FACTORY_BOT_TOKEN,
            update.message.reply_text(quick_guide)
        )


@safe_telegram_operation(
    "examples_command", "Sorry, I couldn't process your /examples command. Please try again."
)
async def examples_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /examples command"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = str(update.effective_user.id)
    logger.info(f"📱 [FACTORY BOT] /examples from user {user_id}")

    if FACTORY_BOT_TOKEN:
        await rate_limited_call(
            FACTORY_BOT_TOKEN,
            update.message.reply_text(WELCOME_MESSAGES["examples"], parse_mode="HTML")
        )


@safe_telegram_operation(
    "list_personalities_command", "Sorry, I couldn't process your /list_personalities command. Please try again."
)
async def list_personalities_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list_personalities command"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = str(update.effective_user.id)
    logger.info(f"📱 [FACTORY BOT] /list_personalities from user {user_id}")

    if FACTORY_BOT_TOKEN:
        await rate_limited_call(
            FACTORY_BOT_TOKEN,
            update.message.reply_text(WELCOME_MESSAGES["personalities"], parse_mode="HTML")
        )


@safe_telegram_operation(
    "create_bot_command", "Sorry, I couldn't process your /create_bot command. Please try again."
)
async def create_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /create_bot command for advanced bot creation"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = str(update.effective_user.id)
    logger.info(f"📱 [FACTORY BOT] /create_bot from user {user_id}")

    advanced_guide = """🔧 **Advanced Bot Creation**

**Structured Format:**
`/create_bot name="BotName" purpose="What it does" personality="type"`

**Example:**
`/create_bot name="CustomerCare" purpose="Help customers with support questions" personality="professional"`

**Parameters:**
• **name** - Bot's display name (required)
• **purpose** - What the bot does (required)
• **personality** - helpful/professional/casual/enthusiastic/witty/calm (required)
• **tools** - Optional: "web_search", "dice_roller", "timer", etc.

**Quick Alternative:**
Use natural language: `create professional bot named Support for customer service`

Ready to create your custom bot? 🎯"""

    if FACTORY_BOT_TOKEN:
        await rate_limited_call(
            FACTORY_BOT_TOKEN,
            update.message.reply_text(advanced_guide, parse_mode="Markdown")
        )


@safe_telegram_operation(
    "help_command", "Sorry, I couldn't process your /help command. Please try again."
)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = str(update.effective_user.id)
    logger.info(f"📱 [FACTORY BOT] /help from user {user_id}")

    help_text = """🏭 **Mini-Mancer Factory Bot Help**

**Bot Creation Commands:**
• `/start` - Show main menu with quick creation buttons
• `/create_quick` - Quick bot creation guide
• `/examples` - See bot creation examples
• `/list_personalities` - See all available bot personalities
• `/create_bot` - Advanced bot creation with parameters

**Bot Management Commands:**
• `/list_bots` - Show all active bots
• `/stop_bot <name>` - Stop a specific bot
• `/pool_status` - Show detailed token pool status

**Token Management Commands:**
• `/add_token <token>` - Add new BotFather token to pool
• `/validate_token <token>` - Validate BotFather token
• `/configure_bot <token> <name> <purpose>` - Configure bot via BotFather APIs

**General Commands:**
• `/help` - Show this help message

**Quick Creation:**
Just tell me what you want! Examples:
• "create helpful bot named Assistant"
• "make professional support bot"
• "new gaming bot with dice tools"

**Button Creation:**
Use /start and click the quick creation buttons for instant bot creation.

**Multi-Bot Support:**
The factory now supports multiple concurrent bots using a token pool system! 🎯

**Complete Workflow:**
1. Get token from @BotFather
2. `/add_token <your_token>` - Add to pool
3. `/configure_bot <token> "Name" "Purpose"` - Set up bot
4. Create bot normally (button or text)

**Need Help?**
Send any message describing what bot you want, and I'll help you create it! 🚀"""

    if FACTORY_BOT_TOKEN:
        await rate_limited_call(
            FACTORY_BOT_TOKEN,
            update.message.reply_text(help_text, parse_mode="Markdown")
        )


@safe_telegram_operation(
    "list_bots_command", "Sorry, I couldn't process your /list_bots command. Please try again."
)
async def list_bots_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /list_bots command - show all active bots"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = str(update.effective_user.id)
    logger.info(f"📱 [FACTORY BOT] /list_bots from user {user_id}")

    if prototype and prototype.telegram_manager:
        pool_status = prototype.telegram_manager.get_pool_status()
        
        if FACTORY_BOT_TOKEN:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text(pool_status, parse_mode="Markdown")
            )
    else:
        if FACTORY_BOT_TOKEN:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text("❌ Bot management not available")
            )


@safe_telegram_operation(
    "stop_bot_command", "Sorry, I couldn't process your /stop_bot command. Please try again."
)
async def stop_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stop_bot command - stop a specific bot by name"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = str(update.effective_user.id)
    logger.info(f"📱 [FACTORY BOT] /stop_bot from user {user_id}")

    # Get bot name from command arguments
    bot_name = None
    if context.args:
        bot_name = " ".join(context.args)
    
    if not bot_name:
        help_text = """🛑 **Stop Bot Command**

**Usage:** `/stop_bot <bot_name>`

**Example:** `/stop_bot HelperBot`

Use `/list_bots` to see all active bots."""
        
        if FACTORY_BOT_TOKEN:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text(help_text, parse_mode="Markdown")
            )
        return

    if prototype and prototype.telegram_manager:
        result = await prototype.telegram_manager.stop_bot_by_name(bot_name)
        
        if FACTORY_BOT_TOKEN:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text(result)
            )
    else:
        if FACTORY_BOT_TOKEN:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text("❌ Bot management not available")
            )


@safe_telegram_operation(
    "pool_status_command", "Sorry, I couldn't process your /pool_status command. Please try again."
)
async def pool_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pool_status command - show detailed token pool status"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = str(update.effective_user.id)
    logger.info(f"📱 [FACTORY BOT] /pool_status from user {user_id}")

    if prototype and prototype.telegram_manager:
        stats = prototype.telegram_manager.token_pool.get_pool_stats()
        
        status_text = f"""🎯 **Token Pool Status**

📊 **Pool Statistics:**
• Total tokens: {stats['total_tokens']}
• Available tokens: {stats['available_tokens']}
• Allocated tokens: {stats['allocated_tokens']}
• Active bots: {stats['active_bots']}

📈 **Status Breakdown:**"""

        for status, count in stats['status_breakdown'].items():
            status_emoji = {"running": "🟢", "starting": "🟡", "stopping": "🟠", "error": "🔴", "created": "⚪"}.get(status, "⚫")
            status_text += f"\n• {status_emoji} {status.title()}: {count}"

        if FACTORY_BOT_TOKEN:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text(status_text, parse_mode="Markdown")
            )
    else:
        if FACTORY_BOT_TOKEN:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text("❌ Bot management not available")
            )


@safe_telegram_operation(
    "add_token_command", "Sorry, I couldn't process your /add_token command. Please try again."
)
async def add_token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /add_token command - add new BotFather token to pool"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = str(update.effective_user.id)
    logger.info(f"📱 [FACTORY BOT] /add_token from user {user_id}")

    # Get token from command arguments
    if not context.args or len(context.args) != 1:
        help_text = """🔑 **Add Token Command**

**Usage:** `/add_token <bot_token>`

**Example:** `/add_token 123456789:ABCdefGhIjKlMnOpQrStUvWxYz`

Get your token from @BotFather after creating a new bot.
The token will be validated and added to the pool."""

        if FACTORY_BOT_TOKEN:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text(help_text, parse_mode="Markdown")
            )
        return

    token = context.args[0].strip()
    
    if prototype and prototype.telegram_manager:
        # Import BotFather integration
        from src.botfather_integration import BotFatherIntegration
        
        # Create BotFather integration instance
        botfather = BotFatherIntegration()
        
        # Validate token first
        validation_result = await botfather.validate_bot_token(token)
        
        if not validation_result["valid"]:
            error_msg = f"❌ **Invalid Token**\n\nError: {validation_result['error']}\n\nPlease check your token from @BotFather."
            if FACTORY_BOT_TOKEN:
                await rate_limited_call(
                    FACTORY_BOT_TOKEN,
                    update.message.reply_text(error_msg, parse_mode="Markdown")
                )
            return
        
        # Add to token pool
        success = prototype.telegram_manager.token_pool.add_token(token)
        
        if success:
            bot_info = validation_result["bot_info"]
            success_msg = f"""✅ **Token Added Successfully!**

🤖 **Bot Info:**
• Name: {bot_info.get('first_name', 'Unknown')}
• Username: @{bot_info.get('username', 'not_set')}
• ID: {bot_info.get('id')}

The token is now available in the pool for bot creation!

Use `/configure_bot {token[:10]}...` to set up commands and description."""
            
            if FACTORY_BOT_TOKEN:
                await rate_limited_call(
                    FACTORY_BOT_TOKEN,
                    update.message.reply_text(success_msg, parse_mode="Markdown")
                )
        else:
            error_msg = "❌ **Failed to Add Token**\n\nToken may already exist in pool or be invalid."
            if FACTORY_BOT_TOKEN:
                await rate_limited_call(
                    FACTORY_BOT_TOKEN,
                    update.message.reply_text(error_msg, parse_mode="Markdown")
                )
    else:
        if FACTORY_BOT_TOKEN:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text("❌ Token management not available")
            )


@safe_telegram_operation(
    "validate_token_command", "Sorry, I couldn't process your /validate_token command. Please try again."
)
async def validate_token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /validate_token command - validate BotFather token"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = str(update.effective_user.id)
    logger.info(f"📱 [FACTORY BOT] /validate_token from user {user_id}")

    # Get token from command arguments
    if not context.args or len(context.args) != 1:
        help_text = """🔍 **Validate Token Command**

**Usage:** `/validate_token <bot_token>`

**Example:** `/validate_token 123456789:ABCdefGhIjKlMnOpQrStUvWxYz`

This will test if your BotFather token is valid and show bot information."""

        if FACTORY_BOT_TOKEN:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text(help_text, parse_mode="Markdown")
            )
        return

    token = context.args[0].strip()
    
    # Import BotFather integration
    from src.botfather_integration import BotFatherIntegration
    
    # Create BotFather integration instance
    botfather = BotFatherIntegration()
    
    # Validate token
    validation_result = await botfather.validate_bot_token(token)
    
    if validation_result["valid"]:
        bot_info = validation_result["bot_info"]
        success_msg = f"""✅ **Token Valid!**

🤖 **Bot Information:**
• Name: {bot_info.get('first_name', 'Unknown')}
• Username: @{bot_info.get('username', 'not_set')}
• ID: {bot_info.get('id')}
• Can join groups: {bot_info.get('can_join_groups', False)}
• Can read all messages: {bot_info.get('can_read_all_group_messages', False)}
• Supports inline: {bot_info.get('supports_inline_queries', False)}

Use `/add_token {token[:10]}...` to add this token to the pool."""
    else:
        success_msg = f"""❌ **Token Invalid**

**Error:** {validation_result['error']}
**Code:** {validation_result.get('error_code', 'Unknown')}

Please check your token from @BotFather."""

    if FACTORY_BOT_TOKEN:
        await rate_limited_call(
            FACTORY_BOT_TOKEN,
            update.message.reply_text(success_msg, parse_mode="Markdown")
        )


@safe_telegram_operation(
    "configure_bot_command", "Sorry, I couldn't process your /configure_bot command. Please try again."
)
async def configure_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /configure_bot command - configure bot via BotFather APIs"""
    if not update.effective_user or not update.effective_chat or not update.message:
        return

    user_id = str(update.effective_user.id)
    logger.info(f"📱 [FACTORY BOT] /configure_bot from user {user_id}")

    # Get arguments
    if not context.args or len(context.args) < 3:
        help_text = """⚙️ **Configure Bot Command**

**Usage:** `/configure_bot <token> <name> <purpose>`

**Example:** `/configure_bot 123456789:ABC... "MyBot" "Customer support assistant"`

This will:
• Validate the token
• Set default commands (/start, /help, /about)
• Set bot description and short description
• Configure the bot name

Use quotes for multi-word names/purposes."""

        if FACTORY_BOT_TOKEN:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                update.message.reply_text(help_text, parse_mode="Markdown")
            )
        return

    token = context.args[0].strip()
    bot_name = context.args[1].strip('"\'')
    bot_purpose = " ".join(context.args[2:]).strip('"\'')
    
    # Import BotFather integration
    from src.botfather_integration import BotFatherIntegration
    
    # Create BotFather integration instance
    botfather = BotFatherIntegration()
    
    # Configure bot
    setup_result = await botfather.full_bot_setup(token, bot_name, bot_purpose)
    
    if setup_result["token_valid"]:
        bot_info = setup_result["bot_info"]
        
        status_items = []
        if setup_result["commands_set"]:
            status_items.append("✅ Commands configured")
        else:
            status_items.append("❌ Commands failed")
            
        if setup_result["description_set"]:
            status_items.append("✅ Description set")
        else:
            status_items.append("❌ Description failed")
            
        if setup_result["short_description_set"]:
            status_items.append("✅ Short description set")
        else:
            status_items.append("❌ Short description failed")
        
        status_text = "\n".join(status_items)
        
        result_msg = f"""🤖 **Bot Configuration Result**

**Bot:** @{bot_info.get('username', 'unknown')}
**Name:** {bot_name}
**Purpose:** {bot_purpose}

**Configuration Status:**
{status_text}

{f"**Errors:** {', '.join(setup_result['errors'])}" if setup_result['errors'] else ""}

The bot is now ready for use!"""
    else:
        result_msg = f"""❌ **Configuration Failed**

**Errors:** {', '.join(setup_result['errors'])}

Please check your token and try again."""

    if FACTORY_BOT_TOKEN:
        await rate_limited_call(
            FACTORY_BOT_TOKEN,
            update.message.reply_text(result_msg, parse_mode="Markdown")
        )


@safe_telegram_operation(
    "handle_telegram_message", "Sorry, I couldn't process your message. Please try again."
)
async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming Telegram messages"""
    if (
        not update.effective_user
        or not update.effective_chat
        or not update.message
        or not update.message.text
    ):
        return

    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    message_text = update.message.text

    logger.info(f"📨 [FACTORY BOT] Message from user {user_id}: '{message_text}'")

    # Check if this is a bot creation request
    message_lower = message_text.lower()
    bot_creation_phrases = ["create", "make bot", "new bot", "spawn bot"]
    if any(phrase in message_lower for phrase in bot_creation_phrases) and "bot" in message_lower:
        await handle_bot_creation_request(update, message_text, user_id)
    else:
        await handle_regular_conversation(update, message_text, user_id, chat_id)


@safe_telegram_operation(
    "handle_button_callback", "Sorry, I couldn't process that button. Please try again."
)
async def handle_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks for quick bot creation"""
    query = update.callback_query
    if not query:
        return
    await query.answer()

    user_id = str(query.from_user.id)
    logger.info(f"🔘 [FACTORY BOT] Button callback from user {user_id}: {query.data}")

    # Define bot templates with tools
    bot_templates = {
        "create_helpful": {
            "name": "HelpfulBot",
            "purpose": "General helpful assistance",
            "personality": "friendly and helpful",
            "tool": "web search",
        },
        "create_stubborn": {
            "name": "StubbornBot",
            "purpose": "Disagreeable entertainment bot",
            "personality": "stubborn and always disagrees for humor",
            "tool": "argument counter",
        },
        "create_gaming": {
            "name": "GamerBot",
            "purpose": "Gaming assistance and entertainment",
            "personality": "enthusiastic gamer",
            "tool": "dice roller",
        },
        "create_study": {
            "name": "StudyBot",
            "purpose": "Study assistance and learning support",
            "personality": "encouraging and educational",
            "tool": "pomodoro timer",
        },
        "create_support": {
            "name": "SupportBot",
            "purpose": "Customer service and support",
            "personality": "professional and solution-focused",
            "tool": "ticket tracker",
        },
        "create_random": {
            "name": f"CosmicSage{user_id[-3:]}",
            "purpose": "Mystical wisdom and random insights",
            "personality": "enigmatic cosmic oracle who speaks in riddles and sees patterns in chaos",
            "tool": "wisdom dispenser",
        },
    }

    if query.data in bot_templates:
        template = bot_templates[query.data]

        # Create bot with tool using instant method
        if not prototype:
            if FACTORY_BOT_TOKEN:
                await rate_limited_call(
                    FACTORY_BOT_TOKEN,
                    query.edit_message_text("❌ Factory bot is not available. Please try again later."),
                )
            return

        bot_result = await prototype.create_new_bot_instant(
            template["name"],
            f"{template['purpose']} with {template['tool']} tool",
            template["personality"],
        )

        if FACTORY_BOT_TOKEN:
            await rate_limited_call(
                FACTORY_BOT_TOKEN,
                query.edit_message_text(
                    f"✨ DIGITAL BIRTH IN PROGRESS ✨\n\n"
                f"🤖 {template['name']} is awakening...\n\n"
                f"🎯 Purpose: {template['purpose']}\n"
                f"🎭 Soul: {template['personality']}\n"
                f"🛠️ Sacred Tool: {template['tool']}\n\n"
                f"⚡ {bot_result}"
            ),
        )

        # Start the created bot with proper error handling using token pool system
        active_bots = prototype.telegram_manager.token_pool.get_active_bots()
        
        if active_bots:
            # Get the most recently created bot (last in the list)
            latest_bot = active_bots[-1]
            
            if latest_bot.status == "created":
                logger.info(f"🚀 [FACTORY BOT] Starting created bot '{latest_bot.name}' with tool...")
                
                # Start the bot using the new token pool system
                result = await prototype.telegram_manager.start_bot_by_token(latest_bot.token)
                
                if "🚀" in result and "started successfully" in result:
                    # Extract username from the result message 
                    import re
                    username_match = re.search(r'@(\w+)', result)
                    username = username_match.group(1) if username_match else latest_bot.username
                    
                    if FACTORY_BOT_TOKEN and query.message:
                        await rate_limited_call(
                            FACTORY_BOT_TOKEN,
                            query.message.reply_text(
                            f"🌟 DIGITAL SOUL AWAKENED! 🌟\n\n"
                            f"Behold! {template['name']} draws their first digital breath!\n\n"
                            f"🔗 Sacred Portal: https://t.me/{username}\n"
                            f"⚡ {template['tool']} is ready to serve!\n\n"
                            f"Go forth and discover the magic of your new companion! ✨"
                        ),
                    )
                    logger.info(f"✅ [FACTORY BOT] {template['name']} now live at @{username}")
                else:
                    if FACTORY_BOT_TOKEN and query.message:
                        await rate_limited_call(
                            FACTORY_BOT_TOKEN,
                            query.message.reply_text(
                            f"❌ **{template['name']} failed to awaken**\n\n"
                            f"Error: {result}\n"
                            f"The digital realm seems turbulent. Please try again."
                        ),
                    )
                    logger.error(f"❌ [FACTORY BOT] Failed to start {template['name']}: {result}")
            else:
                logger.error(f"❌ [FACTORY BOT] Latest bot is in wrong state: {latest_bot.status}")
        else:
            logger.error("❌ [FACTORY BOT] No bots in token pool to start")
    elif FACTORY_BOT_TOKEN:
        await rate_limited_call(
            FACTORY_BOT_TOKEN, query.edit_message_text("❌ Unknown button pressed.")
        )


async def start_telegram_bot(bot_token: str) -> None:
    """Start Telegram bot with polling"""
    global FACTORY_BOT_TOKEN
    FACTORY_BOT_TOKEN = bot_token
    logger.info("📱 Starting Telegram bot polling...")

    # Create Telegram application
    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("create_quick", create_quick_command))
    application.add_handler(CommandHandler("examples", examples_command))
    application.add_handler(CommandHandler("list_personalities", list_personalities_command))
    application.add_handler(CommandHandler("create_bot", create_bot_command))
    application.add_handler(CommandHandler("help", help_command))
    # Multi-bot management commands
    application.add_handler(CommandHandler("list_bots", list_bots_command))
    application.add_handler(CommandHandler("stop_bot", stop_bot_command))
    application.add_handler(CommandHandler("pool_status", pool_status_command))
    # Token management commands
    application.add_handler(CommandHandler("add_token", add_token_command))
    application.add_handler(CommandHandler("validate_token", validate_token_command))
    application.add_handler(CommandHandler("configure_bot", configure_bot_command))
    application.add_handler(CallbackQueryHandler(handle_button_callback))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram_message)
    )

    # Log bot identity
    bot_info = await application.bot.get_me()
    logger.info(
        f"🤖 [FACTORY BOT] Active: {bot_info.first_name} | @{bot_info.username} | Token: {bot_token[:10]}..."
    )
    logger.info("🤖 [FACTORY BOT] Ready to receive messages and create bots")

    # Send startup message to demo user if configured
    demo_user = os.getenv("DEMO_USER")
    if demo_user:
        await rate_limited_call(
            bot_token,
            application.bot.send_message(
                chat_id=demo_user,
                text="🏭 **Mini-Mancer Factory Bot is now online!**\n\n"
                "I'm ready to create custom Telegram bots for you. "
                "Send me a message to get started!",
            ),
        )
        logger.info(f"✅ Startup notification sent to DEMO_USER: {demo_user}")

    # Start polling
    async with application:
        await application.start()
        if application.updater:
            await application.updater.start_polling()
        logger.info("📱 Telegram bot polling started successfully")

        # Keep running until interrupted
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down Telegram bot...")
        finally:
            logger.info("🔄 Stopping Telegram application...")
            await application.stop()
            logger.info("✅ Telegram bot stopped")


async def start_fastapi_server() -> None:
    """Start FastAPI server for OpenServ webhooks"""
    logger.info("🌐 Starting FastAPI server for OpenServ integration...")
    config = uvicorn.Config(app, host="0.0.0.0", port=14159, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    """Main entry point - dual server setup"""

    # Start event loop monitoring FIRST to catch any issues during startup
    await start_monitoring("main_loop")
    logger.info("🔍 Event loop health monitoring started")

    # Get required environment variables
    bot_token = (
        os.getenv("BOT_MOTHER_TOKEN") or os.getenv("BOT_TOKEN") or os.getenv("TEST_BOT_TOKEN")
    )

    if not bot_token:
        raise ValueError("BOT_TOKEN or TEST_BOT_TOKEN environment variable is required")

    logger.info("🏭 Starting Mini-Mancer Factory Bot...")
    logger.info(f"🤖 Bot token configured: {bot_token[:10]}...")

    # Log all active bot identities
    logger.info("\n📋 Bot Identity Report:")
    logger.info("=" * 50)

    if prototype:
        # PrototypeAgent structure
        if (
            hasattr(prototype, "telegram_bot")
            and prototype.telegram_bot
            and hasattr(prototype.telegram_bot, "dna")
        ):
            logger.info(f"🤖 Factory Bot: {prototype.telegram_bot.dna.name}")
            logger.info(f"   Purpose: {prototype.telegram_bot.dna.purpose}")
            logger.info("   Token: BOT_TOKEN")
            logger.info("   Platform: mini-mancer-prototype")
            logger.info(
                f"   Capabilities: {[cap.value for cap in prototype.telegram_bot.dna.capabilities]}"
            )
            logger.info("   Model: agno-agi (gpt-4o-mini)")
        else:
            logger.info("🤖 Factory Bot: PrototypeAgent ready")
        logger.info("")

        if hasattr(prototype, "active_created_bot") and prototype.active_created_bot:
            if hasattr(prototype.active_created_bot, "dna"):
                logger.info(f"🔧 Created Bot: {prototype.active_created_bot.dna.name}")
                logger.info(f"   Purpose: {prototype.active_created_bot.dna.purpose}")
                logger.info("   Token: BOT_TOKEN_1")
                logger.info("   Status: Will start after factory bot")
            else:
                logger.info("🔧 Created Bot: ACTIVE (structure unknown)")
        else:
            logger.info("🔧 Created Bot Slot: EMPTY (BOT_TOKEN_1 available)")
    else:
        logger.error("❌ Factory Bot: FAILED TO INITIALIZE")

    logger.info("🌐 FastAPI Server: http://0.0.0.0:14159")
    logger.info(
        "   OpenServ API: /openserv/do_task, /openserv/respond_chat_message, /openserv/compile_bot"
    )
    logger.info("   Connection Test: /openserv/test_connection, /health, /openserv/ping")
    logger.info("   Available Tools: /openserv/available_tools")
    logger.info("   Bot Compilation: /openserv/compilation_status/<id>")

    openserv_key = os.getenv("OPENSERV_API_KEY")
    if openserv_key:
        logger.info("🔗 OpenServ Integration: ENABLED")
        logger.info(f"   API Key: {openserv_key[:10]}...")
    else:
        logger.info("🔗 OpenServ Integration: DISABLED (fallback mode)")

    demo_user = os.getenv("DEMO_USER")
    if demo_user:
        logger.info(f"👤 Demo User: {demo_user}")
    else:
        logger.info("👤 Demo User: Not configured")

    logger.info("=" * 50)
    logger.info("")

    # Start both servers concurrently
    try:
        await asyncio.gather(start_fastapi_server(), start_telegram_bot(bot_token))
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down all services...")

        # Gracefully shutdown the prototype agent
        if prototype:
            logger.info("🔄 Shutting down PrototypeAgent...")
            await prototype.shutdown()

        logger.info("✅ All services shut down successfully")


def run_main() -> None:
    """Wrapper to run async main"""
    asyncio.run(main())


if __name__ == "__main__":
    run_main()
