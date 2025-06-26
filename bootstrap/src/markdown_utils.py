"""
Markdown formatting utilities for Telegram messages.

Handles escaping of special characters that interfere with markdown formatting.
"""

def escape_markdown(text: str) -> str:
    """
    Escape markdown special characters in text to prevent formatting issues.
    
    Particularly important for bot usernames containing underscores which
    would otherwise be interpreted as italic formatting in Telegram.
    
    Args:
        text: Text that may contain markdown special characters
        
    Returns:
        Text with markdown characters properly escaped
    """
    if not text:
        return text
    
    # Escape markdown special characters
    # Order matters - escape backslashes first to avoid double-escaping
    escape_chars = {
        '\\': '\\\\',  # Backslash (must be first)
        '_': '\\_',   # Underscore (main issue for usernames)
        '*': '\\*',   # Asterisk 
        '`': '\\`',   # Backtick
        '[': '\\[',   # Left square bracket
        ']': '\\]',   # Right square bracket
    }
    
    result = text
    for char, escaped in escape_chars.items():
        result = result.replace(char, escaped)
    
    return result


def escape_username(username: str) -> str:
    """
    Escape markdown characters in a bot username.
    
    Specialized function for usernames that ensures @ prefix is preserved
    and underscores are properly escaped.
    
    Args:
        username: Bot username (with or without @ prefix)
        
    Returns:
        Username with markdown characters escaped
    """
    if not username:
        return username
    
    # Handle @ prefix separately
    if username.startswith('@'):
        prefix = '@'
        name_part = username[1:]
    else:
        prefix = ''
        name_part = username
    
    # Escape the name part
    escaped_name = escape_markdown(name_part)
    
    return f"{prefix}{escaped_name}"


def format_bot_link(username: str, display_name: str = None) -> str:
    """
    Format a bot username as a clickable link in markdown.
    
    Args:
        username: Bot username (with or without @ prefix)  
        display_name: Optional display name (defaults to username)
        
    Returns:
        Markdown-formatted clickable link
    """
    if not username:
        return ""
    
    # Ensure @ prefix
    clean_username = username.lstrip('@')
    
    # Use display name or default to username
    display = display_name or f"@{clean_username}"
    escaped_display = escape_markdown(display)
    
    # Create markdown link: [display](https://t.me/username)
    return f"[{escaped_display}](https://t.me/{clean_username})"


def safe_markdown_message(template: str, **kwargs) -> str:
    """
    Format a markdown message template with automatic escaping of variables.
    
    Args:
        template: Message template with {variable} placeholders
        **kwargs: Variables to substitute, will be automatically escaped
        
    Returns:
        Formatted message with escaped variables
    """
    # Escape all string values in kwargs
    escaped_kwargs = {}
    for key, value in kwargs.items():
        if isinstance(value, str):
            escaped_kwargs[key] = escape_markdown(value)
        else:
            escaped_kwargs[key] = value
    
    return template.format(**escaped_kwargs)


# Test function
def test_markdown_escaping():
    """Test markdown escaping functionality."""
    test_cases = [
        ("protomancer_supreme_bot", "protomancer\\_supreme\\_bot"),
        ("@test_bot_123", "@test\\_bot\\_123"),
        ("normal_text", "normal\\_text"),
        ("*bold*_italic_", "\\*bold\\*\\_italic\\_"),
        ("", ""),
        (None, None)
    ]
    
    print("🧪 Testing markdown escaping...")
    
    for input_text, expected in test_cases:
        if input_text is None:
            result = escape_markdown(input_text)
            assert result == expected, f"Failed: {input_text} -> {result} (expected {expected})"
            continue
            
        result = escape_markdown(input_text)
        print(f"  '{input_text}' -> '{result}'")
        assert result == expected, f"Failed: {input_text} -> {result} (expected {expected})"
    
    print("✅ All markdown escaping tests passed!")


if __name__ == "__main__":
    test_markdown_escaping()