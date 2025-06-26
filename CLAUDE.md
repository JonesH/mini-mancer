# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mini-mancer is a Python project that uses `agno` as its main AI agent framework, integrating OpenServ → Agno → Telegram for bot creation and deployment. The project uses uv for dependency management and virtual environment handling.

## Development Environment

- Python version: 3.11+ (specified in .python-version)
- Package manager: uv
- Virtual environment: `.venv/` (managed by uv)

## Common Commands

### Setup
```bash
# Install dependencies
uv sync
# Add new dependencies to the local venv
uv add <package>

# Activate virtual environment (if needed)
source .venv/bin/activate
```

### Running the Application
```bash
# Run the main application locally
uv run python main.py

# Run with Docker (recommended for development)
docker compose up mini-mancer -d --force-recreate --build
```

### Code Quality & Testing
```bash
# Run comprehensive code quality check
./scripts/format.sh

# Individual quality tools
uv run ruff check --fix src/ main.py     # Linting & auto-fixes
uv run black src/ main.py                # Code formatting
uv run isort src/ main.py                # Import organization
uv run mypy src/ main.py                 # Type checking

# Run tests
uv run pytest tests/                     # Run test suite
```

## Code Style Guidelines

### Clean Code Principles
- Write self-documenting code with clear variable and function names
- Keep functions small and focused on a single responsibility
- Prefer explicit over implicit behavior
- Use meaningful names that reveal intent

### DRY (Don't Repeat Yourself)
- Extract common functionality into reusable functions
- Use constants for repeated values
- Factor out duplicate logic into utility functions

### Type Hints
- Use modern Python 3.11+ built-in generics instead of typing imports:
  - Use `list[str]` instead of `List[str]`
  - Use `dict[str, int]` instead of `Dict[str, int]`
  - Use `set[int]` instead of `Set[int]`
  - Use `tuple[str, ...]` instead of `Tuple[str, ...]`
  - Use `str | None` instead of `Union[str, None]` or `Optional[str]`
- Only import from typing when necessary (e.g., `Protocol`, `TypeVar`, `Generic`)

### Control Flow
- **Use guard clauses and early returns** - Avoid deep nesting:
  ```python
  # Good
  def process_data(data):
      if not data:
          return None
      if not data.is_valid():
          return None
      
      return data.transform()
  
  # Avoid
  def process_data(data):
      if data:
          if data.is_valid():
              return data.transform()
      return None
  ```

- **No nested conditionals** - Extract complex conditions into functions:
  ```python
  # Good
  def is_valid_user(user):
      return user.is_active and user.email_verified and user.has_permission()
  
  if not is_valid_user(user):
      return
  
  # Avoid
  if user.is_active:
      if user.email_verified:
          if user.has_permission():
              # nested logic
  ```

### Loop Handling
- **Extract loop bodies into separate functions** when complex:
  ```python
  # Good
  def process_item(item):
      # complex processing logic
      return transformed_item
  
  def process_all_items(items):
      return [process_item(item) for item in items]
  
  # Avoid putting complex logic directly in loop bodies
  ```

### Indentation and Nesting
- Keep indentation shallow (max 2-3 levels)
- Use early returns to reduce nesting
- Extract nested logic into separate functions
- Prefer flat structure over deeply nested code

### Error Handling
- Avoid excessive or comprehensive error handling; let exceptions and tracebacks bubble up
- Only catch exceptions when there's a clear, necessary recovery path

### Comments and Documentation
- Avoid comments unless code isn't self-explanatory
- Provide short, concise docstrings for public-facing methods

## Project Structure

### Core Application
- `main.py` - Entry point with dual Telegram + FastAPI servers
- `src/agent_controller.py` - Core AgentController orchestrating all components
- `src/prototype_agent.py` - Compatibility layer and main exports

### Bot System
- `src/agents/telegram_bot_template.py` - Telegram bot template and webhook handler
- `src/models/agent_dna.py` - Agent DNA system and templates
- `src/models/bot_requirements.py` - Comprehensive bot requirements and validation
- `src/bot_compilation_pipeline.py` - Advanced bot testing and quality assurance

### Integration & APIs
- `src/api_router.py` - FastAPI route handlers for OpenServ integration
- `src/api_models.py` - Pydantic models for API requests/responses
- `src/telegram_integration.py` - Telegram bot lifecycle management
- `src/botfather_integration.py` - BotFather automation using Telethon client API
- `src/token_pool_manager.py` - Multi-bot token pool management system

