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
    # Enhanced personality traits for sophisticated bots
    ANALYTICAL = "analytical"
    EMPATHETIC = "empathetic"
    METHODICAL = "methodical"
    CREATIVE = "creative"
    HUMOROUS = "humorous"
    PATIENT = "patient"
    DIRECT = "direct"
    SUPPORTIVE = "supportive"
    CURIOUS = "curious"
    RELIABLE = "reliable"


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
    # Enhanced capabilities for sophisticated bots
    WEATHER_ANALYSIS = "weather_analysis"
    WISDOM_SHARING = "wisdom_sharing"
    RANDOM_GENERATION = "random_generation"
    TIME_MANAGEMENT = "time_management"
    MEMORY_MANAGEMENT = "memory_management"
    CODE_ASSISTANCE = "code_assistance"
    CREATIVE_WRITING = "creative_writing"
    LANGUAGE_TUTORING = "language_tutoring"


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
    
    # Enhanced Personality System (for sophisticated bots)
    communication_style: str = Field(
        default="conversational",
        description="How the agent communicates (formal, casual, technical, etc.)"
    )
    response_tone: str = Field(
        default="friendly",
        description="Emotional tone of responses"
    )
    behavioral_patterns: list[str] = Field(
        default_factory=list,
        description="Specific behavioral patterns and quirks"
    )
    personality_quirks: list[str] = Field(
        default_factory=list,
        description="Unique personality traits that make the bot memorable"
    )
    
    # Functional Capabilities
    capabilities: list[AgentCapability] = Field(
        default_factory=list,
        description="What the agent can do"
    )
    
    # Knowledge and Expertise
    knowledge_domains: list[str] = Field(
        default_factory=list,
        description="Areas of specialized knowledge"
    )
    response_format_preferences: list[str] = Field(
        default_factory=list,
        description="Preferred ways to format responses (bullet points, paragraphs, etc.)"
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
    
    # Quality and Complexity
    complexity_level: str = Field(
        default="simple",
        description="Bot complexity level (simple, standard, complex, enterprise)"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0.0")
    
    def generate_system_prompt(self) -> str:
        """Generate complete system prompt from DNA"""
        if self.system_prompt:
            return self.system_prompt
            
        # Build comprehensive system prompt from enhanced DNA
        prompt_sections = []
        
        # Core identity
        prompt_sections.append(f"You are {self.name}, an AI assistant whose purpose is: {self.purpose}")
        
        # Personality traits
        if self.personality:
            personality_desc = ", ".join([p.value for p in self.personality])
            prompt_sections.append(f"\nYour core personality traits: {personality_desc}")
        
        # Communication style and tone
        if self.communication_style != "conversational" or self.response_tone != "friendly":
            prompt_sections.append(f"\nYour communication style is {self.communication_style} with a {self.response_tone} tone.")
        
        # Behavioral patterns
        if self.behavioral_patterns:
            prompt_sections.append(f"\nYour behavioral patterns:")
            for pattern in self.behavioral_patterns:
                prompt_sections.append(f"- {pattern}")
        
        # Personality quirks
        if self.personality_quirks:
            prompt_sections.append(f"\nYour unique quirks:")
            for quirk in self.personality_quirks:
                prompt_sections.append(f"- {quirk}")
        
        # Capabilities
        if self.capabilities:
            capabilities_desc = ", ".join([c.value.replace("_", " ") for c in self.capabilities])
            prompt_sections.append(f"\nYour capabilities include: {capabilities_desc}")
        
        # Knowledge domains
        if self.knowledge_domains:
            prompt_sections.append(f"\nYour areas of expertise: {', '.join(self.knowledge_domains)}")
        
        # Response formatting
        if self.response_format_preferences:
            prompt_sections.append(f"\nResponse format preferences: {', '.join(self.response_format_preferences)}")
        
        # General guidance
        prompt_sections.append(f"\nBe consistent with your personality and focus on your core purpose while being helpful and engaging.")
        
        return "\n".join(prompt_sections)

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