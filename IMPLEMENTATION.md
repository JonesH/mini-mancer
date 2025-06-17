# IMPLEMENTATION.md

## Revised Architecture: FactoryAgent + Platform Bridge

**Phase 1**: Local FactoryAgent (Pydantic-AI + Telegram MCP) ↔ **Phase 2**: TypeScript Platform Agents

The FactoryAgent acts as a conversational bridge between Telegram users and the OpenServ platform, handling requirements gathering and bidirectional question relay.

---

## Phase 1: FactoryAgent Core (MVP - 3 hours)

### 1. Core Data Models

```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime

class ProjectStatus(Enum):
    GATHERING = "gathering_requirements"
    SUBMITTED = "submitted_to_platform"  
    QUESTIONING = "awaiting_clarification"
    PROCESSING = "creating_agent"
    COMPLETED = "agent_ready"
    FAILED = "creation_failed"

class ConversationState(BaseModel):
    user_id: str
    chat_id: str
    stage: str = "greeting"
    requirements: Dict[str, Any] = Field(default_factory=dict)
    active_project_id: Optional[str] = None
    pending_question: Optional[str] = None

class AgentSpec(BaseModel):
    """Complete specification for agent creation"""
    name: str
    purpose: str
    personality_traits: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    target_platform: str = "telegram"
    system_prompt: str = ""

class ProjectState(BaseModel):
    project_id: str
    user_id: str
    chat_id: str
    status: ProjectStatus
    spec: AgentSpec
    platform_questions: list[str] = Field(default_factory=list)
    current_question_idx: int = 0
    agent_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
```

### 2. Platform API Client (Simple HTTP)

```python
import aiohttp
import asyncio
from typing import Dict, Any

class PlatformClient:
    """HTTP client for OpenServ-style platform API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openserv.dev"):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        self.base_url = base_url
    
    async def submit_agent_spec(self, spec: AgentSpec) -> str:
        """Submit agent specification, returns project_id"""
        try:
            async with self.session.post(
                f"{self.base_url}/v1/agents", 
                json=spec.model_dump()
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["project_id"]
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to submit spec: {e}")
    
    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get current project status and any pending questions"""
        try:
            async with self.session.get(
                f"{self.base_url}/v1/projects/{project_id}"
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to get status: {e}")
    
    async def answer_question(self, project_id: str, answer: str) -> bool:
        """Submit answer to current platform question"""
        try:
            async with self.session.post(
                f"{self.base_url}/v1/projects/{project_id}/answer",
                json={"answer": answer}
            ) as resp:
                return resp.status == 200
        except aiohttp.ClientError:
            return False
    
    async def close(self):
        await self.session.close()
```

### 3. Project Manager & Question Relay

```python
class ProjectManager:
    """Manages project lifecycle and question relay"""
    
    def __init__(self, platform_client: PlatformClient, storage_adapter):
        self.platform = platform_client
        self.storage = storage_adapter
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def create_project(self, spec: AgentSpec, user_id: str, chat_id: str) -> ProjectState:
        """Submit spec to platform and start monitoring"""
        try:
            project_id = await self.platform.submit_agent_spec(spec)
            state = ProjectState(
                project_id=project_id,
                user_id=user_id, 
                chat_id=chat_id,
                status=ProjectStatus.SUBMITTED,
                spec=spec
            )
            
            await self.storage.save(project_id, state, "projects") 
            await self._start_monitoring()
            return state
            
        except Exception as e:
            raise RuntimeError(f"Project creation failed: {e}")
    
    async def answer_current_question(self, project_id: str, answer: str) -> tuple[bool, str]:
        """Answer current question and get next question or status"""
        state = await self.storage.get(project_id, ProjectState, "projects")
        if not state or state.status != ProjectStatus.QUESTIONING:
            return False, "No active question found"
        
        success = await self.platform.answer_question(project_id, answer)
        if success:
            state.current_question_idx += 1
            await self.storage.save(project_id, state, "projects")
            
            # Check if more questions or if processing
            status_data = await self.platform.get_project_status(project_id)
            next_question = self._extract_next_question(status_data)
            
            if next_question:
                return True, f"🤔 {next_question}"
            else:
                state.status = ProjectStatus.PROCESSING
                await self.storage.save(project_id, state, "projects")
                return True, "✅ All questions answered! Creating your agent..."
        
        return False, "❌ Invalid answer. Please try again."
    
    async def _start_monitoring(self):
        """Start async monitoring of all active projects"""
        if not self._monitor_task or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def _monitor_loop(self):
        """Background monitoring of platform project status"""
        while True:
            try:
                projects = await self.storage.list_all(ProjectState, "projects")
                active_projects = [p for p in projects if p.status in {
                    ProjectStatus.SUBMITTED, ProjectStatus.PROCESSING
                }]
                
                if not active_projects:
                    await asyncio.sleep(10)
                    continue
                
                for project in active_projects:
                    try:
                        status_data = await self.platform.get_project_status(project.project_id)
                        await self._update_project_from_status(project, status_data)
                    except Exception as e:
                        project.status = ProjectStatus.FAILED
                        project.error_message = str(e)
                        await self.storage.save(project.project_id, project, "projects")
                
                await asyncio.sleep(5)  # Poll every 5 seconds
                
            except Exception as e:
                print(f"Monitor loop error: {e}")
                await asyncio.sleep(10)
    
    async def _update_project_from_status(self, project: ProjectState, status_data: Dict[str, Any]):
        """Update project state from platform status response"""
        platform_status = status_data.get("status")
        
        if platform_status == "questioning":
            questions = status_data.get("questions", [])
            if questions and project.status != ProjectStatus.QUESTIONING:
                project.platform_questions = questions
                project.current_question_idx = 0
                project.status = ProjectStatus.QUESTIONING
                # Trigger notification to user (handled by FactoryAgent)
                
        elif platform_status == "completed":
            project.status = ProjectStatus.COMPLETED
            project.agent_url = status_data.get("agent_url")
            
        elif platform_status == "failed":
            project.status = ProjectStatus.FAILED
            project.error_message = status_data.get("error", "Unknown error")
        
        await self.storage.save(project.project_id, project, "projects")
    
    def _extract_next_question(self, status_data: Dict[str, Any]) -> Optional[str]:
        """Extract next question from platform response"""
        questions = status_data.get("questions", [])
        current_idx = status_data.get("current_question_index", 0)
        
        if current_idx < len(questions):
            return questions[current_idx]
        return None
```

