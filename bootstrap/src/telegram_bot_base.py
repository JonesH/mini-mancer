from abc import ABC, abstractmethod
import inspect
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

def telegram_bot_command(description: str):
    """
    Decorator for telegram command methods.
    Registers metadata and adds exception handling.
    """
    def decorator(fn):
        # register command name & description
        fn._telegram_cmd = {"name": fn.__name__, "description": description}

        async def wrapped(self, update, context):
            try:
                return await fn(self, update, context)
            except Exception as ex:
                # log full traceback
                logger = getattr(self, "logger", logging.getLogger(__name__))
                logger.error(f"Error in {fn.__name__}: {ex}", exc_info=True)
                # notify user
                try:
                    await update.message.reply_text(
                        "❌ Command failed: " + str(ex),
                        parse_mode="Markdown"
                    )
                except Exception:
                    # swallow reply errors
                    pass
        wrapped._telegram_cmd = fn._telegram_cmd
        return wrapped
    return decorator

class AbstractTelegramBot(ABC):
    def __init__(self, token: str):
        self.token = token
        # collect all @telegram_bot_command methods
        self._commands = []
        for _, method in inspect.getmembers(self, inspect.ismethod):
            meta = getattr(method, "_telegram_cmd", None)
            if meta:
                self._commands.append((meta["name"], meta["description"], method))

        # always include /help
        self._commands.insert(0, ("help", "Show this help message", self._help))

        # build the Application
        self.app = Application.builder().token(self.token).build()
        # register handlers
        for name, _, handler in self._commands:
            self.app.add_handler(CommandHandler(name, handler))

        # abstract message handler for non-commands
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message)
        )

    async def _help(self, update, context):
        lines = ["Available commands:"]
        for name, desc, _ in self._commands:
            lines.append(f"/{name} — {desc}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    @abstractmethod
    async def _on_message(self, update, context):
        """Subclass should handle non-command messages here."""

    async def run(self):
        await self.app.initialize()
        # set MyCommands on Telegram side
        await self.app.bot.set_my_commands([
            {"command": n, "description": d}
            for n, d, _ in self._commands
        ])
        await self.app.start()
        await self.app.updater.start_polling()
        # block until cancelled
        try:
            await self.app.updater.idle()
        finally:
            await self.app.shutdown()
