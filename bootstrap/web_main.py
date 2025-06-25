"""
Bootstrap Mini-Mancer MVP - Web Entry Point

Runs BotMother with both Telegram and FastAPI endpoints for agents.bartix.de deployment.
"""

import asyncio
import logging
import os

from agno.playground import Playground
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import uvicorn

from src.agno_core import AgnoIntelligenceCore
from src.bot_creation_tools import BotCreationTools
from src.event_loop_monitor import start_monitoring, track_agno_call, get_health_report
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


class DualInterfaceBotMother:
    """BotMother with both Telegram and FastAPI interfaces."""
    
    def __init__(self):
        self.bot_token = os.getenv("BOT_MOTHER_TOKEN")
        if not self.bot_token:
            raise ValueError("BOT_MOTHER_TOKEN must be set in environment")
        
        # Initialize bot creation tools
        self.bot_tools = BotCreationTools()
        
        # Initialize shared Agno intelligence with PostgreSQL and tools
        self.intelligence = AgnoIntelligenceCore("bootstrap_botmother")
        self.intelligence.initialize_agent(
            instructions=BOTMOTHER_AI_INSTRUCTIONS,
            tools=[self.bot_tools]
        )
        
        # Initialize Telegram application
        self.telegram_app = Application.builder().token(self.bot_token).build()
        self._setup_telegram_handlers()
        
        # Initialize Agno Playground for FastAPI
        self.playground = Playground(
            agents=[self.intelligence.agent],
            name="BotMother - AI Bot Creation Assistant",
            description="Intelligent Telegram bot creation and management with AI assistance",
            app_id="bootstrap-botmother"
        )
        
        # Add custom health endpoint with monitoring
        self._add_health_endpoint()
        
        logger.info("DualInterfaceBotMother initialized")
    
    def _add_health_endpoint(self):
        """Add custom health endpoint with comprehensive monitoring"""
        from fastapi import Response
        from datetime import datetime
        import time
        
        fastapi_app = self.playground.get_app()
        
        @fastapi_app.get("/health")
        async def health_check():
            """Enhanced health check with comprehensive event loop monitoring"""
            # Get comprehensive health report from event loop monitor
            health_report = get_health_report()
            
            # Analyze health status
            overall_status = "healthy"
            issues = []
            
            # Check event loop health
            for loop_id, loop_health in health_report.get("event_loops", {}).items():
                if loop_health.get("is_blocked", False):
                    overall_status = "degraded"
                    issues.append(f"Event loop {loop_id} is blocked")
                
                if loop_health.get("failed_tasks", 0) > 5:
                    overall_status = "degraded"
                    issues.append(f"Event loop {loop_id} has {loop_health['failed_tasks']} failed tasks")
            
            # Check Agno performance
            agno_metrics = health_report.get("agno_metrics", {})
            if agno_metrics.get("blocking_calls", 0) > 0:
                overall_status = "degraded"
                issues.append(f"Detected {agno_metrics['blocking_calls']} blocking Agno calls")
            
            if agno_metrics.get("failed_calls", 0) > 0:
                overall_status = "degraded"
                issues.append(f"Agno has {agno_metrics['failed_calls']} failed calls")
            
            # Check system resources
            system_info = health_report.get("system", {})
            memory_mb = system_info.get("memory_mb", 0)
            if memory_mb > 1000:  # Over 1GB
                overall_status = "degraded"
                issues.append(f"High memory usage: {memory_mb:.1f}MB")

            return {
                "status": overall_status,
                "service": "bootstrap-mini-mancer",
                "version": "0.1.0",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "fastapi": "operational",
                    "telegram": "operational",
                    "agno_agi": "operational" if agno_metrics.get("failed_calls", 0) == 0 else "degraded",
                    "bot_creation": "enabled",
                    "event_loops": "healthy" if not any(loop.get("is_blocked") for loop in health_report.get("event_loops", {}).values()) else "blocked",
                },
                "monitoring": {
                    "event_loops_count": len(health_report.get("event_loops", {})),
                    "total_tasks": sum(loop.get("total_tasks", 0) for loop in health_report.get("event_loops", {}).values()),
                    "pending_tasks": sum(loop.get("pending_tasks", 0) for loop in health_report.get("event_loops", {}).values()),
                    "failed_tasks": sum(loop.get("failed_tasks", 0) for loop in health_report.get("event_loops", {}).values()),
                    "agno_total_calls": agno_metrics.get("total_calls", 0),
                    "agno_avg_duration": agno_metrics.get("avg_duration", 0),
                    "agno_blocking_calls": agno_metrics.get("blocking_calls", 0),
                    "memory_mb": memory_mb,
                    "cpu_percent": system_info.get("cpu_percent", 0),
                },
                "issues": issues,
                "detailed_health": health_report,
            }
    
    def _setup_telegram_handlers(self):
        """Set up Telegram command and message handlers."""
        self.telegram_app.add_handler(CommandHandler("start", self.telegram_start_command))
        self.telegram_app.add_handler(CommandHandler("help", self.telegram_help_command))
        self.telegram_app.add_handler(CommandHandler("create_bot", self.telegram_create_bot_command))
        self.telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.telegram_handle_message))
    
    async def telegram_start_command(self, update, context):
        """Handle Telegram /start command."""
        user_id = str(update.effective_user.id)
        logger.info(f"Telegram start command from user {user_id}")
        
        # MONITOR: Track Agno call performance
        @track_agno_call
        async def make_agno_call():
            return await self.intelligence.process_message(
                BOT_START_INSTRUCTIONS,
                user_id,
                session_id=f"telegram_{user_id}"
            )
        
        response = await make_agno_call()
        
        # Truncate if too long for Telegram
        if len(response) > MAX_TELEGRAM_MESSAGE_LENGTH:
            response = response[:TRUNCATE_AT_LENGTH] + RESPONSE_TRUNCATED_MESSAGE
        
        await update.message.reply_text(response)
    
    async def telegram_help_command(self, update, context):
        """Handle Telegram /help command."""
        user_id = str(update.effective_user.id)
        logger.info(f"Telegram help command from user {user_id}")
        
        # MONITOR: Track Agno call performance  
        @track_agno_call
        async def make_agno_call():
            return await self.intelligence.process_message(
                BOT_HELP_INSTRUCTIONS,
                user_id,
                session_id=f"telegram_{user_id}"
            )
        
        response = await make_agno_call()
        
        # Truncate if too long for Telegram
        if len(response) > MAX_TELEGRAM_MESSAGE_LENGTH:
            response = response[:TRUNCATE_AT_LENGTH] + RESPONSE_TRUNCATED_MESSAGE
        
        await update.message.reply_text(response)
    
    async def telegram_create_bot_command(self, update, context):
        """Handle Telegram /create_bot command."""
        user_id = str(update.effective_user.id)
        logger.info(f"Telegram create bot command from user {user_id}")
        
        # MONITOR: Track Agno call performance
        @track_agno_call  
        async def make_agno_call():
            return await self.intelligence.process_message(
                BOT_CREATE_INSTRUCTIONS,
                user_id,
                session_id=f"telegram_{user_id}"
            )
        
        response = await make_agno_call()
        
        # Truncate if too long for Telegram
        if len(response) > MAX_TELEGRAM_MESSAGE_LENGTH:
            response = response[:TRUNCATE_AT_LENGTH] + RESPONSE_TRUNCATED_MESSAGE
        
        await update.message.reply_text(response)
    
    async def telegram_handle_message(self, update, context):
        """Handle regular Telegram text messages."""
        user_id = str(update.effective_user.id)
        message_text = update.message.text
        
        logger.info(f"Telegram message from user {user_id}: {message_text[:50]}...")
        
        # MONITOR: Track Agno call performance
        @track_agno_call
        async def make_agno_call():
            return await self.intelligence.process_message(
                message_text, 
                user_id,
                session_id=f"telegram_{user_id}"
            )
        
        response = await make_agno_call()
        
        # Truncate if too long for Telegram
        if len(response) > MAX_TELEGRAM_MESSAGE_LENGTH:
            response = response[:TRUNCATE_AT_LENGTH] + RESPONSE_TRUNCATED_MESSAGE
        
        await update.message.reply_text(response)
    
    async def run_telegram(self):
        """Run the Telegram bot."""
        logger.info("Starting Telegram BotMother...")
        
        # Start the bot
        await self.telegram_app.initialize()
        await self.telegram_app.start()
        await self.telegram_app.updater.start_polling()
        
        logger.info("✅ Telegram BotMother is running!")
        
        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down Telegram bot...")
        finally:
            await self.telegram_app.updater.stop()
            await self.telegram_app.stop()
            await self.telegram_app.shutdown()
    
    def get_fastapi_app(self):
        """Get the FastAPI app for web deployment."""
        return self.playground.get_app()
    
    async def start_telegram_task(self):
        """Start Telegram bot as async task."""
        logger.info("Starting Telegram bot task...")
        await self.run_telegram()


