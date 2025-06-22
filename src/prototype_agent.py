"""
Minimal Prototype Agent - Integrates OpenServ + Telegram + Agno-AGI

REFACTORED: This file now imports the refactored AgentController for better organization.
The original 1000+ line god class has been broken down into focused modules:

- api_models.py: Pydantic request/response models
- telegram_integration.py: Bot creation and management
- api_router.py: FastAPI route handlers
- agent_controller.py: Core orchestration

This maintains backward compatibility while improving maintainability.
"""

# Backward compatibility imports
from .agent_controller import AgentController
from .api_models import (
    BotCompilationRequest,
    BotCompilationStatus,
    OpenServChatRequest,
    OpenServTaskRequest,
)

# For backward compatibility, expose the AgentController as PrototypeAgent
PrototypeAgent = AgentController

# Create app and prototype instances for main.py compatibility
try:
    prototype = AgentController()
    app = prototype.app
except Exception as e:
    import logging
    logging.error(f"Failed to initialize prototype agent: {e}")
    prototype = None
    app = None

# Re-export models for existing imports
__all__ = [
    "PrototypeAgent",
    "prototype",
    "app",
    "OpenServTaskRequest",
    "OpenServChatRequest",
    "BotCompilationRequest",
    "BotCompilationStatus"
]
