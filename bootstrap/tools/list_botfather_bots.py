import os
import yaml
import asyncio
from dotenv import load_dotenv
from src.telethon_client import TelethonSessionManager

load_dotenv()

async def main():
    # initialize a Telethon user-client for BotFather
    session = TelethonSessionManager("list_botfather_bots")
    client = await session.initialize_client()

    # ask BotFather for your bot list
    await client.send_message("BotFather", "/mybots")
    await asyncio.sleep(3)   # give BotFather time to reply

    # fetch the latest BotFather response
    messages = await client.get_messages("BotFather", limit=1)
    out: list[dict] = []
    if messages and messages[0].text:
        for line in messages[0].text.splitlines():
            l = line.strip()
            if l.startswith("@"):
                out.append({"username": l})

    # clean up
    await session.disconnect()

    os.makedirs("bootstrap/data", exist_ok=True)
    with open("bootstrap/data/botfather_bots.yaml", "w") as f:
        yaml.safe_dump(out, f)

if __name__ == "__main__":
    asyncio.run(main())
