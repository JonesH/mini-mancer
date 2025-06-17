import httpx
from .models import TelegramBotConfig


class OpenServPlatformClient:
    """HTTP client for OpenServ platform API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openserv.dev"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )
    
    async def deploy_bot(self, config: TelegramBotConfig) -> dict:
        """Deploy a Telegram bot configuration to the platform"""
        response = await self.client.post(
            f"{self.base_url}/v1/bots/telegram/deploy",
            json={
                "token": config.token,
                "display_name": config.display_name,
                "welcome_message": config.welcome_message,
                "commands": [
                    {"command": "start", "description": "Start the bot"},
                    {"command": "help", "description": "Show help message"}
                ]
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def get_bot_status(self, bot_token: str) -> dict:
        """Get the status of a deployed bot"""
        response = await self.client.get(
            f"{self.base_url}/v1/bots/telegram/{bot_token}/status"
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()