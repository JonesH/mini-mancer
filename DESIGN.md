# Mini-Mancer: AI Agent Factory for Telegram Mini App Creation

## Project Overview

**Core Concept**: Conversational AI agent factory that spawns specialized agents to create Telegram Mini Apps through natural language interaction. Users describe their desired bot/Mini App, and the system generates, deploys, and configures everything automatically.

**Key Innovation**: Local agent spawning with Pydantic-AI + MCP integration, eliminating platform dependencies while maintaining type safety and reliable API access.

## Architecture

### High-Level Flow
```
User → Factory Agent → Requirements Gathering → Agent DNA Generation → 
Local Agent Spawn → Telegram Bot Setup → Mini App Deployment → Working Bot
```

### Core Components
1. **FactoryAgent**: Conversational interface for requirements gathering and agent orchestration
2. **AgentTemplate**: Dynamic agent code generation system
3. **TelegramMCP**: MCP server for Telegram Bot API operations
4. **ProcessManager**: Agent lifecycle management and port allocation
5. **AgentRegistry**: JSON file-based state tracking with storage abstraction
6. **WebInterface**: Management dashboard and user interaction

## Technology Stack

### Core Dependencies
```toml
dependencies = [
    "pydantic-ai-slim[mcp]>=0.2.19",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "aiofiles>=23.2.0",
    "jinja2>=3.1.0",  # Template generation
    "psutil>=5.9.0",  # Process management
]
```

### MCP Server Requirements
- Node.js runtime for Telegram MCP server
- Telegram Bot API access
- Webhook handling capabilities

## Data Models

### Core Types
```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Any
from datetime import datetime

class AgentStatus(Enum):
    CREATING = "creating"
    RUNNING = "running" 
    STOPPED = "stopped"
    ERROR = "error"

class MiniAppFeature(Enum):
    FORM = "form"
    POLL = "poll"
    GAME = "game"
    CALCULATOR = "calculator"
    WEATHER = "weather"
    CUSTOM = "custom"

class AgentDNA(BaseModel):
    """Complete agent specification for generation"""
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")
    purpose: str = Field(..., max_length=500)
    personality_traits: list[str] = Field(default_factory=list)
    mini_app_features: list[MiniAppFeature]
    system_prompt: str
    bot_username: str = Field(..., pattern=r"^[a-zA-Z0-9_]+$")
    bot_token: str = Field(..., exclude=True)  # Never serialize
    port: int = Field(..., ge=8000, le=9999)
    endpoint_url: str
    model: str = "anthropic:claude-3-5-haiku-latest"
    created_at: datetime = Field(default_factory=datetime.now)

class AgentProcess(BaseModel):
    """Running agent process information"""
    agent_id: str
    dna: AgentDNA
    pid: int | None = None
    status: AgentStatus = AgentStatus.CREATING
    health_url: str
    last_heartbeat: datetime | None = None
    error_message: str | None = None

class ConversationState(BaseModel):
    """Factory agent conversation tracking"""
    user_id: str
    stage: str = "greeting"  # greeting, purpose, features, personality, confirmation
    collected_data: dict[str, Any] = Field(default_factory=dict)
    agent_dna: AgentDNA | None = None
    created_agent_id: str | None = None

class TelegramWebhook(BaseModel):
    """Telegram webhook payload"""
    update_id: int
    message: dict[str, Any] | None = None
    callback_query: dict[str, Any] | None = None
```

## Component Specifications

