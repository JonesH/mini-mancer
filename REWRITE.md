# Mini-Mancer Rewrite Plan

## Current State
- `bot_factory_agent.py`: 1615 lines of complex pydantic-ai code
- Multiple broken/unused components sending JSON to Telegram users
- Complex MCP setup that doesn't work properly
- Duplicate functionality across multiple files

## Architecture Decision: Switch to Agno-AGI

### Why Agno-AGI over Pydantic-AI:
- **Simpler API**: Much cleaner agent creation and tool integration
- **Platform Integration**: Native support for multiple platforms (Telegram, Slack, etc.)
- **Better OpenServ Alignment**: Designed for platform deployment patterns
- **Model Flexibility**: OpenAI, Claude, Groq, Ollama, xAI support
- **Built-in Storage**: SQLite storage, vector databases, RAG capabilities

## Planned Deletions
1. **DELETE**: `src/telegram_client.py` (48 lines, unused - no imports found)
2. **DELETE**: `src/factory/openserv_client.py` (296 lines, mock/unused code)
3. **REWRITE**: `src/factory/bot_factory_agent.py` (1615 → ~300 lines)

**Total Reduction**: ~1900 lines deleted, ~300 lines of clean code added

## Critical Integration Challenge: Endpoint Conflicts

### Competing Requirements:
- **Telegram**: Expects `/webhook` or `/telegram_webhook` (POST)
- **OpenServ**: Expects `/do_task` and `/respond_chat_message` (POST)  
- **Agno-AGI**: May expect its own endpoints/port

### Solution: Single FastAPI App with Route Prefixes
```python
# Single app with path-based routing
@app.post("/telegram/webhook")      # Telegram webhooks
@app.post("/openserv/do_task")      # OpenServ task processing
@app.post("/openserv/respond_chat_message")  # OpenServ chat
```

## New Architecture

### PrototypeAgent Integration:
```python
class PrototypeAgent:
    def __init__(self):
        # Single FastAPI app for all integrations
        self.app = FastAPI()
        
        # Telegram via existing TelegramBotTemplate (KEEP - it's good code)
        self.telegram_bot = TelegramBotTemplate(agent_dna, bot_token=TEST_BOT_TOKEN)
        
        # Agno-AGI for core intelligence
        self.agno_agent = Agent(model=OpenAIChat(id="gpt-4o"), tools=[...])
        
        # Route separation - no conflicts
        self._setup_routes()
```

### Components to KEEP:
- `src/agents/telegram_bot_template.py` ✅ - Quality implementation using AgentDNA
- `src/agents/__init__.py` ✅ - Clean module exports
- AgentDNA system ✅ - Proper bot specification

### Testing Strategy:
- Use `TEST_BOT_TOKEN` environment variable
- Single port (8000) with path-based routing  
- Test all three integrations independently

## Benefits:
- **90%+ code reduction** (1615 → ~300 lines)
- **No JSON in Telegram** - proper message formatting
- **OpenServ compatibility** - FastAPI pattern alignment
- **Leverages existing quality code** (TelegramBotTemplate)
- **Clean endpoint separation** - no integration conflicts