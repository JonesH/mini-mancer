"""
SimpleEchoBot - Individual echo bot that repeats back messages

Each SimpleEchoBot is an independent Telegram bot that echoes back
any message it receives. No AI involved - pure echo functionality.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from markdown_utils import escape_username

logger = logging.getLogger(__name__)


class SimpleEchoBot:
    """A simple bot that echoes back messages it receives."""
    
    def __init__(self, name: str, username: str, token: str, created_by: str):
        self.name = name
        self.username = username
        self.token = token
        self.created_by = created_by
        self.created_at = datetime.now()
        
        # Bot state
        self.is_running = False
        self.app: Application | None = None
        self.bot_task: asyncio.Task | None = None
        
        # Statistics
        self.message_count = 0
        self.start_time: datetime | None = None
        
        logger.info(f"SimpleEchoBot '{name}' initialized (@{username})")
    
    def _setup_handlers(self):
        """Set up Telegram message handlers for the echo bot."""
        if not self.app:
            return
        
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        
        # Echo handler for all text messages
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo_handler))
        
        # Handle non-text messages with info response
        self.app.add_handler(MessageHandler(~filters.TEXT, self.non_text_handler))
    
    async def start_command(self, update, context):
        """Handle /start command."""
        user = update.effective_user
        username = user.username or user.first_name or "User"
        
        logger.info(f"Echo bot '{self.name}' /start from @{username}")
        
        escaped_username = escape_username(f"@{self.username}")
        response = f"""👋 **Hello from {self.name}!**

I'm a simple echo bot created by SimpleBotMother.

**What I do:**
🔄 I repeat back any message you send me
📝 I count how many messages I've echoed
⚡ I respond instantly (no AI delays)

**Commands:**
/start - Show this welcome message
/help - Get help information  
/stats - See my statistics

**Try it out:**
Send me any text message and I'll echo it back to you!

*Created by: @{self.created_by if hasattr(self, 'created_by') else 'Unknown'}*"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def help_command(self, update, context):
        """Handle /help command."""
        user = update.effective_user
        username = user.username or user.first_name or "User"
        
        logger.info(f"Echo bot '{self.name}' /help from @{username}")
        
        response = f"""🆘 **{self.name} Help**

**What I am:**
I'm a simple echo bot - I repeat back whatever you send me.

**How to use me:**
1️⃣ Send me any text message
2️⃣ I'll echo it back to you immediately
3️⃣ That's it! No complex features.

**Available commands:**
• `/start` - Welcome message
• `/help` - This help message
• `/stats` - My statistics

**Examples:**
You: "Hello echo bot!"
Me: "Echo: Hello echo bot!"

You: "What's the weather like?"
Me: "Echo: What's the weather like?"

**Features:**
✅ Instant responses (no AI processing)
✅ Message counting
✅ Simple and reliable
✅ Works with any text

**Note:** I only echo text messages. Other media types get a simple response."""
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def stats_command(self, update, context):
        """Handle /stats command."""
        user = update.effective_user
        username = user.username or user.first_name or "User"
        
        logger.info(f"Echo bot '{self.name}' /stats from @{username}")
        
        # Calculate uptime
        uptime_str = "Not started"
        if self.start_time:
            uptime = datetime.now() - self.start_time
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            uptime_str = f"{hours}h {minutes}m"
        
        escaped_username = escape_username(f"@{self.username}")
        response = f"""📊 **{self.name} Statistics**

**Basic Info:**
• Bot Name: {self.name}
• Username: {escaped_username}
• Status: {'🟢 Running' if self.is_running else '⚪ Stopped'}

**Activity:**
• Messages Echoed: {self.message_count}
• Uptime: {uptime_str}
• Created: {self.created_at.strftime('%Y-%m-%d %H:%M')}

**Creator:**
• Created by: {self.created_by}

**Bot Type:**
• Type: Simple Echo Bot
• AI Powered: ❌ No (Pure echo)
• Response Time: ⚡ Instant

Send me a message to increase the echo counter!"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def echo_handler(self, update, context):
        """Handle regular text messages by echoing them back."""
        user = update.effective_user
        message_text = update.message.text
        username = user.username or user.first_name or "User"
        
        # Increment message counter
        self.message_count += 1
        
        logger.info(f"Echo bot '{self.name}' echoing message #{self.message_count} from @{username}: {message_text[:30]}...")
        
        # Create echo response
        echo_response = f"Echo: {message_text}"
        
        # Add message counter for some variety
        if self.message_count % 10 == 0:
            echo_response += f"\n\n*Message #{self.message_count} echoed! 🎉*"
        
        await update.message.reply_text(echo_response, parse_mode='Markdown')
    
    async def non_text_handler(self, update, context):
        """Handle non-text messages (photos, stickers, etc.)."""
        user = update.effective_user
        username = user.username or user.first_name or "User"
        
        logger.info(f"Echo bot '{self.name}' received non-text from @{username}")
        
        # Determine message type
        message_type = "message"
        if update.message.photo:
            message_type = "photo"
        elif update.message.sticker:
            message_type = "sticker"
        elif update.message.document:
            message_type = "document"
        elif update.message.video:
            message_type = "video"
        elif update.message.audio:
            message_type = "audio"
        elif update.message.voice:
            message_type = "voice message"
        
        response = f"""📷 **{self.name} - Media Response**

