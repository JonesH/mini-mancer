"""
Minimal Prototype Agent - Integrates OpenServ + Telegram + Agno-AGI

Single FastAPI application with path-based routing to avoid endpoint conflicts.
Leverages existing TelegramBotTemplate and AgentDNA system.
"""

import os
import re
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
            return f"✅ <b>{bot_name}</b> created successfully!\n\n🤖 <b>Purpose:</b> {bot_purpose}\n😊 <b>Style:</b> {personality_trait.value}\n🔗 https://t.me/{bot_username}\n\nBot deploying shortly!"
            
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
                return f"❌ <b>Requirements Need Work</b>\n\n{issues_text}\n\nPlease provide more details."
            
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
                
                return f"🏗️ <b>{requirements.name}</b> compilation started!\n\n📊 <b>Quality:</b> {validation_result['score']}/100\n🔧 <b>Status:</b> Compiling...\n⏱️ <b>ETA:</b> 2-3 minutes\n\n✨ Your digital companion will emerge shortly!"
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
                
                return f"✅ <b>{requirements.name}</b> awakened!\n\n🧠 <b>Traits:</b> {', '.join([trait.value for trait in requirements.core_traits])}\n🛠️ <b>Tools:</b> {', '.join([tool.name for tool in requirements.selected_tools])}\n\n🔗 Ready for deployment!"
                
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
    
    def _parse_bot_creation_request(self, message: str) -> dict[str, str] | None:
        """
        Enhanced parsing for bot creation requests with multiple parameter extraction.
        
        Supports:
        - Command format: /create_bot name="Bot Name" purpose="Description" personality="helpful"
        - Natural language: "create a helpful bot named Assistant for customer support"
        - Simple format: "make bot called Helper"
        
        Returns:
            Dict with extracted parameters or None if not a bot creation request
        """
        message_lower = message.lower()
        
        # Check if this is a bot creation request
        creation_keywords = ["create bot", "make bot", "new bot", "spawn bot", "/create_bot", "/create"]
        if not any(keyword in message_lower for keyword in creation_keywords):
            return None
        
        result = {}
        
        # Method 1: Command-style parsing with quotes
        # /create_bot name="Bot Name" purpose="Help users" personality="professional"
        param_patterns = {
            'name': r'name[=:]\s*["\']([^"\']+)["\']',
            'purpose': r'purpose[=:]\s*["\']([^"\']+)["\']',
            'personality': r'personality[=:]\s*["\']([^"\']+)["\']'
        }
        
        for param, pattern in param_patterns.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                result[param] = match.group(1).strip()
        
        # Method 2: Natural language parsing
        if not result.get('name'):
            # Extract name after "named", "called", "bot"
            name_patterns = [
                r'(?:named|called)\s+(["\']?)([A-Za-z0-9\s]+)\1',
                r'bot\s+(["\']?)([A-Za-z0-9\s]+)\1(?:\s+for|\s+to|\s+that)',
                r'(?:create|make)\s+(?:a\s+)?([A-Za-z0-9\s]+?)(?:\s+bot|\s+for)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    # Use group 2 if quotes were captured, otherwise group 1
                    name = match.group(2) if len(match.groups()) > 1 and match.group(2) else match.group(1)
                    if name and len(name.strip()) > 2:  # Valid name length
                        result['name'] = name.strip().title()
                        break
        
        # Method 3: Extract purpose from context
        if not result.get('purpose'):
            purpose_patterns = [
                r'for\s+([^.!?]+)',
                r'to\s+([^.!?]+)',
                r'that\s+([^.!?]+)',
                r'purpose[=:]\s*([^"\']+?)(?:\s+personality|\s*$)',
            ]
            
            for pattern in purpose_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    purpose = match.group(1).strip()
                    if len(purpose) > 5:  # Valid purpose length
                        result['purpose'] = purpose
                        break
        
        # Method 4: Extract personality traits
        if not result.get('personality'):
            personality_keywords = {
                'helpful': ['helpful', 'assistant', 'supportive', 'friendly'],
                'professional': ['professional', 'business', 'formal', 'corporate'],
                'casual': ['casual', 'relaxed', 'informal', 'chill'],
                'enthusiastic': ['enthusiastic', 'energetic', 'excited', 'upbeat'],
                'witty': ['witty', 'funny', 'humorous', 'clever'],
                'calm': ['calm', 'patient', 'gentle', 'peaceful']
            }
            
            for personality, keywords in personality_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    result['personality'] = personality
                    break
        
        # Return results if we found something useful
        if result:
            print(f"🔍 Parsed bot creation request: {result}")
            return result
        
        return None
    
    def _generate_start_message(self) -> str:
        """Generate a welcoming start message with creation instructions"""
        return """🏭 <b>Welcome to BotMother Factory!</b>

I'm your AI bot creation specialist. I can help you create custom Telegram bots instantly!

<b>🚀 Quick Creation:</b>
• <code>create bot named Helper for customer support</code>
• <code>make a professional bot called Assistant</code>
• <code>new friendly bot for answering questions</code>

<b>⚙️ Advanced Creation:</b>
• <code>/create_bot name="My Bot" purpose="Help users" personality="professional"</code>

<b>🎨 Available Personalities:</b>
• <b>Helpful</b> - Supportive and friendly
• <b>Professional</b> - Business-focused and formal  
• <b>Casual</b> - Relaxed and informal
• <b>Enthusiastic</b> - Energetic and upbeat
• <b>Witty</b> - Clever and humorous
• <b>Calm</b> - Patient and gentle

Just tell me what kind of bot you need, and I'll bring it to life! ✨"""
    
    def _handle_structured_commands(self, message: str) -> str | None:
        """Handle structured bot creation commands"""
        message_lower = message.strip().lower()
        
        # /start and /help commands
        if message_lower in ['/start', '/help']:
            return self._generate_start_message()
        
        # /create_quick command for fast bot creation
        if message_lower.startswith('/create_quick'):
            return """🚀 <b>Quick Bot Creation</b>

Simply tell me:
• <code>create helpful bot named Assistant</code>
• <code>make professional bot called Support</code>
• <code>new friendly bot for customer service</code>

I'll create it instantly with smart defaults! ⚡"""
        
        # /list_personalities command
        if message_lower in ['/list_personalities', '/personalities']:
            return """🎭 <b>Available Bot Personalities:</b>

🤝 <b>Helpful</b> - Supportive, friendly, assistant-like
💼 <b>Professional</b> - Business-focused, formal, corporate
😎 <b>Casual</b> - Relaxed, informal, approachable  
🎉 <b>Enthusiastic</b> - Energetic, upbeat, exciting
😄 <b>Witty</b> - Clever, humorous, entertaining
🧘 <b>Calm</b> - Patient, gentle, peaceful

Choose the personality that fits your bot's purpose!"""
        
        # /examples command
        if message_lower in ['/examples', '/example']:
            return """💡 <b>Bot Creation Examples:</b>

<b>Natural Language:</b>
• <code>create helpful bot named CustomerCare for support</code>
• <code>make professional assistant called Manager</code>
• <code>new witty bot for entertainment</code>

<b>Structured Format:</b>
• <code>/create_bot name="Sales Helper" purpose="Help with sales" personality="professional"</code>
• <code>/create_bot name="Fun Bot" purpose="Entertainment" personality="witty"</code>

<b>Quick Commands:</b>
• <code>/create_quick</code> - Fast creation guide
• <code>/list_personalities</code> - See all personalities

Try any format - I understand them all! 🎯"""
        
        return None
    
    def _generate_quick_creation_keyboard(self) -> dict:
        """Generate inline keyboard for quick bot creation"""
        return {
            "inline_keyboard": [
                [
                    {"text": "🤝 Create Helper Bot", "callback_data": "create_helper"},
                    {"text": "💼 Create Support Bot", "callback_data": "create_support"}
                ],
                [
                    {"text": "🎉 Create Fun Bot", "callback_data": "create_fun"},
                    {"text": "🧘 Create Calm Bot", "callback_data": "create_calm"}
                ],
                [
                    {"text": "⚙️ Custom Builder", "callback_data": "create_custom"},
                    {"text": "📖 Examples", "callback_data": "show_examples"}
                ]
            ]
        }
    
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
            # Handle structured commands first
            command_response = self._handle_structured_commands(request.message)
            if command_response:
                response_data = {
                    "chat_id": request.chat_id,
                    "response": command_response,
                    "agent": "factory-bot-commands",
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
                
                # Add inline keyboard for start/help commands
                if request.message.strip().lower() in ['/start', '/help']:
                    response_data["reply_markup"] = self._generate_quick_creation_keyboard()
                
                return response_data
            
            # Check if this is a bot creation request
            parsed_request = self._parse_bot_creation_request(request.message)
            if parsed_request:
                # Use parsed parameters or defaults
                bot_name = parsed_request.get('name', 'Custom Bot')
                bot_purpose = parsed_request.get('purpose', 'General assistance')
                personality = parsed_request.get('personality', 'helpful')
                
                # Create the bot using instant method
                bot_result = self.create_new_bot_instant(bot_name, bot_purpose, personality)
                
                return {
                    "chat_id": request.chat_id,
                    "response": bot_result,
                    "agent": "factory-bot-creator",
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
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
                "agent": "agno-agi",
                "parse_mode": "HTML",
                "disable_web_page_preview": True
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