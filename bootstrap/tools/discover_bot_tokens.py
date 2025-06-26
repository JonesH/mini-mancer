#!/usr/bin/env python3
"""
Token Discovery Tool - Discover and validate all bot tokens in environment

This tool scans environment variables for BOT_TOKEN_* patterns and validates
each token using the Telegram Bot API to show available bots for echo bot deployment.
"""

import asyncio
import os
import re
from typing import Dict, List, Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class BotTokenDiscovery:
    """Discover and validate bot tokens from environment variables."""
    
    def __init__(self):
        self.bot_api_base = "https://api.telegram.org/bot"
        self.discovered_tokens: Dict[str, Dict[str, Any]] = {}
        # Reload environment to ensure we have latest values
        load_dotenv(override=True)
    
    def discover_tokens_from_env(self) -> Dict[str, str]:
        """Find all BOT_TOKEN_* environment variables."""
        tokens = {}
        
        # Debug: Print all environment variables that contain TOKEN
        print("🔍 Debugging environment variables containing 'TOKEN':")
        for key, value in os.environ.items():
            if 'TOKEN' in key:
                print(f"   {key} = {value[:20]}..." if value else f"   {key} = (empty)")
        
        # Get all environment variables
        for key, value in os.environ.items():
            # Match BOT_*_TOKEN pattern (BOT_MOTHER_TOKEN) or BOT_TOKEN_* pattern (BOT_TOKEN_1, BOT_TOKEN_2, etc.)
            if ((key.startswith('BOT_') and key.endswith('_TOKEN')) or 
                (key.startswith('BOT_TOKEN_'))) and value:
                tokens[key] = value
        
        return tokens
    
    async def validate_bot_token(self, token: str) -> Dict[str, Any]:
        """Validate a bot token using Telegram Bot API getMe endpoint."""
        try:
            url = f"{self.bot_api_base}{token}/getMe"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        bot_info = data["result"]
                        return {
                            "valid": True,
                            "id": bot_info["id"],
                            "is_bot": bot_info["is_bot"],
                            "first_name": bot_info["first_name"],
                            "username": bot_info["username"],
                            "can_join_groups": bot_info.get("can_join_groups", False),
                            "can_read_all_group_messages": bot_info.get("can_read_all_group_messages", False),
                            "supports_inline_queries": bot_info.get("supports_inline_queries", False)
                        }
                    else:
                        return {
                            "valid": False,
                            "error": data.get("description", "Unknown API error")
                        }
                else:
                    return {
                        "valid": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}"
            }
    
    async def discover_and_validate_all(self) -> Dict[str, Dict[str, Any]]:
        """Discover all tokens and validate them concurrently."""
        print("🔍 Discovering bot tokens from environment...")
        
        # Find all tokens
        env_tokens = self.discover_tokens_from_env()
        print(f"Found {len(env_tokens)} bot token(s) in environment")
        
        if not env_tokens:
            print("❌ No bot tokens found in environment variables!")
            return {}
        
        # Validate all tokens concurrently
        print("\n📡 Validating tokens with Telegram Bot API...")
        
        validation_tasks = []
        for env_var, token in env_tokens.items():
            task = self.validate_bot_token(token)
            validation_tasks.append((env_var, token, task))
        
        # Execute all validations
        results = {}
        for env_var, token, task in validation_tasks:
            validation_result = await task
            
            results[env_var] = {
                "token": token,
                "token_preview": f"{token[:20]}...",
                "validation": validation_result
            }
        
        self.discovered_tokens = results
        return results
    
    def print_discovery_report(self):
        """Print a formatted report of discovered tokens."""
        if not self.discovered_tokens:
            print("❌ No tokens discovered yet. Run discover_and_validate_all() first.")
            return
        
        print("\n" + "="*80)
        print("🤖 BOT TOKEN DISCOVERY REPORT")
        print("="*80)
        
        valid_count = 0
        invalid_count = 0
        
        for env_var, token_data in self.discovered_tokens.items():
            token_preview = token_data["token_preview"]
            validation = token_data["validation"]
            
            print(f"\n📍 Environment Variable: {env_var}")
            print(f"   Token: {token_preview}")
            
            if validation["valid"]:
                valid_count += 1
                bot_info = validation
                print(f"   ✅ Status: VALID")
                print(f"   🏷️  Bot ID: {bot_info['id']}")
                print(f"   👤 Name: {bot_info['first_name']}")
                print(f"   🔗 Username: @{bot_info['username']}")
                print(f"   👥 Can join groups: {bot_info['can_join_groups']}")
                print(f"   📨 Read all messages: {bot_info['can_read_all_group_messages']}")
                print(f"   🔍 Inline queries: {bot_info['supports_inline_queries']}")
                
                # Determine usage status
                if env_var == "BOT_MOTHER_TOKEN":
                    print(f"   🚩 Usage: IN USE (SimpleBotMother)")
                else:
                    print(f"   🆓 Usage: AVAILABLE FOR ECHO BOTS")
                    
            else:
                invalid_count += 1
                print(f"   ❌ Status: INVALID")
                print(f"   💥 Error: {validation['error']}")
        
        print(f"\n" + "="*80)
        print(f"📊 SUMMARY: {valid_count} valid, {invalid_count} invalid")
        
        # Show available tokens for echo bots
        available_tokens = []
        for env_var, token_data in self.discovered_tokens.items():
            if (token_data["validation"]["valid"] and 
                env_var != "BOT_MOTHER_TOKEN"):  # Exclude BotMother token
                available_tokens.append((env_var, token_data))
        
        if available_tokens:
            print(f"\n🎯 AVAILABLE FOR ECHO BOTS ({len(available_tokens)} tokens):")
            for env_var, token_data in available_tokens:
                validation = token_data["validation"]
                print(f"   • @{validation['username']} ({validation['first_name']})")
        else:
            print(f"\n⚠️  NO TOKENS AVAILABLE FOR ECHO BOTS")
            print("   Add more BOT_TOKEN_X environment variables to create echo bots")
        
        print("="*80)
    
    def get_available_echo_tokens(self) -> List[Dict[str, Any]]:
        """Get list of tokens available for echo bot deployment."""
        available = []
        
        for env_var, token_data in self.discovered_tokens.items():
            if (token_data["validation"]["valid"] and 
                env_var != "BOT_MOTHER_TOKEN"):  # Exclude BotMother
                
                available.append({
                    "env_var": env_var,
                    "token": token_data["token"],
                    "username": token_data["validation"]["username"],
                    "name": token_data["validation"]["first_name"],
                    "bot_id": token_data["validation"]["id"]
                })
        
        return available


async def main():
    """Main discovery and validation workflow."""
    print("🚀 Starting Bot Token Discovery...")
    
    discovery = BotTokenDiscovery()
    
    # Discover and validate all tokens
    results = await discovery.discover_and_validate_all()
    
    if not results:
        print("\n❌ No bot tokens found. Please check your .env file.")
        print("Expected format: BOT_TOKEN_1=your_token_here")
        return
    
    # Print detailed report
    discovery.print_discovery_report()
    
    # Show available tokens for echo deployment
    available_tokens = discovery.get_available_echo_tokens()
    
    if available_tokens:
        print(f"\n✅ Ready to deploy {len(available_tokens)} echo bot(s)!")
        print("These tokens can be used by SimpleBotMother for echo bot creation.")
    else:
        print("\n⚠️  No tokens available for echo bots.")
        print("Add more BOT_TOKEN_X variables to .env file to enable echo bot creation.")


if __name__ == "__main__":
    asyncio.run(main())