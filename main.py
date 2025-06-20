"""
Mini-Mancer Entry Point - Factory Bot with Direct Bot Creation
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our prototype app
from src.prototype_agent import app

def main():
    """Main entry point - simple FastAPI server"""
    
    # Get required environment variables
    bot_token = os.getenv("BOT_TOKEN") or os.getenv("TEST_BOT_TOKEN")
    
    if not bot_token:
        raise ValueError("BOT_TOKEN or TEST_BOT_TOKEN environment variable is required")
    
    print("🏭 Starting Mini-Mancer Factory Bot...")
    print(f"🤖 Using bot token: {bot_token[:10]}...")
    print("🌐 Server will be available on http://localhost:14159")
    
    # Run FastAPI server on port 14159 (matches docker-compose)
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=14159, 
        log_level="info"
    )

if __name__ == "__main__":
    main()