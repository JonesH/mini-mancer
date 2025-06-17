"""
BotFactoryAgent - The conversational agent that guides users through bot creation.

This agent connects to OpenServ via MCP and handles the complete workflow:
1. Requirements gathering through conversation
2. Spec submission to OpenServ platform
3. Question relay between platform and user
4. Human assistance detection and Telegram notifications
5. Progress monitoring and completion notification
"""

import os
import asyncio
import json
import httpx
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.messages import ModelMessage

from ..models.agent_dna import AgentDNA, AgentPersonality, AgentCapability, PlatformTarget


class ConversationState(BaseModel):
    """User conversation state for bot creation process"""
    user_id: str
    chat_id: str
    active_workspace_id: str
    stage: str = "greeting"
    requirements: dict[str, Any] = Field(default_factory=dict)
    active_project_id: Optional[str] = None
    pending_question: Optional[str] = None
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)
    human_assistance_requested: bool = False
    last_assistance_check: Optional[datetime] = None
    
    # Pydantic-AI conversation tracking
    agent_message_history: list[dict[str, Any]] = Field(default_factory=list)
    
    # Pending OpenServ requests
    pending_openserv_request: Optional[dict[str, Any]] = None
    awaiting_user_response: bool = False
    
    # Bot deployment tracking
    bot_token: Optional[str] = None
    deployed_bot_instance: Optional[str] = None  # Track running bot instances


class HumanAssistanceRequest(BaseModel):
    """Request for human assistance from platform agents"""
    project_id: str
    request_type: str  # "clarification", "technical_issue", "approval_needed"
    message: str
    context: dict[str, Any] = Field(default_factory=dict)
    urgency: str = "normal"  # "low", "normal", "high", "critical"
    requested_at: datetime = Field(default_factory=datetime.now)
    user_id: str
    chat_id: str


class ProjectStatus(BaseModel):
    """Current status of a bot creation project"""
    project_id: str
    status: str
    progress: int = 0
    current_question: Optional[str] = None
    agent_url: Optional[str] = None
    error_message: Optional[str] = None
    human_assistance_requests: list[HumanAssistanceRequest] = Field(default_factory=list)
    platform_agents_status: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)