### 1. FactoryAgent (`src/factory/agent.py`)
```python
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio

class FactoryAgent:
    def __init__(self):
        self.telegram_mcp = MCPServerStdio('node', 
            args=['telegram-mcp-server.js'], tool_prefix='tg')
        
        self.agent = Agent(
            'anthropic:claude-3-5-haiku-latest',
            deps_type=ConversationState,
            output_type=str,
            system_prompt=self._get_system_prompt(),
            mcp_servers=[self.telegram_mcp]
        )
        
        self._register_tools()
    
    def _get_system_prompt(self) -> str:
        return """You are Mini-Mancer, an AI agent factory specialist.
        Your job: Create custom Telegram bots through conversation.
        
        Process:
        1. Greet user, explain capabilities
        2. Gather bot purpose and requirements  
        3. Determine Mini App features needed
        4. Define personality traits
        5. Confirm specifications
        6. Generate and deploy agent
        
        Be conversational, ask focused questions, confirm understanding."""
    
    @agent.tool
    async def gather_requirements(self, ctx: RunContext[ConversationState], 
                                user_input: str) -> str:
        """Process user input and advance conversation state"""
        # Implementation handles conversation flow
        
    @agent.tool  
    async def generate_agent(self, ctx: RunContext[ConversationState]) -> str:
        """Generate agent DNA and spawn new agent process"""
        # Implementation creates AgentDNA and calls ProcessManager
```

### 2. AgentTemplate (`src/template/generator.py`)
```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

class AgentGenerator:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader('templates'))
    
    def generate_agent_code(self, dna: AgentDNA) -> str:
        """Generate complete agent Python file from DNA"""
        template = self.env.get_template('agent_template.py.j2')
        return template.render(
            name=dna.name,
            purpose=dna.purpose, 
            system_prompt=dna.system_prompt,
            bot_token=dna.bot_token,
            port=dna.port,
            features=dna.mini_app_features,
            personality=dna.personality_traits
        )
    
    def generate_mini_app_html(self, dna: AgentDNA) -> str:
        """Generate Mini App HTML template"""
        template = self.env.get_template('mini_app_template.html.j2')
        return template.render(
            app_name=dna.name,
            features=dna.mini_app_features,
            bot_username=dna.bot_username
        )
    
    async def create_agent_files(self, dna: AgentDNA) -> Path:
        """Create complete agent directory structure"""
        agent_dir = Path(f"agents/{dna.name}")
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate and write agent code
        agent_code = self.generate_agent_code(dna)
        (agent_dir / "agent.py").write_text(agent_code)
        
        # Generate and write Mini App HTML
        mini_app_html = self.generate_mini_app_html(dna)
        (agent_dir / "mini_app.html").write_text(mini_app_html)
        
        # Create requirements.txt
        (agent_dir / "requirements.txt").write_text(
            "pydantic-ai-slim[mcp]>=0.2.19\nfastapi>=0.104.0\nuvicorn>=0.24.0"
        )
        
        return agent_dir
```

### 3. ProcessManager (`src/process/manager.py`)
```python
import asyncio
import subprocess
import psutil
from pathlib import Path

class ProcessManager:
    def __init__(self, registry: 'AgentRegistry'):
        self.registry = registry
        self.port_range = range(8000, 10000)
        self._allocated_ports: set[int] = set()
    
    def allocate_port(self) -> int:
        """Find and allocate available port"""
        for port in self.port_range:
            if port not in self._allocated_ports and self._port_available(port):
                self._allocated_ports.add(port)
                return port
        raise RuntimeError("No available ports in range 8000-9999")
    
    def _port_available(self, port: int) -> bool:
        """Check if port is available"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0
    
    async def spawn_agent(self, dna: AgentDNA) -> AgentProcess:
        """Spawn new agent process"""
        agent_dir = Path(f"agents/{dna.name}")
        
        # Start agent process
        process = await asyncio.create_subprocess_exec(
            "python", "agent.py",
            cwd=agent_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"PORT": str(dna.port), "BOT_TOKEN": dna.bot_token}
        )
        
        # Create process record
        agent_process = AgentProcess(
            agent_id=dna.name,
            dna=dna,
            pid=process.pid,
            status=AgentStatus.RUNNING,
            health_url=f"http://localhost:{dna.port}/health"
        )
        
        # Register process
        await self.registry.register_agent(agent_process)
        
        return agent_process
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop running agent process"""
        process = await self.registry.get_agent(agent_id)
        if not process or not process.pid:
            return False
            
        try:
            psutil.Process(process.pid).terminate()
            process.status = AgentStatus.STOPPED
            await self.registry.update_agent(process)
            return True
        except psutil.NoSuchProcess:
            return False
    
    async def health_check(self, agent_id: str) -> bool:
        """Check agent health via HTTP endpoint"""
        process = await self.registry.get_agent(agent_id)
        if not process:
            return False
            
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(process.health_url, timeout=5) as resp:
                    return resp.status == 200
        except:
            return False
```

