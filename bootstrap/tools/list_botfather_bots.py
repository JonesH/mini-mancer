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
    print("🔍 Sending /mybots to BotFather...")
    await client.send_message("BotFather", "/mybots")
    await asyncio.sleep(3)   # give BotFather time to reply
    print("⏳ Received reply from BotFather, processing pages...")

    # Initialize lists to store bot usernames and callback IDs
    bot_usernames = []
    bot_ids = []
    pagination_buttons = True
    page = 1
    while pagination_buttons:
        print(f"--- Page {page} ---")
        # Fetch the latest BotFather response
        messages = await client.get_messages("BotFather", limit=1)
        if messages and messages[0].text:
            print("💬 Raw message text:")
            print(messages[0].text)
            for line in messages[0].text.splitlines():
                l = line.strip()
                if l.startswith("@"):
                    bot_usernames.append(l)
            print(f"✅ Found {len(bot_usernames)} bot(s) so far: {bot_usernames}")

            # Extract bot IDs from inline buttons
            if messages[0].reply_markup and messages[0].reply_markup.rows:
                for row in messages[0].reply_markup.rows:
                    for button in row.buttons:
                        text = button.text
                        if text in ("Next", "Prev", "<<", ">>", "«", "»"):
                            continue
                        if button.data:
                            data = button.data.decode()
                            bot_ids.append(data)
                            print(f"🔘 Found bot callback ID: {data} (button text: '{text}')")
            print(f"🗃️ Aggregated IDs so far: {bot_ids}")

            # Check for pagination buttons
            if messages[0].reply_markup and messages[0].reply_markup.rows:
                pagination_buttons = any("Next" in button.text for button in messages[0].reply_markup.rows[0].buttons)
            else:
                pagination_buttons = False
            if pagination_buttons:
                print("➡️ 'Next' button detected, requesting next page...")
                # Click the next button
                await client.send_message("BotFather", "Next")
                await asyncio.sleep(3)  # Wait for the next page
                page += 1
        else:
            pagination_buttons = False

    # Completed pagination, final list of bots and IDs:
    print(f"🎯 Final bot list ({len(bot_usernames)}): {bot_usernames}")
    print(f"🎯 Final bot callback IDs ({len(bot_ids)}): {bot_ids}")
    # Save the collected bot usernames to a YAML file
    os.makedirs("data", exist_ok=True)
    with open("data/botfather_bots.yaml", "w") as f:
        yaml.safe_dump(bot_usernames, f)

if __name__ == "__main__":
    asyncio.run(main())