### 4. FactoryAgent (Corrected Pydantic-AI Integration)

```python
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio

class FactoryAgent:
    """Conversational agent for Telegram bot creation"""
    
    def __init__(self, platform_api_key: str, storage_adapter):
        # Correct MCP server setup
        self.telegram_mcp = MCPServerStdio(
            'node',
            args=['mcp-servers/telegram-bot-mcp/dist/index.js'],
            tool_prefix='tg'
        )
        
        self.platform = PlatformClient(platform_api_key)
        self.project_manager = ProjectManager(self.platform, storage_adapter)
        
        # Correct agent initialization with MCP
        self.agent = Agent(
            'anthropic:claude-3-5-haiku-latest',
            deps_type=ConversationState,
            system_prompt="""You are Mini-Mancer, an AI agent creation assistant.

Your role:
1. Guide users through bot creation via friendly conversation
2. Gather: bot name, purpose, personality traits, desired features  
3. Use tools to submit specs to platform and relay questions
4. Keep users informed of progress and completion

Be conversational, helpful, and ensure all requirements are collected before submission.""",
            mcp_servers=[self.telegram_mcp]
        )
        
        self.conversations: Dict[str, ConversationState] = {}
        
        # Register agent tools
        self._register_tools()
    
    def _register_tools(self):
        """Register tools for platform interaction"""
        
        @self.agent.tool
        async def create_agent_project(self, ctx: RunContext[ConversationState]) -> str:
            """Submit collected requirements to create agent project"""
            if not self._requirements_complete(ctx.deps.requirements):
                return "❌ Missing required information. Please provide: name, purpose, and at least one feature."
            
            try:
                spec = AgentSpec(**ctx.deps.requirements)
                project = await self.project_manager.create_project(
                    spec, ctx.deps.user_id, ctx.deps.chat_id
                )
                ctx.deps.active_project_id = project.project_id
                ctx.deps.stage = "monitoring"
                
                return f"🚀 Project created! ID: {project.project_id}\n⏳ Submitting to platform..."
                
            except Exception as e:
                return f"❌ Failed to create project: {e}"
        
        @self.agent.tool
        async def check_project_status(self, ctx: RunContext[ConversationState]) -> str:
            """Check current project status and handle questions"""
            if not ctx.deps.active_project_id:
                return "❌ No active project"
            
            project = await self.project_manager.storage.get(
                ctx.deps.active_project_id, ProjectState, "projects"
            )
            if not project:
                return "❌ Project not found"
            
            match project.status:
                case ProjectStatus.QUESTIONING:
                    if project.platform_questions and project.current_question_idx < len(project.platform_questions):
                        question = project.platform_questions[project.current_question_idx]
                        ctx.deps.pending_question = question
                        return f"🤔 Platform question:\n{question}"
                    return "⏳ Processing questions..."
                    
                case ProjectStatus.COMPLETED:
                    return f"✅ Your agent is ready!\n🔗 Access: {project.agent_url}"
                    
                case ProjectStatus.FAILED:
                    return f"❌ Creation failed: {project.error_message}"
                    
                case _:
                    return f"⏳ Status: {project.status.value.replace('_', ' ').title()}"
        
        @self.agent.tool  
        async def answer_platform_question(self, ctx: RunContext[ConversationState], answer: str) -> str:
            """Submit answer to current platform question"""
            if not ctx.deps.active_project_id:
                return "❌ No active project"
            
            if not ctx.deps.pending_question:
                return "❌ No pending question"
            
            success, message = await self.project_manager.answer_current_question(
                ctx.deps.active_project_id, answer
            )
            
            if success:
                ctx.deps.pending_question = None
            
            return message
    
    def _requirements_complete(self, requirements: Dict[str, Any]) -> bool:
        """Check if minimum requirements are collected"""
        required_fields = ["name", "purpose"]
        return all(requirements.get(field) for field in required_fields)
    
    async def handle_telegram_update(self, update: Dict[str, Any]) -> str:
        """Process incoming Telegram update"""
        message = update.get('message', {})
        user_id = str(message.get('from', {}).get('id', ''))
        chat_id = str(message.get('chat', {}).get('id', ''))
        text = message.get('text', '')
        
        # Get or create conversation state
        state = self.conversations.get(user_id, ConversationState(
            user_id=user_id, 
            chat_id=chat_id
        ))
        
        # Run agent with MCP integration
        async with self.agent.run_mcp_servers():
            result = await self.agent.run(text, deps=state)
        
        # Update conversation state
        self.conversations[user_id] = state
        
        return result.output
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.platform.close()
        if self.project_manager._monitor_task:
            self.project_manager._monitor_task.cancel()
```

