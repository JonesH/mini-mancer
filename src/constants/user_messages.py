"""
User-facing message constants for Mini-Mancer bot system.

All user-facing strings are centralized here for easy management and consistency.
"""

# Welcome and help messages
WELCOME_MESSAGES = {
    "start": """🏭 <b>Mini-Mancer Factory Bot is now online!</b>

I'm ready to create custom Telegram bots for you.

<b>Examples:</b> <code>create helpful bot named Assistant</code> or <code>make professional support bot</code>

Just tell me what bot you need! ✨""",
    
    "quick_creation": """🚀 <b>Quick Bot Creation</b>

Simply tell me:
• <code>create helpful bot named Assistant</code>
• <code>make professional bot called Support</code>
• <code>new friendly bot for customer service</code>

I'll create it instantly with smart defaults! ⚡""",
    
    "personalities": """🎭 <b>Available Bot Personalities:</b>

🤝 <b>Helpful</b> - Supportive, friendly, assistant-like
💼 <b>Professional</b> - Business-focused, formal, corporate
😎 <b>Casual</b> - Relaxed, informal, approachable  
🎉 <b>Enthusiastic</b> - Energetic, upbeat, exciting
😄 <b>Witty</b> - Clever, humorous, entertaining
🧘 <b>Calm</b> - Patient, gentle, peaceful

Choose the personality that fits your bot's purpose!""",
    
    "examples": """💡 <b>Bot Creation Examples:</b>

<b>Natural Language:</b>
• <code>create helpful bot named CustomerCare for support</code>
• <code>make professional assistant called Manager</code>
• <code>new witty bot for entertainment</code>

<b>Structured Format:</b>
• <code>/create_bot name="Sales Helper" purpose="Help with sales" personality="professional"</code>
• <code>/create_bot name="Fun Bot" purpose="Entertainment" personality="witty"</code>

<b>Quick Commands:</b>
• <code>/create_quick</code> - Fast creation guide
• <code>/list_personalities</code> - See all personalities

Try any format - I understand them all! 🎯"""
}

# Bot creation success messages
BOT_CREATION_MESSAGES = {
    "instant_success": "✅ <b>{bot_name}</b> created successfully!\n\n🤖 <b>Purpose:</b> {bot_purpose}\n😊 <b>Style:</b> {personality}\n🔗 https://t.me/{bot_username}\n\nBot deploying shortly!",
    
    "advanced_compilation": "🏗️ <b>{bot_name}</b> compilation started!\n\n📊 <b>Quality:</b> {quality_score}/100\n🔧 <b>Status:</b> Compiling...\n⏱️ <b>ETA:</b> 2-3 minutes\n\n✨ Your digital companion will emerge shortly!",
    
    "advanced_success": "✅ <b>{bot_name}</b> awakened!\n\n🧠 <b>Traits:</b> {traits}\n🛠️ <b>Tools:</b> {tools}\n\n🔗 Ready for deployment!",
    
    "requirements_invalid": "❌ <b>Requirements Need Work</b>\n\n{issues}\n\nPlease provide more details."
}

# Error messages
ERROR_MESSAGES = {
    "bot_creation_error": "❌ Error creating bot: {error}",
    "advanced_creation_error": "❌ Error creating sophisticated bot: {error}",
    "general_error": "Sorry, I encountered an error: {error}",
    "unknown_content": "I received your message, but I'm not sure how to handle this type of content yet.",
    "bot_creation_disabled": "❌ Bot creation is currently disabled. BOT_TOKEN_1 is not configured.",
    "invalid_bot_name": "❌ Bot name must be at least 2 characters long.",
    "invalid_bot_purpose": "❌ Bot purpose must be at least 5 characters long.",
    "bot_start_failed": "❌ Failed to start bot: {error}",
    "bot_already_exists": "⚠️ A bot is already running. Stop the current bot first.",
    "no_bot_to_stop": "❌ No bot is currently running to stop.",
    "empty_message": "❌ Cannot process empty messages.",
    "ai_error": "❌ AI processing temporarily unavailable. Please try again.",
    "empty_response": "❌ AI generated an empty response. Please try again."
}

# File and media handling messages
MEDIA_MESSAGES = {
    "photo_no_capability": "📷 I received your photo, but I don't have image analysis capabilities enabled.",
    "photo_received": "📷 I can see you sent me a photo{caption_text}. Image analysis would happen here in a full implementation!",
    "document_no_capability": "📎 I received your file, but I don't have file handling capabilities enabled.",
    "document_received": "📎 I received your file '{filename}'. File processing would happen here in a full implementation!"
}

# Inline keyboard button texts
KEYBOARD_BUTTONS = {
    "create_helper": "🤝 Create Helper Bot",
    "create_support": "💼 Create Support Bot", 
    "create_fun": "🎉 Create Fun Bot",
    "create_calm": "🧘 Create Calm Bot",
    "custom_builder": "⚙️ Custom Builder",
    "show_examples": "📖 Examples"
}

# Chat prompt templates (for fallback responses)
CHAT_PROMPTS = {
    "factory_bot_fallback": """Respond to this chat message:
User: {user_message}
Chat ID: {chat_id}
User ID: {user_id}

You are a factory bot that can create new Telegram bots.
If the user wants to create a bot, ask them for:
- Bot name
- Bot purpose 
- Personality (helpful, professional, casual, etc.)

Provide a helpful, conversational response."""
}

# Helper functions to format messages
def format_bot_success(bot_name: str, bot_purpose: str, personality: str, bot_username: str) -> str:
    """Format instant bot creation success message"""
    return BOT_CREATION_MESSAGES["instant_success"].format(
        bot_name=bot_name,
        bot_purpose=bot_purpose, 
        personality=personality,
        bot_username=bot_username
    )

def format_advanced_compilation(bot_name: str, quality_score: int) -> str:
    """Format advanced bot compilation message"""
    return BOT_CREATION_MESSAGES["advanced_compilation"].format(
        bot_name=bot_name,
        quality_score=quality_score
    )

def format_advanced_success(bot_name: str, traits: str, tools: str) -> str:
    """Format advanced bot success message"""
    return BOT_CREATION_MESSAGES["advanced_success"].format(
        bot_name=bot_name,
        traits=traits,
        tools=tools
    )

def format_requirements_error(issues: str) -> str:
    """Format requirements validation error"""
    return BOT_CREATION_MESSAGES["requirements_invalid"].format(issues=issues)

def format_photo_message(caption: str = "") -> str:
    """Format photo received message"""
    caption_text = f" with caption: '{caption}'" if caption else ""
    return MEDIA_MESSAGES["photo_received"].format(caption_text=caption_text)

def format_document_message(filename: str) -> str:
    """Format document received message"""
    return MEDIA_MESSAGES["document_received"].format(filename=filename)

def format_chat_fallback(user_message: str, chat_id: str, user_id: str) -> str:
    """Format fallback chat prompt"""
    return CHAT_PROMPTS["factory_bot_fallback"].format(
        user_message=user_message,
        chat_id=chat_id,
        user_id=user_id
    )