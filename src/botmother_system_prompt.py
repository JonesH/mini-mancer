"""
BotMother System Prompt - The Ultimate Bot Creation Assistant

DEPRECATED: This module is maintained for backward compatibility.
New implementations should use src.prompts.botmother_prompts module.
"""

# Import from the new modular prompt system
from .prompts.botmother_prompts import BOTMOTHER_COMPLETE_SYSTEM_PROMPT


# Maintain backward compatibility
BOTMOTHER_SYSTEM_PROMPT = BOTMOTHER_COMPLETE_SYSTEM_PROMPT

# Export for easy importing
__all__ = ["BOTMOTHER_SYSTEM_PROMPT"]
