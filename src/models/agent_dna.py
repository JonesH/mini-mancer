"""
AgentDNA - Core domain models for defining and spawning AI agents.

Minimal, composable models that capture the essence of an agent's identity,
capabilities, and behavioral patterns for replication across platforms.
"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class AgentPersonality(str, Enum):
    """Core personality archetypes for agents"""
    HELPFUL = "helpful"
    WITTY = "witty" 
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"
    PLAYFUL = "playful"


class AgentCapability(str, Enum):
    """Core capabilities that agents can possess"""
    CHAT = "chat"
    IMAGE_ANALYSIS = "image_analysis"
    WEB_SEARCH = "web_search"
    FILE_HANDLING = "file_handling"
    SCHEDULING = "scheduling"
    REMINDERS = "reminders"
    CALCULATIONS = "calculations"
    TRANSLATIONS = "translations"


class PlatformTarget(str, Enum):
    """Supported platforms for agent deployment"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    WEB = "web"


class AgentDNA(BaseModel):
    """
    The complete genetic blueprint for an AI agent.
    Contains all information needed to spawn identical agents across platforms.
    """
    
    # Core Identity
    name: str = Field(..., description="Agent's display name")
    purpose: str = Field(..., description="Primary function or role")
    
    # Behavioral Traits
    personality: list[AgentPersonality] = Field(
        default_factory=list,
        description="Core personality traits"
    )
    
    # Functional Capabilities
    capabilities: list[AgentCapability] = Field(
        default_factory=list,
        description="What the agent can do"
    )
    
    # Platform Configuration
    target_platform: PlatformTarget = Field(
        default=PlatformTarget.TELEGRAM,
        description="Primary deployment platform"
    )
    
    # Prompt Engineering
    system_prompt: str = Field(
        default="",
        description="Base system prompt template"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0.0")
    
    def generate_system_prompt(self) -> str:
        """Generate complete system prompt from DNA"""
        if self.system_prompt:
            return self.system_prompt
            
        personality_desc = ", ".join([p.value for p in self.personality])
        capabilities_desc = ", ".join([c.value.replace("_", " ") for c in self.capabilities])
        
        return f"""You are {self.name}, an AI assistant whose purpose is: {self.purpose}

Your personality traits: {personality_desc}
Your capabilities include: {capabilities_desc}

Be consistent with your personality and focus on your core purpose while being helpful and engaging."""

    def clone_for_platform(self, platform: PlatformTarget) -> "AgentDNA":
        """Create a platform-specific variant of this agent"""
        cloned = self.model_copy()
        cloned.target_platform = platform
        cloned.version = f"{self.version}-{platform.value}"
        return cloned


class AgentTemplate(BaseModel):
    """
    Template for generating specific types of agents.
    Contains DNA patterns and configuration for common agent archetypes.
    """
    
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template display name")
    description: str = Field(..., description="What this template creates")
    
    # Base DNA pattern
    base_dna: AgentDNA = Field(..., description="Core agent blueprint")
    
    # Customization options
    customizable_fields: list[str] = Field(
        default_factory=list,
        description="Which DNA fields users can modify"
    )
    
    # Required user inputs
    required_inputs: list[str] = Field(
        default_factory=list,
        description="Fields user must provide"
    )
    
    def instantiate(self, user_inputs: dict[str, str]) -> AgentDNA:
        """Create specific agent instance from template and user inputs"""
        dna = self.base_dna.model_copy()
        
        # Apply user customizations
        for field, value in user_inputs.items():
            if field in self.customizable_fields and hasattr(dna, field):
                setattr(dna, field, value)
        
        return dna


# Pre-built templates for common agent types
TELEGRAM_BOT_TEMPLATE = AgentTemplate(
    template_id="telegram_basic_bot",
    name="Basic Telegram Bot",
    description="A friendly, helpful Telegram bot for general conversation and assistance",
    base_dna=AgentDNA(
        name="TelegramBot",
        purpose="Provide helpful assistance and friendly conversation to Telegram users",
        personality=[AgentPersonality.HELPFUL, AgentPersonality.CASUAL],
        capabilities=[AgentCapability.CHAT, AgentCapability.IMAGE_ANALYSIS],
        target_platform=PlatformTarget.TELEGRAM
    ),
    customizable_fields=["name", "purpose", "personality"],
    required_inputs=["name", "purpose"]
)

TASK_ASSISTANT_TEMPLATE = AgentTemplate(
    template_id="task_assistant",
    name="Task Assistant Bot",
    description="A productivity-focused bot for task management and reminders",
    base_dna=AgentDNA(
        name="TaskBot",
        purpose="Help users organize tasks, set reminders, and stay productive",
        personality=[AgentPersonality.PROFESSIONAL, AgentPersonality.HELPFUL],
        capabilities=[
            AgentCapability.CHAT,
            AgentCapability.SCHEDULING,
            AgentCapability.REMINDERS,
            AgentCapability.CALCULATIONS
        ],
        target_platform=PlatformTarget.TELEGRAM
    ),
    customizable_fields=["name", "personality"],
    required_inputs=["name"]
)