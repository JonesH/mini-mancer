import asyncio
import os
from typing import Any, Dict
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import uvicorn
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from src.factory.bot_factory_agent import BotFactoryAgent

load_dotenv()

# Global factory agent instance
factory_agent = None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    await update.message.reply_text(
        "🏭 Hello! I'm Mini-Mancer, your AI bot creation assistant!\n\n"
        "I help you create custom Telegram bots through the OpenServ platform. "
        "I can guide you through the entire process, from gathering requirements to deployment.\n\n"
        "🤖 **What I can do:**\n"
        "• Guide you through bot creation requirements\n"
        "• Submit specifications to OpenServ platform\n"
        "• Monitor creation progress\n"
        "• Send you notifications when platform agents need help\n"
        "• Handle questions and clarifications\n\n"
        "💬 **Get started by telling me:**\n"
        "What kind of bot would you like to create?\n\n"
        "Example: \"I want to create a study helper bot\" or \"Help me make a customer service bot\""
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    message_text = update.message.text

    print(f"📨 Received message from user {user_id} in chat {chat_id}: {message_text}")

    global factory_agent
    try:
        # First check if this user has a pending OpenServ conversation
        openserv_user_id = f"openserv_{user_id}"
        conversation_state = factory_agent.conversations.get(openserv_user_id)

        if conversation_state and conversation_state.awaiting_user_response:
            # User is responding to an OpenServ question
            print(f"🔄 Continuing OpenServ conversation for user {user_id}")
            response = await factory_agent.continue_openserv_conversation(openserv_user_id, message_text)
            await update.message.reply_text(response)
            print(f"📤 Sent OpenServ continuation response to user")
        else:
            # Regular bot creation conversation
            print(f"🤖 Processing regular message with BotFactoryAgent...")
            response = await factory_agent.handle_message(user_id, chat_id, message_text)
            print(f"✅ BotFactoryAgent response: {response}")
            await update.message.reply_text(response)
            print(f"📤 Sent response to user")

    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        print(f"❌ Error handling message: {e}")
        print(f"📤 Sending error message to user")
        await update.message.reply_text(error_msg)


async def handle_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks from inline keyboards"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    chat_id = str(query.message.chat_id)
    callback_data = query.data

    print(f"🔘 Button callback from user {user_id}: {callback_data}")

    global factory_agent
    try:
        # Process the callback with factory agent
        response = await factory_agent.handle_deployment_callback(callback_data, chat_id, user_id)

        # Answer the callback query and send response
        await query.answer()
        await query.edit_message_text(text=response, parse_mode='Markdown')

        print(f"✅ Button callback processed and response sent")

    except Exception as e:
        error_msg = f"Sorry, I encountered an error processing your request: {str(e)}"
        print(f"❌ Error handling button callback: {e}")
        await query.answer()
        await query.edit_message_text(text=error_msg)


# FastAPI app
app = FastAPI(title="Mini-Mancer BotFactoryAgent")

@app.post("/")
async def handle_openserv_action(request: Request):
    """Main OpenServ webhook endpoint - handles all platform actions"""
    try:
        action = await request.json()
        action_type = action.get("type")

        print(f"📥 Received OpenServ action: {action_type}")

        global factory_agent
        if not factory_agent:
            print("❌ Factory agent not initialized")
            return {"message": "Agent not ready"}

        # Handle different OpenServ action types
        if action_type == "do-task":
            await handle_do_task(action)
        elif action_type == "respond-chat-message":
            await handle_respond_chat_message(action)
        else:
            print(f"⚠️ Unknown action type: {action_type}")

        # Immediately respond to the platform (required by OpenServ)
        return {"message": "OK"}

    except Exception as e:
        print(f"❌ Error handling OpenServ action: {e}")
        return {"message": "Error", "error": str(e)}

async def handle_do_task(action: Dict[str, Any]):
    """Handle OpenServ task execution"""
    task = action.get("task", {})
    workspace = action.get("workspace", {})

    task_id = task.get("id")
    workspace_id = workspace.get("id")

    print(f"🔧 Handling task {task_id} in workspace {workspace_id}")

    # Process the task with our factory agent
    # This is where you'd implement specific task logic
    # For now, just acknowledge the task
    return action #(f"✅ Task {task_id} processed")

async def handle_respond_chat_message(action: Dict[str, Any]):
    """Handle OpenServ chat message response"""
    global factory_agent
    if not factory_agent:
        print("❌ Factory agent not initialized")
        return

    try:
        result = await factory_agent.handle_openserv_request(action)
        print(f"✅ OpenServ request processed: {result}")
    except Exception as e:
        print(f"❌ Error processing OpenServ chat message: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "running", "service": "Mini-Mancer BotFactoryAgent"}


async def start_http_server():
    """Start FastAPI server on port 14159"""
    config = uvicorn.Config(app, host="localhost", port=14159, log_level="info")
    server = uvicorn.Server(config)
    print("🌐 FastAPI server listening on port 14159")
    await server.serve()


async def main():
    """Main entry point - launches BotFactoryAgent with minimal logic"""
    openserv_api_key = os.getenv("OPENSERV_API_KEY")
    bot_token = os.getenv("BOT_TOKEN")
    demo_user = os.getenv("DEMO_USER")

    if not openserv_api_key:
        raise ValueError("OPENSERV_API_KEY environment variable is required")
    if not bot_token:
        raise ValueError("BOT_TOKEN environment variable is required")
    if not demo_user:
        raise ValueError("DEMO_USER environment variable is required")

    print("🏭 Starting Mini-Mancer BotFactoryAgent...")

    # Initialize BotFactoryAgent
    global factory_agent
    factory_agent = BotFactoryAgent(
        openserv_api_key=openserv_api_key,
        telegram_bot_token=bot_token
    )

    print("🔗 BotFactoryAgent initialized and connected to OpenServ")

    # Create Telegram application
    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_button_callback))

    # Start HTTP server in background task
    print("🌐 Starting FastAPI server...")
    server_task = asyncio.create_task(start_http_server())

    # Start Telegram bot polling (this will run until interrupted)
    print("🚀 Starting Telegram bot polling...")
    try:
        async with application:
            await application.start()
            await application.updater.start_polling()
            print("Started polling!")

            # Send startup message to DEMO_USER
            startup_message = (
                "🏭 Mini-Mancer BotFactoryAgent is now online!\n\n"
                "I'm ready to help you create custom Telegram bots through the OpenServ platform. "
                "I can also monitor for assistance requests and notify you when platform agents need help.\n\n"
                "💬 Send me a message to get started!"
            )
            try:
                await application.bot.send_message(chat_id=demo_user, text=startup_message)
                print(f"✅ Startup message sent to DEMO_USER: {demo_user}")
            except Exception as e:
                print(f"❌ Failed to send startup message to {demo_user}: {e}")

            # Keep the application running
            await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        # Cancel background tasks
        server_task.cancel()

        try:
            await server_task
        except asyncio.CancelledError:
            pass

        # Cleanup factory agent
        if factory_agent:
            await factory_agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
