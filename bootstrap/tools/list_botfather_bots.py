import os
import yaml
import asyncio
from dotenv import load_dotenv
from src.botfather_integration import BotFatherIntegration

load_dotenv()

async def main():
    bf = BotFatherIntegration()
    out = []
    # assume BOT_TOKEN_1…BOT_TOKEN_N in env
    for k, v in os.environ.items():
        if k.startswith("BOT_TOKEN_"):
            info = await bf.validate_bot_token(v)
            out.append({
                "token_env": k,
                "bot_id": info.get("id"),
                "username": info.get("username"),
                "first_name": info.get("first_name"),
                "description": info.get("description", "")
            })
    os.makedirs("bootstrap/data", exist_ok=True)
    with open("bootstrap/data/botfather_bots.yaml", "w") as f:
        yaml.safe_dump(out, f)

if __name__ == "__main__":
    asyncio.run(main())
