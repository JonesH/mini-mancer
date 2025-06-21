"""
Test Utilities and Helper Functions - Supporting utilities for Mini-Mancer testing

Provides reusable utilities for:
- Test data generation and management
- Resource cleanup and management
- Mock objects and test fixtures
- Common test patterns and helpers
- Test environment setup and teardown
"""

import asyncio
import pytest
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from unittest.mock import Mock, AsyncMock

from telegram import Bot, Message, User, Chat, Update
from telegram.ext import Application


@dataclass
class MockTelegramObjects:
    """Container for mock Telegram objects"""
    bot: Mock
    user: Mock
    chat: Mock
    message: Mock
    update: Mock


class TestDataGenerator:
    """Generate test data for various testing scenarios"""
    
    @staticmethod
    def create_mock_telegram_objects(
        bot_id: int = 12345,
        user_id: int = 67890,
        chat_id: int = -100123456789,
        message_id: int = 1001
    ) -> MockTelegramObjects:
        """Create mock Telegram objects for testing"""
        
        # Mock Bot
        mock_bot = Mock(spec=Bot)
        mock_bot.id = bot_id
        mock_bot.first_name = "TestBot"
        mock_bot.username = "testbot"
        mock_bot.token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        
        # Mock User
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.first_name = "TestUser"
        mock_user.username = "testuser"
        mock_user.is_bot = False
        
        # Mock Chat
        mock_chat = Mock(spec=Chat)
        mock_chat.id = chat_id
        mock_chat.type = "private"
        mock_chat.first_name = "TestUser"
        
        # Mock Message
        mock_message = Mock(spec=Message)
        mock_message.message_id = message_id
        mock_message.from_user = mock_user
        mock_message.chat = mock_chat
        mock_message.text = "Test message"
        mock_message.date = time.time()
        
        # Mock Update
        mock_update = Mock(spec=Update)
        mock_update.update_id = 10001
        mock_update.message = mock_message
        mock_update.effective_user = mock_user
        mock_update.effective_chat = mock_chat
        
        return MockTelegramObjects(
            bot=mock_bot,
            user=mock_user,
            chat=mock_chat,
            message=mock_message,
            update=mock_update
        )
    
    @staticmethod
    def generate_bot_creation_requests() -> List[Dict[str, Any]]:
        """Generate various bot creation request scenarios"""
        return [
            {
                "name": "helpful_assistant",
                "request": "Create a helpful assistant bot named HelperBot",
                "expected_name": "HelperBot",
                "expected_personality": "helpful",
                "should_succeed": True
            },
            {
                "name": "gaming_bot",
                "request": "Make a gaming bot called GamerBot with dice tools",
                "expected_name": "GamerBot", 
                "expected_personality": "gaming",
                "should_succeed": True
            },
            {
                "name": "empty_request",
                "request": "",
                "expected_name": None,
                "expected_personality": None,
                "should_succeed": False
            },
            {
                "name": "too_long",
                "request": "Create a bot " + "x" * 5000,
                "expected_name": None,
                "expected_personality": None,
                "should_succeed": False
            },
            {
                "name": "special_characters",
                "request": "Create a bot named 🤖TestBot🤖 with special features",
                "expected_name": "🤖TestBot🤖",
                "expected_personality": "special",
                "should_succeed": True
            }
        ]
    
    @staticmethod
    def generate_conversation_test_data() -> List[Dict[str, Any]]:
        """Generate conversation test scenarios"""
        return [
            {
                "category": "greeting",
                "messages": ["Hello", "Hi there", "Good morning", "Hey"],
                "expected_responses": ["greeting", "hello", "hi"]
            },
            {
                "category": "help_request",
                "messages": ["Can you help me?", "I need assistance", "Help please"],
                "expected_responses": ["help", "assist", "sure", "how can"]
            },
            {
                "category": "bot_creation",
                "messages": ["Create a bot", "Make a new bot", "I want a bot"],
                "expected_responses": ["create", "bot", "name", "purpose"]
            },
            {
                "category": "invalid_input",
                "messages": ["", "   ", "🤖🤖🤖", "x" * 100],
                "expected_responses": ["error", "invalid", "sorry", "try again"]
            }
        ]


class ResourceManager:
    """Manage test resources and cleanup"""
    
    def __init__(self):
        self.temp_dirs: List[Path] = []
        self.temp_files: List[Path] = []
        self.created_bots: List[Bot] = []
        self.running_tasks: List[asyncio.Task] = []
        self.cleanup_callbacks: List[callable] = []
    
    def create_temp_directory(self, prefix: str = "mini_mancer_test_") -> Path:
        """Create a temporary directory for testing"""
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_temp_file(self, content: str = "", suffix: str = ".txt", prefix: str = "test_") -> Path:
        """Create a temporary file for testing"""
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        temp_file = Path(temp_path)
        
        with open(fd, 'w') as f:
            f.write(content)
        
        self.temp_files.append(temp_file)
        return temp_file
    
    def register_bot(self, bot: Bot):
        """Register a bot for cleanup"""
        self.created_bots.append(bot)
    
    def register_task(self, task: asyncio.Task):
        """Register a task for cleanup"""
        self.running_tasks.append(task)
    
    def register_cleanup_callback(self, callback: callable):
        """Register a cleanup callback"""
        self.cleanup_callbacks.append(callback)
    
    async def cleanup_all(self):
        """Clean up all registered resources"""
        print("🧹 Starting resource cleanup...")
        
        # Cancel running tasks
        for task in self.running_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close bots
        for bot in self.created_bots:
            try:
                await bot.close()
            except Exception as e:
                print(f"⚠️ Error closing bot: {e}")
        
        # Run cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                print(f"⚠️ Error in cleanup callback: {e}")
        
        # Remove temporary files
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as e:
                print(f"⚠️ Error removing temp file {temp_file}: {e}")
        
        # Remove temporary directories
        for temp_dir in self.temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"⚠️ Error removing temp dir {temp_dir}: {e}")
        
        print("✅ Resource cleanup completed")