I received your {message_type}, but I can only echo text messages!

To test my echo functionality:
• Send me a text message
• I'll echo it back immediately

**Current stats:**
• Text messages echoed: {self.message_count}

Try sending me some text! 📝"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def start(self) -> Dict[str, Any]:
        """Start the echo bot."""
        if self.is_running:
            return {
                "success": True,
                "message": f"Bot '{self.name}' is already running",
                "status": "running"
            }
        
        try:
            logger.info(f"Starting echo bot '{self.name}'...")
            
            # Create Telegram application
            self.app = Application.builder().token(self.token).build()
            self._setup_handlers()
            
            # Start the bot
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            logger.info(f"✅ Echo bot '{self.name}' started successfully (@{self.username})")
            
            return {
                "success": True,
                "message": f"Bot '{self.name}' started successfully",
                "status": "running",
                "username": f"@{self.username}",
                "telegram_link": f"https://t.me/{self.username}"
            }
            
        except Exception as e:
            logger.error(f"Failed to start echo bot '{self.name}': {e}")
            self.is_running = False
            return {
                "success": False,
                "error": f"Failed to start bot: {str(e)}",
                "status": "stopped"
            }
    
    async def stop(self) -> Dict[str, Any]:
        """Stop the echo bot."""
        if not self.is_running:
            return {
                "success": True,
                "message": f"Bot '{self.name}' is already stopped",
                "status": "stopped"
            }
        
        try:
            logger.info(f"Stopping echo bot '{self.name}'...")
            
            if self.app:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
                self.app = None
            
            self.is_running = False
            
            logger.info(f"✅ Echo bot '{self.name}' stopped successfully")
            
            return {
                "success": True,
                "message": f"Bot '{self.name}' stopped successfully",
                "status": "stopped",
                "username": f"@{self.username}"
            }
            
        except Exception as e:
            logger.error(f"Failed to stop echo bot '{self.name}': {e}")
            return {
                "success": False,
                "error": f"Failed to stop bot: {str(e)}",
                "status": "error"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status and statistics."""
        uptime_seconds = 0
        if self.start_time and self.is_running:
            uptime_seconds = int((datetime.now() - self.start_time).total_seconds())
        
        return {
            "name": self.name,
            "username": f"@{self.username}",
            "status": "running" if self.is_running else "stopped",
            "is_running": self.is_running,
            "message_count": self.message_count,
            "uptime_seconds": uptime_seconds,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "telegram_link": f"https://t.me/{self.username}",
            "bot_type": "SimpleEchoBot"
        }


async def test_simple_echo_bot():
    """Test SimpleEchoBot functionality."""
    print("🤖 Testing SimpleEchoBot...")
    
    # This would normally be a real token for testing
    test_token = "test_token"
    
    bot = SimpleEchoBot(
        name="Test Echo Bot",
        username="test_echo_bot",
        token=test_token,
        created_by="test_user"
    )
    
    # Test status
    status = bot.get_status()
    print(f"Bot status: {status}")
    
    print("✅ SimpleEchoBot test completed")


if __name__ == "__main__":
    asyncio.run(test_simple_echo_bot())