# Global instance for web deployment
bot_mother = DualInterfaceBotMother()

# FastAPI app for agents.bartix.de deployment
app = bot_mother.get_fastapi_app()


async def run_fastapi_server():
    """Run FastAPI server with uvicorn."""
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=14159,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Main entry point - runs both Telegram and FastAPI with coordinated event loop."""
    # Start event loop monitoring FIRST to catch startup issues
    await start_monitoring("bootstrap_main_loop")
    logger.info("🔍 Bootstrap event loop health monitoring started")
    
    logger.info("Starting Bootstrap Mini-Mancer MVP with dual interfaces on port 14159")
    
    # Create tasks for both services in same event loop
    telegram_task = asyncio.create_task(bot_mother.start_telegram_task())
    fastapi_task = asyncio.create_task(run_fastapi_server())
    
    logger.info("Both Telegram and FastAPI tasks started")
    logger.info("📊 Health monitoring available at http://localhost:14159/health")
    
    # Run both services concurrently
    try:
        await asyncio.gather(telegram_task, fastapi_task)
    except KeyboardInterrupt:
        logger.info("Shutting down all services...")
        telegram_task.cancel()
        fastapi_task.cancel()
        
        try:
            await asyncio.gather(telegram_task, fastapi_task, return_exceptions=True)
        except Exception as e:
            logger.info(f"Cleanup completed: {e}")


if __name__ == "__main__":
    # For local development
    asyncio.run(main())