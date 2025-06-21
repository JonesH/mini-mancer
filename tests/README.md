# Mini-Mancer Automated Testing Framework

Comprehensive automated testing system for validating Mini-Mancer bot creation and management functionality using real Telegram API interactions.

## Overview

This testing framework provides automated validation of:
- **Factory Bot Operations** - Bot creation commands, inline keyboards, error handling
- **Created Bot Interactions** - Personality validation, tool integration, AI responses  
- **Integration Testing** - End-to-end workflows, API integration, system resilience
- **Performance Testing** - Concurrency, memory usage, stress testing, rate limiting
- **Utility Functions** - Test helpers, mock objects, resource management

## Test Structure

```
tests/
├── conftest.py              # Core test fixtures and configuration
├── test_factory_bot.py      # Factory bot functionality tests
├── test_created_bots.py     # Created bot validation tests  
├── test_integration.py      # End-to-end integration tests
├── test_performance.py      # Performance and stress tests
├── test_utils.py           # Test utilities and helpers
├── pytest.ini             # Pytest configuration
└── README.md              # This documentation
```

## Setup Requirements

### Environment Variables

Required for Telegram API testing:
```bash
# Factory bot token (primary bot)
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Created bot token (for testing created bots)  
BOT_TOKEN_1=789012:XYZ-GHI5678jklMn-abc90V3w2x456fg22

# Test chat and user IDs
TEST_CHAT_ID=123456789        # Chat ID for sending test messages
TEST_USER_ID=987654321        # User ID for test interactions

# Optional: Demo user for notifications
DEMO_USER=123456789
```

### Dependencies

Install testing dependencies using uv:
```bash
# Add testing dependencies to project
uv add --group test pytest pytest-asyncio python-telegram-bot psutil

# Development dependencies
uv add --group dev pytest-mock pytest-timeout pytest-xdist
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test categories
uv run pytest -m factory_bot      # Factory bot tests only
uv run pytest -m created_bot      # Created bot tests only  
uv run pytest -m integration      # Integration tests only
uv run pytest -m performance      # Performance tests only
```

### Test Categories

Tests are organized by markers:

- `factory_bot` - Factory bot creation and management
- `created_bot` - Individual bot personality and functionality
- `integration` - End-to-end workflows and system integration
- `performance` - Concurrency, memory, and stress testing
- `api` - API integration and rate limiting
- `slow` - Long-running tests (>30s)
- `network` - Tests requiring Telegram API access
- `mock` - Tests using mock objects
- `unit` - Individual component tests

### Network vs Mock Testing

```bash
# Run only network-dependent tests (requires real bot tokens)
uv run pytest -m network

# Run only mock tests (no external dependencies)
uv run pytest -m mock

# Skip slow tests
uv run pytest -m "not slow"

# Run quick validation suite
uv run pytest -m "not slow and not performance"
```

## Test Configuration

### Performance Tuning

Parallel execution:
```bash
# Run tests in parallel (requires pytest-xdist)
uv run pytest -n auto

# Run specific number of workers
uv run pytest -n 4
```

Timeout management:
```bash
# Set custom timeout (default: 300s)
uv run pytest --timeout=600

# Run with specific timeout for slow tests
uv run pytest -m slow --timeout=900
```

### Test Environment

Configure test behavior via environment variables:
```bash
# Enable debug logging
LOG_LEVEL=DEBUG uv run pytest

# Test mode flag
TEST_MODE=true uv run pytest

# Disable cleanup for debugging
PYTEST_DISABLE_CLEANUP=true uv run pytest
```

## Test Categories Explained

### 1. Factory Bot Tests (`test_factory_bot.py`)

Tests the main bot creation interface:

**Core Functionality:**
- `/start` command and inline keyboard display
- Text-based bot creation requests
- Bot name extraction and validation
- Inline keyboard button interactions

**Error Handling:**
- Invalid input processing
- Rate limiting behavior  
- Concurrent request handling
- Recovery from errors