class MockBotBehavior:
    """Simulate bot behaviors for testing"""
    
    def __init__(self, personality: str = "helpful"):
        self.personality = personality
        self.message_count = 0
        self.response_delay = 1.0
        
    async def simulate_response(self, message: str) -> str:
        """Simulate a bot response based on personality"""
        await asyncio.sleep(self.response_delay)
        self.message_count += 1
        
        # Simulate different personality responses
        if self.personality == "helpful":
            return f"I'd be happy to help you with: {message[:50]}..."
        elif self.personality == "stubborn":
            return f"I disagree with your statement: {message[:50]}..."
        elif self.personality == "gaming":
            return f"That sounds like fun! Let's play with: {message[:50]}..."
        elif self.personality == "study":
            return f"Let's focus on learning about: {message[:50]}..."
        else:
            return f"Interesting point about: {message[:50]}..."
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get bot interaction statistics"""
        return {
            "personality": self.personality,
            "messages_processed": self.message_count,
            "average_response_delay": self.response_delay
        }


class TestEnvironmentManager:
    """Manage test environment setup and configuration"""
    
    def __init__(self):
        self.original_env_vars = {}
        self.test_config = {}
    
    def set_test_environment_variables(self, env_vars: Dict[str, str]):
        """Set environment variables for testing"""
        import os
        
        for key, value in env_vars.items():
            if key in os.environ:
                self.original_env_vars[key] = os.environ[key]
            os.environ[key] = value
    
    def restore_environment_variables(self):
        """Restore original environment variables"""
        import os
        
        for key, original_value in self.original_env_vars.items():
            os.environ[key] = original_value
        
        # Remove test-only variables
        test_only_vars = set(self.test_config.keys()) - set(self.original_env_vars.keys())
        for key in test_only_vars:
            if key in os.environ:
                del os.environ[key]
    
    def create_test_configuration(self) -> Dict[str, Any]:
        """Create a test configuration"""
        return {
            "test_mode": True,
            "mock_telegram_api": True,
            "disable_logging": False,
            "fast_mode": True,
            "cleanup_after_test": True
        }


@pytest.fixture(scope="function")
def resource_manager():
    """Fixture providing resource management for tests"""
    manager = ResourceManager()
    try:
        yield manager
    finally:
        asyncio.create_task(manager.cleanup_all())


@pytest.fixture(scope="function")
def mock_telegram_objects():
    """Fixture providing mock Telegram objects"""
    return TestDataGenerator.create_mock_telegram_objects()


@pytest.fixture(scope="function")
def test_data_generator():
    """Fixture providing test data generation utilities"""
    return TestDataGenerator()


@pytest.fixture(scope="function")
def test_environment():
    """Fixture providing test environment management"""
    env_manager = TestEnvironmentManager()
    
    # Set up test environment
    test_env_vars = {
        "PYTEST_RUNNING": "true",
        "LOG_LEVEL": "DEBUG",
        "TEST_MODE": "true"
    }
    env_manager.set_test_environment_variables(test_env_vars)
    
    try:
        yield env_manager
    finally:
        env_manager.restore_environment_variables()


class AsyncTestHelper:
    """Helper utilities for async testing"""
    
    @staticmethod
    async def wait_for_condition(
        condition_func: callable,
        timeout: float = 10.0,
        check_interval: float = 0.1
    ) -> bool:
        """Wait for a condition to become true"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            await asyncio.sleep(check_interval)
        
        return False
    
    @staticmethod
    async def run_with_timeout(coro, timeout: float = 30.0):
        """Run a coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            pytest.fail(f"Operation timed out after {timeout}s")
    
    @staticmethod
    async def collect_async_results(tasks: List[asyncio.Task], timeout: float = 60.0):
        """Collect results from multiple async tasks"""
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
            return results
        except asyncio.TimeoutError:
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            pytest.fail(f"Async task collection timed out after {timeout}s")


@pytest.fixture(scope="function")
def async_test_helper():
    """Fixture providing async testing utilities"""
    return AsyncTestHelper()


def pytest_configure(config):
    """Additional pytest configuration for test utilities"""
    # Add custom markers for utility tests
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "mock: Tests using mock objects")
    config.addinivalue_line("markers", "cleanup: Tests focusing on resource cleanup")
    config.addinivalue_line("markers", "utility: Tests for utility functions")