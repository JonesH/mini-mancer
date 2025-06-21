"""
Thinking Tool - Advanced reasoning and analysis capabilities for sophisticated AI agents

This tool provides structured thinking, analysis, and reasoning capabilities
for complex decision-making and problem-solving tasks.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ThoughtProcess(BaseModel):
    """Structured representation of a thinking process"""
    topic: str
    analysis_type: str  # "requirement_analysis", "bot_design", "problem_solving", "creative_ideation"
    thoughts: List[str] = Field(default_factory=list)
    considerations: List[str] = Field(default_factory=list)
    pros_and_cons: Dict[str, List[str]] = Field(default_factory=dict)
    conclusions: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    confidence_level: float = 0.5  # 0.0 to 1.0
    timestamp: datetime = Field(default_factory=datetime.now)


class ThinkingTool:
    """
    Advanced thinking and reasoning tool for AI agents
    
    Provides structured analysis, decision-making frameworks,
    and complex reasoning capabilities.
    """
    
    def __init__(self):
        self.thought_history: List[ThoughtProcess] = []
        self.active_context: Dict[str, Any] = {}
    
    def deep_think(self, topic: str, context: Dict[str, Any] = None) -> ThoughtProcess:
        """
        Perform deep, structured thinking on a topic
        
        Args:
            topic: The subject to think about
            context: Additional context for the thinking process
            
        Returns:
            Structured thought process with analysis and conclusions
        """
        if context:
            self.active_context.update(context)
        
        thought_process = ThoughtProcess(
            topic=topic,
            analysis_type="deep_analysis"
        )
        
        # Initial thoughts
        thought_process.thoughts = [
            f"Analyzing the topic: {topic}",
            "Considering multiple perspectives and approaches",
            "Evaluating potential implications and outcomes"
        ]
        
        # Add context-specific considerations
        if context:
            for key, value in context.items():
                thought_process.considerations.append(f"Context - {key}: {value}")
        
        # Store in history
        self.thought_history.append(thought_process)
        
        return thought_process
    
    def analyze_requirements(self, requirements: Dict[str, Any]) -> ThoughtProcess:
        """
        Analyze bot requirements with structured thinking
        
        Args:
            requirements: Bot requirements to analyze
            
        Returns:
            Detailed analysis of requirements completeness and quality
        """
        thought_process = ThoughtProcess(
            topic="Bot Requirements Analysis",
            analysis_type="requirement_analysis"
        )
        
        # Analyze requirement completeness
        thought_process.thoughts.extend([
            "Examining requirement completeness and clarity",
            "Identifying potential gaps or ambiguities",
            "Assessing feasibility and complexity"
        ])
        
        # Specific considerations
        thought_process.considerations.extend([
            "Are the core purposes clearly defined?",
            "Is the target audience well-understood?",
            "Are personality traits coherent and consistent?",
            "Do selected tools align with intended use cases?",
            "Are there any conflicting requirements?"
        ])
        
        # Pros and cons
        thought_process.pros_and_cons = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "risks": []
        }
        
        # Analyze based on available requirements
        if "name" in requirements:
            thought_process.pros_and_cons["strengths"].append("Bot has clear identity")
        
        if "purpose" in requirements and len(requirements.get("purpose", "")) > 20:
            thought_process.pros_and_cons["strengths"].append("Purpose is well-defined")
        else:
            thought_process.pros_and_cons["weaknesses"].append("Purpose needs more detail")
        
        # Conclusions and next steps
        thought_process.conclusions = [
            "Requirements analysis reveals areas for enhancement",
            "Structured approach will improve bot quality"
        ]
        
        thought_process.next_steps = [
            "Gather additional details where needed",
            "Validate requirements with user",
            "Proceed with bot architecture design"
        ]
        
        thought_process.confidence_level = 0.8
        
        self.thought_history.append(thought_process)
        return thought_process
    
    def design_bot_architecture(self, requirements: Dict[str, Any]) -> ThoughtProcess:
        """
        Think through bot architecture and design decisions
        
        Args:
            requirements: Bot requirements for architecture design
            
        Returns:
            Structured thinking about optimal bot design
        """
        thought_process = ThoughtProcess(
            topic="Bot Architecture Design",
            analysis_type="bot_design"
        )
        
        thought_process.thoughts.extend([
            "Designing optimal personality architecture",
            "Selecting appropriate tools and capabilities",
            "Balancing complexity with usability",
            "Ensuring coherent user experience"
        ])
        
        # Architecture considerations
        thought_process.considerations.extend([
            "How should personality traits interact?",
            "What's the optimal tool combination?",
            "How complex should the system prompt be?",
            "What are the performance implications?",
            "How will this scale with usage?"
        ])
        
        # Design trade-offs
        thought_process.pros_and_cons = {
            "simple_design": [
                "Faster response times",
                "Easier to debug",
                "Lower complexity"
            ],
            "complex_design": [
                "Richer personality",
                "More capabilities",
                "Better user experience",
                "Higher maintenance overhead"
            ]
        }
        
        thought_process.conclusions = [
            "Architecture should match complexity requirements",
            "Personality coherence is critical for user experience",
            "Tool selection should be purposeful, not random"
        ]
        
        thought_process.next_steps = [
            "Create detailed personality matrix",
            "Map tools to specific use cases",
            "Generate comprehensive system prompt",
            "Plan testing strategy"
        ]
        
        thought_process.confidence_level = 0.9
        
        self.thought_history.append(thought_process)
        return thought_process
    
    def creative_ideation(self, prompt: str, context: Dict[str, Any] = None) -> ThoughtProcess:
        """
        Generate creative ideas and solutions
        
        Args:
            prompt: Creative prompt or challenge
            context: Additional context for ideation
            
        Returns:
            Structured creative thinking process
        """
        thought_process = ThoughtProcess(
            topic=f"Creative Ideation: {prompt}",
            analysis_type="creative_ideation"
        )
        
        thought_process.thoughts.extend([
            "Exploring creative possibilities",
            "Thinking outside conventional boundaries",
            "Combining unexpected elements",
            "Considering innovative approaches"
        ])
        
        thought_process.considerations.extend([
            "What unique perspectives can we apply?",
            "How can we surprise and delight users?",
            "What unconventional approaches might work?",
            "How can we make this memorable?"
        ])
        
        thought_process.conclusions = [
            "Creativity emerges from structured exploration",
            "Innovation requires balancing novelty with usefulness"
        ]
        
        thought_process.confidence_level = 0.7
        
        self.thought_history.append(thought_process)
        return thought_process
    
    def problem_solve(self, problem: str, constraints: List[str] = None) -> ThoughtProcess:
        """
        Structured problem-solving approach
        
        Args:
            problem: Problem statement to solve
            constraints: Any constraints or limitations
            
        Returns:
            Structured problem-solving analysis
        """
        thought_process = ThoughtProcess(
            topic=f"Problem Solving: {problem}",
            analysis_type="problem_solving"
        )
        
        thought_process.thoughts.extend([
            "Breaking down the problem into components",
            "Identifying root causes and contributing factors",
            "Exploring multiple solution pathways",
            "Evaluating solution feasibility"
        ])
        
        if constraints:
            thought_process.considerations.extend([
                f"Constraint: {constraint}" for constraint in constraints
            ])
        
        thought_process.considerations.extend([
            "What are the key success criteria?",
            "What resources are available?",
            "What are the risks and mitigation strategies?",
            "How will we measure success?"
        ])
        
        thought_process.conclusions = [
            "Systematic approach increases solution quality",
            "Multiple perspectives reveal better solutions"
        ]
        
        thought_process.next_steps = [
            "Prioritize solution options",
            "Create implementation plan",
            "Define success metrics",
            "Begin iterative development"
        ]
        
        thought_process.confidence_level = 0.85
        
        self.thought_history.append(thought_process)
        return thought_process
    
    def get_thinking_summary(self) -> str:
        """
        Generate a summary of recent thinking processes
        
        Returns:
            Text summary of recent thoughts and insights
        """
        if not self.thought_history:
            return "No recent thinking processes recorded."
        
        recent_thoughts = self.thought_history[-3:]  # Last 3 thinking processes
        
        summary_parts = []
        summary_parts.append("🧠 **Recent Thinking Summary:**\n")
        
        for i, thought in enumerate(recent_thoughts, 1):
            summary_parts.append(f"**{i}. {thought.topic}**")
            summary_parts.append(f"   Type: {thought.analysis_type}")
            summary_parts.append(f"   Key Insights: {'; '.join(thought.conclusions[:2])}")
            summary_parts.append(f"   Confidence: {thought.confidence_level:.1%}")
            summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    def clear_context(self):
        """Clear active thinking context"""
        self.active_context.clear()
    
    def get_thought_history(self) -> List[ThoughtProcess]:
        """Get complete thinking history"""
        return self.thought_history.copy()


# Tool registration for Agno integration
def create_thinking_tool() -> ThinkingTool:
    """Create and return a new thinking tool instance"""
    return ThinkingTool()


# Example usage functions that can be called by AI agents
def think_about(topic: str, context: Dict[str, Any] = None) -> str:
    """Simple interface for AI agents to use thinking tool"""
    tool = create_thinking_tool()
    result = tool.deep_think(topic, context)
    
    return f"""
