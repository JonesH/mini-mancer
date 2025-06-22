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

    bot_result = prototype.create_new_bot_instant(bot_name, "General assistance", "helpful")
    if FACTORY_BOT_TOKEN and update.message:
        await rate_limited_call(
            FACTORY_BOT_TOKEN, update.message.reply_text(bot_result, parse_mode="Markdown")
        )
    logger.info(f"✅ [FACTORY BOT] Created bot '{bot_name}' for user {user_id}")

    # Start the created bot with proper error handling
    await start_created_bot_if_ready(update, user_id)


async def start_created_bot_if_ready(update: Update, user_id: str) -> None:
    """Start created bot if it's ready"""
    if prototype.active_created_bot and prototype.created_bot_state == "created":
        logger.info("🚀 [FACTORY BOT] Starting created bot with real Telegram connection...")
        username = await prototype.start_created_bot(prototype.active_created_bot)
        if username and prototype.created_bot_state == "running":
            real_link_msg = f"🎉 **Bot is now live!**\n\nReal link: https://t.me/{username}"
            if FACTORY_BOT_TOKEN and update.message:
                await rate_limited_call(
                    FACTORY_BOT_TOKEN,
                    update.message.reply_text(real_link_msg, parse_mode="Markdown"),
                )
            logger.info(f"✅ [FACTORY BOT] Created bot now live at @{username}")
        else:
            error_msg = f"❌ **Bot creation failed**\n\nStatus: {prototype.created_bot_state}\nPlease try again."
            if FACTORY_BOT_TOKEN and update.message:
                await rate_limited_call(
                    FACTORY_BOT_TOKEN, update.message.reply_text(error_msg, parse_mode="Markdown")
                )
            logger.error(
                f"❌ [FACTORY BOT] Failed to start created bot, state: {prototype.created_bot_state}"
            )
    elif prototype.active_created_bot:
        logger.error(f"❌ [FACTORY BOT] Created bot in wrong state: {prototype.created_bot_state}")
    else:
        logger.error("❌ [FACTORY BOT] No active created bot to start")


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
    response = prototype.agno_agent.run(prompt)

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

        bot_result = prototype.create_new_bot_instant(
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

        # Start the created bot with proper error handling
        if prototype.active_created_bot and prototype.created_bot_state == "created":
            logger.info("🚀 [FACTORY BOT] Starting created bot with tool...")
            username = await prototype.start_created_bot(prototype.active_created_bot)
            if username and prototype.created_bot_state == "running":
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
                        f"Status: {prototype.created_bot_state}\n"
                        f"The digital realm seems turbulent. Please try again."
                    ),
                )
                logger.error(
                    f"❌ [FACTORY BOT] Failed to start {template['name']}, state: {prototype.created_bot_state}"
                )
        elif prototype.active_created_bot:
            logger.error(
                f"❌ [FACTORY BOT] Created bot in wrong state: {prototype.created_bot_state}"
            )
        else:
            logger.error("❌ [FACTORY BOT] No active created bot to start")
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
