"""
API Router Module for Mini-Mancer FastAPI Application

Handles all FastAPI route definitions and request handling.
Extracted from prototype_agent.py for better organization.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .api_models import (
    BotCompilationRequest,
    BotCompilationStatus,
    OpenServChatRequest,
    OpenServTaskRequest,
    TestMonitorEvent,
    TestMonitorStats,
)
from .models.bot_requirements import AVAILABLE_TOOLS, ToolCategory
from .test_monitor import get_dashboard_html, monitor


logger = logging.getLogger(__name__)


class APIRouter:
    """Handles all API route logic for the FastAPI application"""

    def __init__(
        self, telegram_manager: Any, agno_agent: Any, bot_compilation_queue: dict[str, Any], completed_bot_specs: dict[str, Any]
    ) -> None:
        self.telegram_manager = telegram_manager
        self.agno_agent = agno_agent
        self.bot_compilation_queue = bot_compilation_queue
        self.completed_bot_specs = completed_bot_specs

    async def root(self) -> dict[str, Any]:
        """Root endpoint"""
        return {
            "message": "Mini-Mancer Prototype",
            "version": "1.0.0",
            "integrations": ["OpenServ", "Telegram", "Agno-AGI"],
            "status": "running",
        }

    async def openserv_main(self, request: Request) -> dict[str, Any]:
        """Main OpenServ endpoint for general requests"""
        body = await request.json()
        logger.info(f"📥 OpenServ main request: {body}")

        return {
            "status": "received",
            "message": "Request processed by Mini-Mancer",
            "timestamp": datetime.now().isoformat(),
            "processed_by": "prototype_agent",
        }

    async def openserv_compile_bot(self, request: BotCompilationRequest) -> dict[str, Any]:
        """OpenServ bot compilation workflow endpoint"""
        logger.info(f"🏗️ Bot compilation request for user {request.user_id}")
        logger.info(f"   Mode: {request.compilation_mode}")
        logger.info(f"   Requirements keys: {list(request.requirements.keys())}")

        try:
            # Convert requirements dict to BotRequirements object
            from .models.bot_requirements import BotRequirements

            requirements = BotRequirements(**request.requirements)

            # Use the telegram manager to create the bot
            result = self.telegram_manager.create_bot_advanced(
                requirements, self.bot_compilation_queue
            )

            return {
                "status": "accepted",
                "compilation_id": f"comp_{len(self.bot_compilation_queue)}",
                "message": result,
                "estimated_duration_minutes": 3,
                "user_id": request.user_id,
            }

        except Exception as e:
            logger.error(f"❌ Bot compilation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")

    async def get_compilation_status(self, compilation_id: str) -> BotCompilationStatus:
        """Get bot compilation status"""
        if compilation_id not in self.bot_compilation_queue:
            raise HTTPException(status_code=404, detail="Compilation ID not found")

        compilation_data = self.bot_compilation_queue[compilation_id]

        return BotCompilationStatus(
            compilation_id=compilation_id,
            status=compilation_data["status"],
            progress_percentage=compilation_data["progress"],
            estimated_completion="2-3 minutes",
            bot_preview={
                "name": compilation_data["requirements"].name,
                "complexity": compilation_data["requirements"].complexity_level.value,
                "tools_count": len(compilation_data["requirements"].selected_tools),
            },
        )

    async def get_available_tools(self) -> dict[str, Any]:
        """Get available tools for bot creation"""
        tools_by_category: dict[str, list[dict[str, Any]]] = {}

        for tool_id, tool in AVAILABLE_TOOLS.items():
            category = tool.category.value
            if category not in tools_by_category:
                tools_by_category[category] = []

            tools_by_category[category].append(
                {
                    "id": tool_id,
                    "name": tool.name,
                    "description": tool.description,
                    "complexity": tool.integration_complexity,
                    "integration_effort": tool.integration_complexity,
                }
            )

        return {
            "tools_by_category": tools_by_category,
            "total_tools": len(AVAILABLE_TOOLS),
            "categories": [cat.value for cat in ToolCategory],
        }

    async def test_openserv_connection(self) -> dict[str, Any]:
        """Test connection from Mini-Mancer to OpenServ"""
        # This would test the reverse connection in a real implementation
        logger.info("🔗 Testing OpenServ connection...")

        return {
            "status": "success",
            "message": "Connection test completed",
            "mini_mancer_status": "operational",
            "timestamp": datetime.now().isoformat(),
            "test_type": "mini_mancer_to_openserv",
        }

    async def health_check(self) -> dict[str, Any]:
        """Health check endpoint for OpenServ to verify Mini-Mancer"""
        bot_status = "enabled" if self.telegram_manager.is_bot_creation_available() else "disabled"

        return {
            "status": "healthy",
            "service": "mini-mancer",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "fastapi": "operational",
                "telegram": "operational",
                "agno_agi": "operational",
                "bot_creation": bot_status,
            },
        }

    async def openserv_ping(self, request: Request) -> dict[str, Any]:
        """Simple ping endpoint for connectivity testing"""
        body = await request.json()

        return {
            "status": "pong",
            "received": body,
            "timestamp": datetime.now().isoformat(),
            "service": "mini-mancer",
        }

    async def openserv_do_task(self, request: OpenServTaskRequest) -> dict[str, Any]:
        """Execute a task from OpenServ workflow"""
        logger.info(f"🎯 OpenServ task: {request.task_type} (ID: {request.task_id})")

        # Task execution logic would go here
        # For now, simulate task processing

        return {
            "task_id": request.task_id,
            "status": "completed",
            "result": f"Task {request.task_type} processed successfully",
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": 150,
        }

    async def openserv_respond_chat(self, request: OpenServChatRequest) -> dict[str, Any]:
        """Handle chat message from OpenServ"""
        logger.info(f"💬 OpenServ chat message from {request.user_id}: {request.message[:50]}...")

        try:
            # Use the agno agent to generate a response
            if self.agno_agent:
                response = self.agno_agent.run(request.message)
                content = response.content if hasattr(response, "content") else str(response)
            else:
                content = "I received your message, but I'm in a simplified mode right now."

            return {
                "response": content,
                "chat_id": request.chat_id,
                "user_id": request.user_id,
                "timestamp": datetime.now().isoformat(),
                "processed_by": "agno_agent",
            }

        except Exception as e:
            logger.error(f"❌ Chat response failed: {e}")
            return {
                "response": "I'm sorry, I encountered an error processing your message.",
                "chat_id": request.chat_id,
                "user_id": request.user_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    async def test_monitor_dashboard(self) -> HTMLResponse:
        """Serve the test monitoring dashboard"""
        return HTMLResponse(content=get_dashboard_html())

    async def test_monitor_websocket(self, websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time test monitoring"""
        await websocket.accept()
        logger.info("🔌 Test monitor WebSocket connected")

        try:
            # Send initial connection confirmation
            await websocket.send_json(
                {
                    "type": "connection",
                    "status": "connected",
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Register this websocket with the monitor
            await monitor.connect_websocket(websocket)

            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for messages from client (like ping/keepalive)
                    data = await websocket.receive_json()

                    # Echo back for keepalive
                    if data.get("type") == "ping":
                        await websocket.send_json(
                            {"type": "pong", "timestamp": datetime.now().isoformat()}
                        )

                except Exception as e:
                    logger.debug(f"WebSocket message error: {e}")
                    break

        except WebSocketDisconnect:
            logger.info("🔌 Test monitor WebSocket disconnected")
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
        finally:
            # Clean up the websocket registration
            monitor.disconnect_websocket(websocket)

    async def get_test_events(self, limit: int = 100, event_type: str | None = None) -> dict[str, Any]:
        """Get recent test events for monitoring"""
        events = monitor.get_events(limit=limit, event_type=event_type)

        return {
            "events": [
                TestMonitorEvent(event_type=event["type"], timestamp=event["timestamp"], data=event)
                for event in events
            ],
            "total_returned": len(events),
            "filter_applied": event_type is not None,
        }

    async def get_test_stats(self) -> TestMonitorStats:
        """Get test monitoring statistics"""
        stats = monitor.get_stats()

        return TestMonitorStats(
            total_events=stats.get("total_events", 0),
            events_by_type=stats.get("events_by_type", {}),
            uptime_seconds=stats.get("uptime_seconds", 0),
        )
