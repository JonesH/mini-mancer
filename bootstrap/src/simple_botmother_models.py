from pydantic import BaseModel
from typing import Optional

class BotCreatorResult(BaseModel):
    success: bool
    username: Optional[str]
    status: Optional[str]
    telegram_link: Optional[str]
    error: Optional[str]
