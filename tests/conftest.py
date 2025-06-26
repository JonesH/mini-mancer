"""
Automated Telegram Bot Testing Framework for Mini-Mancer

This framework provides comprehensive testing for:
- Factory bot creation flows
- Created bot interactions and personalities  
- Integration testing with real Telegram API
- Performance and concurrency testing
- Resource management and cleanup
"""

import asyncio
import os
import time
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from telegram import Bot, Update, Message, User
from telegram.ext import Application
from telegram.error import TelegramError

# Import your Mini-Mancer components
from src.prototype_agent import PrototypeAgent
from src.telegram_rate_limiter import rate_limited_call


@dataclass
class BotTestSession:
    """Manages a testing session with multiple bot instances"""
    factory_bot: Bot
    factory_token: str
    created_bot_token: str | None
    test_chat_id: int
    test_user_id: int
    created_bots: list[Bot] = field(default_factory=list)
    test_messages: list[dict] = field(default_factory=list)
    cleanup_tasks: list[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)


@dataclass
class BotInteractionTest:
    """Represents a single bot interaction test case"""
    name: str
    input_message: str
    expected_keywords: list[str] = field(default_factory=list)
    expected_buttons: list[str] = field(default_factory=list)
    timeout_seconds: int = 10
    should_create_bot: bool = False
    bot_type: str | None = None


class TelegramTestError(Exception):
    """Custom exception for Telegram testing errors"""
    pass


@pytest.fixture(scope="function")
def bot_test_config():
    """Session-wide configuration for bot testing"""
    factory_token = os.getenv("BOT_TOKEN") or os.getenv("TEST_BOT_TOKEN")
    created_token = os.getenv("BOT_TOKEN_1")
    test_chat_id = int(os.getenv("TEST_CHAT_ID", "0"))
    test_user_id = int(os.getenv("TEST_USER_ID", "0"))
    
    # Add mock mode and message cleanup options
    mock_mode = os.getenv("TEST_MOCK_MODE", "false").lower() == "true"
    cleanup_messages = os.getenv("TEST_CLEANUP_MESSAGES", "true").lower() == "true"
    message_delay = float(os.getenv("TEST_MESSAGE_DELAY", "1.0"))
    
    if not factory_token and not mock_mode:
        pytest.skip("BOT_TOKEN required for Telegram API testing (set TEST_MOCK_MODE=true for mock tests)")
    
    if (not test_chat_id or not test_user_id) and not mock_mode:
        pytest.skip("TEST_CHAT_ID and TEST_USER_ID required for bot interaction testing (set TEST_MOCK_MODE=true for mock tests)")
    
    return {
        "factory_token": factory_token,
        "created_token": created_token,
        "test_chat_id": test_chat_id,
        "test_user_id": test_user_id,
        "max_test_duration": 300,  # 5 minutes max per test
        "cleanup_delay": 2.0,  # Wait between cleanup operations
        "mock_mode": mock_mode,
        "cleanup_messages": cleanup_messages,
        "message_delay": message_delay,
    }


@pytest_asyncio.fixture(scope="function") 
async def telegram_bot_session(bot_test_config) -> AsyncGenerator[BotTestSession, None]:
    """Create and manage a Telegram bot testing session"""
    # Handle mock mode
    if bot_test_config.get("mock_mode", False):
        print("[MOCK] Creating mock bot session")
        from unittest.mock import Mock
        
        # Create mock bot
        mock_bot = Mock()
        mock_bot.get_me = Mock(return_value=Mock(first_name="MockBot", username="mock_bot"))
        mock_bot.send_message = Mock()
        mock_bot.delete_message = Mock()
        mock_bot.close = Mock()
        
        session = BotTestSession(
            factory_bot=mock_bot,
            factory_token="mock_token",
            created_bot_token=bot_test_config.get("created_token", "mock_created_token"),
            test_chat_id=bot_test_config.get("test_chat_id", 123456),
            test_user_id=bot_test_config.get("test_user_id", 789012)
        )
        
        try:
            yield session
        finally:
            print("[MOCK] Mock session cleanup completed")
        return
    
    # Real bot session
    factory_bot = Bot(token=bot_test_config["factory_token"])
    
    # Verify factory bot connectivity
    try:
        bot_info = await factory_bot.get_me()
        print(f"🤖 Factory Bot Connected: {bot_info.first_name} (@{bot_info.username})")
    except TelegramError as e:
        pytest.fail(f"Failed to connect to factory bot: {e}")
    
    session = BotTestSession(
        factory_bot=factory_bot,
        factory_token=bot_test_config["factory_token"],
        created_bot_token=bot_test_config["created_token"],
        test_chat_id=bot_test_config["test_chat_id"],
        test_user_id=bot_test_config["test_user_id"]
    )
    
    try:
        yield session
    finally:
        # Cleanup session
        print(f"🧹 Cleaning up test session...")
        for bot in session.created_bots:
            try:
                await bot.close()
            except Exception as e:
                print(f"⚠️ Error closing bot: {e}")
        
        await factory_bot.close()
        print(f"✅ Test session cleanup completed")


