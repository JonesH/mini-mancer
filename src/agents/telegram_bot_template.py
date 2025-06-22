"""
Telegram Bot Agent Template - A living template that can be brought to life with AgentDNA.

This template provides the structural foundation for Telegram bots, with AgentDNA
providing the personality, capabilities, and behavioral instructions.
"""

from datetime import datetime
from typing import Any

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field

from ..constants import (
    ERROR_MESSAGES,
    MEDIA_MESSAGES,
    format_document_message,
    format_photo_message,
)
from ..models.agent_dna import AgentCapability, AgentDNA


class TelegramContext(BaseModel):
    """Runtime context for Telegram bot interactions"""
    user_id: str
    chat_id: str
    username: str | None = None
    message_id: int | None = None
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    user_preferences: dict[str, Any] = Field(default_factory=dict)


class TelegramBotTemplate:
    """
    A template for creating Telegram bots that can be brought to life with AgentDNA.

    The template provides the platform-specific functionality (Telegram API integration,
    message handling, etc.) while AgentDNA provides the personality and capabilities.
    """

    def __init__(
        self,
        agent_dna: AgentDNA,
        model: str = "gpt-4o-mini",
        bot_token: str | None = None
    ):
        self.dna = agent_dna
        self.bot_token = bot_token
        self.active_contexts: dict[str, TelegramContext] = {}

        # Create the AI agent with DNA-generated system prompt
        self.agent = Agent(
            model=OpenAIChat(id=model),
            description=self._build_system_prompt(),
            markdown=True,
        )

        # Register capabilities as tools
        self._register_capability_tools()

    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt from AgentDNA"""
        base_prompt = self.dna.generate_system_prompt()

        # Add Telegram-specific instructions
        telegram_instructions = """

TELEGRAM PLATFORM INSTRUCTIONS:
- You are operating as a Telegram bot
- Users interact with you through text messages, photos, and files
- Keep responses concise but helpful (Telegram users prefer shorter messages)
- Use emojis appropriately to make conversations more engaging
- Remember conversation context between messages
- Be responsive to user preferences and adapt your communication style
- IMPORTANT: Keep responses under 200 words when possible
- Use *bold* format for emphasis (not **bold**)
- Avoid overly long explanations - be direct and helpful

