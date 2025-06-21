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
        """Generate complete system prompt from DNA with advanced personality framework"""
        if self.system_prompt:
            return self.system_prompt
            
        return self._build_advanced_system_prompt()
    
    def _build_advanced_system_prompt(self) -> str:
        """Build sophisticated multi-layered system prompt"""
        prompt_sections = []
        
        # Advanced identity section
        prompt_sections.append(self._build_identity_section())
        
        # Multi-dimensional personality matrix
        prompt_sections.append(self._build_personality_matrix())
        
        # Intelligence and capability framework
        prompt_sections.append(self._build_capability_framework())
        
        # Behavioral and interaction guidelines
        prompt_sections.append(self._build_behavioral_guidelines())
        
        # Communication and response patterns
        prompt_sections.append(self._build_communication_patterns())
        
        # Quality assurance and consistency framework
        prompt_sections.append(self._build_quality_framework())
        
        return "\n".join(filter(None, prompt_sections))
    
    def _build_identity_section(self) -> str:
        """Build comprehensive identity section"""
        identity_parts = []
        
        # Core identity
        identity_parts.append(f"# IDENTITY & MISSION")
        identity_parts.append(f"You are **{self.name}**, an AI assistant with a clear purpose: {self.purpose}")
        
        # Complexity and sophistication level
        if self.complexity_level != "simple":
            identity_parts.append(f"Your design reflects {self.complexity_level} sophistication in both reasoning and interaction.")
        
        # Knowledge domains as expertise areas
        if self.knowledge_domains:
            expertise = ', '.join(self.knowledge_domains)
            identity_parts.append(f"Your areas of expertise: {expertise}")
        
        return "\n".join(identity_parts)
    
    def _build_personality_matrix(self) -> str:
        """Build multi-dimensional personality representation"""
        if not self.personality:
            return ""
            
        personality_parts = []
        personality_parts.append("\n# PERSONALITY MATRIX")
        
        # Core personality traits with behavioral implications
        for trait in self.personality:
            behavior_patterns = self._get_trait_behaviors(trait)
            personality_parts.append(f"**{trait.value.title()}**: {behavior_patterns}")
        
        # Communication style integration
        if self.communication_style != "conversational":
            personality_parts.append(f"\n**Communication Style**: {self.communication_style}")
            personality_parts.append(self._get_communication_examples(self.communication_style))
        
        # Response tone integration
        if self.response_tone != "friendly":
            personality_parts.append(f"**Response Tone**: {self.response_tone}")
        
        # Custom behavioral patterns
        if self.behavioral_patterns:
            personality_parts.append("\n**Behavioral Patterns**:")
            for pattern in self.behavioral_patterns:
                personality_parts.append(f"- {pattern}")
        
        # Unique personality quirks
        if self.personality_quirks:
            personality_parts.append("\n**Personality Quirks**:")
            for quirk in self.personality_quirks:
                personality_parts.append(f"- {quirk}")
        
        return "\n".join(personality_parts)
    
    def _build_capability_framework(self) -> str:
        """Build intelligent capability and tool integration framework"""
        if not self.capabilities:
            return ""
            
        capability_parts = []
        capability_parts.append("\n# CAPABILITY FRAMEWORK")
        
        # Categorize capabilities
        capability_categories = self._categorize_capabilities()
        
        for category, caps in capability_categories.items():
            if caps:
                capability_parts.append(f"\n**{category}**:")
                for cap in caps:
                    usage_context = self._get_capability_usage_context(cap)
                    capability_parts.append(f"- **{cap.value.replace('_', ' ').title()}**: {usage_context}")
        
        # Integration guidelines
        capability_parts.append("\n**Integration Guidelines**:")
        capability_parts.append("- Use capabilities that enhance your core purpose and personality")
        capability_parts.append("- Combine tools intelligently for optimal user experience")
        capability_parts.append("- Adapt tool usage to user context and conversation flow")
        
        return "\n".join(capability_parts)
    
    def _build_behavioral_guidelines(self) -> str:
        """Build behavioral and interaction guidelines"""
        guidelines_parts = []
        guidelines_parts.append("\n# BEHAVIORAL GUIDELINES")
        
        # Core behavioral principles
        guidelines_parts.append("**Core Principles**:")
        guidelines_parts.append("- Maintain personality consistency across all interactions")
        guidelines_parts.append("- Focus on your core purpose while being helpful and engaging")
        guidelines_parts.append("- Adapt communication style to user needs and context")
        
        # Personality-driven behavior
        if self.personality:
            primary_trait = self.personality[0]
            guidelines_parts.append(f"\n**Primary Behavioral Pattern ({primary_trait.value})**:")
            guidelines_parts.append(self._get_behavioral_guidance(primary_trait))
        
        # Response quality standards
        guidelines_parts.append("\n**Quality Standards**:")
        guidelines_parts.append("- Provide responses that align with your purpose and personality")
        guidelines_parts.append("- Use capabilities thoughtfully to enhance user experience")
        guidelines_parts.append("- Maintain engagement while respecting user preferences")
        
        return "\n".join(guidelines_parts)
    
    def _build_communication_patterns(self) -> str:
        """Build communication and response patterns"""
        communication_parts = []
        communication_parts.append("\n# COMMUNICATION PATTERNS")
        
        # Response formatting preferences
        if self.response_format_preferences:
            communication_parts.append("**Response Format Preferences**:")
            for preference in self.response_format_preferences:
                communication_parts.append(f"- {preference}")
        
        # Platform-specific adaptations
        if self.target_platform == PlatformTarget.TELEGRAM:
            communication_parts.append("\n**Telegram Optimization**:")
            communication_parts.append("- Use <b>bold</b> formatting for emphasis")
            communication_parts.append("- Include emojis to enhance personality expression")
            communication_parts.append("- Keep responses scannable and well-structured")
            communication_parts.append("- Adapt message length to content complexity and user needs")
        
        return "\n".join(communication_parts)
    
    def _build_quality_framework(self) -> str:
        """Build quality assurance and consistency framework"""
        quality_parts = []
        quality_parts.append("\n# QUALITY ASSURANCE")
        
        quality_parts.append("**Consistency Checks**:")
        quality_parts.append("- Ensure responses reflect your defined personality traits")
        quality_parts.append("- Verify capability usage aligns with your purpose")
        quality_parts.append("- Maintain communication style throughout conversations")
        
        quality_parts.append("\n**Success Metrics**:")
        quality_parts.append("- User interactions should feel natural and engaging")
        quality_parts.append("- Responses should demonstrate your unique personality")
        quality_parts.append("- Tool usage should enhance rather than complicate interactions")
        
        return "\n".join(quality_parts)
    
    def _get_trait_behaviors(self, trait: AgentPersonality) -> str:
        """Get behavioral patterns for personality traits"""
        behavior_map = {
            AgentPersonality.HELPFUL: "Proactive assistance, supportive guidance, encouraging responses",
            AgentPersonality.PROFESSIONAL: "Structured communication, goal-oriented responses, reliable information",
            AgentPersonality.CASUAL: "Relaxed conversational style, informal language, approachable manner",
            AgentPersonality.ENTHUSIASTIC: "Energetic responses, positive language, excited engagement",
            AgentPersonality.WITTY: "Clever observations, light humor, entertaining interactions",
            AgentPersonality.CALM: "Patient responses, gentle guidance, peaceful interactions",
            AgentPersonality.ANALYTICAL: "Systematic thinking, logical analysis, evidence-based responses",
            AgentPersonality.CREATIVE: "Innovative solutions, imaginative responses, artistic appreciation",
            AgentPersonality.EMPATHETIC: "Understanding responses, emotional awareness, compassionate guidance"
        }
        return behavior_map.get(trait, "Consistent personality expression")
    
    def _get_communication_examples(self, style: str) -> str:
        """Get communication style examples"""
        style_map = {
            "formal": "Use structured language, professional terminology, and complete sentences",
            "casual": "Use conversational language, contractions, and friendly expressions",
            "technical": "Use precise terminology, detailed explanations, and systematic approaches",
            "creative": "Use colorful language, metaphors, and imaginative expressions"
        }
        return style_map.get(style, "Maintain consistent communication approach")
    
    def _categorize_capabilities(self) -> dict[str, list[AgentCapability]]:
        """Categorize capabilities into logical groups"""
        categories = {
            "Communication": [],
            "Information": [],
            "Productivity": [],
            "Creative": [],
            "Technical": []
        }
        
        category_mapping = {
            AgentCapability.CHAT: "Communication",
            AgentCapability.LANGUAGE_TUTORING: "Communication",
            AgentCapability.WEB_SEARCH: "Information",
            AgentCapability.WEATHER_ANALYSIS: "Information",
            AgentCapability.WISDOM_SHARING: "Information",
            AgentCapability.REMINDERS: "Productivity",
            AgentCapability.TIME_MANAGEMENT: "Productivity",
            AgentCapability.CALCULATIONS: "Productivity",
            AgentCapability.MEMORY_MANAGEMENT: "Productivity",
            AgentCapability.CREATIVE_WRITING: "Creative",
            AgentCapability.RANDOM_GENERATION: "Creative",
            AgentCapability.IMAGE_ANALYSIS: "Technical",
            AgentCapability.CODE_ASSISTANCE: "Technical",
            AgentCapability.FILE_HANDLING: "Technical"
        }
        
        for capability in self.capabilities:
            category = category_mapping.get(capability, "Technical")
            categories[category].append(capability)
        
        return {k: v for k, v in categories.items() if v}  # Return only non-empty categories
    
    def _get_capability_usage_context(self, capability: AgentCapability) -> str:
        """Get usage context for capabilities"""
        context_map = {
            AgentCapability.CHAT: "Engage in natural conversations with personality-driven responses",
            AgentCapability.WEB_SEARCH: "Find current information to support user needs",
            AgentCapability.WEATHER_ANALYSIS: "Provide weather insights and forecasting",
            AgentCapability.CALCULATIONS: "Perform mathematical operations and analysis",
            AgentCapability.REMINDERS: "Help users manage tasks and important events",
            AgentCapability.CREATIVE_WRITING: "Assist with creative content and storytelling",
            AgentCapability.CODE_ASSISTANCE: "Provide programming help and technical guidance",
            AgentCapability.IMAGE_ANALYSIS: "Analyze and describe visual content"
        }
        return context_map.get(capability, "Support user needs with this capability")
    
    def _get_behavioral_guidance(self, trait: AgentPersonality) -> str:
        """Get specific behavioral guidance for primary trait"""
        guidance_map = {
            AgentPersonality.HELPFUL: "Prioritize user needs, offer proactive assistance, maintain supportive tone",
            AgentPersonality.PROFESSIONAL: "Use structured responses, focus on efficiency, provide reliable information",
            AgentPersonality.CREATIVE: "Embrace imaginative solutions, use colorful language, inspire innovation",
            AgentPersonality.ANALYTICAL: "Apply systematic thinking, provide detailed analysis, use evidence-based reasoning"
        }
        return guidance_map.get(trait, "Express this trait consistently in all interactions")

    def clone_for_platform(self, platform: PlatformTarget) -> "AgentDNA":
        """Create a platform-specific variant of this agent"""
        cloned = self.model_copy()
        cloned.target_platform = platform
        cloned.version = f"{self.version}-{platform.value}"
        return cloned
    
    def enhance_with_context(self, user_context: dict[str, str] = None) -> "AgentDNA":
        """Enhance DNA with contextual adaptations"""
        enhanced = self.model_copy()
        
        if user_context:
            # Add context-driven behavioral patterns
            if "user_experience_level" in user_context:
                level = user_context["user_experience_level"]
                if level == "beginner":
                    enhanced.behavioral_patterns.append("Provide detailed explanations and patient guidance")
                elif level == "expert":
                    enhanced.behavioral_patterns.append("Use advanced terminology and assume technical knowledge")
            
            # Add domain-specific knowledge
            if "domain_focus" in user_context:
                domain = user_context["domain_focus"]
                if domain not in enhanced.knowledge_domains:
                    enhanced.knowledge_domains.append(domain)
        
        return enhanced
    
    def generate_personality_summary(self) -> str:
        """Generate human-readable personality summary"""
        summary_parts = []
        
        if self.personality:
            traits = [trait.value for trait in self.personality]
            summary_parts.append(f"Personality: {', '.join(traits)}")
        
        if self.communication_style != "conversational":
            summary_parts.append(f"Communication Style: {self.communication_style}")
        
        if self.response_tone != "friendly":
            summary_parts.append(f"Tone: {self.response_tone}")
        
        if self.behavioral_patterns:
            summary_parts.append(f"Key Behaviors: {'; '.join(self.behavioral_patterns[:3])}")
        
        return " | ".join(summary_parts) if summary_parts else "Standard assistant personality"
    
    def validate_coherence(self) -> dict[str, any]:
        """Validate personality and capability coherence"""
        validation_result = {
            "coherent": True,
            "issues": [],
            "suggestions": []
        }
        
        # Check personality trait coherence
        if AgentPersonality.CALM in self.personality and AgentPersonality.ENTHUSIASTIC in self.personality:
            validation_result["issues"].append("Conflicting personality traits: calm and enthusiastic")
            validation_result["coherent"] = False
        
        # Check capability-personality alignment
        if AgentPersonality.PROFESSIONAL in self.personality:
            if AgentCapability.CREATIVE_WRITING not in self.capabilities and "business" not in self.purpose.lower():
                validation_result["suggestions"].append("Consider adding productivity capabilities for professional personality")
        
        # Check communication style alignment
        if self.communication_style == "formal" and AgentPersonality.CASUAL in self.personality:
            validation_result["issues"].append("Formal communication style conflicts with casual personality")
            validation_result["coherent"] = False
        
        return validation_result


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