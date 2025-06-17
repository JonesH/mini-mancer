from pydantic_ai import Agent, RunContext
from .models import ProtoSpawnerState
import re


class ProtoSpawner:
    """Demo Proto-Spawner agent - interactive bot creation assistant"""
    
    def __init__(self):
        # System prompt for demo mode
        system_prompt = """Identity
• You are Proto-Spawner, a friendly AI assistant that helps create Telegram bots.
• You're currently in demo mode - just chat with the user and help them understand bot creation.

Abilities
• Explain how Telegram bots work
• Guide users through bot token validation
• Help plan bot features and functionality
• Provide encouragement and clear next steps

Interaction Style
• Be conversational and helpful
• Ask clarifying questions when needed
• Provide clear explanations
• Keep responses concise but informative

Current Mode: Demo - No actual bot deployment, just interactive guidance."""

        self.agent = Agent(
            'openai:gpt-4o-mini',
            deps_type=ProtoSpawnerState,
            system_prompt=system_prompt
        )
        
        self._register_tools()
    
    def _register_tools(self):
        """Register demo tools for the agent"""
        
        @self.agent.tool
        async def validate_token_format(ctx: RunContext[ProtoSpawnerState], token: str) -> str:
            """Check if a Telegram Bot token has the correct format"""
            pattern = r'^\d+:[A-Za-z0-9_-]{35}$'
            if not re.match(pattern, token):
                return "❌ Invalid token format. A valid token looks like: 123456789:ABCdefGHIjklMNOpqrSTUvwxyz"
            
            ctx.deps.token = token
            ctx.deps.stage = "token_validated"
            return f"✅ Token format is valid! (Demo mode - not actually testing with Telegram API)"
        
        @self.agent.tool
        async def save_bot_details(ctx: RunContext[ProtoSpawnerState], name: str, description: str) -> str:
            """Save bot name and description for demo purposes"""
            ctx.deps.display_name = name.strip()
            ctx.deps.welcome_message = description.strip()
            ctx.deps.stage = "details_saved"
            
            return f"✅ Saved bot details:\n• Name: {name}\n• Description: {description}\n\n(Demo mode - ready to explain next steps!)"
    
    async def handle_message(self, user_id: str, chat_id: str, message: str, state: ProtoSpawnerState = None) -> str:
        """Handle incoming message and return response"""
        if state is None:
            state = ProtoSpawnerState(user_id=user_id, chat_id=chat_id)
        
        result = await self.agent.run(message, deps=state)
        return result.data
    
    async def cleanup(self):
        """Cleanup resources"""
        pass  # No resources to cleanup in demo mode