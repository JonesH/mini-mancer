"""
Agno Intelligence Core - Phase 1 Foundation

Unified intelligence layer using Agno with Memory.v2 for all conversations.
This provides the AI capabilities that will power both BotMother and child bots.
"""

import os
import logging
from typing import Optional, Any
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.memory.v2 import Memory
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class AgnoIntelligenceCore:
    """Core Agno intelligence manager for all bot conversations."""
    
    def __init__(self, agent_name: str = "bootstrap_agent"):
        self.agent_name = agent_name
        self.agno_api_key = os.getenv("AGNO_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.agent: Optional[Agent] = None
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set in .env for Agno")
    
    def initialize_agent(self, instructions: str = None) -> Agent:
        """Initialize Agno agent with Memory.v2."""
        if self.agent:
            return self.agent
        
        default_instructions = """
        You are an intelligent assistant powered by Agno with advanced memory capabilities.
        You maintain context across conversations and provide helpful, accurate responses.
        You are part of the Bootstrap Mini-Mancer system for creating and managing Telegram bots.
        """
        
        self.agent = Agent(
            model=OpenAIChat(id="gpt-4o"),
            memory=Memory(),  # Memory.v2 for conversation history
            instructions=instructions or default_instructions,
            add_history_to_messages=True,
            num_history_runs=3
        )
        
        logger.info(f"Agno agent '{self.agent_name}' initialized with Memory.v2")
        return self.agent
    
    async def process_message(self, 
                            message: str, 
                            user_id: str, 
                            session_id: str = None) -> str:
        """
        Process message through Agno agent with Memory.v2 context.
        
        Args:
            message: User message to process
            user_id: Unique user identifier for memory isolation
            session_id: Optional session identifier for context separation
        """
        if not self.agent:
            self.initialize_agent()
        
        # Create unique session ID if not provided
        if not session_id:
            session_id = f"{self.agent_name}_{user_id}"
        
        # Process through Agno with Memory.v2
        response = self.agent.run(
            message, 
            user_id=user_id,
            session_id=session_id
        )
        
        logger.debug(f"Agno processed message: {message[:50]}... → {str(response)[:50]}...")
        return str(response)
    
    def create_specialized_agent(self, 
                                personality: str, 
                                role: str,
                                agent_id: str) -> 'AgnoIntelligenceCore':
        """Create a specialized Agno agent for child bots."""
        specialized_instructions = f"""
        You are {personality}.
        Your role: {role}
        
        You maintain your own conversation context and personality consistently.
        You are an intelligent Telegram bot created by the Bootstrap Mini-Mancer system.
        """
        
        specialized_core = AgnoIntelligenceCore(agent_name=agent_id)
        specialized_core.initialize_agent(specialized_instructions)
        
        logger.info(f"Specialized Agno agent created: {agent_id} ({personality})")
        return specialized_core
    
    def get_memory_stats(self) -> dict[str, Any]:
        """Get Memory.v2 statistics for monitoring."""
        if not self.agent or not self.agent.memory:
            return {"status": "no_memory"}
        
        return {
            "status": "active",
            "agent_name": self.agent_name,
            "memory_type": type(self.agent.memory).__name__
        }


async def test_agno_intelligence():
    """Test Agno intelligence core functionality."""
    print("🧠 Testing Agno intelligence core...")
    
    # Initialize intelligence core
    intelligence = AgnoIntelligenceCore("test_agent")
    agent = intelligence.initialize_agent()
    
    # Test basic conversation
    test_user_id = "test_user_123"
    response1 = await intelligence.process_message(
        "Hello, can you remember my name is Alice?", 
        test_user_id
    )
    print(f"Response 1: {response1}")
    
    # Test memory continuity
    response2 = await intelligence.process_message(
        "What is my name?", 
        test_user_id
    )
    print(f"Response 2: {response2}")
    
    # Test memory stats
    stats = intelligence.get_memory_stats()
    print(f"Memory stats: {stats}")
    
    # Test specialized agent creation
    specialized = intelligence.create_specialized_agent(
        personality="a helpful coding assistant",
        role="help users with Python programming questions",
        agent_id="coding_helper"
    )
    
    coding_response = await specialized.process_message(
        "How do I create a list in Python?",
        "test_user_456"
    )
    print(f"Specialized response: {coding_response}")
    
    print("✅ Agno intelligence core test completed successfully")
    return True


if __name__ == "__main__":
    import asyncio
    # Test the Agno intelligence core
    asyncio.run(test_agno_intelligence())