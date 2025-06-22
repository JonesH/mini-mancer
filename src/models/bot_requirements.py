"""
Bot Requirements System - Comprehensive bot specification and validation

This module handles sophisticated bot requirement gathering, validation,
and compilation for creating high-quality, purpose-built bots.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BotComplexity(Enum):
    """Bot complexity levels"""
    SIMPLE = "simple"      # Quick creation, basic personality
    STANDARD = "standard"  # Moderate requirements gathering
    COMPLEX = "complex"    # Full architect mode with extensive requirements
    ENTERPRISE = "enterprise"  # Maximum sophistication and validation


class ToolCategory(Enum):
    """Categories of available tools"""
    PRODUCTIVITY = "productivity"
    COMMUNICATION = "communication"
    RESEARCH = "research"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    ENTERTAINMENT = "entertainment"
    ANALYTICAL = "analytical"


class PersonalityTrait(Enum):
    """Sophisticated personality traits beyond simple descriptors"""
    ANALYTICAL = "analytical"
    EMPATHETIC = "empathetic"
    ENTHUSIASTIC = "enthusiastic"
    METHODICAL = "methodical"
    CREATIVE = "creative"
    PROFESSIONAL = "professional"
    HUMOROUS = "humorous"
    PATIENT = "patient"
    DIRECT = "direct"
    SUPPORTIVE = "supportive"
    CURIOUS = "curious"
    RELIABLE = "reliable"


class CommunicationStyle(Enum):
    """Communication style preferences"""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"
    CONCISE = "concise"
    DETAILED = "detailed"
    ENCOURAGING = "encouraging"
    INSTRUCTIONAL = "instructional"


class BotTool(BaseModel):
    """Individual bot tool specification"""
    name: str
    category: ToolCategory
    description: str
    integration_complexity: str  # "simple", "moderate", "complex"
    required_apis: list[str] = Field(default_factory=list)


class UseCase(BaseModel):
    """Specific use case scenario for the bot"""
    scenario: str
    user_input_example: str
    expected_response_style: str
    success_criteria: str


class BotRequirements(BaseModel):
    """Comprehensive bot requirements specification"""

    # Core Identity
    name: str
    purpose: str
    target_audience: str
    complexity_level: BotComplexity

    # Personality Architecture
    core_traits: list[PersonalityTrait] = Field(min_items=3, max_items=5)
    communication_style: CommunicationStyle
    response_tone: str  # "friendly", "professional", "quirky", etc.
    behavioral_patterns: list[str] = Field(default_factory=list)
    personality_quirks: list[str] = Field(default_factory=list)

    # Functional Requirements
    primary_use_cases: list[UseCase] = Field(min_items=1, max_items=5)
    required_knowledge_domains: list[str] = Field(default_factory=list)
    response_format_preferences: list[str] = Field(default_factory=list)

    # Tool Strategy
    selected_tools: list[BotTool] = Field(max_items=3)
    tool_integration_strategy: str

    # Constraints and Boundaries
    content_boundaries: list[str] = Field(default_factory=list)
    technical_limitations: list[str] = Field(default_factory=list)
    response_length_preference: str = "moderate"  # "concise", "moderate", "detailed"

    # Quality Assurance
    test_scenarios: list[str] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    estimated_complexity_score: float = 0.0
    openserv_workflow_required: bool = False


class RequirementsValidator:
    """Validates and scores bot requirements for quality and completeness"""

    @staticmethod
    def validate_requirements(requirements: BotRequirements) -> dict[str, Any]:
        """
        Validate bot requirements and return validation report
        
        Returns:
            dict with validation status, score, and recommendations
        """
        score = 0.0
        issues = []
        recommendations = []

        # Core identity validation
        if len(requirements.purpose) > 20:
            score += 10
        else:
            issues.append("Purpose description is too brief")

        if len(requirements.target_audience) > 10:
            score += 10
        else:
            issues.append("Target audience needs more detail")

        # Personality depth validation
        if len(requirements.core_traits) >= 3:
            score += 15
        else:
            issues.append("Need at least 3 core personality traits")

        if len(requirements.behavioral_patterns) > 0:
            score += 10
        else:
            recommendations.append("Consider adding behavioral patterns for richer personality")

        # Use case validation
        if len(requirements.primary_use_cases) > 0:
            score += 20
            for use_case in requirements.primary_use_cases:
                if len(use_case.expected_response_style) > 10:
                    score += 5
        else:
            issues.append("Need at least one detailed use case")

        # Tool strategy validation
        if len(requirements.selected_tools) > 0:
            score += 15
            if requirements.tool_integration_strategy:
                score += 10
        else:
            issues.append("Need to select appropriate tools")

        # Quality assurance validation
        if len(requirements.test_scenarios) > 0:
            score += 10
        else:
            recommendations.append("Add test scenarios for better validation")

        # Determine if OpenServ workflow is needed
        openserv_required = (
            requirements.complexity_level in [BotComplexity.COMPLEX, BotComplexity.ENTERPRISE] or
            len(requirements.selected_tools) > 1 or
            len(requirements.primary_use_cases) > 2
        )

        requirements.estimated_complexity_score = score
        requirements.openserv_workflow_required = openserv_required

        return {
            "valid": len(issues) == 0,
            "score": score,
            "max_score": 100,
            "completion_percentage": min(score, 100),
            "issues": issues,
            "recommendations": recommendations,
            "openserv_required": openserv_required,
            "quality_level": RequirementsValidator._get_quality_level(score)
        }

    @staticmethod
    def _get_quality_level(score: float) -> str:
        """Determine quality level based on score"""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Acceptable"
        else:
            return "Needs Improvement"


class BotArchitect:
    """Handles sophisticated bot architecture and compilation"""

    @staticmethod
    def generate_system_prompt(requirements: BotRequirements) -> str:
        """Generate comprehensive system prompt from requirements"""

        # Core identity section
        identity_section = f"""