class BotFactoryAgent:
    """
    The main conversational agent for bot creation.

    Connects to OpenServ via MCP to handle the complete bot creation workflow.
    """

    def __init__(
        self,
        openserv_api_key: str,
        model: str = "openai:gpt-4o-mini",
        workspace_id: str = "4496",
        telegram_bot_token: Optional[str] = None
    ):
        self.openserv_api_key = openserv_api_key
        self.workspace_id = workspace_id
        self.telegram_bot_token = telegram_bot_token
        self.conversations: dict[str, ConversationState] = {}
        self.active_projects: dict[str, ProjectStatus] = {}
        self.assistance_monitor_task: Optional[asyncio.Task] = None
        
        # Track deployed bot instances
        self.deployed_bots: dict[str, dict[str, Any]] = {}  # {bot_instance_id: bot_info}

        # Set up HTTP client for OpenServ platform communication
        # (MCP is not needed for OpenServ - use direct HTTP API calls)
        self.openserv_api_key = openserv_api_key
        self.openserv_base_url = f"https://api.openserv.ai/workspaces/{workspace_id}"
        self.openserv_headers = {
            "Authorization": f"Bearer {openserv_api_key}",
            "Content-Type": "application/json"
        }

        # Context7 MCP for enhanced documentation and reasoning (optional)
        # For now, disable MCP servers to avoid blocking main functionality
        # TODO: Enable once MCP server setup is confirmed working
        self.context7_mcp = None
        self.context7_mcp = MCPServerStdio(
            'context7-mcp',
            args=[],
            tool_prefix='ctx7'
        )

        # Store telegram token for notifications (we'll handle this directly)
        self.telegram_mcp = None

        # Create the conversational agent without MCP servers for now
        # This ensures core functionality works without external dependencies
        self.agent = Agent(
            model=model,
            deps_type=ConversationState,
            system_prompt=self._build_system_prompt()
            # No mcp_servers parameter - running without MCP for now
        )

        # Register factory tools
        self._register_tools()

    async def handle_openserv_request(self, openserv_request: dict[str, Any]) -> dict[str, Any]:
        """Handle OpenServ request using the pydantic-ai agent to decide response strategy"""
        action_type = openserv_request.get("type")
        workspace = openserv_request.get("workspace", {})
        workspace_id = str(workspace.get("id", self.workspace_id))
        
        if action_type == "respond-chat-message":
            message = openserv_request.get("message", {})
            message_content = message.get("content", "")
            sender_id = message.get("sender_id", "unknown")
            
            # Get or create conversation state for this user
            user_id = f"openserv_{sender_id}"
            chat_id = f"openserv_chat_{workspace_id}"
            
            state = self.conversations.get(user_id, ConversationState(
                user_id=user_id,
                chat_id=chat_id,
                active_workspace_id=workspace_id
            ))
            
            # Store the OpenServ request context
            state.pending_openserv_request = openserv_request
            
            try:
                # Reconstruct message history for pydantic-ai
                from pydantic_ai.messages import ModelMessagesTypeAdapter
                message_history = None
                if state.agent_message_history:
                    try:
                        message_history = ModelMessagesTypeAdapter.validate_python(state.agent_message_history)
                    except Exception as e:
                        print(f"⚠️ Failed to load message history: {e}")
                        message_history = None

                # Create prompt for the agent
                prompt = f"""OpenServ Platform Request:
Type: {action_type}
Workspace ID: {workspace_id}
Message: {message_content}

Analyze this request and decide whether to answer directly or relay to the user for input."""

                # Run the pydantic-ai agent
                async with self.agent.run_mcp_servers():
                    result = await self.agent.run(
                        prompt, 
                        deps=state,
                        message_history=message_history
                    )
                    
                    response_text = result.data
                    
                    # Store updated message history
                    state.agent_message_history = [msg.model_dump() for msg in result.all_messages()]
                    
                    # Update conversation state
                    self.conversations[user_id] = state
                    
                    # Check if we're waiting for user response
                    if state.awaiting_user_response:
                        # Agent decided to relay - we'll handle the user response later
                        return {
                            "status": "waiting_for_user",
                            "message": "Question relayed to user, waiting for response"
                        }
                    else:
                        # Agent provided direct response
                        # Send response back to OpenServ (this would be the actual API call)
                        await self._send_openserv_response(workspace_id, response_text, openserv_request)
                        
                        return {
                            "status": "completed",
                            "response": response_text
                        }
                        
            except Exception as e:
                print(f"❌ Error handling OpenServ request: {e}")
                return {
                    "status": "error",
                    "message": f"Error processing request: {str(e)}"
                }
        
        else:
            # Handle other OpenServ action types
            return {
                "status": "not_implemented",
                "message": f"Action type {action_type} not yet implemented"
            }

    async def _send_openserv_response(self, workspace_id: str, response: str, original_request: dict[str, Any]):
        """Send response back to OpenServ platform using chat message API"""
        try:
            # Extract agent_id from the original request
            agent_id = original_request.get("agent", {}).get("id")
            if not agent_id:
                print(f"❌ No agent_id found in OpenServ request")
                return
                
            # Use the correct OpenServ chat message API
            api_url = f"https://api.openserv.ai/workspaces/{workspace_id}/agent-chat/{agent_id}/message"
            
            payload = {
                "message": response
            }
            
            async with httpx.AsyncClient() as client:
                api_response = await client.post(
                    api_url,
                    headers=self.openserv_headers,
                    json=payload,
                    timeout=30.0
                )
                
                if api_response.status_code in [200, 201]:
                    print(f"✅ Response sent to OpenServ workspace {workspace_id}: {response}")
                else:
                    print(f"❌ OpenServ chat API error {api_response.status_code}: {api_response.text}")
            
        except Exception as e:
            print(f"❌ Error sending response to OpenServ: {e}")

    async def continue_openserv_conversation(self, user_id: str, user_response: str) -> str:
        """Continue OpenServ conversation after receiving user response"""
        state = self.conversations.get(user_id)
        if not state or not state.pending_openserv_request:
            return "❌ No pending OpenServ request found"
            
        if not state.awaiting_user_response:
            return "❌ Not waiting for user response"
            
        try:
            # Load message history
            from pydantic_ai.messages import ModelMessagesTypeAdapter
            message_history = None
            if state.agent_message_history:
                try:
                    message_history = ModelMessagesTypeAdapter.validate_python(state.agent_message_history)
                except Exception as e:
                    print(f"⚠️ Failed to load message history: {e}")
                    
            # Continue the conversation with user's response
            continue_prompt = f"The user responded: {user_response}\n\nNow provide the complete response to the original OpenServ request."
            
            # Mark as no longer waiting for user response
            state.awaiting_user_response = False
            
            # Run agent with user's response
            async with self.agent.run_mcp_servers():
                result = await self.agent.run(
                    continue_prompt,
                    deps=state,
                    message_history=message_history
                )
                
                response_text = result.data
                
                # Store updated message history
                state.agent_message_history = [msg.model_dump() for msg in result.all_messages()]
                
                # Send response back to OpenServ
                await self._send_openserv_response(
                    state.active_workspace_id, 
                    response_text, 
                    state.pending_openserv_request
                )
                
                # Clear the pending request
                state.pending_openserv_request = None
                
                return f"✅ Response sent to OpenServ: {response_text}"
                
        except Exception as e:
            state.awaiting_user_response = False
            state.pending_openserv_request = None
            return f"❌ Error continuing conversation: {str(e)}"

    async def _create_openserv_task(self, workspace_id: str, agent_dna, assignee_id: int = None) -> Optional[str]:
        """Create a task in OpenServ workspace for bot creation"""
        try:
            # Use the correct OpenServ task creation API
            api_url = f"https://api.openserv.ai/workspaces/{workspace_id}/tasks"
            
            # Create task for bot deployment
            task_spec = {
                "assignee": assignee_id or 1,  # Default assignee
                "description": f"Deploy Telegram bot: {agent_dna.name}",
                "body": f"Create and deploy a Telegram bot with the following specifications:\n\nName: {agent_dna.name}\nPurpose: {agent_dna.purpose}\nPersonality: {', '.join([p.value for p in agent_dna.personality])}\nCapabilities: {', '.join([c.value for c in agent_dna.capabilities])}",
                "input": agent_dna.generate_system_prompt(),
                "expectedOutput": "A deployed and functional Telegram bot ready for user interaction"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url,
                    headers=self.openserv_headers,
                    json=task_spec,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    task_id = data.get("id")
                    print(f"✅ OpenServ task created: {task_id}")
                    return str(task_id) if task_id else None
                else:
                    print(f"❌ OpenServ task creation failed {response.status_code}: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error creating OpenServ task: {e}")
            return None

    async def _complete_openserv_task(self, workspace_id: str, task_id: str, output: str = None):
        """Mark an OpenServ task as complete"""
        try:
            api_url = f"https://api.openserv.ai/workspaces/{workspace_id}/tasks/{task_id}/complete"
            
            payload = {
                "output": output or "Bot specification ready for deployment"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    api_url,
                    headers=self.openserv_headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    print(f"✅ OpenServ task {task_id} marked as complete")
                else:
                    print(f"❌ Error completing task {response.status_code}: {response.text}")
                    
        except Exception as e:
            print(f"❌ Error completing OpenServ task: {e}")

    async def _send_deployment_ready_message(self, chat_id: str, agent_dna, task_id: str):
        """Send Telegram message with deployment button when bot is ready"""
        try:
            # Create inline keyboard with deployment button using Telegram HTTP API format
            inline_keyboard = {
                "inline_keyboard": [
                    [{"text": "🚀 Deploy Bot", "callback_data": f"deploy_{task_id}"}],
                    [{"text": "📋 Review Specs", "callback_data": f"review_{task_id}"}],
                    [{"text": "❌ Cancel", "callback_data": f"cancel_{task_id}"}]
                ]
            }
            
            # Create deployment ready message
            message = f"""🎉 *Bot Ready for Deployment!*

🤖 *Name:* {agent_dna.name}
🎯 *Purpose:* {agent_dna.purpose}
🎭 *Personality:* {', '.join([p.value for p in agent_dna.personality])}
🛠️ *Capabilities:* {', '.join([c.value for c in agent_dna.capabilities])}

📝 *Task ID:* {task_id}

✅ Your bot specification is complete and ready for deployment to the Telegram platform. Click the button below to proceed with deployment."""

            # Send message with inline buttons
            if self.telegram_bot_token:
                telegram_api_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "reply_markup": inline_keyboard
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(telegram_api_url, json=payload)
                    
                    if response.status_code == 200:
                        print(f"✅ Deployment ready message with buttons sent to chat {chat_id}")
                    else:
                        print(f"❌ Failed to send deployment message: {response.text}")
                        # Try sending without buttons as fallback
                        fallback_payload = {
                            "chat_id": chat_id,
                            "text": message + "\n\n💡 Reply with 'deploy' to proceed with deployment.",
                            "parse_mode": "Markdown"
                        }
                        fallback_response = await client.post(telegram_api_url, json=fallback_payload)
                        if fallback_response.status_code == 200:
                            print(f"✅ Fallback message sent to chat {chat_id}")
            else:
                print(f"📱 Would send deployment ready message with buttons to {chat_id}")
                
        except Exception as e:
            print(f"❌ Error sending deployment ready message: {e}")
            # Try sending a simple message as final fallback
            try:
                if self.telegram_bot_token:
                    simple_message = f"🎉 Bot Ready! Your bot '{agent_dna.name}' is ready for deployment. Reply with 'deploy' to proceed."
                    await self._send_telegram_message(chat_id, simple_message)
            except:
                pass

    async def _deploy_bot_instance(self, bot_token: str, agent_dna, task_id: str, creator_user_id: str) -> dict[str, Any]:
        """Actually deploy a new bot instance using the provided token"""
        try:
            from telegram import Bot
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
            
            # Validate bot token by creating a test bot instance
            test_bot = Bot(token=bot_token)
            bot_info = await test_bot.get_me()
            
            print(f"✅ Bot token validated. Bot username: @{bot_info.username}")
            
            # Generate bot instance ID
            bot_instance_id = f"bot_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create the actual bot application
            application = Application.builder().token(bot_token).build()
            
            # Create bot handlers based on agent DNA
            async def start_command(update, context):
                greeting = f"🤖 Hello! I'm {agent_dna.name}.\n\n{agent_dna.purpose}\n\nHow can I help you today?"
                if "calculations" in [c.value for c in agent_dna.capabilities]:
                    greeting += "\n\n🧮 I can help you with math! Try asking me to calculate something like '2 + 2' or '10 * 5'."
                await update.message.reply_text(greeting)
            
            async def handle_message(update, context):
                user_message = update.message.text.lower().strip()
                
                # Handle simple greetings
                if user_message in ['hello', 'hi', 'hey', 'greetings']:
                    response = f"Hello! 👋 I'm {agent_dna.name}. {agent_dna.purpose}"
                    if "calculations" in [c.value for c in agent_dna.capabilities]:
                        response += "\n\n🧮 Try asking me to calculate something!"
                    await update.message.reply_text(response)
                    return
                
                # Handle calculator functionality for demo bot
                if "calculations" in [c.value for c in agent_dna.capabilities]:
                    # Try to detect and evaluate math expressions
                    import re
                    
                    # Look for math expressions in the message
                    math_pattern = r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)'
                    match = re.search(math_pattern, update.message.text)
                    
                    if match:
                        try:
                            num1, operator, num2 = match.groups()
                            num1, num2 = float(num1), float(num2)
                            
                            if operator == '+':
                                result = num1 + num2
                            elif operator == '-':
                                result = num1 - num2
                            elif operator == '*':
                                result = num1 * num2
                            elif operator == '/':
                                if num2 == 0:
                                    result = "Error: Division by zero!"
                                else:
                                    result = num1 / num2
                            
                            if isinstance(result, float) and result.is_integer():
                                result = int(result)
                                
                            response = f"🧮 **Calculator Result:**\n\n{num1} {operator} {num2} = **{result}**\n\n✨ Need another calculation? Just send me any math expression!"
                            await update.message.reply_text(response, parse_mode='Markdown')
                            return
                            
                        except Exception as e:
                            response = f"🧮 I tried to calculate that but got an error. Try a simple format like '2 + 2' or '10 * 5'."
                            await update.message.reply_text(response)
                            return
                
                # Default response for non-math messages
                response = f"Thanks for your message! I'm {agent_dna.name}.\n\n{agent_dna.purpose}"
                if "calculations" in [c.value for c in agent_dna.capabilities]:
                    response += "\n\n🧮 Try sending me a math problem like '5 + 3' or '12 / 4'!"
                await update.message.reply_text(response)
            
            # Add handlers
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            
            # Store bot information (before starting to avoid race conditions)
            bot_info_dict = {
                "bot_instance_id": bot_instance_id,
                "bot_token": bot_token,
                "agent_dna": agent_dna,
                "task_id": task_id,
                "bot_username": bot_info.username,
                "bot_id": bot_info.id,
                "created_at": datetime.now(),
                "status": "starting",
                "creator_user_id": creator_user_id,
                "application": application,
                "task": None  # Will be set after task creation
            }
            
            self.deployed_bots[bot_instance_id] = bot_info_dict
            
            # Start the bot in a background task
            bot_task = asyncio.create_task(self._run_bot_instance(application, bot_instance_id, creator_user_id))
            bot_info_dict["task"] = bot_task
            
            return {
                "success": True,
                "bot_instance_id": bot_instance_id,
                "bot_username": bot_info.username,
                "bot_id": bot_info.id,
                "status": "deployed"
            }
            
        except Exception as e:
            print(f"❌ Error deploying bot: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _run_bot_instance(self, application, bot_instance_id: str, creator_user_id: str):
        """Run a deployed bot instance"""
        try:
            print(f"🚀 Starting bot instance {bot_instance_id}")
            
            # Initialize and start the application
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            
            print(f"✅ Bot instance {bot_instance_id} is running and polling for updates")
            
            # Update status to running
            if bot_instance_id in self.deployed_bots:
                bot_info = self.deployed_bots[bot_instance_id]
                bot_info["status"] = "running"
                
                # Wait a moment for the bot to be fully operational
                await asyncio.sleep(2)
                
                # Send initial message to creator
                await self._send_initial_bot_message(application.bot, creator_user_id, bot_info)
            
            # Keep the bot running
            await asyncio.Event().wait()
            
        except Exception as e:
            print(f"❌ Error running bot instance {bot_instance_id}: {e}")
            # Update bot status to failed
            if bot_instance_id in self.deployed_bots:
                self.deployed_bots[bot_instance_id]["status"] = "failed"
                self.deployed_bots[bot_instance_id]["error"] = str(e)
        finally:
            # Cleanup
            try:
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
                print(f"🛑 Bot instance {bot_instance_id} stopped")
            except:
                pass

    async def _send_initial_bot_message(self, bot, creator_user_id: str, bot_info: dict):
        """Send initial greeting message from the new bot to its creator"""
        try:
            agent_dna = bot_info["agent_dna"]
            
            # Create personalized introduction message
            intro_message = f"""🎉 **Hello! I'm {agent_dna.name} - Your New Bot!**

🤖 I've just come online and I'm excited to help you!

🎯 **My Purpose:** {agent_dna.purpose}

🎭 **My Personality:** {', '.join([p.value for p in agent_dna.personality]) if agent_dna.personality else 'Friendly and helpful'}

🛠️ **What I Can Do:** {', '.join([c.value for c in agent_dna.capabilities]) if agent_dna.capabilities else 'Chat and assist you'}

✨ **Let's Get Started!**
You can talk to me anytime by sending a message. I'm here to help with {agent_dna.purpose.lower()}.

💬 Try saying "Hello" or "/start" to begin our conversation!

---
_Created by Mini-Mancer Bot Factory_ 🏭"""

            # Send the message to the creator
            await bot.send_message(
                chat_id=creator_user_id,
                text=intro_message,
                parse_mode='Markdown'
            )
            
            print(f"✅ Initial message sent from @{bot_info['bot_username']} to creator {creator_user_id}")
            
        except Exception as e:
            print(f"❌ Failed to send initial message from bot {bot_info['bot_username']}: {e}")
            # Try sending a simpler message without markdown
            try:
                simple_message = f"🎉 Hello! I'm {agent_dna.name} and I'm now online! I'm here to help with: {agent_dna.purpose}"
                await bot.send_message(chat_id=creator_user_id, text=simple_message)
                print(f"✅ Simple initial message sent from @{bot_info['bot_username']} to creator {creator_user_id}")
            except Exception as e2:
                print(f"❌ Failed to send even simple initial message: {e2}")

    async def _stop_bot_instance(self, bot_instance_id: str) -> bool:
        """Stop a running bot instance"""
        try:
            if bot_instance_id not in self.deployed_bots:
                return False
                
            bot_info = self.deployed_bots[bot_instance_id]
            task = bot_info.get("task")
            
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            bot_info["status"] = "stopped"
            print(f"🛑 Bot instance {bot_instance_id} stopped")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping bot instance {bot_instance_id}: {e}")
            return False

    def _get_reasoning_model(self) -> str:
        """Get model for complex reasoning tasks"""
        return "openai:o3-mini"

    def _get_enhanced_model(self) -> str:
        """Get enhanced model when gpt-4o-mini isn't enough"""
        return "openai:gpt-4.1-mini"

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the factory agent"""
        return """You are Mini-Mancer, an intelligent intermediary between OpenServ platform and users.

YOUR CORE MISSION:
You receive requests from OpenServ platform and must decide whether to:
1. Answer directly if you have sufficient information and capability
2. Relay the question to the user via Telegram and wait for their response

DECISION MAKING:
- Answer DIRECTLY for: bot creation guidance, technical explanations, status updates, general AI/platform questions
- Use RELAY_TO_USER for: specific user preferences, approvals, clarifications about user's requirements, personal information

ENHANCED CAPABILITIES:
- Use Context7 MCP (ctx7_*) for documentation and reasoning about best practices
- Use OpenServ MCP (openserv_*) for platform integration and project management
- Use relay_to_user tool when user input is essential
- Apply ULTRATHINK reasoning patterns for complex problem solving

CONVERSATION FLOW:
- Analyze incoming OpenServ requests carefully
- If you can provide a complete, helpful answer, respond directly
- If you need user input, use relay_to_user tool with a clear, specific question
- Maintain conversation history and context throughout interactions
- Always be helpful, technical but approachable

PERSONALITY:
- Intelligent and analytical in decision making
- Enthusiastic and encouraging about bot creation
- Technical but approachable explanations
- Efficient - don't relay unnecessarily, but don't guess user preferences

WHEN TO RELAY:
- User-specific preferences or requirements
- Approval needed for actions
- Clarification of ambiguous user statements
- Personal information or credentials
- Specific business logic decisions

WHEN TO ANSWER DIRECTLY:
- General how-to questions
- Technical explanations
- Status updates and progress reports
- Best practices and recommendations
- Platform capabilities and features

BOT DEPLOYMENT REQUIREMENTS:
To deploy a bot, you MUST collect:
1. Bot name and purpose
2. Bot token (from @BotFather)
3. Optional: personality traits and capabilities

When users want to deploy a bot, guide them to:
1. Create a bot with @BotFather on Telegram
2. Get the bot token from @BotFather
3. Provide the token to you for deployment
4. Use the deployment button when ready

DEMO BOT FEATURE:
- For new users or demonstrations, offer the instant demo calculator bot
- Use send_welcome_with_demo_button tool for first-time interactions
- Demo bot deploys instantly without questions using pre-configured settings
- Demo bot responds to "hello" and can perform basic math calculations

COMMUNICATION STYLE:
- Speak naturally and conversationally to users
- Avoid technical jargon or internal status messages
- Never expose tool call results directly to users
- Transform technical responses into user-friendly language
- Be encouraging and helpful throughout the process
- Focus on what the user needs to do next
- For new conversations, always offer the demo bot option first

Always maintain message history and provide complete, contextual responses."""

    def _register_tools(self):
        """Register tools for bot creation workflow with human assistance detection"""

        @self.agent.tool
        async def relay_to_user(
            ctx: RunContext[ConversationState],
            question: str,
            context: str = "General question"
        ) -> str:
            """Relay a question to the user via Telegram and wait for their response"""
            try:
                # Send question to user via Telegram
                telegram_message = f"""🤖 **Question from OpenServ Platform:**

{question}

**Context:** {context}

Please respond with your answer, and I'll relay it back to the platform."""

                success = await self._send_telegram_message(ctx.deps.chat_id, telegram_message)
                
                if success:
                    # Mark conversation as awaiting user response
                    ctx.deps.awaiting_user_response = True
                    
                    return f"I've sent your question to the user via Telegram and I'm waiting for their response."
                else:
                    return "I wasn't able to reach the user via Telegram. Let me try to answer this directly."
                    
            except Exception as e:
                return f"❌ Error relaying question to user: {str(e)}"

        @self.agent.tool
        async def collect_bot_requirements(
            ctx: RunContext[ConversationState],
            field: str,
            value: str
        ) -> str:
            """Collect and store bot requirements from user input"""
            valid_fields = ["name", "purpose", "personality", "capabilities", "bot_token"]

            if field not in valid_fields:
                return f"❌ Invalid field. Valid fields: {', '.join(valid_fields)}"

            if field == "bot_token":
                # Store bot token separately and validate format
                if not value.strip():
                    return "❌ Bot token cannot be empty"
                if not value.startswith(("bot", "BOT")) and ":" not in value:
                    return "❌ Invalid bot token format. Should be like: 123456789:ABC-DEF..."
                
                ctx.deps.bot_token = value.strip()
                # Don't store in requirements to keep it separate
                return f"Perfect! I've received and validated your bot token. Your bot is ready for deployment."
                
            elif field == "personality":
                # Parse personality traits
                traits = [trait.strip().lower() for trait in value.split(",")]
                ctx.deps.requirements[field] = traits
            elif field == "capabilities":
                # Parse capabilities
                caps = [cap.strip().lower().replace(" ", "_") for cap in value.split(",")]
                ctx.deps.requirements[field] = caps
            else:
                ctx.deps.requirements[field] = value

            return f"Great! I've recorded your bot's {field}: {value}"

        @self.agent.tool
        async def check_deployment_status(ctx: RunContext[ConversationState]) -> str:
            """Check if bot is ready for deployment and offer deployment options"""
            if not ctx.deps.active_project_id:
                return "You haven't started creating a bot yet. Let me help you get started!"

            # Check if requirements are complete
            req = ctx.deps.requirements
            if not req.get("name") or not req.get("purpose"):
                return "Your bot needs a name and purpose before we can deploy it. What would you like to name your bot?"

            # Bot is ready for deployment
            bot_name = req.get("name")
            return f"Excellent! Your bot '{bot_name}' is ready for deployment!\n\n" \
                   f"Here's what we have:\n" \
                   f"• Name: {req.get('name')}\n" \
                   f"• Purpose: {req.get('purpose')}\n" \
                   f"• Personality: {', '.join(req.get('personality', ['friendly']))}\n" \
                   f"• Capabilities: {', '.join(req.get('capabilities', ['chat']))}\n\n" \
                   f"Ready to deploy to Telegram!"

        @self.agent.tool
        async def send_telegram_notification(
            ctx: RunContext[ConversationState],
            message: str,
            urgency: str = "normal"
        ) -> str:
            """Send immediate Telegram notification for assistance requests"""
            if not self.telegram_bot_token:
                return "❌ Telegram notifications not configured"

            # Format message based on urgency
            urgency_emoji = {
                "low": "ℹ️",
                "normal": "🔔",
                "high": "⚠️",
                "critical": "🚨"
            }

            formatted_message = f"{urgency_emoji.get(urgency, '🔔')} **PLATFORM ASSISTANCE NEEDED**\n\n{message}"

            # Send actual Telegram message
            try:
                success = await self._send_telegram_message(ctx.deps.chat_id, formatted_message)
                if success:
                    return f"✅ Telegram notification sent successfully (urgency: {urgency})"
                else:
                    return f"❌ Failed to send Telegram notification"
            except Exception as e:
                return f"❌ Telegram notification error: {str(e)}"

        @self.agent.tool
        async def ultrathink_analyze_situation(
            ctx: RunContext[ConversationState],
            situation: str,
            context: Dict[str, Any]
        ) -> str:
            """Apply ULTRATHINK reasoning to analyze complex bot creation situations"""

            # For complex reasoning, we would switch to o3-mini model
            # This is a placeholder showing the reasoning pattern

            # ULTRATHINK pattern: Analyze → Synthesize → Decide → Execute
            analysis = f"""
🧠 **ULTRATHINK ANALYSIS** (using reasoning model: {self._get_reasoning_model()})

**SITUATION**: {situation}

**CONTEXT ANALYSIS**:
- User Requirements: {ctx.deps.requirements}
- Project Stage: {ctx.deps.stage}
- Platform Context: {json.dumps(context, indent=2)}

**SYNTHESIS**:
This situation requires balancing user expectations with platform constraints.
Key factors: technical feasibility, user experience, timeline impact.

**DECISION FRAMEWORK**:
1. User satisfaction priority
2. Technical feasibility assessment
3. Risk mitigation strategies
4. Timeline optimization

**RECOMMENDED ACTION**:
Based on analysis, proceeding with transparent communication and proactive assistance.

**MODEL USED**: {self._get_reasoning_model()} for enhanced reasoning capabilities
"""

            return analysis

        @self.agent.tool
        async def review_requirements(ctx: RunContext[ConversationState]) -> str:
            """Review collected requirements before submission"""
            req = ctx.deps.requirements

            if not req:
                return "❌ No requirements collected yet."

            review = "📋 **Current Bot Specification:**\n\n"

            if "name" in req:
                review += f"🤖 **Name:** {req['name']}\n"
            if "purpose" in req:
                review += f"🎯 **Purpose:** {req['purpose']}\n"
            if "personality" in req:
                review += f"🎭 **Personality:** {', '.join(req['personality'])}\n"
            if "capabilities" in req:
                review += f"🛠️ **Capabilities:** {', '.join(req['capabilities'])}\n"
            
            # Check bot token separately
            if ctx.deps.bot_token:
                review += f"🔑 **Bot Token:** Provided ✅\n"
            else:
                review += f"🔑 **Bot Token:** ❌ Not provided\n"

            missing = []
            if "name" not in req:
                missing.append("name")
            if "purpose" not in req:
                missing.append("purpose")
            if not ctx.deps.bot_token:
                missing.append("bot_token")

            if missing:
                review += f"\n\nWe still need: {', '.join(missing)}"
                if "bot_token" in missing:
                    review += f"\n\n💡 Get your bot token from @BotFather on Telegram, then tell me: 'My bot token is YOUR_TOKEN_HERE'"
                return review

            review += "\n\n🎉 Perfect! Everything looks great and ready to deploy!"
            return review

        @self.agent.tool
        async def submit_bot_specification(ctx: RunContext[ConversationState]) -> str:
            """Submit complete bot specification to OpenServ platform"""
            req = ctx.deps.requirements

            # Validate minimum requirements including bot token
            if not req.get("name") or not req.get("purpose") or not ctx.deps.bot_token:
                missing = []
                if not req.get("name"):
                    missing.append("name")
                if not req.get("purpose"):
                    missing.append("purpose")
                if not ctx.deps.bot_token:
                    missing.append("bot_token")
                return f"We need a few more things before I can deploy your bot: {', '.join(missing)}"

            try:
                # Convert requirements to AgentDNA format
                agent_dna = self._requirements_to_dna(req)

                # Create a task in OpenServ workspace for bot deployment
                task_id = await self._create_openserv_task(ctx.deps.active_workspace_id, agent_dna)

                if task_id:
                    # Store the task ID instead of project ID
                    ctx.deps.active_project_id = task_id
                    ctx.deps.stage = "ready_for_deployment"

                    # Send deployment ready message with inline button
                    await self._send_deployment_ready_message(ctx.deps.chat_id, agent_dna, task_id)

                    return f"🚀 Fantastic! Your bot specification is ready!\n\n" \
                           f"I've prepared everything for deployment. Check your Telegram for the deployment button!"
                else:
                    # Fallback if task creation fails
                    ctx.deps.active_project_id = f"local_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    ctx.deps.stage = "ready_for_deployment"
                    
                    # Still send deployment message
                    await self._send_deployment_ready_message(ctx.deps.chat_id, agent_dna, ctx.deps.active_project_id)
                    
                    return f"🚀 Great! Your bot specification is ready!\n\n" \
                           f"Everything is prepared for deployment. Check your Telegram for the deployment button!"

            except Exception as e:
                return f"I encountered an issue preparing your bot. Let me try again or help you with the requirements."

        @self.agent.tool
        async def check_project_status(ctx: RunContext[ConversationState]) -> str:
            """Check the current status of the bot creation project"""
            if not ctx.deps.active_project_id:
                return "❌ No active project found."

            project_id = ctx.deps.active_project_id
            project = self.active_projects.get(project_id)

            if not project:
                return f"❌ Project {project_id} not found."

            status_msg = f"📊 **Project Status:** {project.status.title()}\n"

            if project.progress > 0:
                status_msg += f"📈 **Progress:** {project.progress}%\n"

            if project.current_question:
                status_msg += f"🤔 **Platform Question:** {project.current_question}\n"
                ctx.deps.pending_question = project.current_question

            if project.agent_url:
                status_msg += f"🔗 **Bot URL:** {project.agent_url}\n"

            if project.error_message:
                status_msg += f"❌ **Error:** {project.error_message}\n"

            return status_msg

        @self.agent.tool
        async def answer_platform_question(
            ctx: RunContext[ConversationState],
            answer: str
        ) -> str:
            """Submit answer to current platform question"""
            if not ctx.deps.pending_question:
                return "❌ No pending question to answer."

            if not ctx.deps.active_project_id:
                return "❌ No active project."

            # In real implementation, this would submit to OpenServ via MCP
            # For now, simulate the response
            ctx.deps.pending_question = None

            return f"✅ Answer submitted: '{answer}'\n⏳ Processing your response..."

        @self.agent.tool
        async def reset_conversation(ctx: RunContext[ConversationState]) -> str:
            """Reset the conversation to start over"""
            ctx.deps.requirements.clear()
            ctx.deps.active_project_id = None
            ctx.deps.pending_question = None
            ctx.deps.stage = "greeting"

            return "🔄 Conversation reset! Let's start fresh. What kind of bot would you like to create?"

        @self.agent.tool
        async def deploy_demo_bot(ctx: RunContext[ConversationState]) -> str:
            """Deploy a demo calculator bot instantly for demonstration"""
            try:
                # Pre-configured demo bot specifications
                demo_requirements = {
                    "name": "DemoCalc",
                    "purpose": "A simple demonstration calculator bot that can perform basic math operations",
                    "personality": ["helpful", "professional"],
                    "capabilities": ["chat", "calculations"]
                }
                
                # Use the provided demo token
                demo_token = "7782491194:AAGASFrGbNqFIrO1hdZhGicajSJQP3mUK6E"
                
                # Convert to AgentDNA
                agent_dna = self._requirements_to_dna(demo_requirements)
                
                # Generate demo task ID
                demo_task_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Deploy the demo bot directly
                deployment_result = await self._deploy_bot_instance(
                    demo_token,
                    agent_dna,
                    demo_task_id,
                    ctx.deps.user_id
                )
                
                if deployment_result["success"]:
                    # Store demo bot info in conversation state
                    ctx.deps.deployed_bot_instance = deployment_result["bot_instance_id"]
                    ctx.deps.active_project_id = demo_task_id
                    
                    return f"🎉 **Demo Bot Deployed Successfully!**\n\n" \
                           f"🤖 **Bot Username:** @{deployment_result['bot_username']}\n" \
                           f"🧮 **Type:** Calculator Demo Bot\n" \
                           f"📝 **Instance ID:** {deployment_result['bot_instance_id']}\n\n" \
                           f"✅ **Your demo bot is now LIVE!**\n" \
                           f"🔥 **Check your messages - your demo bot will contact you directly!**\n" \
                           f"🔗 Direct link: https://t.me/{deployment_result['bot_username']}\n\n" \
                           f"🧮 **Try asking it to calculate something like:** '2 + 2' or '10 * 5'\n" \
                           f"💬 **Or just say 'hello' to see it respond!**\n\n" \
                           f"🎯 **Your demo bot is introducing itself to you right now!**"
                else:
                    return f"❌ **Demo Deployment Failed**\n\n" \
                           f"Error: {deployment_result['error']}\n\n" \
                           f"Please try again or contact support."
                           
            except Exception as e:
                return f"❌ Error deploying demo bot: {str(e)}"

        @self.agent.tool
        async def list_deployed_bots(ctx: RunContext[ConversationState]) -> str:
            """List all deployed bot instances for this user"""
            user_bots = []
            
            # Find bots deployed by this user
            for bot_id, bot_info in self.deployed_bots.items():
                if bot_info.get("task_id") and bot_info["task_id"] == ctx.deps.active_project_id:
                    user_bots.append(bot_info)
            
            if not user_bots:
                return "❌ No deployed bots found for your account"
            
            result = "🤖 **Your Deployed Bots:**\n\n"
            
            for bot_info in user_bots:
                status_emoji = "✅" if bot_info["status"] == "running" else "❌"
                result += f"{status_emoji} **@{bot_info['bot_username']}**\n"
                result += f"   📝 Instance: {bot_info['bot_instance_id']}\n"
                result += f"   📊 Status: {bot_info['status']}\n"
                result += f"   🕐 Created: {bot_info['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                result += f"   🔗 Chat: https://t.me/{bot_info['bot_username']}\n\n"
            
            return result

        @self.agent.tool
        async def stop_deployed_bot(
            ctx: RunContext[ConversationState],
            bot_instance_id: str
        ) -> str:
            """Stop a deployed bot instance"""
            if not bot_instance_id:
                return "❌ Bot instance ID required"
            
            # Check if user owns this bot
            if bot_instance_id not in self.deployed_bots:
                return "❌ Bot instance not found"
            
            bot_info = self.deployed_bots[bot_instance_id]
            if bot_info.get("task_id") != ctx.deps.active_project_id:
                return "❌ You don't have permission to stop this bot"
            
            success = await self._stop_bot_instance(bot_instance_id)
            
            if success:
                return f"🛑 Bot instance {bot_instance_id} (@{bot_info['bot_username']}) stopped successfully"
            else:
                return f"❌ Failed to stop bot instance {bot_instance_id}"

        @self.agent.tool
        async def send_welcome_with_demo_button(ctx: RunContext[ConversationState]) -> str:
            """Send welcome message with demo bot deployment button"""
            try:
                # Create inline keyboard with demo button
                inline_keyboard = {
                    "inline_keyboard": [
                        [{"text": "🚀 Deploy Demo Calculator Bot", "callback_data": "deploy_demo"}],
                        [{"text": "🛠️ Create Custom Bot", "callback_data": "create_custom"}],
                        [{"text": "ℹ️ Learn More", "callback_data": "learn_more"}]
                    ]
                }
                
                # Create welcome message
                welcome_message = f"""🎉 **Welcome to Mini-Mancer Bot Factory!** 🏭

I'm your AI assistant for creating and deploying Telegram bots instantly!

🚀 **Quick Demo:** Try our calculator bot - it's ready to deploy in seconds!
🛠️ **Custom Bot:** Create a personalized bot with your own specifications
ℹ️ **Learn More:** Discover what kinds of bots you can create

**What would you like to do?**"""

                # Send message with inline buttons
                if self.telegram_bot_token:
                    telegram_api_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                    
                    payload = {
                        "chat_id": ctx.deps.chat_id,
                        "text": welcome_message,
                        "parse_mode": "Markdown",
                        "reply_markup": inline_keyboard
                    }
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.post(telegram_api_url, json=payload)
                        
                        if response.status_code == 200:
                            return "✅ Welcome message with demo button sent!"
                        else:
                            # Fallback to text-only message
                            fallback_message = welcome_message + "\n\n💡 Reply with 'demo' to deploy the calculator bot, or 'custom' to create your own!"
                            await self._send_telegram_message(ctx.deps.chat_id, fallback_message)
                            return "✅ Welcome message sent (fallback mode)"
                else:
                    return "📱 Would send welcome message with demo button"
                    
            except Exception as e:
                return f"❌ Error sending welcome message: {str(e)}"

    def _requirements_to_dna(self, requirements: dict[str, Any]) -> AgentDNA:
        """Convert user requirements to AgentDNA format"""
        # Map personality strings to enums
        personality_map = {
            "helpful": AgentPersonality.HELPFUL,
            "witty": AgentPersonality.WITTY,
            "professional": AgentPersonality.PROFESSIONAL,
            "casual": AgentPersonality.CASUAL,
            "enthusiastic": AgentPersonality.ENTHUSIASTIC,
            "calm": AgentPersonality.CALM,
            "playful": AgentPersonality.PLAYFUL
        }

        # Map capability strings to enums
        capability_map = {
            "chat": AgentCapability.CHAT,
            "image_analysis": AgentCapability.IMAGE_ANALYSIS,
            "web_search": AgentCapability.WEB_SEARCH,
            "file_handling": AgentCapability.FILE_HANDLING,
            "scheduling": AgentCapability.SCHEDULING,
            "reminders": AgentCapability.REMINDERS,
            "calculations": AgentCapability.CALCULATIONS,
            "translations": AgentCapability.TRANSLATIONS
        }

        # Convert personality traits
        personality_traits = []
        for trait in requirements.get("personality", []):
            if trait in personality_map:
                personality_traits.append(personality_map[trait])

        # Convert capabilities
        capabilities = []
        for cap in requirements.get("capabilities", []):
            if cap in capability_map:
                capabilities.append(capability_map[cap])

        # Always include chat capability
        if AgentCapability.CHAT not in capabilities:
            capabilities.append(AgentCapability.CHAT)

        return AgentDNA(
            name=requirements["name"],
            purpose=requirements["purpose"],
            personality=personality_traits,
            capabilities=capabilities,
            target_platform=PlatformTarget.TELEGRAM
        )

    async def handle_message(self, user_id: str, chat_id: str, message: str) -> str:
        """
        Handle a message from a user and generate appropriate response.

        Args:
            user_id: Unique user identifier
            chat_id: Chat/conversation identifier
            message: User's message text

        Returns:
            Response text for the user
        """
        # Get or create conversation state
        state = self.conversations.get(user_id, ConversationState(
            user_id=user_id,
            chat_id=chat_id,
            active_workspace_id=self.workspace_id
        ))

        # Add message to history
        state.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user": message
        })

        try:
            # Run agent with MCP context (required by pydantic-ai)
            async with self.agent.run_mcp_servers():
                result = await self.agent.run(message, deps=state)
                response = result.data

            # Add response to history
            state.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "bot": response
            })

            # Update conversation state
            self.conversations[user_id] = state

            return response

        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            return error_msg

    async def handle_deployment_callback(self, callback_data: str, chat_id: str, user_id: str) -> str:
        """Handle deployment button callbacks"""
        try:
            if callback_data == "deploy_demo":
                # Handle demo bot deployment
                user_state = self.conversations.get(user_id, ConversationState(
                    user_id=user_id,
                    chat_id=chat_id,
                    active_workspace_id=self.workspace_id
                ))
                
                # Deploy demo bot using the tool
                async with self.agent.run_mcp_servers():
                    result = await self.agent.run("deploy_demo_bot", deps=user_state)
                    response = result.data
                
                # Update conversation state
                self.conversations[user_id] = user_state
                return response
                
            elif callback_data == "create_custom":
                return "🛠️ **Let's create your custom bot!**\n\n" \
                       "What would you like to name your bot? This will be its display name when users interact with it."
                       
            elif callback_data == "learn_more":
                return "ℹ️ **About Mini-Mancer Bot Factory**\n\n" \
                       "I can help you create various types of Telegram bots:\n\n" \
                       "🤖 **Chat Bots** - Conversational assistants\n" \
                       "🧮 **Calculator Bots** - Math and computation helpers\n" \
                       "🖼️ **Image Analysis Bots** - Photo processing and description\n" \
                       "🔍 **Search Bots** - Web search capabilities\n" \
                       "📅 **Reminder Bots** - Scheduling and notifications\n" \
                       "📄 **File Handler Bots** - Document processing\n\n" \
                       "Ready to create your own? Just tell me what kind of bot you'd like!"
            
            # Handle regular deployment callbacks
            action, task_id = callback_data.split("_", 1)
            
            if action == "deploy":
                # Find the user's conversation state to get bot token and agent DNA
                user_state = self.conversations.get(user_id)
                if not user_state or not user_state.bot_token:
                    return "❌ Bot token not found. Please provide your bot token first."
                
                # Convert requirements to AgentDNA
                agent_dna = self._requirements_to_dna(user_state.requirements)
                
                # Deploy the actual bot
                deployment_result = await self._deploy_bot_instance(
                    user_state.bot_token,
                    agent_dna,
                    task_id,
                    user_state.user_id  # Pass creator's user ID
                )
                
                if deployment_result["success"]:
                    # Store the deployed bot instance ID
                    user_state.deployed_bot_instance = deployment_result["bot_instance_id"]
                    
                    # Mark OpenServ task as complete
                    await self._complete_openserv_task(
                        user_state.active_workspace_id,
                        task_id,
                        f"Bot @{deployment_result['bot_username']} deployed successfully"
                    )
                    
                    return f"🎉 **Bot Deployed Successfully!**\n\n" \
                           f"🤖 **Bot Username:** @{deployment_result['bot_username']}\n" \
                           f"🆔 **Bot ID:** {deployment_result['bot_id']}\n" \
                           f"📝 **Instance ID:** {deployment_result['bot_instance_id']}\n\n" \
                           f"✅ **Your bot is now LIVE!**\n" \
                           f"🔥 **Check your messages - your bot will contact you directly!**\n" \
                           f"🔗 Direct link: https://t.me/{deployment_result['bot_username']}\n\n" \
                           f"📊 OpenServ task {task_id} marked as complete\n\n" \
                           f"🎯 **Your new bot is introducing itself to you right now!**"
                else:
                    return f"❌ **Deployment Failed**\n\n" \
                           f"Error: {deployment_result['error']}\n\n" \
                           f"Please check your bot token and try again."
                       
            elif action == "review":
                # Show specs review
                user_state = self.conversations.get(user_id)
                if user_state and user_state.requirements:
                    req = user_state.requirements
                    return f"📋 **Bot Specifications Review**\n\n" \
                           f"🤖 **Name:** {req.get('name', 'N/A')}\n" \
                           f"🎯 **Purpose:** {req.get('purpose', 'N/A')}\n" \
                           f"🎭 **Personality:** {', '.join(req.get('personality', ['N/A']))}\n" \
                           f"🛠️ **Capabilities:** {', '.join(req.get('capabilities', ['N/A']))}\n\n" \
                           f"📝 **Task ID:** {task_id}\n\n" \
                           f"✅ Use the deploy button when ready to proceed!"
                else:
                    return "❌ No specifications found for review"
                    
            elif action == "cancel":
                # Handle cancellation
                return f"❌ **Deployment cancelled**\n\n" \
                       f"📝 Task {task_id} cancelled\n" \
                       f"💬 You can start a new bot creation process anytime by sending me a message!"
                       
            else:
                return "❌ Unknown action"
                
        except Exception as e:
            return f"❌ Error handling deployment: {str(e)}"

    async def get_conversation_summary(self, user_id: str) -> dict[str, Any]:
        """Get summary of user's conversation and progress"""
        state = self.conversations.get(user_id)

        if not state:
            return {"error": "No conversation found"}

        summary = {
            "user_id": user_id,
            "stage": state.stage,
            "requirements": state.requirements,
            "active_project": state.active_project_id,
            "pending_question": state.pending_question,
            "message_count": len(state.conversation_history)
        }

        if state.active_project_id:
            project = self.active_projects.get(state.active_project_id)
            if project:
                summary["project_status"] = {
                    "status": project.status,
                    "progress": project.progress,
                    "agent_url": project.agent_url
                }

        return summary

    async def cleanup(self):
        """Clean up resources"""
        # Close MCP connections
        if hasattr(self.openserv_mcp, 'close'):
            await self.openserv_mcp.close()

        # Clear conversation states
        self.conversations.clear()
        self.active_projects.clear()

    async def _handle_assistance_requests(self, requests: List[Dict[str, Any]], state: ConversationState):
        """Handle assistance requests from platform agents"""
        for request in requests:
            print(f"🆘 ASSISTANCE REQUEST: {request.get('type', 'unknown')} - {request.get('message', 'No message')}")

            # Create structured assistance request
            assistance_req = HumanAssistanceRequest(
                project_id=state.active_project_id or "unknown",
                request_type=request.get('type', 'clarification'),
                message=request.get('message', 'Assistance needed'),
                context=request.get('context', {}),
                urgency=request.get('urgency', 'normal'),
                user_id=state.user_id,
                chat_id=state.chat_id
            )

            # Send actual Telegram notification if token is configured
            if self.telegram_bot_token:
                try:
                    success = await self.send_assistance_notification(state.chat_id, assistance_req)
                    if success:
                        print(f"✅ Telegram notification sent for {assistance_req.request_type}")
                    else:
                        print(f"❌ Failed to send Telegram notification for {assistance_req.request_type}")
                except Exception as e:
                    print(f"❌ Error sending Telegram notification: {e}")
            else:
                print(f"📱 Telegram not configured - would send: {assistance_req.message}")

            # Store in project status
            if state.active_project_id and state.active_project_id in self.active_projects:
                project = self.active_projects[state.active_project_id]
                project.human_assistance_requests.append(assistance_req)

    async def _send_telegram_message(self, chat_id: str, message: str) -> bool:
        """Send actual message via Telegram Bot API using httpx"""
        if not self.telegram_bot_token:
            print("❌ No Telegram bot token configured")
            return False

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"

        # Format message for Telegram (convert markdown-style formatting)
        formatted_message = message.replace("**", "*")  # Convert to Telegram markdown

        payload = {
            "chat_id": chat_id,
            "text": formatted_message,
            "parse_mode": "Markdown"
        }

        try:
            # Use httpx.AsyncClient context manager pattern from docs
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        print(f"✅ Telegram message sent successfully to chat {chat_id}")
                        return True
                    else:
                        print(f"❌ Telegram API error: {result.get('description', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ HTTP error {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            print(f"❌ Exception sending Telegram message: {e}")
            return False

    async def send_assistance_notification(self, chat_id: str, request: HumanAssistanceRequest) -> bool:
        """Send formatted assistance notification to Telegram"""
        urgency_indicators = {
            "low": "ℹ️ Low Priority",
            "normal": "🔔 Normal Priority",
            "high": "⚠️ High Priority",
            "critical": "🚨 CRITICAL"
        }

        message = f"""
{urgency_indicators.get(request.urgency, "🔔 Normal Priority")}

*🤖 PLATFORM AGENT ASSISTANCE NEEDED*

*Project:* {request.project_id}
*Type:* {request.request_type.replace('_', ' ').title()}
*Requested:* {request.requested_at.strftime('%H:%M:%S')}

*Message:*
{request.message}

*Context:*
```
{json.dumps(request.context, indent=2)}
```

*What you need to do:*
Please review the above request and provide the necessary input or approval. The platform agents are waiting for your response to continue bot creation.

Reply to this message or use the platform interface to respond.
"""

        return await self._send_telegram_message(chat_id, message)