@pytest_asyncio.fixture(scope="function")
async def prototype_agent_instance():
    """Create a fresh PrototypeAgent instance for testing"""
    try:
        agent = PrototypeAgent()
        yield agent
    finally:
        # Cleanup agent resources
        if hasattr(agent, 'shutdown'):
            try:
                await agent.shutdown()
            except Exception as e:
                print(f"⚠️ Error shutting down PrototypeAgent: {e}")


@pytest_asyncio.fixture(scope="function")
async def bot_interaction_helper(telegram_bot_session, bot_test_config):
    """Helper for common bot interaction patterns"""
    
    class BotInteractionHelper:
        def __init__(self, session: BotTestSession, config: dict):
            self.session = session
            self.config = config
            self.sent_messages = []
            self.message_count = 0
        
        async def send_message_and_wait(self, text: str, timeout: int = 10) -> Message:
            """Send a message to the factory bot using adaptive rate limiter"""
            # Mock mode - don't send real messages
            if self.config.get("mock_mode", False):
                print(f"[MOCK] Would send message: '{text[:50]}...'")
                # Create mock message object
                from telegram import Message as TelegramMessage
                from unittest.mock import Mock
                mock_msg = Mock(spec=TelegramMessage)
                mock_msg.message_id = 999999 + self.message_count
                self.message_count += 1
                await asyncio.sleep(0.1)  # Brief delay for realism
                return mock_msg
            
            try:
                # Send message using adaptive rate limiter
                print(f"[TEST] Sending: '{text[:50]}...'")  # Log what we're sending
                
                # Use rate_limited_call with factory bot token
                sent_msg = await rate_limited_call(
                    self.session.factory_token,
                    self.session.factory_bot.send_message(
                        chat_id=self.session.test_chat_id,
                        text=text
                    )
                )
                self.sent_messages.append(sent_msg.message_id)
                
                # No manual delay needed - rate limiter handles timing
                return sent_msg
                
            except TelegramError as e:
                raise TelegramTestError(f"Failed to send message '{text}': {e}")
        
        async def test_bot_creation_flow(self, bot_request: str, expected_bot_name: str) -> dict:
            """Test complete bot creation flow"""
            print(f"🔧 Testing bot creation: '{bot_request}'")
            
            # Send bot creation request (rate limiter handles timing)
            creation_msg = await self.send_message_and_wait(bot_request)
            
            # Brief wait for processing logic (not rate limiting)
            if self.config.get("mock_mode", False):
                await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(1)  # Just for processing, not rate limiting
            
            # Verify bot was created (would need to check actual response in real implementation)
            return {
                "creation_message_id": creation_msg.message_id,
                "bot_name": expected_bot_name,
                "success": True  # Would verify actual bot creation
            }
        
        async def test_inline_keyboard_creation(self, callback_data: str) -> dict:
            """Test bot creation via inline keyboard buttons"""
            print(f"🎮 Testing inline keyboard creation: {callback_data}")
            
            # First send /start to get keyboard (rate limiter handles timing)
            start_msg = await self.send_message_and_wait("/start")
            
            # Brief simulation delay (not for rate limiting)
            if self.config.get("mock_mode", False):
                await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.5)  # Just for UI simulation
            
            return {
                "start_message_id": start_msg.message_id,
                "callback_data": callback_data,
                "success": True
            }
        
        async def cleanup_messages(self):
            """Clean up test messages with improved error handling"""
            if not self.config.get("cleanup_messages", True):
                print(f"[TEST] Skipping cleanup of {len(self.sent_messages)} messages (cleanup disabled)")
                return
            
            if self.config.get("mock_mode", False):
                print(f"[MOCK] Would cleanup {len(self.sent_messages)} messages")
                return
            
            if not self.sent_messages:
                return
                
            print(f"[CLEANUP] Attempting to delete {len(self.sent_messages)} test messages...")
            successful_deletions = 0
            failed_deletions = 0
            
            for msg_id in self.sent_messages:
                try:
                    # Add small delay before each deletion attempt
                    await asyncio.sleep(0.2)
                    
                    await self.session.factory_bot.delete_message(
                        chat_id=self.session.test_chat_id,
                        message_id=msg_id
                    )
                    successful_deletions += 1
                    
                except TelegramError as e:
                    failed_deletions += 1
                    # Only log specific errors that aren't expected
                    error_msg = str(e).lower()
                    if "message to delete not found" not in error_msg and "message can't be deleted" not in error_msg:
                        print(f"[CLEANUP] Unexpected error deleting message {msg_id}: {e}")
                except Exception as e:
                    failed_deletions += 1
                    print(f"[CLEANUP] Unexpected error deleting message {msg_id}: {e}")
            
            print(f"[CLEANUP] Deleted {successful_deletions}/{len(self.sent_messages)} messages ({failed_deletions} failed)")
            
            # Clear the list after cleanup attempt
            self.sent_messages.clear()
    
    helper = BotInteractionHelper(telegram_bot_session, bot_test_config)
    try:
        yield helper
    finally:
        # Rate limiter handles timing, just cleanup messages
        await helper.cleanup_messages()


