"""
Minimal Prototype Agent - Integrates OpenServ + Telegram + Agno-AGI

Single FastAPI application with path-based routing to avoid endpoint conflicts.
Leverages existing TelegramBotTemplate and AgentDNA system.
"""

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agno.agent import Agent
from agno.models.openai import OpenAIChat

from .agents import TelegramBotTemplate, TelegramWebhookHandler
from .models.agent_dna import TELEGRAM_BOT_TEMPLATE


class TelegramWebhookRequest(BaseModel):
    """Telegram webhook payload"""
    update_id: int
    message: dict[str, Any] | None = None


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
        self.created_bot_token = os.getenv("BOT_TOKEN_1")
        
        if not self.factory_token:
            raise ValueError("BOT_TOKEN or TEST_BOT_TOKEN environment variable required")
        if not self.created_bot_token:
            raise ValueError("BOT_TOKEN_1 environment variable required for created bots")
        
        # Track the currently active created bot
        self.active_created_bot: TelegramBotTemplate | None = None
        self.created_bot_application = None
        
        # Create agent DNA for a helpful assistant
        agent_dna = TELEGRAM_BOT_TEMPLATE.instantiate({
            "name": "PrototypeBot",
            "purpose": "Demonstrate integrated OpenServ + Telegram + Agno-AGI functionality"
        })
        
        # Initialize Agno agent for core intelligence with bot creation capability
        factory_prompt = f"""
        {agent_dna.generate_system_prompt()}
        
        SPECIAL CAPABILITY: BOT CREATION
        You are a factory bot that can create new Telegram bots for users.
        
        When a user asks you to create a bot:
        1. Ask for basic details: bot name, purpose, personality
        2. Use your bot creation tool to spawn the new bot
        3. Return the t.me link to the user
        
        Keep bot creation simple - focus on name, purpose, and basic personality only.
        """
        
        self.agno_agent = Agent(
            model=OpenAIChat(id="gpt-4o-mini"),
            description=factory_prompt,
            markdown=True,
            add_history_to_messages=True,
        )
        
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
        """Register bot creation tool with the factory agent"""
        # For now, skip tool registration and handle bot creation in chat responses
        # In full implementation, we'd use agno's tool system properly
        pass
        
    def create_new_bot(self, bot_name: str, bot_purpose: str, personality: str = "helpful") -> str:
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
✅ **Bot Created Successfully!**

🤖 **Name:** {bot_name}
🎯 **Purpose:** {bot_purpose}  
😊 **Personality:** {personality_trait.value}
🔗 **Link:** https://t.me/{bot_username}

Your new bot will be deployed shortly! The link will be active once deployment completes.
            """.strip()
            
        except Exception as e:
            return f"❌ Error creating bot: {str(e)}"
    
    async def start_created_bot(self, bot_template: TelegramBotTemplate) -> str:
        """Start the created bot with actual Telegram polling"""
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        
        try:
            # Stop previous bot if exists
            await self.stop_created_bot()
            
            # Create Telegram application for the created bot
            self.created_bot_application = Application.builder().token(self.created_bot_token).build()
            
            # Add handlers for the created bot
            async def created_bot_start(update, context):
                response = await bot_template.handle_message({
                    "from": {"id": update.effective_user.id, "username": update.effective_user.username},
                    "chat": {"id": update.effective_chat.id},
                    "text": "/start",
                    "message_id": update.message.message_id
                })
                await update.message.reply_text(response)
            
            async def created_bot_message(update, context):
                response = await bot_template.handle_message({
                    "from": {"id": update.effective_user.id, "username": update.effective_user.username},
                    "chat": {"id": update.effective_chat.id},
                    "text": update.message.text,
                    "message_id": update.message.message_id
                })
                await update.message.reply_text(response)
            
            self.created_bot_application.add_handler(CommandHandler("start", created_bot_start))
            self.created_bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, created_bot_message))
            
            # Start the bot
            await self.created_bot_application.initialize()
            await self.created_bot_application.start()
            await self.created_bot_application.updater.start_polling()
            
            # Get bot info
            bot_info = await self.created_bot_application.bot.get_me()
            
            print(f"🤖 Created Bot Started: @{bot_info.username}")
            return bot_info.username
            
        except Exception as e:
            print(f"❌ Error starting created bot: {e}")
            return ""
    
    async def stop_created_bot(self):
        """Stop the currently running created bot"""
        if self.created_bot_application:
            try:
                await self.created_bot_application.updater.stop()
                await self.created_bot_application.stop()
                await self.created_bot_application.shutdown()
                print("🛑 Previous created bot stopped")
            except Exception as e:
                print(f"❌ Error stopping created bot: {e}")
            finally:
                self.created_bot_application = None
                self.active_created_bot = None
    
    def _setup_routes(self):
        """Setup FastAPI routes with proper path separation"""
        
        @self.app.get("/")
        async def root():
            return {
                "service": "mini-mancer-prototype",
                "status": "running",
                "endpoints": {
                    "telegram": "/telegram/webhook",
                    "openserv_tasks": "/openserv/do_task", 
                    "openserv_chat": "/openserv/respond_chat_message"
                }
            }
        
        @self.app.post("/telegram/webhook")
        async def telegram_webhook(request: TelegramWebhookRequest):
            """Handle Telegram webhooks via existing TelegramBotTemplate"""
            try:
                # Convert request to dict for handler
                webhook_data = request.model_dump()
                
                # Process via existing telegram handler
                response = await self.telegram_handler.handle_webhook(webhook_data)
                
                return response
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Telegram webhook error: {e}")
        
        @self.app.post("/openserv/do_task")
        async def openserv_do_task(request: OpenServTaskRequest):
            """Handle OpenServ task processing via Agno agent"""
            try:
                # Use Agno agent to process the task
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
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Task processing error: {e}")
        
        @self.app.post("/openserv/respond_chat_message")
        async def openserv_respond_chat(request: OpenServChatRequest):
            """Handle OpenServ chat messages via Agno agent"""
            try:
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
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Chat response error: {e}")


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