### Utilities & Infrastructure
- `src/utils/` - Error handling and utility functions
- `src/constants/` - User-facing messages and constants
- `src/tools/thinking_tool.py` - Advanced reasoning capabilities
- `src/test_monitor.py` - Real-time test monitoring and WebSocket dashboard

### Configuration & Quality
- `pyproject.toml` - Project configuration, dependencies, and quality tool settings
- `scripts/format.sh` - Automated code quality script
- `tests/` - Comprehensive test suite
- `docker-compose.yaml` - PostgreSQL + app containerization

## Key Dependencies

- `agno` - The main AI agent framework for intelligent bot creation
- `fastapi` - Web framework for OpenServ integration endpoints
- `python-telegram-bot` - Telegram bot API integration
- `telethon` - Telegram client API for BotFather automation and testing
- `psycopg[binary]` - PostgreSQL database connectivity

## Git Guidelines

### CRITICAL RULES - NEVER BREAK THESE:

 • **NEVER** use `git add -A` or `git add .` - these are dangerous and can add unintended files
 • **ALWAYS** add files explicitly by name: `git add specific_file.py`
 • **ALWAYS** check `git status` and `git diff --staged` before committing
 • **NEVER** commit without reviewing exactly what is being staged
 • **NEVER** put credentials, API keys, tokens, or secrets directly in code
 • **ALWAYS** use environment variables or secure credential management for sensitive data

### Commit Message Rules:
 • **NEVER** add "Co-Authored-By: Claude" or any AI attribution to commit messages
 • **NEVER** add "Generated with Claude Code" to commit messages  
 • Keep commit messages clean and professional
 • Focus on what changed and why, not who/what wrote it

## Code Quality Standards

### Automated Quality Pipeline
The project uses a comprehensive quality pipeline with three integrated tools:

- **Ruff** - Fast Python linter and formatter with extensive rule coverage
- **Black** - Opinionated code formatter for consistent styling
- **isort** - Import organization and sorting
- **MyPy** - Static type checking for type safety

### Quality Metrics
- **Ruff violations**: Target < 10 cosmetic issues
- **MyPy compliance**: All type annotations must pass validation
- **Test coverage**: Maintain comprehensive test suite
- **Import organization**: No star imports, explicit imports only

### Running Quality Checks
```bash
# Complete quality check (recommended)
./scripts/format.sh

# Fix most issues automatically
uv run ruff check --fix src/ main.py

# Manual quality tools
uv run black src/ main.py        # Format code
uv run isort src/ main.py        # Organize imports  
uv run mypy src/ main.py         # Type checking
```

### Quality Gates
- All code must pass MyPy type checking
- Ruff violations should be minimal (< 10 cosmetic issues)
- No F-series errors (undefined names, imports, etc.)
- Modern Python 3.11+ type annotations required

## Telegram Bot Testing Protocol

### MANDATORY TELEGRAM BOT TESTING:

**CRITICAL RULE:** Never claim a Telegram bot command is "fixed" or "working" without actual functional testing via Telegram API.

**Testing Protocol:**
1. **PRIMARY TEST METHOD:** Use Telegram CLIENT API (Telethon) with user credentials to test created bots
2. **CRITICAL:** NEVER use bot API (curl with bot tokens) to test created bots - use CLIENT API only
3. **Verification Required:** Confirm bot responds as expected to real user interactions  
4. **Error Validation:** Verify no crashes, malfunction, or error messages to users
5. **Success Criteria:** User receives intended response content and formatting

**Testing Tools:**
- **CORRECT:** Use Telethon with TELEGRAM_API_ID/TELEGRAM_API_HASH to act as real user
- **CORRECT:** Send messages TO created bots using client API
- **WRONG:** Never use curl with bot tokens to test created bots
- Verify response content matches expectations
- Check logs only as secondary validation

**What "Working" Means:**
- ✅ User sends command and gets expected response
- ✅ No error messages delivered to user
- ✅ Formatting displays correctly in Telegram
- ❌ NOT "code compiles without syntax errors"
- ❌ NOT "container starts successfully"
- ❌ NOT "no immediate crashes in logs"

**Example Testing Approach:**
```python
# CORRECT: Use Telethon to test created bots
from telethon import TelegramClient

client = TelegramClient('session', API_ID, API_HASH)
await client.start()

# Send message TO created bot as real user
await client.send_message('@created_bot_username', 'Hello bot!')

# Wait for and verify bot response
# This is the ONLY way to properly test created bots
```

**NEVER DO THIS for created bots:**
```bash
# WRONG: Don't use bot API to test created bots
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" # WRONG!
```

## BotFather Integration & Token Management

