import os
import yaml
import re
import asyncio
from dotenv import load_dotenv
from src.telethon_client import TelethonSessionManager

load_dotenv()

async def main():
    # initialize a Telethon user-client for BotFather
    session = TelethonSessionManager("list_botfather_bots")
    client = await session.initialize_client()

    # ask BotFather for your bot list
    print("🔍 Sending /tokens to BotFather...")
    await client.send_message("BotFather", "/tokens")
    await asyncio.sleep(3)   # give BotFather time to reply
    print("⏳ Received reply from BotFather, processing list...")

    bot_usernames = []
    messages = await client.get_messages("BotFather", limit=1)
    if messages and messages[0].text:
        print("💬 Raw message text:")
        print(messages[0].text)
        for line in messages[0].text.splitlines():
            l = line.strip()
            if l.startswith("@"):
                bot_usernames.append(l)
        print(f"🎯 Final bot list ({len(bot_usernames)}): {bot_usernames}")
    else:
        print("❌ No response from BotFather")
    # Retrieve tokens for each bot via BotFather callbacks
    token_map = {}
    for username in bot_usernames:
        print(f"🔍 Retrieving token for {username}")
        await client.send_message("BotFather", "/token")
        await asyncio.sleep(1)
        await client.send_message("BotFather", username)
        await asyncio.sleep(3)
        messages = await client.get_messages("BotFather", limit=3)
        for msg in messages:
            if msg.text:
                match = re.search(r'(\d+:[A-Za-z0-9_-]+)', msg.text)
                if match:
                    token_map[username] = match.group(1)
                    print(f"🔑 Token for {username}: {token_map[username][:10]}...")
                    break
    # Save the collected data to a YAML file
    os.makedirs("data", exist_ok=True)
    with open("data/botfather_bots.yaml", "w") as f:
        yaml.safe_dump({
            "bot_usernames": bot_usernames,
            "bot_tokens": token_map
        }, f)

if __name__ == "__main__":
    asyncio.run(main())
