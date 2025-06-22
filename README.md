# Mini-Mancer 🤖

**Sophisticated AI Bot Creation System**

Mini-Mancer is a Python-based AI bot factory that creates intelligent Telegram bots through a sophisticated OpenServ → Agno → Telegram integration. It features BotMother, an enhanced GPT-4o factory bot that can create both instant bots and architecturally sophisticated bots with comprehensive requirements gathering.

## 🏗️ Architecture

```
OpenServ ↔ FastAPI ↔ Agno-AGI ↔ Telegram
    ↓           ↓         ↓          ↓
 Workflows   API Layer  Intelligence  Bots
```

- **OpenServ Integration**: Workflow automation and task processing
- **Agno Framework**: Core AI intelligence with GPT-4o
- **Dual Bot System**: BotMother (factory) + dynamically created bots
- **All-Polling Architecture**: No webhooks, pure polling for reliability

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- uv (package manager)
- PostgreSQL (optional, dockerized)
- Telegram Bot Token(s)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd mini-mancer

# Install dependencies
uv sync

# Setup environment
cp .env.example .env
# Edit .env with your tokens and configuration

# Run with Docker (recommended)
docker compose up -d

# Or run directly
uv run python main.py
```

### Environment Variables

```bash
# Required
BOT_TOKEN=your_telegram_bot_token_here
BOT_TOKEN_1=second_bot_token_for_created_bots
OPENAI_API_KEY=your_openai_api_key
AGNO_API_KEY=your_agno_api_key

# Optional
BOT_MOTHER_TOKEN=specific_botmother_token
OPENSERV_API_KEY=your_openserv_api_key
OPENSERV_URL=http://localhost:8080
DEMO_USER=your_telegram_user_id
ERROR_CHANNEL_ID=your_telegram_error_channel_id
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/postgres
```

See `.env.example` for complete configuration documentation.

## ✨ Features

### BotMother Factory Bot
- **Enhanced GPT-4o Intelligence**: Upgraded from basic models
- **Dual Creation Modes**: Instant creation + sophisticated architect mode
- **Advanced Requirements Gathering**: Comprehensive interview process
- **Thinking Tools**: Structured reasoning and analysis capabilities
- **Quality Assurance**: Validation and testing before deployment

### Bot Creation System
- **Instant Mode**: Quick bot creation with magic buttons (preserves original functionality)
- **Architect Mode**: Sophisticated bots with full requirements analysis
- **12 Personality Traits**: Analytical, empathetic, creative, professional, etc.
- **Communication Styles**: Formal, casual, technical, friendly, concise
- **Quality Scoring**: 0-100% validation of bot specifications
- **Tool Integration**: Strategic selection from 10+ available tools

### OpenServ Integration
- **8+ API Endpoints**: Complete workflow integration
- **Bidirectional Testing**: Connection verification both ways
- **Bot Compilation Pipeline**: Multi-stage bot creation and testing
- **Task Processing**: Automated workflow execution
- **Health Monitoring**: System status and performance tracking

### Testing & Quality Assurance
- **Comprehensive Test Framework**: 49+ automated tests for all system components
- **Real Telegram API Testing**: Validates actual bot interactions and workflows
- **Performance Monitoring**: Memory usage, response times, and concurrency metrics
- **Mock Testing Support**: CI/CD friendly testing without external dependencies
- **Automated Validation**: Bot personality, tool integration, and error handling tests

### Error Monitoring & Debugging
- **Telegram Error Channel**: Real-time error notifications with full context and tracebacks
- **Centralized Error Handling**: @safe_telegram_operation decorator for clean error management
- **Rich Error Context**: User ID, chat ID, operation details, and system state in every error
- **User-Friendly Responses**: Clean error messages for users while detailed logs go to developers
- **System Monitoring**: Automatic memory, CPU, and bot state reporting in error logs

### Test Monitoring & Rate Limiting
- **Real-Time Test Dashboard**: WebSocket-based monitoring at `/test-monitor`
- **Live Agent Interactions**: See bot messages, AI responses, and API calls in real-time
- **Global Rate Limiting**: Token bucket algorithm prevents Telegram API limits
- **Test Channel Logging**: Auto-setup for Telegram test logging channels
- **API Call Monitoring**: Track all Telegram API calls with rate limiting

## 🔗 API Endpoints

### Core Integration
- `POST /openserv/do_task` - Process OpenServ tasks
- `POST /openserv/respond_chat_message` - Handle chat messages
- `POST /openserv/compile_bot` - Sophisticated bot compilation

### Bot Management
- `GET /openserv/available_tools` - List available bot tools
- `GET /openserv/compilation_status/{id}` - Check compilation progress

### System Health
- `GET /health` - Health check for OpenServ → Mini-Mancer
- `POST /openserv/test_connection` - Test Mini-Mancer → OpenServ
- `POST /openserv/ping` - Ping/pong connectivity test

## 📱 Usage Examples

### Instant Bot Creation
```
/start
[Click "🤖 Helpful Assistant" button]
✨ Bot created and deployed instantly
```

### Custom Bot Creation
```
User: "Create a sophisticated customer service bot"
BotMother: "I sense the need for something special... tell me about your specific requirements..."
[Comprehensive requirements gathering process]
✨ Architect mode creates sophisticated bot with full validation
```

### OpenServ Workflow
```bash
curl -X POST http://localhost:14159/openserv/compile_bot \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": {...},
    "user_id": "12345",
    "compilation_mode": "standard"
  }'
