"""
API Models for Mini-Mancer OpenServ Integration

Pydantic models for request/response handling in the FastAPI application.
Extracted from prototype_agent.py for better organization.
"""

from typing import Any

from pydantic import BaseModel


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


class BotCompilationRequest(BaseModel):
    """OpenServ bot compilation workflow request"""
    requirements: dict[str, Any]  # BotRequirements as dict
    user_id: str
    compilation_mode: str = "standard"  # "simple", "standard", "complex"


class BotCompilationStatus(BaseModel):
    """Bot compilation status response"""
    compilation_id: str
    status: str  # "queued", "compiling", "testing", "completed", "failed"
    progress_percentage: int
    estimated_completion: str
    bot_preview: dict[str, Any] | None = None


class TestMonitorEvent(BaseModel):
    """Test monitoring event model"""
    event_type: str
    timestamp: str
    data: dict[str, Any]


class TestMonitorStats(BaseModel):
    """Test monitoring statistics model"""
    total_events: int
    events_by_type: dict[str, int]
    uptime_seconds: float