**Performance:**
- Response time measurement
- Concurrent creation stress testing
- Endurance testing

Example:
```python
async def test_text_based_bot_creation(bot_interaction_helper):
    result = await bot_interaction_helper.test_bot_creation_flow(
        "Create a helpful assistant bot named HelperBot",
        "HelperBot"
    )
    assert result["success"]
```

### 2. Created Bot Tests (`test_created_bots.py`)

Validates individual bot personalities and capabilities:

**Personality Testing:**
- Response consistency with defined personality traits
- Forbidden trait avoidance
- Personality-specific language patterns

**Tool Integration:**
- Tool activation and functionality
- Tool-personality integration
- Tool response formats

**AI Quality:**
- Response relevance and coherence
- Response time consistency
- Error recovery from problematic prompts

Example:
```python
async def test_bot_personality_consistency(personality_test_case):
    # Test multiple messages for personality consistency
    for message in test_case.test_messages:
        response = await send_message_to_created_bot(message)
        assert any(trait in response for trait in test_case.expected_traits)
```

### 3. Integration Tests (`test_integration.py`)

End-to-end workflow validation:

**Complete Workflows:**
- Full bot lifecycle from creation to deployment
- Factory-to-created-bot handoff
- Multiple bot creation sequences

**System Integration:**
- OpenServ API integration
- Agno-AGI integration
- Cross-component communication

**Resilience Testing:**
- Error injection and recovery
- System health validation
- Component failure handling

Example:
```python
async def test_complete_bot_lifecycle():
    # 1. Create bot via factory
    creation_result = await create_bot_via_factory()
    
    # 2. Verify bot startup
    assert await verify_bot_startup()
    
    # 3. Test bot interaction
    assert await test_created_bot_interaction()
    
    # 4. Verify cleanup
    assert await verify_resource_cleanup()
```

### 4. Performance Tests (`test_performance.py`)

System performance and scalability validation:

**Concurrency Testing:**
- Simultaneous bot creation requests
- Mixed operation load testing
- Resource contention handling

**Memory Management:**
- Memory leak detection
- Resource cleanup verification
- Long-running stability

**API Performance:**
- Telegram API rate limiting
- Response time consistency
- Error rate monitoring

Example:
```python
async def test_concurrent_bot_creation_stress():
    # Create 10 concurrent bot creation requests
    tasks = [create_bot(f"StressBot{i}") for i in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_rate = calculate_success_rate(results)
    assert success_rate >= 0.8  # 80% success rate minimum
```

## Mock Testing Framework

For testing without Telegram API dependencies:

```python
from test_utils import TestDataGenerator, MockBotBehavior

# Generate mock Telegram objects
mock_objects = TestDataGenerator.create_mock_telegram_objects()

# Simulate bot behavior
mock_bot = MockBotBehavior(personality="helpful")
response = await mock_bot.simulate_response("Hello")
```

## Resource Management

Automatic cleanup of test resources:

```python
async def test_with_resources(resource_manager):
    # Create temporary resources
    temp_file = resource_manager.create_temp_file("test data")
    temp_dir = resource_manager.create_temp_directory()
    
    # Register bot for cleanup
    resource_manager.register_bot(test_bot)
    
    # Resources automatically cleaned up after test
```

## Debugging Tests

### Verbose Logging

```bash
# Enable detailed logging
uv run pytest --log-cli-level=DEBUG -s

# Capture print statements
uv run pytest -s

# Show local variables on failure
uv run pytest --tb=long
```

### Test Isolation

```bash
# Run single test
uv run pytest tests/test_factory_bot.py::TestFactoryBotCreation::test_start_command

# Run with specific markers
uv run pytest -m "factory_bot and not slow"

# Stop on first failure
uv run pytest -x
```

### Performance Analysis

