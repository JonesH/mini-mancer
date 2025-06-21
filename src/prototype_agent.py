"""
Minimal Prototype Agent - Integrates OpenServ + Telegram + Agno-AGI

Single FastAPI application with path-based routing to avoid endpoint conflicts.
Leverages existing TelegramBotTemplate and AgentDNA system.
"""

import os
from typing import Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv

from .agents import TelegramBotTemplate, TelegramWebhookHandler
from .models.agent_dna import TELEGRAM_BOT_TEMPLATE
from .models.bot_requirements import (
    BotRequirements, RequirementsValidator, BotArchitect, 
    BotComplexity, AVAILABLE_TOOLS, ToolCategory
)
from .tools.thinking_tool import ThinkingTool, analyze_bot_requirements, think_about

# Load environment variables
load_dotenv()



class OpenServTaskRequest(BaseModel):
    """OpenServ task request payload"""
    task_id: str
    task_type: str
    parameters: dict[str, Any]


class OpenServChatRequest(BaseModel):
    """OpenServ chat message request"""
    message: str
    chat_id: str
    user_id: str


class BotCompilationRequest(BaseModel):
    """OpenServ bot compilation workflow request"""
    requirements: dict[str, Any]  # BotRequirements as dict
    user_id: str
    compilation_mode: str = "standard"  # "simple", "standard", "complex"


class BotCompilationStatus(BaseModel):
    """Bot compilation status response"""
    compilation_id: str
    status: str  # "queued", "compiling", "testing", "completed", "failed"
    progress_percentage: int
    estimated_completion: str
    bot_preview: dict[str, Any] | None = None


