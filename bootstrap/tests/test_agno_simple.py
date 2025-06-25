#!/usr/bin/env python3
"""
Simple test of Agno intelligence core to verify it's working.
"""

import asyncio
import logging
from src.agno_core import AgnoIntelligenceCore

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agno_directly():
    """Test Agno intelligence core directly."""
    print("🧠 Testing Agno intelligence core directly...")
    
    try:
        # Initialize intelligence core
        intelligence = AgnoIntelligenceCore("test_agent")
        agent = intelligence.initialize_agent()
        
        print(f"✅ Agno agent initialized: {agent}")
        
        # Test basic conversation
        test_user_id = "test_user_123"
        response = await intelligence.process_message(
            "Hello, my name is Alice. Please introduce yourself.", 
            test_user_id
        )
        print(f"Response: {response}")
        
        # Test memory
        response2 = await intelligence.process_message(
            "What is my name?", 
            test_user_id
        )
        print(f"Memory test response: {response2}")
        
        print("✅ Agno intelligence test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Agno test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_agno_directly())