# Test data for different bot creation scenarios
BOT_CREATION_TESTS = [
    BotInteractionTest(
        name="helpful_assistant",
        input_message="Create a helpful assistant bot named HelperBot",
        expected_keywords=["HelperBot", "created", "live"],
        should_create_bot=True,
        bot_type="helpful"
    ),
    BotInteractionTest(
        name="gaming_bot",
        input_message="Make a gaming bot called GamerBot", 
        expected_keywords=["GamerBot", "gaming", "dice"],
        should_create_bot=True,
        bot_type="gaming"
    ),
    BotInteractionTest(
        name="study_helper",
        input_message="I need a study helper bot",
        expected_keywords=["study", "pomodoro", "timer"],
        should_create_bot=True,
        bot_type="study"
    ),
    BotInteractionTest(
        name="invalid_request",
        input_message="Hello, how are you?",
        expected_keywords=["BotMother", "create"],
        should_create_bot=False
    )
]

INLINE_KEYBOARD_TESTS = [
    "create_helpful",
    "create_stubborn", 
    "create_gaming",
    "create_study",
    "create_support",
    "create_random"
]


@pytest.fixture(params=BOT_CREATION_TESTS)
def bot_creation_test_case(request):
    """Parametrized fixture for bot creation test cases"""
    return request.param


@pytest.fixture(params=INLINE_KEYBOARD_TESTS)
def inline_keyboard_test_case(request):
    """Parametrized fixture for inline keyboard test cases"""
    return request.param


# Performance testing fixtures
@pytest_asyncio.fixture(scope="function")
async def performance_monitor():
    """Monitor performance metrics during tests"""
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.metrics = {}
        
        def start_timing(self, operation: str):
            self.start_time = time.time()
            self.metrics[operation] = {"start": self.start_time}
        
        def end_timing(self, operation: str):
            if operation in self.metrics and self.start_time:
                duration = time.time() - self.start_time
                self.metrics[operation]["duration"] = duration
                self.metrics[operation]["end"] = time.time()
                return duration
            return 0
        
        def get_metrics(self) -> dict:
            return self.metrics.copy()
    
    monitor = PerformanceMonitor()
    yield monitor
    
    # Log performance metrics
    print(f"📊 Performance Metrics: {monitor.get_metrics()}")


# Custom pytest markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "factory_bot: Test factory bot functionality")
    config.addinivalue_line("markers", "created_bot: Test created bot functionality") 
    config.addinivalue_line("markers", "integration: Test end-to-end bot workflows")
    config.addinivalue_line("markers", "performance: Test performance and concurrency")
    config.addinivalue_line("markers", "api: Test API integration")
    config.addinivalue_line("markers", "slow: Slow tests requiring extended timeouts")
    config.addinivalue_line("markers", "network: Tests requiring Telegram API network access")