MESSAGE HANDLING:
- Process text messages for conversation
- Analyze images when users send photos
- Handle file uploads when relevant to your capabilities
- Respond to commands that start with '/'
"""

        return base_prompt + telegram_instructions

    def _register_capability_tools(self):
        """Register tools based on agent's DNA capabilities"""
        # For prototype, we'll keep this simple and let the agent handle capabilities
        # through its description rather than registering explicit tools
        # In a full implementation, we'd use agno's tool system here
        pass

    async def handle_message(self, message_data: dict[str, Any]) -> str:
        """
        Handle incoming Telegram message and generate response.

        Args:
            message_data: Raw Telegram message data

        Returns:
            Response text to send back to user
        """
        # Extract message info
        user_info = message_data.get("from", {})
        chat_info = message_data.get("chat", {})
        text = message_data.get("text", "")

        user_id = str(user_info.get("id", ""))
        chat_id = str(chat_info.get("id", ""))
        username = user_info.get("username")
        message_id = message_data.get("message_id")

        # Get or create context
        context = self._get_or_create_context(
            user_id, chat_id, username, message_id
        )

        # Add message to conversation history
        context.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user": text,
            "message_id": message_id
        })

        try:
            print(f"🧠 [BOT TEMPLATE] Processing message: '{text}' from user {user_id}")

            # Validate input
            if not text or len(text.strip()) == 0:
                return ERROR_MESSAGES["empty_message"]

            if len(text) > 4000:  # Telegram message limit
                text = text[:4000] + "..."
                print("⚠️ [BOT TEMPLATE] Message truncated due to length")

            # Generate response using AI agent with timeout
            try:
                result = self.agent.run(text)
                if not result or not hasattr(result, 'content'):
                    raise ValueError("Invalid response from AI agent")
                response = result.content
            except Exception as ai_error:
                print(f"❌ [BOT TEMPLATE] AI agent error: {ai_error}")
                return ERROR_MESSAGES["ai_error"]

            # Validate response
            if not response or len(response.strip()) == 0:
                return ERROR_MESSAGES["empty_response"]

            # Apply Telegram formatting fixes and length limits
            response = self._format_for_telegram(response)

            print(f"🧠 [BOT TEMPLATE] Generated response: '{response[:100]}...'")

            # Add response to conversation history
            context.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "bot": response
            })

            return response

        except Exception as e:
            error_response = ERROR_MESSAGES["general_error"].format(error=str(e))
            print(f"❌ [BOT TEMPLATE] Error processing message: {e}")

            # Add error to conversation history for debugging
            context.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })

            return error_response

    async def handle_photo(self, photo_data: dict[str, Any]) -> str:
        """Handle photo messages"""
        if AgentCapability.IMAGE_ANALYSIS not in self.dna.capabilities:
            return MEDIA_MESSAGES["photo_no_capability"]

        # In a real implementation, would download and analyze the photo
        caption = photo_data.get("caption", "")
        return format_photo_message(caption)

    async def handle_document(self, document_data: dict[str, Any]) -> str:
        """Handle document/file messages"""
        if AgentCapability.FILE_HANDLING not in self.dna.capabilities:
            return MEDIA_MESSAGES["document_no_capability"]

        filename = document_data.get("file_name", "unknown file")
        return format_document_message(filename)

    def _format_for_telegram(self, text: str) -> str:
        """
        Format text for proper Telegram markdown rendering and length limits.
        
        Args:
            text: Raw text response
            
        Returns:
            Formatted text suitable for Telegram
        """
        # Apply Telegram-specific markdown fixes
        # Fix bold formatting - Telegram uses *text* for bold
        text = text.replace("**", "*")

        # Ensure proper line spacing for readability
        text = text.replace("\n\n\n", "\n\n")

        # Apply Telegram message length limit (4096 characters)
        max_length = 4000  # Leave some buffer
        if len(text) > max_length:
            text = text[:max_length] + "...\n\n_Message truncated due to length_"

        return text

    def _get_or_create_context(
        self,
        user_id: str,
        chat_id: str,
        username: str | None,
        message_id: int | None
    ) -> TelegramContext:
        """Get existing context or create new one for user"""
        if user_id not in self.active_contexts:
            self.active_contexts[user_id] = TelegramContext(
                user_id=user_id,
                chat_id=chat_id,
                username=username,
                message_id=message_id
            )
        else:
            # Update context with latest message info
            context = self.active_contexts[user_id]
            context.message_id = message_id

        return self.active_contexts[user_id]

    def get_agent_info(self) -> dict[str, Any]:
        """Get information about this agent instance"""
        return {
            "name": self.dna.name,
            "purpose": self.dna.purpose,
            "personality": [p.value for p in self.dna.personality],
            "capabilities": [c.value for c in self.dna.capabilities],
            "platform": self.dna.target_platform.value,
            "version": self.dna.version,
            "created_at": self.dna.created_at.isoformat(),
            "active_conversations": len(self.active_contexts)
        }

    async def shutdown(self):
        """Clean shutdown of the bot"""
        # Save any persistent context data
        # Close connections, etc.
        self.active_contexts.clear()


class TelegramWebhookHandler:
    """
    Handles incoming Telegram webhooks and routes them to the appropriate bot template.
    """

    def __init__(self, bot_template: TelegramBotTemplate):
        self.bot = bot_template

    async def handle_webhook(self, webhook_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process incoming Telegram webhook.

        Args:
            webhook_data: Raw webhook payload from Telegram

        Returns:
            Response to send back to Telegram API
        """
        try:
            message = webhook_data.get("message")
            if not message:
                return {"ok": True, "description": "No message in webhook"}

            # Determine message type and route accordingly
            response_text = ""

            if "text" in message:
                response_text = await self.bot.handle_message(message)
            elif "photo" in message:
                response_text = await self.bot.handle_photo(message)
            elif "document" in message:
                response_text = await self.bot.handle_document(message)
            else:
                response_text = ERROR_MESSAGES["unknown_content"]

            # Return response for Telegram API
            return {
                "method": "sendMessage",
                "chat_id": message["chat"]["id"],
                "text": response_text,
                "reply_to_message_id": message["message_id"],
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}
