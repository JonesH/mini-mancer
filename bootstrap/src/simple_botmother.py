"""
SimpleBotMother - Non-intelligent bot factory with templated responses
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

from .simple_botmother_templates import (
    START_TEMPLATE,
    CREATE_SUCCESS_TEMPLATE,
    CREATE_ERROR_TEMPLATE,
    STARTBOT_SUCCESS_TEMPLATE,
    STARTBOT_ERROR_TEMPLATE,
    STOPBOT_SUCCESS_TEMPLATE,
    STOPBOT_ERROR_TEMPLATE,
    STATUS_FOUND_TEMPLATE,
    STATUS_NOTFOUND_TEMPLATE,
)
from .simple_botmother_models import BotCreatorResult

load_dotenv()

logger = logging.getLogger(__name__)

class SimpleBotMother(AbstractTelegramBot):
    """Non-intelligent bot factory that creates and manages echo bots."""

    def __init__(self, token: str):
        super().__init__(token)
        self.bot_creator = UnlimitedBotCreator()
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("SimpleBotMother initialized (no AI)")

    @telegram_bot_command("Start SimpleBotMother")
    async def start(self, update, context):
        """Handle /start command with templated response."""
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "User"
        logger.info(f"Start command from user {user_id} (@{username})")
        response = START_TEMPLATE.format(username=username)
        await update.message.reply_text(response, parse_mode='Markdown')

    @telegram_bot_command("Create a new echo bot")
    async def create_bot(self, update, context):
        """Handle /create_bot command."""
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "User"

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

        await update.message.reply_text(
            f"🔄 Creating echo bot '{bot_name}'...\nThis may take a few seconds.",
            parse_mode='Markdown'
        )

        try:
            raw = await self.bot_creator.create_echo_bot(bot_name, user_id)
            result = BotCreatorResult.parse_obj(raw)

            if result.success:
                response = CREATE_SUCCESS_TEMPLATE.format(
                    bot_name=bot_name,
                    escaped_username=escape_username(result.username or ""),
                    status=result.status or "",
                    telegram_link=result.telegram_link or ""
                )
            else:
                response = CREATE_ERROR_TEMPLATE.format(
                    error=result.error or "Unknown error"
                )

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
                    response += (
                        f"{i}. {status_emoji} **{bot['name']}**\n"
                        f"   • Username: {escaped_username}\n"
                        f"   • Status: {bot['status']}\n"
                        f"   • Link: {bot['telegram_link']}\n\n"
                    )
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
            raw = await self.bot_creator.start_bot(bot_name, user_id)
            result = BotCreatorResult.parse_obj(raw)

            if result.success:
                response = STARTBOT_SUCCESS_TEMPLATE.format(
                    bot_name=bot_name,
                    escaped_username=escape_username(result.username or "")
                )
            else:
                response = STARTBOT_ERROR_TEMPLATE.format(
                    bot_name=bot_name,
                    error=result.error or "Unknown error"
                )

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
            raw = await self.bot_creator.stop_bot(bot_name, user_id)
            result = BotCreatorResult.parse_obj(raw)

            if result.success:
                response = STOPBOT_SUCCESS_TEMPLATE.format(
                    bot_name=bot_name,
                    escaped_username=escape_username(result.username or "")
                )
            else:
                response = STOPBOT_ERROR_TEMPLATE.format(
                    bot_name=bot_name,
                    error=result.error or "Unknown error"
                )

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
            raw = await self.bot_creator.get_bot_status(bot_name, user_id)
            result = BotCreatorResult.parse_obj(raw)

            if raw.get("found"):
                status_emoji = "🟢" if result.status == 'running' else "⚪"
                response = STATUS_FOUND_TEMPLATE.format(
                    status_emoji=status_emoji,
                    bot_name=bot_name,
                    escaped_username=escape_username(result.username or ""),
                    status=result.status or "",
                    telegram_link=result.telegram_link or "",
                    created=raw.get("created", "")
                )
            else:
                response = STATUS_NOTFOUND_TEMPLATE.format(bot_name=bot_name)

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
