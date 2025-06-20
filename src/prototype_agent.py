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
        
        # Get bot token from environment
        bot_token = os.getenv("TEST_BOT_TOKEN")
        if not bot_token:
            raise ValueError("TEST_BOT_TOKEN environment variable required")
        
        # Create agent DNA for a helpful assistant
        agent_dna = TELEGRAM_BOT_TEMPLATE.instantiate({
            "name": "PrototypeBot",
            "purpose": "Demonstrate integrated OpenServ + Telegram + Agno-AGI functionality"
        })
        
        # Initialize Agno agent for core intelligence
        self.agno_agent = Agent(
            model=OpenAIChat(id="gpt-4o-mini"),
            description=agent_dna.generate_system_prompt(),
            markdown=True,
            add_history_to_messages=True,
        )
        
        # Initialize Telegram bot using existing template
        self.telegram_bot = TelegramBotTemplate(
            agent_dna=agent_dna,
            model="gpt-4o-mini",
            bot_token=bot_token
        )
        
        # Initialize Telegram webhook handler
        self.telegram_handler = TelegramWebhookHandler(self.telegram_bot)
        
        # Setup routes with path separation to avoid conflicts
        self._setup_routes()
    
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
                # Use Agno agent for chat response
                chat_prompt = f"""
                Respond to this chat message:
                User: {request.message}
                Chat ID: {request.chat_id}
                User ID: {request.user_id}
                
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
prototype = PrototypeAgent()
app = prototype.app


# For development/testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)