```bash
# Show test durations
uv run pytest --durations=10

# Profile test execution
uv run pytest --profile

# Memory usage monitoring (requires memory_profiler)
uv run pytest --memory-profile
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Mini-Mancer Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Install dependencies
        run: uv sync
      
      - name: Run mock tests
        run: uv run pytest -m "mock and not network"
      
      - name: Run network tests
        env:
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
          BOT_TOKEN_1: ${{ secrets.BOT_TOKEN_1 }}
          TEST_CHAT_ID: ${{ secrets.TEST_CHAT_ID }}
          TEST_USER_ID: ${{ secrets.TEST_USER_ID }}
        run: uv run pytest -m "network and not slow"
```

### Test Reports

Generate test reports:
```bash
# HTML report
uv run pytest --html=report.html

# JUnit XML for CI
uv run pytest --junitxml=junit.xml

# Coverage report
uv run pytest --cov=src --cov-report=html
```

## Best Practices

### Test Organization

1. **Use descriptive test names** that explain what is being tested
2. **Group related tests** using classes and clear module organization  
3. **Apply appropriate markers** for test categorization
4. **Keep tests focused** - one concept per test function
5. **Use fixtures** for common setup and teardown

### Async Testing

1. **Use `pytest-asyncio`** for async test support
2. **Await all async operations** properly
3. **Handle timeouts** appropriately for network operations
4. **Clean up resources** in finally blocks or fixtures

### Network Testing

1. **Use real tokens** sparingly and securely
2. **Implement rate limiting** respect in tests
3. **Handle API errors** gracefully
4. **Provide mock alternatives** for CI/CD

### Performance Testing

1. **Set realistic expectations** for performance metrics
2. **Monitor resource usage** during tests
3. **Test under various conditions** (load, errors, etc.)
4. **Collect meaningful metrics** for analysis

## Troubleshooting

### Common Issues

**Telegram API Errors:**
```
TelegramError: Unauthorized
```
- Verify bot tokens are correct and valid
- Check that tokens haven't been revoked
- Ensure test chat/user IDs are accessible to bots

**Test Timeouts:**
```
TimeoutError: Test exceeded 300s timeout
```
- Increase timeout for slow tests: `uv run pytest --timeout=600`
- Check for network connectivity issues
- Verify Telegram API is accessible

**Resource Leaks:**
```
Too many open file descriptors
```
- Ensure all bots are properly closed in teardown
- Use resource manager fixtures for cleanup
- Check for uncancelled asyncio tasks

**Import Errors:**
```
ModuleNotFoundError: No module named 'src'
```
- Run tests from project root directory
- Ensure uv environment is active: `uv run`
- Check project dependencies: `uv sync`

### Debug Mode

Enable comprehensive debugging:
```bash
# Maximum verbosity
uv run pytest -vvv -s --tb=long --log-cli-level=DEBUG

# Stop on first failure with debug
uv run pytest -x --pdb

# Run specific test with debugging
uv run pytest tests/test_factory_bot.py::test_start_command -vvv -s
```

## Contributing

When adding new tests:

1. **Follow naming conventions** (`test_*.py`, `test_*()`)
2. **Add appropriate markers** for categorization
3. **Include docstrings** explaining test purpose
4. **Handle cleanup** properly to avoid resource leaks
5. **Test both success and failure cases**
6. **Update this documentation** for new test categories

## Integration with Mini-Mancer

This testing framework integrates with the Mini-Mancer system by:

- **Testing real bot creation workflows** through the factory bot
- **Validating created bot personalities** and tool integration
- **Monitoring system performance** under various conditions
- **Ensuring reliability** of the bot creation pipeline
- **Providing confidence** for production deployments

The tests serve as both validation and documentation of expected system behavior, making them valuable for development, debugging, and maintenance of the Mini-Mancer platform.

## Quick Start

1. **Set environment variables** for your test bots
2. **Install dependencies**: `uv sync`
3. **Run basic tests**: `uv run pytest -m "not slow"`
4. **Run full test suite**: `uv run pytest`
5. **Check performance**: `uv run pytest -m performance`