🧠 **Deep Thinking on: {topic}**

**Initial Thoughts:**
{chr(10).join([f"• {thought}" for thought in result.thoughts])}

**Key Considerations:**
{chr(10).join([f"• {consideration}" for consideration in result.considerations])}

**Conclusions:**
{chr(10).join([f"• {conclusion}" for conclusion in result.conclusions])}

**Confidence Level:** {result.confidence_level:.1%}
"""


def analyze_bot_requirements(requirements_dict: Dict[str, Any]) -> str:
    """Analyze bot requirements with structured thinking"""
    tool = create_thinking_tool()
    result = tool.analyze_requirements(requirements_dict)
    
    return f"""
🔍 **Requirements Analysis Complete**

**Analysis Focus:** {result.topic}

**Key Observations:**
{chr(10).join([f"• {thought}" for thought in result.thoughts])}

**Critical Questions:**
{chr(10).join([f"• {consideration}" for consideration in result.considerations])}

**Assessment:**
• **Strengths:** {', '.join(result.pros_and_cons.get('strengths', []))}
• **Areas for Improvement:** {', '.join(result.pros_and_cons.get('weaknesses', []))}

**Recommendations:**
{chr(10).join([f"• {step}" for step in result.next_steps])}

**Analysis Confidence:** {result.confidence_level:.1%}
"""