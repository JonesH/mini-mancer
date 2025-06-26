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

    # Initialize a list to store bot usernames
    bot_usernames = []
    pagination_buttons = True
    while pagination_buttons:
        # Fetch the latest BotFather response
        messages = await client.get_messages("BotFather", limit=1)
        if messages and messages[0].text:
            for line in messages[0].text.splitlines():
                l = line.strip()
                if l.startswith("@"):
                    bot_usernames.append(l)

            # Check for pagination buttons
            if messages[0].reply_markup and messages[0].reply_markup.rows:
                pagination_buttons = any("Next" in button.text for button in messages[0].reply_markup.rows[0].buttons)
            else:
                pagination_buttons = False
            if pagination_buttons:
                # Click the next button
                await client.send_message("BotFather", "Next")
                await asyncio.sleep(3)  # Wait for the next page
        else:
            pagination_buttons = False

    # Save the collected bot usernames to a YAML file
    os.makedirs("data", exist_ok=True)
    with open("data/botfather_bots.yaml", "w") as f:
        yaml.safe_dump(bot_usernames, f)

if __name__ == "__main__":
    asyncio.run(main())
