import re
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, validator


class BotStatus(Enum):
    CONFIGURING = "configuring"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    FAILED = "failed"


ChatStage = Literal[
    "greeting", "token_request", "name_request", "message_request", "deploying", "completed"
]
ProtoSpawnerStage = Literal[
    "token_request", "name_request", "message_request", "deploying", "completed"
]


class TelegramBotConfig(BaseModel):
    """Configuration for a Telegram bot"""

    token: str
    display_name: str
    welcome_message: str
    created_at: datetime = Field(default_factory=datetime.now)
    status: BotStatus = BotStatus.CONFIGURING

    @validator("token")
    def validate_token_format(cls, v):
        """Validate Telegram Bot API token format"""
        pattern = r"^\d+:[A-Za-z0-9_-]{35}$"
        if not re.match(pattern, v):
            raise ValueError(
                "Invalid bot token format. Expected format: 123456789:ABCdefGHIjklMNOpqrSTUvwxyz"
            )
        return v


class ChatState(BaseModel):
    """State of a chat conversation"""

    chat_id: str
    user_id: str
    stage: ChatStage = "greeting"
    bot_token: str | None = None
    display_name: str | None = None
    welcome_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class TelegramUpdate(BaseModel):
    """Telegram update structure"""

    update_id: int
    message: dict | None = None
    callback_query: dict | None = None


class BotCommand(BaseModel):
    """Telegram bot command"""

    command: str
    description: str


class OpenServResponse(BaseModel):
    """Response from OpenServ platform"""

    success: bool
    message: str
    data: dict | None = None


class ProtoSpawnerState(BaseModel):
    """State for Proto-Spawner agent"""

    user_id: str
    chat_id: str
    stage: ProtoSpawnerStage = "token_request"
    token: str | None = None
    display_name: str | None = None
    welcome_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
