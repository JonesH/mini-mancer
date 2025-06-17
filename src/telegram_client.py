import asyncio
from telegram import Bot, BotCommand, MenuButtonCommands
from typing import Optional
from .models import TelegramBotConfig


class TelegramBotClient:
    """Client for interacting with Telegram Bot API"""
    
    def __init__(self, token: str):
        self.token = token
        self.bot = Bot(token=token)
    
    async def validate_token(self) -> str:
        """Validate bot token and return bot info"""
        me = await self.bot.get_me()
        return f"Bot @{me.username} ({me.first_name})"
    
    async def setup_bot(self, display_name: str, welcome_message: str):
        """Set up bot with name, description, and commands"""
        await self.bot.set_my_name(name=display_name)
        await self.bot.set_my_description(description=welcome_message)
        
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help message")
        ]
        await self.bot.set_my_commands(commands)
        await self.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    
    async def send_welcome_to_developer(self, developer_chat_id: str, welcome_message: str):
        """Send welcome message to the bot developer"""
        await self.bot.send_message(
            chat_id=developer_chat_id,
            text=f"🎉 Your bot is ready!\n\n{welcome_message}\n\nUse /start and /help to test your bot."
        )
    
    async def get_bot_info(self) -> dict:
        """Get basic bot information"""
        me = await self.bot.get_me()
        return {
            "id": me.id,
            "username": me.username,
            "first_name": me.first_name,
            "can_join_groups": me.can_join_groups,
            "can_read_all_group_messages": me.can_read_all_group_messages,
            "supports_inline_queries": me.supports_inline_queries
        }