```

## 🛠️ Development

### Project Structure
```
mini-mancer/
├── src/
│   ├── models/
│   │   ├── agent_dna.py          # Bot personality system
│   │   └── bot_requirements.py   # Requirements & validation
│   ├── agents/
│   │   └── telegram_bot_template.py  # Bot implementation
│   ├── prompts/
│   │   └── botmother_prompts.py  # Modular prompt system
│   ├── tools/
│   │   └── thinking_tool.py      # Advanced reasoning
│   ├── prototype_agent.py        # Main integration layer
│   └── bot_compilation_pipeline.py  # Quality assurance
├── main.py                       # Entry point
├── docker-compose.yaml          # Infrastructure
└── pyproject.toml              # Dependencies
```

### Key Dependencies
- `agno>=0.5.50` - Core AI framework
- `fastapi>=0.115.13` - API layer
- `python-telegram-bot>=22.1` - Telegram integration
- `openai>=1.0.0` - GPT-4o model access
- `pydantic>=2.11.7` - Data validation
- `psycopg[binary]>=3.0.0` - PostgreSQL connectivity

### Development Commands
```bash
# Development mode
uv run python main.py

# Add dependencies
uv add package_name

# Database (with Docker)
docker compose up postgres -d

# View logs
docker compose logs -f mini-mancer

# Testing
PYTHONPATH=. uv run pytest                    # Run all tests
PYTHONPATH=. uv run pytest -m "not network"   # Run without API calls
PYTHONPATH=. uv run pytest -m factory_bot     # Run factory bot tests
uv run python test_framework_demo.py          # Demo testing framework
```

## 🧪 Testing Framework

Mini-Mancer includes a comprehensive automated testing framework that validates bot creation, deployment, and interaction using real Telegram API calls.

### Test Coverage
- **Factory Bot Tests** (15 tests) - Bot creation commands, inline keyboards, error handling
- **Created Bot Tests** (17 tests) - Personality validation, tool integration, AI responses  
- **Integration Tests** (8 tests) - End-to-end workflows, API integration, system resilience
- **Performance Tests** (9 tests) - Concurrency, memory management, stress testing

### Quick Testing
```bash
# Install test dependencies
uv sync

# Run all tests (requires bot tokens)
PYTHONPATH=. uv run pytest

# Run non-network tests (no tokens needed)
PYTHONPATH=. uv run pytest -m "not network"

# Run specific test categories
PYTHONPATH=. uv run pytest -m factory_bot      # Factory bot functionality
PYTHONPATH=. uv run pytest -m created_bot      # Individual bot validation
PYTHONPATH=. uv run pytest -m integration      # End-to-end workflows
PYTHONPATH=. uv run pytest -m performance      # Performance & stress tests

# Demo the testing framework
uv run python test_framework_demo.py

# Set up test monitoring channel
uv run python -c "from src.telegram_channel_manager import test_channel_setup; import asyncio; asyncio.run(test_channel_setup())"
```

### Test Environment Setup
```bash
# Required for network tests (add to .env)
BOT_TOKEN=your_factory_bot_token
BOT_TOKEN_1=your_created_bot_token  
TEST_CHAT_ID=your_test_chat_id
TEST_USER_ID=your_test_user_id