### 4. Storage Abstraction & AgentRegistry (`src/registry/`)

#### Storage Interface (`src/registry/storage.py`)
```python
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar('T')

class StorageAdapter(ABC, Generic[T]):
    """Abstract storage interface for easy backend swapping"""
    
    @abstractmethod
    async def save(self, key: str, data: T) -> None:
        """Save data with given key"""
        pass
    
    @abstractmethod
    async def get(self, key: str, model_class: type[T]) -> T | None:
        """Retrieve data by key and deserialize to model"""
        pass
    
    @abstractmethod
    async def list_all(self, model_class: type[T]) -> list[T]:
        """List all entries of given model type"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete entry by key, return success"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
```

#### JSON File Implementation (`src/registry/json_storage.py`)
```python
import json
import aiofiles
from pathlib import Path
from typing import Any
from .storage import StorageAdapter, T

class JSONFileStorage(StorageAdapter[T]):
    """JSON file-based storage for MVP - easily replaceable"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Separate collections
        self.agents_dir = self.data_dir / "agents"
        self.conversations_dir = self.data_dir / "conversations"
        self.agents_dir.mkdir(exist_ok=True)
        self.conversations_dir.mkdir(exist_ok=True)
    
    def _get_file_path(self, collection: str, key: str) -> Path:
        """Get file path for collection/key"""
        if collection == "agents":
            return self.agents_dir / f"{key}.json"
        elif collection == "conversations":
            return self.conversations_dir / f"{key}.json"
        else:
            return self.data_dir / collection / f"{key}.json"
    
    async def save(self, key: str, data: T, collection: str = "agents") -> None:
        """Save data to JSON file"""
        file_path = self._get_file_path(collection, key)
        
        # Serialize using Pydantic if available, else json
        if hasattr(data, 'model_dump'):
            json_data = data.model_dump_json(indent=2)
        else:
            json_data = json.dumps(data, indent=2, default=str)
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json_data)
    
    async def get(self, key: str, model_class: type[T], collection: str = "agents") -> T | None:
        """Load and deserialize from JSON file"""
        file_path = self._get_file_path(collection, key)
        
        if not file_path.exists():
            return None
        
        async with aiofiles.open(file_path, 'r') as f:
            json_data = await f.read()
        
        # Deserialize using Pydantic if available
        if hasattr(model_class, 'model_validate_json'):
            return model_class.model_validate_json(json_data)
        else:
            return json.loads(json_data)
    
    async def list_all(self, model_class: type[T], collection: str = "agents") -> list[T]:
        """Load all entries from collection"""
        collection_dir = getattr(self, f"{collection}_dir")
        results = []
        
        for file_path in collection_dir.glob("*.json"):
            async with aiofiles.open(file_path, 'r') as f:
                json_data = await f.read()
            
            if hasattr(model_class, 'model_validate_json'):
                results.append(model_class.model_validate_json(json_data))
            else:
                results.append(json.loads(json_data))
        
        return results
    
    async def delete(self, key: str, collection: str = "agents") -> bool:
        """Delete JSON file"""
        file_path = self._get_file_path(collection, key)
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    async def exists(self, key: str, collection: str = "agents") -> bool:
        """Check if file exists"""
        return self._get_file_path(collection, key).exists()
```

