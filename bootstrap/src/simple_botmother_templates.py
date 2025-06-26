"""
Templates for SimpleBotMother replies.
"""

START_TEMPLATE = """\
🤖 **SimpleBotMother - Bot Factory**

Hello @{username}! I create simple echo bots for you.

**Available Commands:**
/create_bot <name> — Create a new echo bot
/list_bots — Show your created bots
/start_bot <name> — Start a specific bot
/stop_bot <name> — Stop a specific bot
/bot_status <name> — Check the status of a bot
/help — Show this help message

**What I do:**
✅ Create unlimited echo bots (no AI)  
✅ Auto-generate new bot tokens via @BotFather  
✅ Manage multiple bots concurrently  
✅ Start/stop bots on demand  
✅ Track all your created bots

Ready to create your first echo bot? Use `/create_bot MyBot`\
"""

CREATE_SUCCESS_TEMPLATE = """\
✅ **Echo Bot Created Successfully!**

**Bot Name:** {bot_name}  
**Username:** {escaped_username}  
**Status:** {status}  
**Link:** {telegram_link}

Your echo bot is ready! Users can start chatting with it right away.
It will echo back any message sent to it.

**Next Steps:**
• Test it: {telegram_link}  
• Start it: `/start_bot {bot_name}`  
• Check status: `/bot_status {bot_name}`\
"""

CREATE_ERROR_TEMPLATE = """\
❌ **Bot Creation Failed**

**Error:** {error}

**Troubleshooting:**
• Make sure bot tokens are available  
• Check if the bot name is unique  
• Try again in a few moments\
"""

STARTBOT_SUCCESS_TEMPLATE = """\
✅ **Bot Started Successfully!**

**Bot:** {bot_name}  
**Username:** {escaped_username}  
**Status:** Running

Your bot is now live and ready to receive messages!
Users can start chatting with it immediately.\
"""

STARTBOT_ERROR_TEMPLATE = """\
❌ **Failed to Start Bot**

**Bot:** {bot_name}  
**Error:** {error}

**Troubleshooting:**
• Check if the bot exists: `/list_bots`  
• Make sure you own this bot  
• Try stopping and starting again\
"""

STOPBOT_SUCCESS_TEMPLATE = """\
⏹️ **Bot Stopped Successfully!**

**Bot:** {bot_name}  
**Username:** {escaped_username}  
**Status:** Stopped

The bot is no longer responding to messages.
You can start it again with `/start_bot {bot_name}`\
"""

STOPBOT_ERROR_TEMPLATE = """\
❌ **Failed to Stop Bot**

**Bot:** {bot_name}  
**Error:** {error}

**Troubleshooting:**
• Check if the bot exists: `/list_bots`  
• Make sure the bot is currently running  
• Verify you own this bot\
"""

STATUS_FOUND_TEMPLATE = """\
📊 **Bot Status Report**

**{bot_name}**

**Username:** {escaped_username}  
**Status:** {status}  
**Created:** {created}  
**Link:** {telegram_link}

**Actions:**
• Start: `/start_bot {bot_name}`
• Stop: `/stop_bot {bot_name}`\
"""

STATUS_NOTFOUND_TEMPLATE = """\
❌ **Bot Not Found**

**Bot:** {bot_name}

The bot '{bot_name}' was not found in your bot list.

**Check your bots:** `/list_bots`  
**Create new bot:** `/create_bot <name>`\
"""
