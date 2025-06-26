"""
SimpleBotMother - Non-intelligent bot factory with hardcoded responses

Creates and manages simple echo bots without any LLM involvement.
All responses are hardcoded for speed and reliability.
"""

import os
import logging
from typing import Dict, Any

import asyncio
from dotenv import load_dotenv

from telegram_bot_base import AbstractTelegramBot, telegram_bot_command

from simple_echo_bot import SimpleEchoBot
from unlimited_bot_creator import UnlimitedBotCreator
from markdown_utils import escape_username, format_bot_link

load_dotenv()

logger = logging.getLogger(__name__)

class SimpleBotMother(AbstractTelegramBot):
    """Non-intelligent bot factory that creates and manages echo bots."""

    def __init__(self, token: str):
        # Initialize base Telegram bot
        super().__init__(token)

        # Initialize unlimited bot creator for managing echo bots
        self.bot_creator = UnlimitedBotCreator()

        # Track user sessions (simple in-memory storage)
        self.user_sessions: Dict[str, Dict[str, Any]] = {}

        logger.info("SimpleBotMother initialized (no AI)")

    @telegram_bot_command("Start SimpleBotMother")
    async def start(self, update, context):
        """Handle /start command with hardcoded response."""
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "User"

        logger.info(f"Start command from user {user_id} (@{username})")

        response = f"""🤖 **SimpleBotMother - Bot Factory**

Hello @{username}! I create simple echo bots for you.

**Available Commands:**
/create_bot <name> - Create a new echo bot
/list_bots - Show your created bots
/start_bot <name> - Start a specific bot
/stop_bot <name> - Stop a specific bot
/bot_status <name> - Check the status of a bot
/help - Show this help message

**What I do:**
✅ Create unlimited echo bots (no AI)
✅ Auto-generate new bot tokens via @BotFather
✅ Manage multiple bots concurrently
✅ Start/stop bots on demand
✅ Track all your created bots

Ready to create your first echo bot? Use `/create_bot MyBot`"""

        await update.message.reply_text(response, parse_mode='Markdown')

    @telegram_bot_command("Create a new echo bot")
    async def create_bot(self, update, context):
        """Handle /create_bot command."""
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "User"

        # Parse bot name from command
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a bot name!\n\n"
                "Usage: `/create_bot <name>`\n"
                "Example: `/create_bot MyEchoBot`",
                parse_mode='Markdown'
            )
            return

        bot_name = " ".join(context.args)

        logger.info(f"Create bot command from user {user_id}: {bot_name}")

        # Send immediate response
        await update.message.reply_text(
            f"🔄 Creating echo bot '{bot_name}'...\n"
            f"This may take a few seconds.",
            parse_mode='Markdown'
        )

        try:
            # Create the echo bot
            result = await self.bot_creator.create_echo_bot(bot_name, user_id)

            if result["success"]:
                escaped_username = escape_username(result['username'])
                response =f"""✅ **Echo Bot Created Successfully!**

**Bot Name:** {bot_name}
**Username:** {escaped_username}
**Status:** {result['status']}
**Link:** {result['telegram_link']}

Your echo bot is ready! Users can start chatting with it right away.
It will echo back any message sent to it.

**Next Steps:**
• Test it: {result['telegram_link']}
• Start it: `/start_bot {bot_name}`
• Check status: `/bot_status {bot_name}`"""
            else:
                response = f"""❌ **Bot Creation Failed**

**Error:** {result['error']}

**Troubleshooting:**
• Make sure bot tokens are available
• Check if the bot name is unique
• Try again in a few moments"""

            await update.message.reply_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Bot creation error: {e}")
            await update.message.reply_text(
                f"❌ **Bot Creation Error**\n\n"
                f"Technical error: {str(e)}\n\n"
                f"Please try again or contact support.",
                parse_mode='Markdown'
            )

    @telegram_bot_command("List your created bots")
    async def list_bots(self, update, context):
        """Handle /list_bots command."""
        user_id = str(update.effective_user.id)
        logger.info(f"List bots command from user {user_id}")

        try:
            bots = await self.bot_creator.list_user_bots(user_id)

            if not bots:
                response = """📋 **Your Bots**

You haven't created any bots yet.

**Get Started:**
Use `/create_bot <name>` to create your first echo bot!

Example: `/create_bot MyFirstBot`"""
            else:
                response = f"📋 **Your Bots ({len(bots)} total)**\n\n"

                for i, bot in enumerate(bots, 1):
                    status_emoji = "🟢" if bot['status'] == 'running' else "⚪"
                    escaped_username = escape_username(bot['username'])
                    response += f"{i}. {status_emoji} **{bot['name']}**\n"
                    response += f"   • Username: {escaped_username}\n"
                    response += f"   • Status: {bot['status']}\n"
                    response += f"   • Link: {bot['telegram_link']}\n\n"

                response += "**Commands:**\n"
                response += "• `/start_bot <name>` - Start bot\n"
                response += "• `/stop_bot <name>` - Stop bot\n"
                response += "• `/bot_status <name>` - Check status"

            await update.message.reply_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"List bots error: {e}")
            await update.message.reply_text(
                "❌ Error retrieving bot list. Please try again.",
                parse_mode='Markdown'
            )

    @telegram_bot_command("Start a specific bot")
    async def start_bot(self, update, context):
        """Handle /start_bot command."""
        user_id = str(update.effective_user.id)

        if not context.args:
            await update.message.reply_text(
                "❌ Please specify bot name!\n\n"
                "Usage: `/start_bot <name>`\n"
                "Example: `/start_bot MyEchoBot`",
                parse_mode='Markdown'
            )
            return

        bot_name = " ".join(context.args)
        logger.info(f"Start bot command from user {user_id}: {bot_name}")

        try:
            result = await self.bot_creator.start_bot(bot_name, user_id)

            if result["success"]:
                escaped_username = escape_username(result['username'])
                response = f"""✅ **Bot Started Successfully!**

**Bot:** {bot_name}
**Username:** {escaped_username}
**Status:** Running

Your bot is now live and ready to receive messages!
Users can start chatting with it immediately."""
            else:
                response = f"""❌ **Failed to Start Bot**

**Bot:** {bot_name}
**Error:** {result['error']}

**Troubleshooting:**
• Check if the bot exists: `/list_bots`
• Make sure you own this bot
• Try stopping and starting again"""

            await update.message.reply_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Start bot error: {e}")
            await update.message.reply_text(
                f"❌ Error starting bot: {str(e)}",
                parse_mode='Markdown'
            )

    @telegram_bot_command("Stop a specific bot")
    async def stop_bot(self, update, context):
        """Handle /stop_bot command."""
        user_id = str(update.effective_user.id)

        if not context.args:
            await update.message.reply_text(
                "❌ Please specify bot name!\n\n"
                "Usage: `/stop_bot <name>`\n"
                "Example: `/stop_bot MyEchoBot`",
                parse_mode='Markdown'
            )
            return

        bot_name = " ".join(context.args)
        logger.info(f"Stop bot command from user {user_id}: {bot_name}")

        try:
            result = await self.bot_creator.stop_bot(bot_name, user_id)

            if result["success"]:
                escaped_username = escape_username(result['username'])
                response = f"""⏹️ **Bot Stopped Successfully!**

**Bot:** {bot_name}
**Username:** {escaped_username}
**Status:** Stopped

The bot is no longer responding to messages.
You can start it again with `/start_bot {bot_name}`"""
            else:
                response = f"""❌ **Failed to Stop Bot**

**Bot:** {bot_name}
**Error:** {result['error']}

**Troubleshooting:**
• Check if the bot exists: `/list_bots`
• Make sure the bot is currently running
• Verify you own this bot"""

            await update.message.reply_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Stop bot error: {e}")
            await update.message.reply_text(
                f"❌ Error stopping bot: {str(e)}",
                parse_mode='Markdown'
            )

    @telegram_bot_command("Check the status of a bot")
    async def bot_status(self, update, context):
        """Handle /bot_status command."""
        user_id = str(update.effective_user.id)

        if not context.args:
            await update.message.reply_text(
                "❌ Please specify bot name!\n\n"
                "Usage: `/bot_status <name>`\n"
                "Example: `/bot_status MyEchoBot`",
                parse_mode='Markdown'
            )
            return

        bot_name = " ".join(context.args)
        logger.info(f"Bot status command from user {user_id}: {bot_name}")

        try:
            status = await self.bot_creator.get_bot_status(bot_name, user_id)

            if status["found"]:
                status_emoji = "🟢" if status['status'] == 'running' else "⚪"
                escaped_username = escape_username(status['username'])
                response = f"""📊 **Bot Status Report**

{status_emoji} **{bot_name}**

**Username:** {escaped_username}
**Status:** {status['status']}
**Created:** {status['created']}
**Link:** {status['telegram_link']}

**Actions:**
• Start: `/start_bot {bot_name}`
• Stop: `/stop_bot {bot_name}`"""
            else:
                response = f"""❌ **Bot Not Found**

**Bot:** {bot_name}

The bot '{bot_name}' was not found in your bot list.

**Check your bots:** `/list_bots`
**Create new bot:** `/create_bot <name>`"""

            await update.message.reply_text(response, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Bot status error: {e}")
            await update.message.reply_text(
                f"❌ Error checking bot status: {str(e)}",
                parse_mode='Markdown'
            )

    async def _on_message(self, update, context):
        """Handle regular text messages with simple hardcoded responses."""
        user_id = str(update.effective_user.id)
        message_text = update.message.text

        logger.info(f"Message from user {user_id}: {message_text[:50]}...")

        # Simple keyword-based responses (no AI)
        text_lower = message_text.lower()

        if any(word in text_lower for word in ['hello', 'hi', 'hey']):
            response = "👋 Hello! I'm SimpleBotMother. Use /help to see what I can do!"
        elif any(word in text_lower for word in ['create', 'make', 'new']):
            response = "🤖 Want to create a bot? Use `/create_bot <name>` command!"
        elif any(word in text_lower for word in ['help', 'commands']):
            response = "ℹ️ Use /help to see all available commands!"
        elif any(word in text_lower for word in ['status', 'running']):
            response = "📊 Check your bots with /list_bots command!"
        elif any(word in text_lower for word in ['thanks', 'thank you', 'thanks!']):
            response = "😊 You're welcome! Happy to help with bot creation!"
        else:
            response = """🤖 **SimpleBotMother**

I only respond to specific commands. Here are the main ones:

• `/create_bot <name>` - Create echo bot
• `/list_bots` - Show your bots
• `/help` - Full help guide

Type a command to get started!"""

        await update.message.reply_text(response, parse_mode='Markdown')