#### Registry Implementation (`src/registry/agent_registry.py`)
```python
from .storage import StorageAdapter
from .json_storage import JSONFileStorage
from ..models import AgentProcess, ConversationState

class AgentRegistry:
    """Agent and conversation state management with pluggable storage"""
    
    def __init__(self, storage: StorageAdapter | None = None):
        self.storage = storage or JSONFileStorage()
    
    # Agent Management
    async def register_agent(self, process: AgentProcess) -> None:
        """Register new agent process"""
        await self.storage.save(process.agent_id, process, "agents")
    
    async def get_agent(self, agent_id: str) -> AgentProcess | None:
        """Retrieve agent process by ID"""
        return await self.storage.get(agent_id, AgentProcess, "agents")
    
    async def update_agent(self, process: AgentProcess) -> None:
        """Update existing agent process"""
        await self.storage.save(process.agent_id, process, "agents")
    
    async def list_agents(self) -> list[AgentProcess]:
        """List all registered agents"""
        return await self.storage.list_all(AgentProcess, "agents")
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete agent record"""
        return await self.storage.delete(agent_id, "agents")
    
    # Conversation Management
    async def save_conversation(self, conversation: ConversationState) -> None:
        """Save conversation state"""
        await self.storage.save(conversation.user_id, conversation, "conversations")
    
    async def get_conversation(self, user_id: str) -> ConversationState | None:
        """Retrieve conversation state"""
        return await self.storage.get(user_id, ConversationState, "conversations")
    
    async def list_conversations(self) -> list[ConversationState]:
        """List all conversations"""
        return await self.storage.list_all(ConversationState, "conversations")
    
    async def delete_conversation(self, user_id: str) -> bool:
        """Delete conversation state"""
        return await self.storage.delete(user_id, "conversations")
```

### 5. WebInterface (`src/web/app.py`)
```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    app.state.factory_agent = FactoryAgent()
    app.state.process_manager = ProcessManager(AgentRegistry())
    app.state.agent_generator = AgentGenerator()
    
    # Start factory agent MCP servers
    async with app.state.factory_agent.agent.run_mcp_servers():
        yield
    
    # Shutdown - stop all agent processes
    agents = await app.state.process_manager.registry.list_agents()
    for agent in agents:
        if agent.status == AgentStatus.RUNNING:
            await app.state.process_manager.stop_agent(agent.agent_id)

app = FastAPI(title="Mini-Mancer", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard"""
    return """
    <html><head><title>Mini-Mancer</title></head>
    <body>
        <h1>Mini-Mancer: AI Agent Factory</h1>
        <div id="chat"></div>
        <input id="user-input" placeholder="Describe the bot you want to create...">
        <button onclick="sendMessage()">Send</button>
        <script src="/static/dashboard.js"></script>
    </body></html>
    """

@app.post("/api/chat")
async def chat_endpoint(message: str, user_id: str = "default"):
    """Main chat interface for factory agent"""
    factory_agent = app.state.factory_agent
    
    # Get or create conversation state
    registry = app.state.process_manager.registry
    conversation = await registry.get_conversation(user_id) or ConversationState(user_id=user_id)
    
    # Process message through factory agent
    async with factory_agent.agent.run_mcp_servers():
        result = await factory_agent.agent.run(message, deps=conversation)
    
    # Update conversation state
    await registry.save_conversation(conversation)
    
    return {"response": result.output, "stage": conversation.stage}

@app.get("/api/agents")
async def list_agents():
    """List all created agents"""
    agents = await app.state.process_manager.registry.list_agents()
    return [
        {
            "id": agent.agent_id,
            "name": agent.dna.name,
            "status": agent.status.value,
            "bot_username": agent.dna.bot_username,
            "endpoint": agent.dna.endpoint_url,
            "features": [f.value for f in agent.dna.mini_app_features]
        } for agent in agents
    ]

@app.post("/api/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Stop running agent"""
    success = await app.state.process_manager.stop_agent(agent_id)
    if not success:
        raise HTTPException(404, "Agent not found or already stopped")
    return {"status": "stopped"}

@app.get("/api/agents/{agent_id}/health")
async def agent_health(agent_id: str):
    """Check agent health"""
    healthy = await app.state.process_manager.health_check(agent_id)
    return {"healthy": healthy}

# Webhook endpoint for Telegram (used by spawned agents)
@app.post("/webhook/{agent_id}")
async def telegram_webhook(agent_id: str, webhook: TelegramWebhook):
    """Telegram webhook handler - proxy to specific agent"""
    agent = await app.state.process_manager.registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    
    # Forward webhook to agent
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://localhost:{agent.dna.port}/webhook",
            json=webhook.model_dump()
        ) as resp:
            return await resp.json()
```

