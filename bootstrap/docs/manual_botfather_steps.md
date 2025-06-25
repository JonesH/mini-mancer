# Manual BotFather Steps for New BotMother

## Step 1: Create New Bot via @BotFather

1. **Start conversation with @BotFather**
   - Send: `/newbot`

2. **Set bot name**
   - Send: `Bootstrap BotMother MVP`

3. **Set bot username**
   - Send: `BootstrapBotMotherMVP_bot`
   - (If taken, try: `BootstrapBotMotherV2_bot`, `BootstrapBotMother2024_bot`, etc.)

4. **Copy the token**
   - BotFather will respond with the bot token
   - Format: `1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ`

## Step 2: Configure Bot Commands

1. **Set commands**
   - Send: `/setcommands`
   - Select your new bot
   - Send this command list:

```
start - Welcome message and introduction to BotMother
help - Get help and guidance on bot creation
create_bot - Start the process of creating a new Telegram bot
list_bots - View all bots you've created
configure_bot - Configure settings for an existing bot
bot_status - Check the status of your bots
```

## Step 3: Set Bot Description

1. **Set description**
   - Send: `/setdescription`
   - Select your new bot
   - Send:

```
🤖 BotMother - Your Intelligent Bot Factory

I'm an AI-powered assistant that helps you create and manage Telegram bots. Whether you're looking to build a simple chatbot or a complex automation tool, I'll guide you through the entire process with intelligent conversations and step-by-step assistance.

✨ Powered by Agno intelligence with advanced memory capabilities
🔧 Built with the Bootstrap Mini-Mancer MVP system
```

## Step 4: Set Short Description

1. **Set about text**
   - Send: `/setabouttext`
   - Select your new bot
   - Send: `🤖 AI-powered bot creation assistant. Create and manage Telegram bots with intelligent guidance!`

## Step 5: Update Environment

After getting the new token, update your `.env` file:

```bash
# Replace the BOT_MOTHER_TOKEN with your new token
BOT_MOTHER_TOKEN=YOUR_NEW_TOKEN_HERE
```

Then restart docker compose.