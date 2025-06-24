"""
Bootstrap Mini-Mancer MVP - Main Entry Point

Runs BotMother using Phase 1 foundation components.
"""

import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src.agno_core import AgnoIntelligenceCore
from src.constants import (
    BOT_CREATE_INSTRUCTIONS,
    BOT_HELP_INSTRUCTIONS,
    BOT_START_INSTRUCTIONS,
    BOTMOTHER_AI_INSTRUCTIONS,
    MAX_TELEGRAM_MESSAGE_LENGTH,
    RESPONSE_TRUNCATED_MESSAGE,
    TRUNCATE_AT_LENGTH,
)


load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BootstrapBotMother:
    """Simple BotMother using Phase 1 foundation."""

    def __init__(self):
        self.bot_token = os.getenv("BOT_MOTHER_TOKEN")
        if not self.bot_token:
            raise ValueError("BOT_MOTHER_TOKEN must be set in environment")

        # Initialize Agno intelligence
        self.intelligence = AgnoIntelligenceCore("bootstrap_botmother")
        self.intelligence.initialize_agent(instructions=BOTMOTHER_AI_INSTRUCTIONS)

        # Initialize Telegram application
        self.app = Application.builder().token(self.bot_token).build()
        self._setup_handlers()

        logger.info("BootstrapBotMother initialized")

    def _setup_handlers(self):
        """Set up Telegram command and message handlers."""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("create_bot", self.create_bot_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update, context):
        """Handle /start command."""
        user_id = str(update.effective_user.id)
        logger.info(f"Start command from user {user_id}")

        response = await self.intelligence.process_message(
            BOT_START_INSTRUCTIONS,
            user_id
        )

        # Truncate if too long for Telegram
        if len(response) > MAX_TELEGRAM_MESSAGE_LENGTH:
            response = response[:TRUNCATE_AT_LENGTH] + RESPONSE_TRUNCATED_MESSAGE

        await update.message.reply_text(response)

    async def help_command(self, update, context):
        """Handle /help command."""
        user_id = str(update.effective_user.id)
        logger.info(f"Help command from user {user_id}")

        response = await self.intelligence.process_message(
            BOT_HELP_INSTRUCTIONS,
            user_id
        )

        # Truncate if too long for Telegram
        if len(response) > MAX_TELEGRAM_MESSAGE_LENGTH:
            response = response[:TRUNCATE_AT_LENGTH] + RESPONSE_TRUNCATED_MESSAGE

        await update.message.reply_text(response)

    async def create_bot_command(self, update, context):
        """Handle /create_bot command."""
        user_id = str(update.effective_user.id)
        logger.info(f"Create bot command from user {user_id}")

        response = await self.intelligence.process_message(
            BOT_CREATE_INSTRUCTIONS,
            user_id
        )

        # Truncate if too long for Telegram
        if len(response) > MAX_TELEGRAM_MESSAGE_LENGTH:
            response = response[:TRUNCATE_AT_LENGTH] + RESPONSE_TRUNCATED_MESSAGE

        await update.message.reply_text(response)

    async def handle_message(self, update, context):
        """Handle regular text messages."""
        user_id = str(update.effective_user.id)
        message_text = update.message.text

        logger.info(f"Message from user {user_id}: {message_text[:50]}...")

        response = await self.intelligence.process_message(message_text, user_id)

        # Truncate if too long for Telegram
        if len(response) > MAX_TELEGRAM_MESSAGE_LENGTH:
            response = response[:TRUNCATE_AT_LENGTH] + RESPONSE_TRUNCATED_MESSAGE

        await update.message.reply_text(response)

    async def run(self):
        """Run the BotMother bot."""
        logger.info("Starting BootstrapBotMother...")

        # Start the bot
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

        logger.info("✅ BootstrapBotMother is running and ready!")

        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()


async def main():
    """Main entry point."""
    logger.info("Starting Bootstrap Mini-Mancer MVP")

    bot_mother = BootstrapBotMother()
    await bot_mother.run()


if __name__ == "__main__":
    asyncio.run(main())