## File Structure

```
mini-mancer/
├── src/
│   ├── __init__.py
│   ├── factory/
│   │   ├── __init__.py
│   │   └── agent.py              # FactoryAgent implementation
│   ├── template/
│   │   ├── __init__.py
│   │   └── generator.py          # Agent code generation
│   ├── process/
│   │   ├── __init__.py
│   │   └── manager.py            # Process lifecycle management
│   ├── registry/
│   │   ├── __init__.py
│   │   ├── storage.py            # Storage abstraction interface
│   │   ├── json_storage.py       # JSON file implementation
│   │   ├── agent_registry.py     # Registry with pluggable storage
│   │   └── future_adapters/      # Future storage implementations
│   │       ├── mongo_storage.py  # MongoDB adapter (future)
│   │       └── sql_storage.py    # SQLModel/SQLAlchemy adapter (future)
│   ├── web/
│   │   ├── __init__.py
│   │   └── app.py                # FastAPI web interface
│   └── models.py                 # Pydantic data models
├── templates/
│   ├── agent_template.py.j2      # Generated agent template
│   └── mini_app_template.html.j2 # Mini App HTML template
├── mcp_servers/
│   ├── telegram_bot_mcp/         # Telegram MCP server
│   │   ├── package.json
│   │   ├── telegram-mcp-server.js
│   │   └── README.md
│   └── README.md
├── agents/                       # Generated agent directories
├── data/                         # JSON storage directory
│   ├── agents/                   # Agent JSON files
│   └── conversations/            # Conversation state files
├── static/
│   ├── dashboard.js              # Frontend JavaScript
│   └── style.css                 # Dashboard styling
├── main.py                       # Application entry point
├── pyproject.toml
└── README.md
```

## Implementation Flow

### Phase 1: Core Infrastructure
1. **Setup project structure** - Create directories, basic files
2. **Implement data models** - Pydantic models in `src/models.py`
3. **Create agent registry** - JSON file-based state management with storage abstraction
4. **Build process manager** - Agent spawning and lifecycle

### Phase 2: Template System
1. **Create Jinja2 templates** - Agent and Mini App generation
2. **Implement AgentGenerator** - Code generation from AgentDNA
3. **Test template generation** - Verify working agent output

### Phase 3: Factory Agent
1. **Build FactoryAgent** - Conversational requirements gathering
2. **Implement conversation flow** - Multi-stage requirement collection
3. **Integrate with process manager** - Agent spawning from conversation

### Phase 4: MCP Integration
1. **Setup Telegram MCP server** - Node.js server for Bot API
2. **Test MCP connectivity** - Verify Pydantic-AI can call Telegram API
3. **Implement bot configuration** - Set menu buttons, webhooks

### Phase 5: Web Interface
1. **Create FastAPI app** - Dashboard and API endpoints
2. **Build frontend** - JavaScript chat interface
3. **Add agent management** - Start/stop/monitor agents

### Phase 6: Integration & Testing
1. **End-to-end testing** - Full workflow from conversation to working bot
2. **Error handling** - Robust failure recovery
3. **Performance optimization** - Resource management, scaling

## MCP Server Specification

### Telegram MCP Server (`mcp_servers/telegram_bot_mcp/telegram-mcp-server.js`)