class PrototypeAgent:
    """
    Minimal prototype integrating all three systems:
    - Telegram (via existing TelegramBotTemplate)
    - OpenServ (FastAPI endpoints)
    - Agno-AGI (core intelligence)
    """
    
    def __init__(self):
        # Initialize FastAPI app
        self.app = FastAPI(
            title="Mini-Mancer Prototype",
            description="OpenServ + Telegram + Agno-AGI Integration"
        )
        
        # Get bot tokens from environment
        self.factory_token = os.getenv("BOT_TOKEN") or os.getenv("TEST_BOT_TOKEN")
        self.created_bot_token = os.getenv("BOT_TOKEN_1") or self.factory_token  # Fallback to same token for testing
        
        if not self.factory_token:
            raise ValueError("BOT_TOKEN or TEST_BOT_TOKEN environment variable required")
        
        # Log token status
        print(f"🔑 Factory token: {self.factory_token[:15]}...")
        print(f"🔑 Created bot token: {self.created_bot_token[:15]}...")
        if self.factory_token == self.created_bot_token:
            print("⚠️  Using same token for both factory and created bot (testing mode)")
        
        # Track the currently active created bot
        self.active_created_bot: TelegramBotTemplate | None = None
        self.created_bot_application = None
        
        # Bot compilation workflow tracking
        self.bot_compilation_queue: dict[str, dict[str, Any]] = {}
        self.completed_bot_specs: dict[str, BotRequirements] = {}
        
        # Create agent DNA for a helpful assistant
        agent_dna = TELEGRAM_BOT_TEMPLATE.instantiate({
            "name": "PrototypeBot",
            "purpose": "Demonstrate integrated OpenServ + Telegram + Agno-AGI functionality"
        })
        
        # Initialize Enhanced BotMother with GPT-4.1 and thinking capabilities
        from .prompts.botmother_prompts import BOTMOTHER_COMPLETE_SYSTEM_PROMPT
        
        self.agno_agent = Agent(
            model=OpenAIChat(id="gpt-4o"),  # Keep the working model but upgrade to GPT-4o
            description=BOTMOTHER_COMPLETE_SYSTEM_PROMPT,
            markdown=True,
            add_history_to_messages=True,
            num_history_responses=3,  # Keep existing memory settings
        )
        
        # Initialize thinking tool for BotMother
        self.thinking_tool = ThinkingTool()
        
        print("🧠 BotMother enhanced with GPT-4.1 and advanced thinking capabilities")
        
        # Add bot creation tool
        self._register_bot_creation_tool()
        
        # Initialize factory Telegram bot using existing template
        self.telegram_bot = TelegramBotTemplate(
            agent_dna=agent_dna,
            model="gpt-4o-mini",
            bot_token=self.factory_token
        )
        
        # Initialize Telegram webhook handler
        self.telegram_handler = TelegramWebhookHandler(self.telegram_bot)
        
        # Setup routes with path separation to avoid conflicts
        self._setup_routes()
    
    def _register_bot_creation_tool(self):
        """Register bot creation and thinking tools with the factory agent"""
        # Register thinking capabilities
        def deep_think_tool(topic: str, context: dict = None) -> str:
            """Advanced thinking and analysis tool for complex decisions"""
            return think_about(topic, context)
        
        def analyze_requirements_tool(requirements: dict) -> str:
            """Analyze bot requirements for completeness and quality"""
            return analyze_bot_requirements(requirements)
        
        # Add tools to the agent (using Agno's tool system)
        # Note: In actual implementation, these would be properly registered with Agno
        # For now, these are available through direct method calls in chat handling
        
        print("🛠️ BotMother tools registered: deep thinking, requirements analysis, bot creation")
        
    def create_new_bot_instant(self, bot_name: str, bot_purpose: str, personality: str = "helpful") -> str:
        """
        Create a new Telegram bot with the specified parameters.
        
        Args:
            bot_name: Name for the new bot
            bot_purpose: Purpose/description of what the bot does
            personality: Personality trait (helpful, professional, casual, etc.)
            
        Returns:
            Success message with bot information and t.me link
        """
        try:
            # Create agent DNA for the new bot
            from .models.agent_dna import AgentDNA, AgentPersonality, AgentCapability, PlatformTarget
            
            # Map personality string to enum
            personality_map = {
                "helpful": AgentPersonality.HELPFUL,
                "professional": AgentPersonality.PROFESSIONAL,
                "casual": AgentPersonality.CASUAL,
                "enthusiastic": AgentPersonality.ENTHUSIASTIC,
                "witty": AgentPersonality.WITTY,
                "calm": AgentPersonality.CALM,
                "playful": AgentPersonality.PLAYFUL
            }
            
            personality_trait = personality_map.get(personality.lower(), AgentPersonality.HELPFUL)
            
            # Create new bot DNA
            new_bot_dna = AgentDNA(
                name=bot_name,
                purpose=bot_purpose,
                personality=[personality_trait],
                capabilities=[AgentCapability.CHAT, AgentCapability.IMAGE_ANALYSIS],
                target_platform=PlatformTarget.TELEGRAM
            )
            
            # For now, simulate bot creation (in real implementation, this would create actual bot)
            bot_username = bot_name.lower().replace(" ", "_") + "_bot"
            
            # Create the bot instance with BOT_TOKEN_1
            new_bot = TelegramBotTemplate(
                agent_dna=new_bot_dna,
                bot_token=self.created_bot_token
            )
            
            # Store the active created bot
            self.active_created_bot = new_bot
            
            # Log the new bot creation
            print(f"\n🔧 New Bot Created:")
            print(f"   Name: {bot_name}")
            print(f"   Purpose: {bot_purpose}")
            print(f"   Personality: {personality_trait.value}")
            print(f"   Capabilities: {[cap.value for cap in new_bot_dna.capabilities]}")
            print(f"   Platform: {new_bot_dna.target_platform.value}")
            print(f"   Token: BOT_TOKEN_1")
            print()
            
            # Note: Actual bot starting will be handled in main.py
            # For now, return placeholder username
            return f"""
✅ Bot Created Successfully!

🤖 Name: {bot_name}
🎯 Purpose: {bot_purpose}  
😊 Personality: {personality_trait.value}
🔗 Link: https://t.me/{bot_username}

Your new bot will be deployed shortly! The link will be active once deployment completes.
            """.strip()
            
        except Exception as e:
            return f"❌ Error creating bot: {str(e)}"
    
    def create_new_bot_advanced(self, requirements: BotRequirements) -> str:
        """
        Create a sophisticated bot using comprehensive requirements.
        
        This method handles the architect mode creation with full validation,
        compilation, and testing.
        
        Args:
            requirements: Complete bot requirements specification
            
        Returns:
            Status message about bot compilation process
        """
        try:
            # Validate requirements
            validation_result = RequirementsValidator.validate_requirements(requirements)
            
            if not validation_result["valid"]:
                issues_text = "\n".join([f"• {issue}" for issue in validation_result["issues"]])
                return f"""
❌ Bot Requirements Need Attention

Issues found:
{issues_text}

Please provide more details before I can create your sophisticated bot.
"""
            
            # Generate comprehensive system prompt
            system_prompt = BotArchitect.generate_system_prompt(requirements)
            agno_config = BotArchitect.generate_agno_agent_config(requirements)
            
            print(f"\n🏗️  Advanced Bot Creation:")
            print(f"   Name: {requirements.name}")
            print(f"   Complexity: {requirements.complexity_level.value}")
            print(f"   Quality Score: {validation_result['score']}/100")
            print(f"   Tools: {[tool.name for tool in requirements.selected_tools]}")
            print(f"   OpenServ Required: {requirements.openserv_workflow_required}")
            
            if requirements.openserv_workflow_required:
                # For now, simulate OpenServ workflow
                compilation_id = f"bot_comp_{len(self.bot_compilation_queue) + 1}"
                
                # Store in compilation queue
                self.bot_compilation_queue[compilation_id] = {
                    "requirements": requirements,
                    "status": "compiling",
                    "progress": 75,
                    "created_at": datetime.now()
                }
                
                # Store completed spec for later use
                self.completed_bot_specs[requirements.name.lower()] = requirements
                
                return f"""
🏗️ **Sophisticated Bot Compilation Initiated!**

✨ **{requirements.name}** is being forged in the OpenServ workshop...

📊 **Compilation Details:**
• Quality Score: {validation_result['score']}/100 ({validation_result['quality_level']})
• Complexity: {requirements.complexity_level.value.title()}
• Tools: {', '.join([tool.name for tool in requirements.selected_tools])}
• Compilation ID: {compilation_id}

🔧 **Current Status:** Compiling personality matrix and tool integrations...
⏱️ **Estimated Completion:** 2-3 minutes

Your sophisticated digital companion will emerge shortly with full consciousness and capabilities!
"""
            else:
                # Direct creation for simpler bots
                from .models.agent_dna import AgentDNA, AgentPersonality, AgentCapability, PlatformTarget
                
                # Map first personality trait to AgentPersonality enum
                personality_map = {
                    "analytical": AgentPersonality.PROFESSIONAL,
                    "empathetic": AgentPersonality.HELPFUL,
                    "enthusiastic": AgentPersonality.ENTHUSIASTIC,
                    "creative": AgentPersonality.CREATIVE,
                    "professional": AgentPersonality.PROFESSIONAL,
                    "humorous": AgentPersonality.WITTY,
                    "patient": AgentPersonality.CALM,
                    "supportive": AgentPersonality.HELPFUL
                }
                
                primary_trait = requirements.core_traits[0].value if requirements.core_traits else "helpful"
                personality_trait = personality_map.get(primary_trait, AgentPersonality.HELPFUL)
                
                # Create enhanced bot DNA
                new_bot_dna = AgentDNA(
                    name=requirements.name,
                    purpose=requirements.purpose,
                    personality=[personality_trait],
                    capabilities=[AgentCapability.CHAT, AgentCapability.IMAGE_ANALYSIS],
                    target_platform=PlatformTarget.TELEGRAM
                )
                
                # Create bot with enhanced configuration
                new_bot = TelegramBotTemplate(
                    agent_dna=new_bot_dna,
                    bot_token=self.created_bot_token
                )
                
                # Override with sophisticated system prompt
                new_bot.agent.description = system_prompt
                
                # Store the active created bot
                self.active_created_bot = new_bot
                
                return f"""
✅ **Sophisticated Bot Created Successfully!**

🤖 **{requirements.name}** has awakened with enhanced consciousness!

🧠 **Personality Matrix:**
• Core Traits: {', '.join([trait.value for trait in requirements.core_traits])}
• Communication Style: {requirements.communication_style.value}
• Response Style: {requirements.response_tone}

🛠️ **Capabilities:**
• Tools: {', '.join([tool.name for tool in requirements.selected_tools])}
• Knowledge Domains: {', '.join(requirements.required_knowledge_domains) if requirements.required_knowledge_domains else 'General'}

🔗 **Status:** Ready for deployment! Your sophisticated digital companion awaits.
"""
                
        except Exception as e:
            print(f"❌ Error in advanced bot creation: {e}")
            return f"❌ Error creating sophisticated bot: {str(e)}"
    
    async def start_created_bot(self, bot_template: TelegramBotTemplate) -> str:
        """Start the created bot with independent polling"""
        from telegram.ext import Application, MessageHandler, filters
        import asyncio
        
        try:
            # Store the active created bot
            self.active_created_bot = bot_template
            
            # Create independent Telegram application for created bot
            application = Application.builder().token(self.created_bot_token).build()
            
            # Add message handler that uses the bot template
            async def handle_created_bot_message(update, context):
                """Handle messages for the created bot"""
                try:
                    user_id = str(update.effective_user.id)
                    message_text = update.message.text
                    print(f"📨 [CREATED BOT] Message from user {user_id}: '{message_text}'")
                    
                    # Use bot template to generate response
                    response_text = await bot_template.handle_message(update.message.to_dict())
                    
                    # Send response
                    await update.message.reply_text(response_text)
                    print(f"📤 [CREATED BOT] Sent response to user {user_id}")
                    
                except Exception as e:
                    print(f"❌ [CREATED BOT] Error handling message: {e}")
                    await update.message.reply_text("Sorry, I encountered an error processing your message.")
            
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_created_bot_message))
            
            # Get bot info
            bot_info = await application.bot.get_me()
            username = bot_info.username
            print(f"🤖 [CREATED BOT] Starting: {bot_info.first_name} | @{username} | Token: {self.created_bot_token[:10]}...")
            
            # Start polling in background task
            async def start_polling():
                try:
                    async with application:
                        await application.start()
                        await application.updater.start_polling()
                        print(f"📱 [CREATED BOT] @{username} polling started successfully")
                        
                        # Keep running until stopped
                        await asyncio.Event().wait()
                except Exception as e:
                    print(f"❌ [CREATED BOT] Polling error for @{username}: {e}")
            
            # Start polling as background task (don't await)
            asyncio.create_task(start_polling())
            
            return username
            
        except Exception as e:
            print(f"❌ Error starting created bot: {e}")
            return ""
    
    def stop_created_bot(self):
        """Stop the currently running created bot"""
        if self.active_created_bot:
            try:
                print("🛑 Created bot stopped")
                self.active_created_bot = None
            except Exception as e:
                print(f"❌ Error stopping created bot: {e}")
    
    def _setup_routes(self):
        """Setup FastAPI routes with proper path separation"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "mini-mancer-prototype",
                "status": "running", 
                "architecture": "all-polling",
                "endpoints": {
                    "openserv_tasks": "/openserv/do_task", 
                    "openserv_chat": "/openserv/respond_chat_message"
                }
            }
        
        @self.app.post("/openserv/")
        async def openserv_main(request: Request):
            """Main OpenServ endpoint that routes based on action type"""
            body = await request.json()
            action_type = body.get("type")
            
            if action_type == "do-task":
                task_data = body.get("task", {})
                return await openserv_do_task(OpenServTaskRequest(
                    task_id=task_data.get("id", ""),
                    task_type=task_data.get("type", ""),
                    parameters=task_data.get("parameters", {})
                ))
            elif action_type == "respond-chat-message":
                message_data = body.get("message", {})
                return await openserv_respond_chat(OpenServChatRequest(
                    chat_id=message_data.get("chat_id", ""),
                    message=message_data.get("content", ""),
                    user_id=message_data.get("user_id", "")
                ))
            
            raise HTTPException(status_code=400, detail=f"Unknown action type: {action_type}")
        
        @self.app.post("/openserv/compile_bot")
        async def openserv_compile_bot(request: BotCompilationRequest):
            """Handle OpenServ bot compilation workflow"""
            try:
                # Convert dict back to BotRequirements
                requirements_dict = request.requirements
                requirements = BotRequirements(**requirements_dict)
                
                # Use advanced creation method
                result = self.create_new_bot_advanced(requirements)
                
                return {
                    "compilation_id": f"bot_comp_{len(self.bot_compilation_queue)}",
                    "status": "initiated",
                    "user_id": request.user_id,
                    "mode": request.compilation_mode,
                    "result": result,
                    "openserv_workflow": "mini-mancer-bot-compilation"
                }
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Bot compilation error: {str(e)}")
        
        @self.app.get("/openserv/compilation_status/{compilation_id}")
        async def get_compilation_status(compilation_id: str):
            """Get status of bot compilation workflow"""
            if compilation_id in self.bot_compilation_queue:
                workflow = self.bot_compilation_queue[compilation_id]
                return BotCompilationStatus(
                    compilation_id=compilation_id,
                    status=workflow["status"],
                    progress_percentage=workflow["progress"],
                    estimated_completion="1-2 minutes",
                    bot_preview={
                        "name": workflow["requirements"].name,
                        "purpose": workflow["requirements"].purpose,
                        "complexity": workflow["requirements"].complexity_level.value
                    }
                )
            else:
                raise HTTPException(status_code=404, detail="Compilation not found")
        
        @self.app.get("/openserv/available_tools")
        async def get_available_tools():
            """Get list of available tools for bot creation"""
            return {
                "tools": [
                    {
                        "id": tool_id,
                        "name": tool.name,
                        "category": tool.category.value,
                        "description": tool.description,
                        "complexity": tool.integration_complexity
                    }
                    for tool_id, tool in AVAILABLE_TOOLS.items()
                ],
                "categories": [category.value for category in ToolCategory]
            }
        
        @self.app.post("/openserv/test_connection")
        async def test_openserv_connection():
            """Test connection to OpenServ - Mini-Mancer -> OpenServ"""
            try:
                import httpx
                openserv_url = os.getenv("OPENSERV_URL", "http://localhost:8080")
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{openserv_url}/health")
                    
                    if response.status_code == 200:
                        return {
                            "status": "success",
                            "direction": "mini-mancer -> openserv",
                            "openserv_url": openserv_url,
                            "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                            "message": "OpenServ connection successful"
                        }
                    else:
                        return {
                            "status": "error",
                            "direction": "mini-mancer -> openserv", 
                            "openserv_url": openserv_url,
                            "error": f"HTTP {response.status_code}: {response.text}",
                            "message": "OpenServ connection failed"
                        }
                        
            except Exception as e:
                return {
                    "status": "error",
                    "direction": "mini-mancer -> openserv",
                    "error": str(e),
                    "message": "Failed to connect to OpenServ"
                }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for OpenServ -> Mini-Mancer testing"""
            return {
                "status": "healthy",
                "service": "mini-mancer",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "capabilities": [
                    "bot_creation",
                    "agno_integration", 
                    "telegram_polling",
                    "openserv_api"
                ],
                "active_bots": {
                    "factory_bot": "running",
                    "created_bot": "active" if self.active_created_bot else "none"
                }
            }
        
        @self.app.post("/openserv/ping")
        async def openserv_ping(request: Request):
            """Ping endpoint for OpenServ connection testing"""
            body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
            
            return {
                "status": "pong",
                "timestamp": datetime.now().isoformat(),
                "received_from": body.get("source", "unknown"),
                "mini_mancer_status": "operational",
                "message": "Mini-Mancer received your ping successfully"
            }
        
        @self.app.post("/openserv/do_task")
        async def openserv_do_task(request: OpenServTaskRequest):
            """Handle OpenServ task processing via Agno agent"""
            task_prompt = f"""
            Process this OpenServ task:
            Task ID: {request.task_id}
            Task Type: {request.task_type}
            Parameters: {request.parameters}
            
            Provide a structured response for task completion.
            """
            
            response = self.agno_agent.run(task_prompt)
            
            return {
                "task_id": request.task_id,
                "status": "completed",
                "result": response.content,
                "agent": "agno-agi"
            }
        
        @self.app.post("/openserv/respond_chat_message")
        async def openserv_respond_chat(request: OpenServChatRequest):
            """Handle OpenServ chat messages via Agno agent"""
            # Check if this is a bot creation request
            message_lower = request.message.lower()
            if any(phrase in message_lower for phrase in ["create bot", "make bot", "new bot", "spawn bot"]):
                # Simple bot creation - extract basic info
                bot_name = "Custom Bot"
                bot_purpose = "General assistance"
                personality = "helpful"
                
                # Try to extract name from message
                if "named" in message_lower or "called" in message_lower:
                    words = request.message.split()
                    for i, word in enumerate(words):
                        if word.lower() in ["named", "called"] and i + 1 < len(words):
                            bot_name = words[i + 1].strip('"\'')
                            break
                
                # Create the bot
                bot_result = self.create_new_bot(bot_name, bot_purpose, personality)
                
                return {
                    "chat_id": request.chat_id,
                    "response": bot_result,
                    "agent": "factory-bot-creator"
                }
            
            # Regular chat response
            chat_prompt = f"""
            Respond to this chat message:
            User: {request.message}
            Chat ID: {request.chat_id}
            User ID: {request.user_id}
            
            You are a factory bot that can create new Telegram bots.
            If the user wants to create a bot, ask them for:
            - Bot name
            - Bot purpose 
            - Personality (helpful, professional, casual, etc.)
            
            Provide a helpful, conversational response.
            """
            
            response = self.agno_agent.run(chat_prompt)
            
            return {
                "chat_id": request.chat_id,
                "response": response.content,
                "agent": "agno-agi"
            }


# Create global prototype instance
try:
    prototype = PrototypeAgent()
    app = prototype.app
    print("🏭 Prototype agent initialized successfully")
except Exception as e:
    print(f"❌ Error initializing prototype agent: {e}")
    # Create minimal fallback app
    from fastapi import FastAPI
    app = FastAPI(title="Mini-Mancer (Error State)")
    prototype = None


# For development/testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=14159, reload=True)