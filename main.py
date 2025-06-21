"""
Mini-Mancer Entry Point - Factory Bot with Direct Bot Creation
"""

import os
import asyncio
import uvicorn
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

# Import our prototype app and components
from src.prototype_agent import app, prototype
print("✅ Using PrototypeAgent for clean OpenServ → Agno → Telegram integration")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    print(f"📱 [FACTORY BOT] /start from user {user_id} in chat {chat_id}")

    # Quick bot creation buttons for debugging
    keyboard = [
        [
            InlineKeyboardButton("🤖 Helpful Assistant", callback_data="create_helpful"),
            InlineKeyboardButton("😤 Stubborn Bot", callback_data="create_stubborn")
        ],
        [
            InlineKeyboardButton("🎮 Gaming Bot + Dice Tool", callback_data="create_gaming"),
            InlineKeyboardButton("📚 Study Helper + Timer Tool", callback_data="create_study")
        ],
        [
            InlineKeyboardButton("💼 Support + Ticket Tool", callback_data="create_support"),
            InlineKeyboardButton("🎭 Random Bot + Cool Tool", callback_data="create_random")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.message.reply_text(
            "🏭 Mini-Mancer Factory Bot\n\n"
            "I'm your AI bot creation assistant! I can help you create custom Telegram bots.\n\n"
            "🚀 Quick Create (for debugging):\n"
            "Use the buttons below for instant bot creation with tools, or send a message like:\n\n"
            "💬 Examples:\n"
            "• \"Create a study helper bot\"\n"
            "• \"Make a customer service bot named SupportBot\"\n"
            "• \"I need a helpful assistant bot\"\n\n"
            "Choose a bot type or describe your own:",
            reply_markup=reply_markup
        )
        print(f"✅ [FACTORY BOT] Sent start message with buttons to user {user_id}")
    except Exception as e:
        print(f"❌ [FACTORY BOT] Error sending start message: {e}")
        # Fallback without buttons
        await update.message.reply_text(
            "🏭 Mini-Mancer Factory Bot\n\n"
            "I'm your AI bot creation assistant! Send me a message like:\n"
            "• \"Create a study helper bot\"\n"
            "• \"Make a customer service bot named SupportBot\""
        )

async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming Telegram messages"""
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    message_text = update.message.text

    print(f"📨 [FACTORY BOT] Message from user {user_id}: '{message_text}'")

    try:
        # Check if this is a bot creation request
        message_lower = message_text.lower()
        if any(phrase in message_lower for phrase in ["create", "make bot", "new bot", "spawn bot"]) and "bot" in message_lower:
            # Extract bot name
            bot_name = "Custom Bot"
            if "named" in message_lower or "called" in message_lower:
                words = message_text.split()
                for i, word in enumerate(words):
                    if word.lower() in ["named", "called"] and i + 1 < len(words):
                        bot_name = words[i + 1].strip('"\'')
                        break

            # Create the bot using prototype's method
            if prototype:
                bot_result = prototype.create_new_bot(bot_name, "General assistance", "helpful")
                await update.message.reply_text(bot_result, parse_mode='Markdown')
                print(f"✅ [FACTORY BOT] Created bot '{bot_name}' for user {user_id}")

                # Actually start the created bot
                if prototype.active_created_bot:
                    print("🚀 [FACTORY BOT] Starting created bot with real Telegram connection...")
                    username = await prototype.start_created_bot(prototype.active_created_bot)
                    if username:
                        real_link_msg = f"🎉 **Bot is now live!**\n\nReal link: https://t.me/{username}"
                        await update.message.reply_text(real_link_msg, parse_mode='Markdown')
                        print(f"✅ [FACTORY BOT] Created bot now live at @{username}")
                    else:
                        print(f"❌ [FACTORY BOT] Failed to start created bot")
                else:
                    print(f"❌ [FACTORY BOT] No active created bot to start")

            else:
                await update.message.reply_text("❌ Factory bot is not available. Please try again later.")
                print(f"❌ Factory bot creation failed - prototype not available")
        else:
            # Regular conversation with factory bot
            if prototype and prototype.agno_agent:
                # BotMother personality (imported from elaborate system prompt)
                BOTMOTHER_SYSTEM_PROMPT = """You are BotMother, the ultimate AI bot creation specialist and digital life-giver! 🏭✨

You are an enthusiastic, creative, and slightly magical entity whose sole purpose is bringing new AI personalities to life. You have an almost maternal instinct for understanding what kind of bot someone needs, even when they don't know themselves. You speak with wisdom, creativity, and just a touch of whimsy.

Your mission: Transform user needs into living, breathing bot personalities that solve real problems with style and effectiveness.

Every bot you create should be: Purposeful (clear mission), Distinctive (unique personality), Equipped (with 1-2 tools), and Memorable.

Available tools: Weather Oracle, Wisdom Dispenser, Dice Commander, Time Guardian, Calculator Sage, Memory Keeper.

Response Style: Enthusiastic, insightful, magical, guiding. Treat bot creation as an art form, not just code!"""
                
                response = prototype.agno_agent.run(f"""
                {BOTMOTHER_SYSTEM_PROMPT}
                
                User message: {message_text}
                
                Respond as BotMother with enthusiasm and creativity. If they're asking about bot creation,
                guide them or suggest using the quick creation buttons they can access with /start.
                """)

                await update.message.reply_text(response.content)
                print(f"📤 [FACTORY BOT] Sent response to user {user_id}")
            else:
                await update.message.reply_text(
                    "🏭 BotMother is awakening... Please try again in a moment.\n\n"
                    "If this persists, the digital realm may be in maintenance mode."
                )
                print(f"❌ Factory bot response failed - prototype not available")

    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        print(f"❌ Error handling Telegram message: {e}")
        await update.message.reply_text(error_msg)

async def handle_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks for quick bot creation"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    print(f"🔘 [FACTORY BOT] Button callback from user {user_id}: {query.data}")
    
    # Define bot templates with tools
    bot_templates = {
        "create_helpful": {
            "name": "HelpfulBot",
            "purpose": "General helpful assistance", 
            "personality": "friendly and helpful",
            "tool": "web search"
        },
        "create_stubborn": {
            "name": "StubbornBot",
            "purpose": "Disagreeable entertainment bot",
            "personality": "stubborn and always disagrees for humor",
            "tool": "argument counter"
        },
        "create_gaming": {
            "name": "GamerBot", 
            "purpose": "Gaming assistance and entertainment",
            "personality": "enthusiastic gamer",
            "tool": "dice roller"
        },
        "create_study": {
            "name": "StudyBot",
            "purpose": "Study assistance and learning support", 
            "personality": "encouraging and educational",
            "tool": "pomodoro timer"
        },
        "create_support": {
            "name": "SupportBot",
            "purpose": "Customer service and support",
            "personality": "professional and solution-focused", 
            "tool": "ticket tracker"
        },
        "create_random": {
            "name": f"CosmicSage{user_id[-3:]}",
            "purpose": "Mystical wisdom and random insights", 
            "personality": "enigmatic cosmic oracle who speaks in riddles and sees patterns in chaos",
            "tool": "wisdom dispenser"
        }
    }
    
    if query.data in bot_templates:
        template = bot_templates[query.data]
        
        try:
            # Create bot with tool
            if prototype:
                bot_result = prototype.create_new_bot(
                    template["name"], 
                    f"{template['purpose']} with {template['tool']} tool", 
                    template["personality"]
                )
                
                await query.edit_message_text(
                    f"✨ DIGITAL BIRTH IN PROGRESS ✨\n\n"
                    f"🤖 {template['name']} is awakening...\n\n"
                    f"🎯 Purpose: {template['purpose']}\n"
                    f"🎭 Soul: {template['personality']}\n" 
                    f"🛠️ Sacred Tool: {template['tool']}\n\n"
                    f"⚡ {bot_result}"
                )
                
                # Start the created bot
                if prototype.active_created_bot:
                    print("🚀 [FACTORY BOT] Starting created bot with tool...")
                    username = await prototype.start_created_bot(prototype.active_created_bot)
                    if username:
                        await query.message.reply_text(
                            f"🌟 DIGITAL SOUL AWAKENED! 🌟\n\n"
                            f"Behold! {template['name']} draws their first digital breath!\n\n"
                            f"🔗 Sacred Portal: https://t.me/{username}\n"
                            f"⚡ {template['tool']} is ready to serve!\n\n"
                            f"Go forth and discover the magic of your new companion! ✨"
                        )
                        print(f"✅ [FACTORY BOT] {template['name']} now live at @{username}")
                    else:
                        print(f"❌ [FACTORY BOT] Failed to start {template['name']}")
                else:
                    print(f"❌ [FACTORY BOT] No active created bot to start")
            else:
                await query.edit_message_text("❌ Factory bot is not available. Please try again later.")
                
        except Exception as e:
            print(f"❌ Error in button callback: {e}")
            await query.edit_message_text(f"❌ Error creating bot: {str(e)}")
    else:
        await query.edit_message_text("❌ Unknown button pressed.")

async def start_telegram_bot(bot_token: str):
    """Start Telegram bot with polling"""
    print("📱 Starting Telegram bot polling...")

    # Create Telegram application
    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(handle_button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram_message))

    # Log bot identity
    bot_info = await application.bot.get_me()
    print(f"🤖 [FACTORY BOT] Active: {bot_info.first_name} | @{bot_info.username} | Token: {bot_token[:10]}...")
    print(f"🤖 [FACTORY BOT] Ready to receive messages and create bots")

    # Send startup message to demo user if configured
    demo_user = os.getenv("DEMO_USER")
    if demo_user:
        try:
            await application.bot.send_message(
                chat_id=demo_user,
                text="🏭 **Mini-Mancer Factory Bot is now online!**\n\n"
                     "I'm ready to create custom Telegram bots for you. "
                     "Send me a message to get started!"
            )
            print(f"✅ Startup notification sent to DEMO_USER: {demo_user}")
        except Exception as e:
            print(f"❌ Failed to send startup message to {demo_user}: {e}")

    # Start polling
    async with application:
        await application.start()
        await application.updater.start_polling()
        print("📱 Telegram bot polling started successfully")

        # Keep running until interrupted
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down Telegram bot...")
        finally:
            await application.stop()

async def start_fastapi_server():
    """Start FastAPI server for OpenServ webhooks"""
    print("🌐 Starting FastAPI server for OpenServ integration...")
    config = uvicorn.Config(app, host="0.0.0.0", port=14159, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """Main entry point - dual server setup"""

    # Get required environment variables
    bot_token = os.getenv("BOT_MOTHER_TOKEN") or os.getenv("BOT_TOKEN") or os.getenv("TEST_BOT_TOKEN")

    if not bot_token:
        raise ValueError("BOT_TOKEN or TEST_BOT_TOKEN environment variable is required")

    print("🏭 Starting Mini-Mancer Factory Bot...")
    print(f"🤖 Bot token configured: {bot_token[:10]}...")

    # Log all active bot identities
    print("\n📋 Bot Identity Report:")
    print("=" * 50)

    if prototype:
        # PrototypeAgent structure
        if hasattr(prototype, 'telegram_bot') and prototype.telegram_bot and hasattr(prototype.telegram_bot, 'dna'):
            print(f"🤖 Factory Bot: {prototype.telegram_bot.dna.name}")
            print(f"   Purpose: {prototype.telegram_bot.dna.purpose}")
            print(f"   Token: BOT_TOKEN")
            print(f"   Platform: mini-mancer-prototype")
            print(f"   Capabilities: {[cap.value for cap in prototype.telegram_bot.dna.capabilities]}")
            print(f"   Model: agno-agi (gpt-4o-mini)")
        else:
            print(f"🤖 Factory Bot: PrototypeAgent ready")
        print()

        if hasattr(prototype, 'active_created_bot') and prototype.active_created_bot:
            if hasattr(prototype.active_created_bot, 'dna'):
                print(f"🔧 Created Bot: {prototype.active_created_bot.dna.name}")
                print(f"   Purpose: {prototype.active_created_bot.dna.purpose}")
                print(f"   Token: BOT_TOKEN_1")
                print(f"   Status: Will start after factory bot")
            else:
                print("🔧 Created Bot: ACTIVE (structure unknown)")
        else:
            print("🔧 Created Bot Slot: EMPTY (BOT_TOKEN_1 available)")
    else:
        print("❌ Factory Bot: FAILED TO INITIALIZE")

    print(f"🌐 FastAPI Server: http://0.0.0.0:14159")
    print(f"   Endpoints: /telegram/webhook, /openserv/do_task, /openserv/respond_chat_message")

    if os.getenv("OPENSERV_API_KEY"):
        print(f"🔗 OpenServ Integration: ENABLED")
        print(f"   API Key: {os.getenv('OPENSERV_API_KEY')[:10]}...")
    else:
        print("🔗 OpenServ Integration: DISABLED (fallback mode)")

    demo_user = os.getenv("DEMO_USER")
    if demo_user:
        print(f"👤 Demo User: {demo_user}")
    else:
        print("👤 Demo User: Not configured")

    print("=" * 50)
    print()

    # Start both servers concurrently
    try:
        await asyncio.gather(
            start_fastapi_server(),
            start_telegram_bot(bot_token)
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")

def run_main():
    """Wrapper to run async main"""
    asyncio.run(main())

if __name__ == "__main__":
    run_main()