### 5. FastAPI Application

```python
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import os
from src.registry.json_storage import JSONFileStorage

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Initialize storage and factory agent
    storage = JSONFileStorage("data")
    factory = FactoryAgent(
        platform_api_key=os.getenv("PLATFORM_API_KEY", "test-key"),
        storage_adapter=storage
    )
    app.state.factory = factory
    
    yield
    
    # Cleanup
    await factory.cleanup()

app = FastAPI(title="Mini-Mancer Factory Agent", lifespan=lifespan)

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook"""
    update = await request.json()
    
    try:
        response = await app.state.factory.handle_telegram_update(update)
        
        # Send response via Telegram API (handled by MCP)
        # The MCP server will handle the actual sending
        
        return {"ok": True}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/health")
async def health():
    return {"status": "healthy", "component": "factory_agent"}

@app.get("/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """Get project status for debugging"""
    try:
        project = await app.state.factory.project_manager.storage.get(
            project_id, ProjectState, "projects"
        )
        return project.model_dump() if project else {"error": "Not found"}
    except Exception as e:
        return {"error": str(e)}
```

---

## Phase 2: Platform Agents (TypeScript - 2 hours)

### Platform-Side Architecture

Since OpenServ provides a TypeScript SDK, Phase 2 will implement the actual agent creation logic using TypeScript agents on the platform:

```typescript
// Platform agents handle:
// 1. Code generation from AgentSpec
// 2. Template application  
// 3. Deployment to hosting platform
// 4. Question generation for clarification
// 5. Final agent URL generation

interface AgentCreationAgent {
  processSpec(spec: AgentSpec): Promise<ProjectResult>
  askClarification(questions: string[]): Promise<void>
  generateCode(finalSpec: AgentSpec): Promise<string>
  deployAgent(code: string): Promise<string> // Returns agent URL
}
```

### Communication Flow

1. **FactoryAgent** → HTTP POST `/v1/agents` → **Platform API**
2. **Platform TypeScript Agents** process the spec
3. **Platform** → Question updates → **FactoryAgent polling**
4. **FactoryAgent** → Relay questions → **Telegram User**
5. **User** → Answers → **FactoryAgent** → **Platform API**
6. **Platform** → Final agent URL → **FactoryAgent** → **User**

---

## Key Improvements Made

### ✅ **Corrected Technical Issues**
- Fixed pydantic-ai MCP integration patterns
- Removed incorrect `mcp.call()` usage
- Proper async context manager usage
- Realistic API client implementation

### ✅ **Simplified Architecture**  
- Clear separation: FactoryAgent (Python) + Platform (TypeScript)
- Removed unnecessary MCP for external API calls
- Focused on core conversation flow

### ✅ **Practical Implementation**
- Uses existing OpenServ TypeScript SDK for platform side
- HTTP API for FactoryAgent ↔ Platform communication
- Proper error handling and monitoring
- Storage abstraction for easy migration

### ✅ **MVP Focus**
- Phase 1 delivers complete user experience
- Phase 2 adds platform automation
- Each phase is independently deployable

**Result**: A realistic, implementable plan that leverages each technology's strengths while avoiding the pitfalls found in the original sketch.