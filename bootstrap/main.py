import os
import asyncio
from dotenv import load_dotenv

from src.simple_botmother import SimpleBotMother

load_dotenv()

async def main():
    bot = SimpleBotMother(token=os.getenv("BOT_MOTHER_TOKEN"))
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
