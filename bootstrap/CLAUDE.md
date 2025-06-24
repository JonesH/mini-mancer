# CLAUDE.md - Bootstrap MVP

This file provides guidance to Claude Code when working with the Bootstrap MVP version of Mini-Mancer.

## Project Overview

Bootstrap Mini-Mancer is a minimal viable product (MVP) that strips down the bloated main project to its essential core: creating and testing intelligent Telegram bots. The system focuses on a clean, progressive approach with Telethon-based testing as the foundation.

**Core Functionality:**
- BotMother: Factory bot that creates and manages child bots
- Agno Integration: AI intelligence for conversations and bot creation
- Telethon Testing: Real user testing of all bot interactions
- Bot Registry: Simple tracking of created bots

## Development Environment

- Python version: 3.11+ (specified in .python-version)
- Package manager: uv
- Virtual environment: `.venv/` (managed by uv)
- Testing framework: Telethon client API (MANDATORY)

## Bootstrap Implementation Plan

### Step 0: Telethon Foundation (CRITICAL)
**MUST BE COMPLETED FIRST**
- Get Telethon working with existing API credentials
- Session management and persistence
- Core testing utilities for sending messages TO bots
- Session validation and error handling

### Step 1: Basic BotMother + Telethon Validation  
- Minimal BotMother using existing BOT_MOTHER_TOKEN
- Basic commands: `/start`, `/help`
- **MANDATORY**: Test with Telethon by sending messages TO BotMother
- Verify responses work for real users

### Step 2: Bot Creation + Telethon Testing
- Add `/create_bot` command to BotMother
- Use available tokens for spawned bots
- Bot registry system
- **MANDATORY**: Test spawned bots with Telethon

### Step 3: Agno Intelligence + Conversation Testing
- Integrate existing AGNO_API_KEY
- Natural language conversations
- **MANDATORY**: Test intelligent conversations via Telethon

### Step 4: Intelligent Bot Spawning + Full Validation
- Spawned bots get agno intelligence
- Personality and role assignment
- **MANDATORY**: Test each spawned bot via Telethon

## Telethon Testing Protocol

### CRITICAL RULES - NEVER BREAK THESE:

**MANDATORY TESTING APPROACH:**
- Use Telethon client API to act as real user
- Send messages TO bots being tested
- NEVER use Bot API (curl with bot tokens) for testing created bots
- Test each component immediately after building it

**What "Working" Means:**
- ✅ Real user sends message and gets expected response
- ✅ No error messages delivered to user
- ✅ Formatting displays correctly in Telegram
- ❌ NOT "code compiles without syntax errors"
- ❌ NOT "bot starts without crashing"

**Testing Implementation:**
```python
# CORRECT: Use Telethon to test bots
from telethon import TelegramClient

client = TelegramClient('session', API_ID, API_HASH)
await client.start()

# Send message TO bot as real user
await client.send_message('@bot_username', '/start')

# Wait for and verify bot response
response = await client.get_messages('@bot_username', limit=1)
assert response[0].text == "Expected response"
```

**NEVER DO THIS:**
```bash
# WRONG: Don't use Bot API to test bots
curl -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage"
```

## Code Style Guidelines

### Clean Code Principles
- Write self-documenting code with clear variable and function names
- Keep functions small and focused on single responsibility
- Use meaningful names that reveal intent
- Prefer explicit over implicit behavior

### Type Hints (Modern Python 3.11+)
- Use built-in generics: `list[str]`, `dict[str, int]`, `set[int]`
- Use union syntax: `str | None` instead of `Optional[str]`
- Only import from typing when necessary (`Protocol`, `TypeVar`, `Generic`)

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

- **No nested conditionals** - Extract complex conditions:
```python
# Good
def is_valid_user(user):
    return user.is_active and user.email_verified

if not is_valid_user(user):
    return

# Avoid nested if statements
```

### Error Handling
- Let exceptions bubble up naturally
- Only catch exceptions when there's clear recovery path
- Avoid excessive try/catch blocks

### Indentation and Nesting
- Keep indentation shallow (max 2-3 levels)
- Use early returns to reduce nesting
- Extract nested logic into separate functions

## Dependencies