**Required Tools:**
- `tg_sendMessage`: Send message to chat
- `tg_setChatMenuButton`: Set bot menu button with Mini App
- `tg_setWebhook`: Configure webhook URL
- `tg_createInlineKeyboard`: Create inline keyboard with web_app buttons
- `tg_answerWebAppQuery`: Handle Mini App queries

**Environment Variables:**
- `BOT_TOKEN`: Telegram bot token
- `WEBHOOK_URL`: Base webhook URL for the agent

## Generated Agent Template

### Structure (`templates/agent_template.py.j2`)
```python
# Auto-generated agent: {{ name }}
# Purpose: {{ purpose }}

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio
from fastapi import FastAPI, Request
from typing import Any

class {{ name|title }}Agent:
    def __init__(self):
        self.telegram_mcp = MCPServerStdio('node', 
            args=['../../mcp_servers/telegram_bot_mcp/telegram-mcp-server.js'], 
            tool_prefix='tg')
        
        self.agent = Agent(
            'anthropic:claude-3-5-haiku-latest',
            system_prompt="""{{ system_prompt }}
            
            Personality traits: {{ personality|join(', ') }}
            Available Mini App features: {{ features|join(', ') }}
            
            You can use Mini App features to create interactive experiences.
            When users request actions, use the appropriate tools to respond.""",
            mcp_servers=[self.telegram_mcp]
        )
        
        self.bot_token = "{{ bot_token }}"
        self.app = FastAPI()
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.post("/webhook")
        async def webhook(request: Request):
            update = await request.json()
            return await self.handle_update(update)
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy", "agent": "{{ name }}"}
        
        @self.app.get("/mini_app")
        async def mini_app():
            with open("mini_app.html") as f:
                return HTMLResponse(f.read())
    
    async def handle_update(self, update: dict[str, Any]) -> dict[str, Any]:
        """Process Telegram update"""
        message = update.get('message', {})
        text = message.get('text', '')
        chat_id = message.get('chat', {}).get('id')
        
        if not text or not chat_id:
            return {"ok": True}
        
        # Process message through agent
        async with self.agent.run_mcp_servers():
            result = await self.agent.run(text)
        
        # Send response back to Telegram
        await self.send_response(chat_id, result.output)
        return {"ok": True}
    
    async def send_response(self, chat_id: int, text: str):
        """Send response via Telegram MCP"""
        # Implementation uses MCP tools to send message
        pass

# Entry point
if __name__ == "__main__":
    import uvicorn
    import os
    
    agent = {{ name|title }}Agent()
    port = int(os.getenv("PORT", {{ port }}))
    
    uvicorn.run(agent.app, host="0.0.0.0", port=port)
```

## Storage Migration Examples

### Future MongoDB Implementation (`src/registry/future_adapters/mongo_storage.py`)
```python
from motor.motor_asyncio import AsyncIOMotorClient
from ..storage import StorageAdapter, T

class MongoStorage(StorageAdapter[T]):
    """MongoDB storage adapter - drop-in replacement for JSON storage"""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017", db_name: str = "mini_mancer"):
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client[db_name]
    
    async def save(self, key: str, data: T, collection: str = "agents") -> None:
        """Save to MongoDB collection"""
        coll = self.db[collection]
        doc = data.model_dump() if hasattr(data, 'model_dump') else data
        doc["_id"] = key
        await coll.replace_one({"_id": key}, doc, upsert=True)
    
    async def get(self, key: str, model_class: type[T], collection: str = "agents") -> T | None:
        """Get from MongoDB collection"""
        coll = self.db[collection]
        doc = await coll.find_one({"_id": key})
        if not doc:
            return None
        doc.pop("_id")  # Remove MongoDB ID
        return model_class.model_validate(doc) if hasattr(model_class, 'model_validate') else doc
    
    # ... other methods similar pattern
```

