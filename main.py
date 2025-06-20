"""
Mini-Mancer Entry Point - Factory Bot with Direct Bot Creation
"""

import os
import asyncio
import uvicorn
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

# Import our prototype app and components
from src.prototype_agent import app, prototype

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    
    print(f"📱 Telegram /start from user {user_id} in chat {chat_id}")

    await update.message.reply_text(
        "🏭 **Mini-Mancer Factory Bot**\n\n"
        "I'm your AI bot creation assistant! I can help you create custom Telegram bots.\n\n"
        "🤖 **What I can do:**\n"
        "• Create new Telegram bots with custom personalities\n"
        "• Generate bot specifications and deploy them\n"
        "• Provide bot links for immediate use\n\n"
        "💬 **Examples:**\n"
        "• \"Create a study helper bot\"\n"
        "• \"Make a customer service bot named SupportBot\"\n"
        "• \"I need a helpful assistant bot\"\n\n"
        "What kind of bot would you like me to create?"
    )

async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming Telegram messages"""
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    message_text = update.message.text

    print(f"📨 Telegram message from user {user_id}: {message_text}")

    try:
        # Check if this is a bot creation request
        message_lower = message_text.lower()
        if any(phrase in message_lower for phrase in ["create bot", "make bot", "new bot", "spawn bot"]):
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
                print(f"✅ Created bot '{bot_name}' for user {user_id}")
            else:
                await update.message.reply_text("❌ Factory bot is not available. Please try again later.")
                print(f"❌ Factory bot creation failed - prototype not available")
        else:
            # Regular conversation with factory bot
            if prototype and prototype.agno_agent:
                response = prototype.agno_agent.run(f"""
                User message: {message_text}
                
                You are a factory bot that creates Telegram bots. Be helpful and ask clarifying questions if needed.
                If they want to create a bot, guide them through the process.
                """)
                
                await update.message.reply_text(response.content)
                print(f"📤 Sent response to user {user_id}")
            else:
                await update.message.reply_text(
                    "🏭 Factory bot is initializing. Please try again in a moment.\n\n"
                    "If this persists, the bot may be in maintenance mode."
                )
                print(f"❌ Factory bot response failed - prototype not available")

    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        print(f"❌ Error handling Telegram message: {e}")
        await update.message.reply_text(error_msg)

async def start_telegram_bot(bot_token: str):
    """Start Telegram bot with polling"""
    print("📱 Starting Telegram bot polling...")
    
    # Create Telegram application
    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram_message))

    # Log bot identity
    bot_info = await application.bot.get_me()
    print(f"🤖 Factory Bot Active: {bot_info.first_name} | Telegram: @{bot_info.username} | Token: {bot_token[:10]}...")
    
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
    bot_token = os.getenv("BOT_TOKEN") or os.getenv("TEST_BOT_TOKEN")
    
    if not bot_token:
        raise ValueError("BOT_TOKEN or TEST_BOT_TOKEN environment variable is required")
    
    print("🏭 Starting Mini-Mancer Factory Bot...")
    print(f"🤖 Bot token configured: {bot_token[:10]}...")
    
    # Log all active bot identities
    print("\n📋 Bot Identity Report:")
    print("=" * 50)
    
    if prototype:
        print(f"🤖 Factory Bot: {prototype.telegram_bot.dna.name}")
        print(f"   Purpose: {prototype.telegram_bot.dna.purpose}")
        print(f"   Platform: mini-mancer")
        print(f"   Capabilities: {[cap.value for cap in prototype.telegram_bot.dna.capabilities]}")
        print(f"   Model: agno-agi (gpt-4o-mini)")
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