# Test markers for selective testing
pytest -m "slow"           # Long-running tests
pytest -m "mock"           # Mock tests (no API calls)
pytest -m "api"            # API integration tests
pytest -m "unit"           # Unit tests only
```

### Framework Features
- **Real Telegram API Testing** - Validates actual bot interactions and message flows
- **Mock Testing Support** - CI/CD friendly testing without external dependencies
- **Performance Monitoring** - Memory usage, response times, and concurrency metrics
- **Automated Cleanup** - Resource management and test isolation
- **49+ Test Cases** - Comprehensive validation of all system components
- **Parallel Execution** - Run tests concurrently with `pytest -n auto`

### Test Structure
```
tests/
├── conftest.py              # Core fixtures and session management
├── test_factory_bot.py      # Factory bot functionality tests
├── test_created_bots.py     # Individual bot validation tests
├── test_integration.py      # End-to-end workflow tests
├── test_performance.py      # Performance and stress tests
├── test_utils.py           # Test utilities and helpers
├── pytest.ini             # Test configuration
└── README.md              # Detailed testing documentation
```

**See [tests/README.md](./tests/README.md) for detailed testing documentation, troubleshooting, and advanced usage.**

## 🔬 Test Monitoring Dashboard

Mini-Mancer includes a real-time monitoring dashboard for observing bot interactions during testing and development.

### Accessing the Dashboard
```bash
# Start Mini-Mancer
uv run python main.py

# Open monitoring dashboard in browser
# Visit: http://localhost:14159/test-monitor
```

### Dashboard Features
- **Real-Time Events**: Live WebSocket stream of all bot interactions
- **Event Types**: API calls, bot messages, AI responses, errors, test events
- **Color-Coded Events**: Different colors for different event types
- **Event Filtering**: Filter by event type or search specific content
- **Connection Status**: Shows WebSocket connection and active monitoring

### Event Types
- 🔵 **API Call**: Telegram Bot API calls with rate limiting
- 🟠 **Bot Message**: Messages sent by bots to users
- 🟢 **AI Response**: AI-generated responses from agents
- 🔴 **Error**: Errors and exceptions with full context
- 🟡 **Test Start**: Beginning of automated tests
- 🟣 **Test End**: Test completion with results

### Rate Limiting
All Telegram API calls are automatically rate-limited to prevent hitting API limits:
- **20 requests/second** per bot (configurable via `TELEGRAM_RATE_LIMIT`)
- **Token bucket algorithm** with automatic backoff
- **Per-bot tracking** to handle multiple simultaneous bots
- **Monitoring integration** to log all rate-limited calls

## ⚙️ Configuration

### Bot Personalities
- **Analytical**: Data-driven, methodical responses
- **Empathetic**: Understanding, supportive interactions
- **Creative**: Innovative, imaginative solutions
- **Professional**: Formal, business-appropriate tone
- **Humorous**: Light-hearted, entertaining responses

### Available Tools
- Weather Oracle, Wisdom Dispenser, Dice Commander
- Time Guardian, Calculator Sage, Memory Keeper
- Web Searcher, Code Assistant, Language Tutor
- Creative Writer (10+ tools total)

### Quality Levels
- **Simple**: Basic bot creation (70-80% quality)
- **Standard**: Moderate requirements (80-90% quality)
- **Complex**: Full architect mode (90-95% quality)
- **Enterprise**: Maximum sophistication (95-100% quality)

## 📊 System Status

**Current Version**: 1.0.0-prerelease  
**Architecture**: All-polling, no webhooks  
**Model**: GPT-4o with advanced reasoning  
**Status**: Production-ready with sophisticated features  

## 🔧 Troubleshooting

### Common Issues
1. **Bot not responding**: Check token configuration and network connectivity
2. **OpenServ connection failed**: Verify OPENSERV_URL and API key
3. **Database errors**: Ensure PostgreSQL is running (`docker compose up postgres -d`)
4. **Creation timeout**: Bot compilation may take 2-3 minutes for complex bots
5. **Test import errors**: Ensure `PYTHONPATH=.` is set when running tests
6. **Test network failures**: Verify bot tokens and test chat IDs are configured
7. **Pytest scope errors**: Use function-scoped fixtures for async tests
8. **Missing error visibility**: Set up ERROR_CHANNEL_ID for real-time error monitoring

### Debug Mode
```bash
# Enable verbose logging
export DEBUG=1
uv run python main.py

# Debug testing framework
PYTHONPATH=. uv run pytest -vvv -s --tb=long
PYTHONPATH=. uv run pytest --collect-only  # Check test discovery
uv run python test_framework_demo.py       # Validate framework setup
```

## 🩺 Health Checks

```bash
# Check Mini-Mancer status
curl http://localhost:14159/health

# Test OpenServ connection
curl -X POST http://localhost:14159/openserv/test_connection

# Verify bot creation
curl http://localhost:14159/openserv/available_tools
```

## 📚 Documentation

- [Architecture Analysis](./ARCHITECTURE_ANALYSIS.md) - Detailed operational semantics
- [CLAUDE.md](./CLAUDE.md) - Development guidelines and coding standards
- [Testing Framework](./tests/README.md) - Comprehensive testing documentation and troubleshooting

## 📄 License

MIT License - See LICENSE file for details.

---

**Built with ❤️ using Agno, FastAPI, and advanced AI reasoning**