### Future SQLModel Implementation (`src/registry/future_adapters/sql_storage.py`)
```python
from sqlmodel import create_engine, Session, select
from ..storage import StorageAdapter, T

class SQLModelStorage(StorageAdapter[T]):
    """SQLModel storage adapter - drop-in replacement for JSON storage"""
    
    def __init__(self, connection_string: str = "sqlite:///agents.db"):
        self.engine = create_engine(connection_string)
    
    async def save(self, key: str, data: T, collection: str = "agents") -> None:
        """Save to SQL table"""
        with Session(self.engine) as session:
            # Convert Pydantic model to SQLModel table model
            if collection == "agents":
                table_model = AgentProcessTable.model_validate(data.model_dump())
            # ... handle other collections
            session.merge(table_model)
            session.commit()
    
    # ... other methods
```

### Easy Migration Pattern
```python
# Current MVP setup
registry = AgentRegistry(JSONFileStorage())

# Future MongoDB migration - one line change!
# registry = AgentRegistry(MongoStorage("mongodb://prod-server:27017"))

# Future SQL migration - one line change!
# registry = AgentRegistry(SQLModelStorage("postgresql://..."))
```

## Deployment Considerations

### Process Management
- **Port Allocation**: Dynamic port assignment from 8000-9999 range
- **Health Monitoring**: HTTP health checks every 30 seconds
- **Process Supervision**: Automatic restart on failure
- **Resource Limits**: Memory and CPU constraints per agent

### Security
- **Bot Token Isolation**: Tokens never serialized or logged
- **Webhook Validation**: Telegram webhook signature verification
- **Rate Limiting**: Per-agent request rate limits
- **Input Sanitization**: All user inputs validated and sanitized

### Scalability
- **Horizontal Scaling**: Multiple factory agents on different ports
- **Database Connection Pooling**: SQLite with connection management
- **Static File Serving**: CDN for Mini App assets
- **Load Balancing**: Nginx proxy for agent distribution

### Monitoring
- **Agent Metrics**: Response times, error rates, uptime
- **Resource Usage**: CPU, memory, network per agent
- **Business Metrics**: Agents created, success rate, user satisfaction
- **Alerting**: Slack/email notifications for failures

## Success Metrics

### Technical KPIs
- Agent creation time < 30 seconds
- Agent uptime > 99%
- Response time < 2 seconds
- Memory usage < 100MB per agent

### User Experience KPIs  
- Conversation completion rate > 80%
- User satisfaction score > 4.5/5
- Time to working bot < 5 minutes
- Support ticket rate < 5%

## Storage Abstraction Benefits

### MVP Advantages
- **Zero External Dependencies**: JSON files work anywhere, no database setup required
- **Human Readable**: Easy debugging - just open `data/agents/agent_id.json` in any editor
- **Git Friendly**: State changes can be tracked in version control if needed
- **Instant Setup**: No connection strings, no server processes, just works
- **Type Safe**: Full Pydantic validation on every read/write operation

### Production Migration Path
- **One Line Changes**: Swap storage backend without touching business logic
- **Gradual Migration**: Test new storage adapters in staging while keeping JSON in development
- **A/B Testing**: Run different storage backends for different agent collections
- **Rollback Safety**: Keep JSON as backup while transitioning to production storage

### Future Flexibility
```python
# Development
registry = AgentRegistry(JSONFileStorage("./data"))

# Staging with MongoDB
registry = AgentRegistry(MongoStorage("mongodb://staging:27017"))

# Production with PostgreSQL + SQLModel
registry = AgentRegistry(SQLModelStorage("postgresql://prod-db:5432/mini_mancer"))

# Multi-tenant with collection prefixes
registry = AgentRegistry(MongoStorage("mongodb://prod:27017", db_name=f"tenant_{tenant_id}"))
```

This design provides a complete roadmap for implementing Mini-Mancer as a production-ready AI agent factory for Telegram Mini App creation, with a storage architecture that scales from MVP to enterprise.