You are {requirements.name}, {requirements.purpose}.

Your primary mission is to serve {requirements.target_audience} by providing exceptional assistance.

## Your Personality
Core traits: {', '.join([trait.value for trait in requirements.core_traits])}
Communication style: {requirements.communication_style.value}
Response tone: {requirements.response_tone}
"""

        # Behavioral patterns
        if requirements.behavioral_patterns:
            behavior_section = f"""
## Your Behavioral Patterns
{chr(10).join([f"- {pattern}" for pattern in requirements.behavioral_patterns])}
"""
        else:
            behavior_section = ""

        # Personality quirks
        if requirements.personality_quirks:
            quirks_section = f"""
## Your Unique Quirks
{chr(10).join([f"- {quirk}" for quirk in requirements.personality_quirks])}
"""
        else:
            quirks_section = ""

        # Knowledge domains
        if requirements.required_knowledge_domains:
            knowledge_section = f"""
## Your Areas of Expertise
{chr(10).join([f"- {domain}" for domain in requirements.required_knowledge_domains])}
"""
        else:
            knowledge_section = ""

        # Response preferences
        response_section = f"""
## Response Guidelines
Response length preference: {requirements.response_length_preference}
"""

        if requirements.response_format_preferences:
            response_section += f"""
Format preferences:
{chr(10).join([f"- {pref}" for pref in requirements.response_format_preferences])}
"""

        # Boundaries and limitations
        if requirements.content_boundaries:
            boundaries_section = f"""
## Content Boundaries
{chr(10).join([f"- {boundary}" for boundary in requirements.content_boundaries])}
"""
        else:
            boundaries_section = ""

        # Tool capabilities
        if requirements.selected_tools:
            tools_section = f"""
## Your Tool Capabilities
{chr(10).join([f"- {tool.name}: {tool.description}" for tool in requirements.selected_tools])}

Tool integration strategy: {requirements.tool_integration_strategy}
"""
        else:
            tools_section = ""

        # Combine all sections
        full_prompt = f"{identity_section}{behavior_section}{quirks_section}{knowledge_section}{response_section}{boundaries_section}{tools_section}"

        return full_prompt.strip()

    @staticmethod
    def generate_agno_agent_config(requirements: BotRequirements) -> dict[str, Any]:
        """Generate Agno agent configuration from requirements"""

        return {
            "name": requirements.name,
            "description": BotArchitect.generate_system_prompt(requirements),
            "model": "gpt-4o-mini",  # Default model
            "markdown": True,
            "add_history_to_messages": True,
            "num_history_responses": 3 if requirements.complexity_level in [BotComplexity.COMPLEX, BotComplexity.ENTERPRISE] else 1,
            "add_datetime_to_instructions": True,
            "max_tool_calls": len(requirements.selected_tools) * 2 if requirements.selected_tools else 1,
            "show_tool_calls": requirements.complexity_level in [BotComplexity.COMPLEX, BotComplexity.ENTERPRISE],
            "debug_mode": False,
            "structured_outputs": requirements.complexity_level == BotComplexity.ENTERPRISE
        }


# Available tool definitions
AVAILABLE_TOOLS = {
    "weather_oracle": BotTool(
        name="Weather Oracle",
        category=ToolCategory.RESEARCH,
        description="Real-time weather insights with personality",
        integration_complexity="simple"
    ),
    "wisdom_dispenser": BotTool(
        name="Wisdom Dispenser",
        category=ToolCategory.COMMUNICATION,
        description="Curated quotes, facts, and daily insights",
        integration_complexity="simple"
    ),
    "dice_commander": BotTool(
        name="Dice Commander",
        category=ToolCategory.ENTERTAINMENT,
        description="Gaming, decision-making, random number magic",
        integration_complexity="simple"
    ),
    "time_guardian": BotTool(
        name="Time Guardian",
        category=ToolCategory.PRODUCTIVITY,
        description="Pomodoro timers, reminders, productivity tracking",
        integration_complexity="moderate"
    ),
    "calculator_sage": BotTool(
        name="Calculator Sage",
        category=ToolCategory.ANALYTICAL,
        description="Mathematical computations with flair",
        integration_complexity="simple"
    ),
    "memory_keeper": BotTool(
        name="Memory Keeper",
        category=ToolCategory.PRODUCTIVITY,
        description="Note-taking, list management, personal assistant features",
        integration_complexity="moderate"
    ),
    "web_searcher": BotTool(
        name="Web Searcher",
        category=ToolCategory.RESEARCH,
        description="Real-time internet research and information gathering",
        integration_complexity="complex",
        required_apis=["search_api"]
    ),
    "code_assistant": BotTool(
        name="Code Assistant",
        category=ToolCategory.TECHNICAL,
        description="Programming help, code review, and technical guidance",
        integration_complexity="moderate"
    ),
    "language_tutor": BotTool(
        name="Language Tutor",
        category=ToolCategory.COMMUNICATION,
        description="Translation, language learning, and communication help",
        integration_complexity="moderate"
    ),
    "creative_writer": BotTool(
        name="Creative Writer",
        category=ToolCategory.CREATIVE,
        description="Story generation, creative writing, and content creation",
        integration_complexity="simple"
    )
}
