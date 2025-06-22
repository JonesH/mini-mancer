"""
Telegram Error Handler - Send errors to dedicated Telegram channel for debugging

This module provides centralized error handling that sends detailed error information
to a Telegram channel while providing user-friendly responses to users.
"""

import os
import logging
import traceback
import psutil
from datetime import datetime
from typing import Any, Callable, Optional
from functools import wraps
from dataclasses import dataclass, field

import asyncio
from telegram import Bot
from telegram.error import TelegramError


@dataclass
class ErrorContext:
    """Context information for error reporting"""
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    message_text: Optional[str] = None
    operation: Optional[str] = None
    bot_state: Optional[str] = None
    additional_info: dict[str, Any] = field(default_factory=dict)


class TelegramErrorHandler(logging.Handler):
    """Custom logging handler that sends errors to a Telegram channel"""
    
    def __init__(self, error_channel_id: str, bot_token: str):
        super().__init__()
        self.error_channel_id = error_channel_id
        self.bot = Bot(token=bot_token)
        self.max_message_length = 4000  # Telegram limit minus some buffer
        
    def emit(self, record: logging.LogRecord) -> None:
        """Send log record to Telegram error channel"""
        try:
            # Format the error message
            formatted_message = self.format_error_message(record)
            
            # Send to Telegram channel (async operation in thread)
            asyncio.create_task(self._send_to_telegram(formatted_message))
            
        except Exception:
            # Don't let logging errors break the application
            self.handleError(record)
    
    def format_error_message(self, record: logging.LogRecord) -> str:
        """Format error record into comprehensive Telegram message"""
        lines = []
        
        # Header with severity and timestamp
        severity_emoji = {
            'CRITICAL': '🚨',
            'ERROR': '❌', 
            'WARNING': '⚠️',
            'INFO': '📋'
        }.get(record.levelname, '📝')
        
        lines.append(f"{severity_emoji} **{record.levelname}** - {datetime.now().strftime('%H:%M:%S')}")
        lines.append("")
        
        # Location information
        lines.append(f"📁 **Location:** `{record.filename}:{record.lineno}`")
        lines.append(f"⚙️ **Function:** `{record.funcName}`")
        lines.append("")
        
        # Error context if available
        if hasattr(record, 'error_context'):
            ctx: ErrorContext = record.error_context
            lines.append("🔍 **Context:**")
            if ctx.user_id:
                lines.append(f"   👤 User: `{ctx.user_id}`")
            if ctx.chat_id:
                lines.append(f"   💬 Chat: `{ctx.chat_id}`")
            if ctx.operation:
                lines.append(f"   🎯 Operation: `{ctx.operation}`")
            if ctx.bot_state:
                lines.append(f"   🤖 Bot State: `{ctx.bot_state}`")
            if ctx.message_text:
                # Truncate long messages
                msg_preview = ctx.message_text[:100] + "..." if len(ctx.message_text) > 100 else ctx.message_text
                lines.append(f"   📝 Message: `{msg_preview}`")
            
            # Additional context
            for key, value in ctx.additional_info.items():
                lines.append(f"   📊 {key}: `{value}`")
            lines.append("")
        
        # System information
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            lines.append("💾 **System:**")
            lines.append(f"   Memory: `{memory_mb:.1f}MB`")
            lines.append(f"   CPU: `{cpu_percent:.1f}%`")
            lines.append("")
        except Exception:
            pass
        
        # Error message
        lines.append(f"💬 **Message:** `{record.getMessage()}`")
        lines.append("")
        
        # Traceback if it's an exception
        if record.exc_info:
            lines.append("📚 **Traceback:**")
            lines.append("```")
            lines.append(traceback.format_exception(*record.exc_info))
            lines.append("```")
        
        # Join and truncate if necessary
        message = "\n".join(lines)
        
        if len(message) > self.max_message_length:
            # Truncate and add notice
            truncated = message[:self.max_message_length - 100]
            message = truncated + "\n\n⚠️ *Message truncated due to length*"
        
        return message
    
    async def _send_to_telegram(self, message: str) -> None:
        """Send formatted message to Telegram error channel"""
        try:
            await self.bot.send_message(
                chat_id=self.error_channel_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        except TelegramError as e:
            # Fallback to plain text if Markdown fails
            try:
                plain_message = message.replace('`', '').replace('*', '').replace('_', '')
                await self.bot.send_message(
                    chat_id=self.error_channel_id,
                    text=f"Error sending formatted message: {e}\n\n{plain_message}"
                )
            except TelegramError:
                # If even plain text fails, give up silently
                pass
        except Exception:
            # Don't let error channel errors break the application
            pass


def setup_telegram_error_logging(
    error_channel_id: Optional[str] = None,
    bot_token: Optional[str] = None,
    level: int = logging.ERROR
) -> Optional[TelegramErrorHandler]:
    """Setup Telegram error handler for the root logger"""
    
    # Get configuration from environment if not provided
    if not error_channel_id:
        error_channel_id = os.getenv("ERROR_CHANNEL_ID")
    if not bot_token:
        bot_token = os.getenv("BOT_TOKEN") or os.getenv("TEST_BOT_TOKEN")
    
    if not error_channel_id or not bot_token:
        logging.getLogger(__name__).warning(
            "⚠️ Telegram error handler not configured - ERROR_CHANNEL_ID or BOT_TOKEN missing"
        )
        return None
    
    try:
        # Create and configure the handler
        telegram_handler = TelegramErrorHandler(error_channel_id, bot_token)
        telegram_handler.setLevel(level)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(telegram_handler)
        
        logging.getLogger(__name__).info(
            f"✅ Telegram error handler configured for channel {error_channel_id}"
        )
        
        return telegram_handler
        
    except Exception as e:
        logging.getLogger(__name__).error(
            f"❌ Failed to setup Telegram error handler: {e}"
        )
        return None


def safe_telegram_operation(
    operation_name: str,
    user_friendly_error: str = "Something went wrong. Please try again.",
    include_context: bool = True
):
    """
    Decorator for safe Telegram operations with centralized error handling
    
    Args:
        operation_name: Name of the operation for error context
        user_friendly_error: Message to show users when errors occur
        include_context: Whether to include error context in logs
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger = logging.getLogger(func.__module__)
                
                # Build error context if requested
                error_context = None
                if include_context:
                    error_context = ErrorContext(operation=operation_name)
                    
                    # Try to extract Telegram context from arguments
                    for arg in args:
                        if hasattr(arg, 'effective_user') and arg.effective_user:
                            error_context.user_id = str(arg.effective_user.id)
                        if hasattr(arg, 'effective_chat') and arg.effective_chat:
                            error_context.chat_id = str(arg.effective_chat.id)
                        if hasattr(arg, 'message') and arg.message and hasattr(arg.message, 'text'):
                            error_context.message_text = arg.message.text
                
                # Log the error with context
                if error_context:
                    logger.error(
                        f"Error in {operation_name}: {str(e)}",
                        exc_info=True,
                        extra={'error_context': error_context}
                    )
                else:
                    logger.error(f"Error in {operation_name}: {str(e)}", exc_info=True)
                
                # Return user-friendly error or re-raise based on context
                if 'update' in kwargs or any(hasattr(arg, 'effective_user') for arg in args):
                    # This looks like a Telegram handler, try to send user-friendly message
                    update = kwargs.get('update') or next(
                        (arg for arg in args if hasattr(arg, 'effective_user')), None
                    )
                    if update and hasattr(update, 'message') and update.message:
                        try:
                            await update.message.reply_text(user_friendly_error)
                        except Exception:
                            pass  # If we can't send error message, just log it
                    return None
                else:
                    # Re-raise for non-Telegram operations
                    raise
        
        # Handle sync functions too
        if not asyncio.iscoroutinefunction(func):
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger = logging.getLogger(func.__module__)
                    
                    # Build basic error context
                    error_context = ErrorContext(operation=operation_name) if include_context else None
                    
                    # Log the error
                    if error_context:
                        logger.error(
                            f"Error in {operation_name}: {str(e)}",
                            exc_info=True,
                            extra={'error_context': error_context}
                        )
                    else:
                        logger.error(f"Error in {operation_name}: {str(e)}", exc_info=True)
                    
                    # Re-raise the error for sync functions
                    raise
            
            return sync_wrapper
        
        return wrapper
    return decorator


def log_error_with_context(
    logger: logging.Logger,
    message: str,
    error_context: Optional[ErrorContext] = None,
    exc_info: bool = True
) -> None:
    """
    Log an error with optional context information
    
    Args:
        logger: Logger instance to use
        message: Error message
        error_context: Optional context information
        exc_info: Whether to include exception traceback
    """
    if error_context:
        logger.error(message, exc_info=exc_info, extra={'error_context': error_context})
    else:
        logger.error(message, exc_info=exc_info)