### Minimal Essential Dependencies
```toml
dependencies = [
    "telethon>=1.40.0",           # User client API for testing
    "python-telegram-bot>=22.1",  # Bot framework
    "agno>=0.5.50",              # AI intelligence
    "python-dotenv>=1.1.0",      # Environment variables
    "asyncio",                   # Async support
]
```

### NO BLOATED DEPENDENCIES
- No FastAPI (not needed for MVP)
- No PostgreSQL (use JSON files)
- No complex monitoring systems
- No Docker (keep it simple)

## Project Structure

```
bootstrap/
├── .env.example              # Template environment file
├── .env                      # Actual environment variables
├── pyproject.toml           # Minimal dependencies
├── main.py                  # Entry point
├── src/
│   ├── session_manager.py   # Telethon session handling
│   ├── bot_mother.py        # Core BotMother logic
│   ├── bot_registry.py      # Track created bots
│   ├── agno_intelligence.py # AI integration
│   └── agent_spawner.py     # Create/manage child bots
├── data/
│   ├── bot_registry.json    # Bot storage
│   ├── conversations.json   # Message history
│   └── user_session.session # Telethon session
└── test_bootstrap.py        # Telethon-based tests
```

## Common Commands

### Setup
```bash
# Install dependencies
uv sync

# Setup environment (copy from main project)
cp ../.env .env

# Activate virtual environment if needed
source .venv/bin/activate
```

### Running
```bash
# Run the bootstrap application
uv run python main.py

# Test with Telethon
uv run python test_bootstrap.py
```

### Development
```bash
# Add new dependency
uv add package_name

# Check code quality
uv run ruff check --fix src/ main.py
uv run mypy src/ main.py
```

## Environment Variables

### Required
```bash
# Telethon user client (for testing)
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here

# BotMother factory bot
BOT_MOTHER_TOKEN=your_botmother_token

# AI intelligence
AGNO_API_KEY=your_agno_api_key

# Bot tokens for spawning (at least one required)
BOT_TOKEN_1=first_available_bot_token
BOT_TOKEN_2=second_available_bot_token
```

### Optional
```bash
# Test configuration
TEST_CHAT_ID=your_test_chat_id
TEST_USER_ID=your_test_user_id
DEBUG=true
```

## Git Guidelines

### CRITICAL RULES - NEVER BREAK THESE:

- **NEVER** use `git add -A` or `git add .`
- **ALWAYS** add files explicitly: `git add specific_file.py`
- **ALWAYS** check `git status` and `git diff --staged` before committing
- **NEVER** put credentials, API keys, or tokens in code
- **ALWAYS** use environment variables for sensitive data

### Commit Messages
- Keep messages clean and professional
- Focus on what changed and why
- NO AI attribution in commit messages

## Success Criteria

### Step 0 Success
- Telethon session authenticates successfully
- Can send test message via Telethon
- Session persists between runs

### Step 1 Success
- BotMother responds to `/start` command
- Telethon test can send message TO BotMother and receive response
- Message history is maintained

### Step 2 Success
- BotMother can create new bot using available token
- Created bot responds to basic commands
- Telethon can test created bot independently

### Step 3 Success
- BotMother has intelligent conversations using Agno
- Context is maintained across conversation
- Natural language bot creation works

### Step 4 Success
- Spawned bots are intelligent (not just echo bots)
- Each bot has distinct personality/role
- All bots tested and validated via Telethon

## Development Philosophy

### Progressive Development
1. Build one component at a time
2. Test immediately with Telethon
3. Only proceed after current step is validated
4. Keep codebase minimal and clean

### Testing First
- Telethon testing is not optional
- Test every feature as it's built
- Real user interactions must work
- Follow the testing protocol exactly

### Simplicity Over Features
- Focus on core functionality only
- Avoid feature creep from main project
- Keep dependencies minimal
- Prefer simple solutions

## What We're NOT Building

- Complex OpenServ integration
- FastAPI web servers
- PostgreSQL databases
- Docker containers
- Monitoring dashboards
- Rate limiting systems (initially)
- Complex error channels
- Multi-bot token pools (initially)

The bootstrap MVP focuses on the essential core: intelligent bot creation and testing.