### BotFather Automation System

Mini-mancer includes a comprehensive BotFather integration system that automates bot configuration using the Telethon client API. This system mimics human interaction with @BotFather to configure newly created bots.

### Key Components

**Token Pool Management (`src/token_pool_manager.py`):**
- Multi-bot concurrent deployment system
- Automatic token validation and pool management
- Round-robin token allocation for load balancing
- Persistent token storage with JSON-based pool files

**BotFather Integration (`src/botfather_integration.py`):**
- **CRITICAL:** Uses Telethon client API exclusively (never Bot API for @BotFather communication)
- Automates conversations with @BotFather just like a human user would
- Handles bot configuration: commands, descriptions, short descriptions
- Validates bot tokens using Bot API `getMe` endpoint

### BotFather Workflow Commands

The system provides three main command handlers for token management:

1. **`/add_token <token>`** - Add new BotFather token to pool with validation
2. **`/validate_token <token>`** - Validate existing token and show bot info  
3. **`/configure_bot <token>`** - Full bot setup with commands and descriptions

### BotFather Communication Protocol

**MANDATORY APPROACH:** All BotFather interactions MUST use Telethon client API:

```python
# CORRECT: BotFather automation using Telethon
from telethon import TelegramClient

client = TelegramClient('user_test_session', API_ID, API_HASH)
await client.start()

# 1. Send BotFather command
await client.send_message('BotFather', '/setcommands')
await asyncio.sleep(2)

# 2. Send bot username (NOT token)
await client.send_message('BotFather', '@your_bot_username')
await asyncio.sleep(2)

# 3. Send configuration data
await client.send_message('BotFather', command_list)
```

**Critical BotFather Conversation Flow:**
1. When BotFather receives commands like `/setcommands`, it responds with a ReplyKeyboardMarkup showing bot options
2. **MUST** send the bot username (e.g., `@protomancer_supreme_bot`) as a message, not use callbacks
3. **NEVER** send tokens directly to BotFather - always use username after validating token via Bot API

### Token Validation Process

**Two-Stage Validation:**
1. **Bot API Validation** - Use `https://api.telegram.org/bot{token}/getMe` to validate token and get bot info
2. **BotFather Configuration** - Use bot username (from validation) to configure via @BotFather

```python
# CORRECT: Token validation workflow
# Step 1: Validate token and get username
validation_result = await botfather.validate_bot_token(token)
if validation_result["valid"]:
    bot_username = f"@{validation_result['username']}"
    
    # Step 2: Configure via BotFather using username
    await client.send_message('BotFather', '/setcommands')
    await client.send_message('BotFather', bot_username)  # Use username, not token
```

### Session Management

**Local Development:**
- Uses existing `user_test_session.session` file for authenticated Telethon sessions
- Run locally with: `dotenv run uv run python script.py` to access .env variables
- Session files contain SQLite database with Telegram authentication data

**Container Environment:**
- Telethon sessions require interactive authentication (not suitable for containers)
- Use local environment for BotFather integration testing and development

### Error Handling & Success Detection

**BotFather Response Analysis:**
```python
# Check BotFather responses for success/failure
messages = await client.get_messages('BotFather', limit=3)
for message in messages:
    if message.text:
        text = message.text.lower()
        if any(success in text for success in ['success', 'updated', 'done']):
            return {"success": True}
        elif any(error in text for error in ['error', 'invalid', 'wrong']):
            return {"success": False, "error": message.text}
```

### Testing BotFather Integration

**Use the included test script:**
```bash
# Test BotFather integration locally
dotenv run uv run python test_botfather_integration.py
```

**Verification Steps:**
1. Validate token format and API connectivity
2. Get bot username from Bot API
3. Test @BotFather communication flow
4. Verify configuration was applied successfully
5. Test created bot responds to commands properly

### Common Issues & Solutions

**"Invalid bot selected" Error:**
- Cause: Sending token instead of username to BotFather
- Solution: Always send `@username` after validating token

**Session Authentication Errors:**
- Cause: Missing or invalid Telethon session file
- Solution: Run authentication locally, copy session file to project

**Rate Limiting:**
- BotFather has strict rate limits
- Use `asyncio.sleep(2)` between messages
- Implement exponential backoff for retries

## Event Loop Integration Considerations

### Event Loop Challenges
- The project now needs to integrate multiple event loops:
  - FastAPI's event loop
  - Botmother event loop
  - Event loops for created bots
- Ensuring seamless coordination between these event loops is critical
  - Interesting challenge: making different event loop systems work together flawlessly