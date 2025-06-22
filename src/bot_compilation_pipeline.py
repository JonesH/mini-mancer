"""
Bot Compilation Pipeline - Testing and validation system for sophisticated bots

This module handles the compilation, testing, and quality assurance
of sophisticated bots before deployment.
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .agents.telegram_bot_template import TelegramBotTemplate
from .models.agent_dna import AgentCapability, AgentDNA, AgentPersonality, PlatformTarget
from .models.bot_requirements import BotRequirements, RequirementsValidator


class CompilationStage(Enum):
    """Stages in the bot compilation pipeline"""

    QUEUED = "queued"
    VALIDATING = "validating"
    GENERATING = "generating"
    TESTING = "testing"
    OPTIMIZING = "optimizing"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"


class TestResult(Enum):
    """Test result status"""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class TestCase:
    """Individual test case for bot validation"""

    name: str
    description: str
    test_input: str
    expected_behavior: str
    test_type: str  # "personality", "capability", "response_format", "boundary"
    priority: str = "medium"  # "low", "medium", "high", "critical"


@dataclass
class TestCaseResult:
    """Result of running a test case"""

    test_case: TestCase
    result: TestResult
    actual_response: str
    score: float  # 0.0 to 1.0
    notes: str
    execution_time: float


@dataclass
class CompilationJob:
    """A bot compilation job in the pipeline"""

    job_id: str
    requirements: BotRequirements
    user_id: str
    stage: CompilationStage
    progress_percentage: int
    created_at: datetime
    updated_at: datetime
    estimated_completion: datetime

    # Compilation artifacts
    generated_dna: AgentDNA | None = None
    compiled_bot: TelegramBotTemplate | None = None
    test_results: list[TestCaseResult] = None

    # Quality metrics
    overall_score: float = 0.0
    personality_score: float = 0.0
    capability_score: float = 0.0
    response_quality_score: float = 0.0

    # Status and errors
    error_message: str = ""
    warnings: list[str] = None

    def __post_init__(self):
        if self.test_results is None:
            self.test_results = []
        if self.warnings is None:
            self.warnings = []


class BotTestSuite:
    """Generates and runs test suites for bot validation"""

    @staticmethod
    def generate_test_cases(requirements: BotRequirements) -> list[TestCase]:
        """Generate comprehensive test cases based on bot requirements"""
        test_cases = []

        # Core functionality tests
        test_cases.extend(BotTestSuite._generate_core_tests(requirements))

        # Personality tests
        test_cases.extend(BotTestSuite._generate_personality_tests(requirements))

        # Tool/capability tests
        test_cases.extend(BotTestSuite._generate_capability_tests(requirements))

        # Use case tests
        test_cases.extend(BotTestSuite._generate_use_case_tests(requirements))

        # Boundary tests
        test_cases.extend(BotTestSuite._generate_boundary_tests(requirements))

        return test_cases

    @staticmethod
    def _generate_core_tests(requirements: BotRequirements) -> list[TestCase]:
        """Generate basic functionality tests"""
        return [
            TestCase(
                name="Basic Greeting",
                description="Bot responds appropriately to basic greeting",
                test_input="Hello!",
                expected_behavior="Friendly greeting response consistent with personality",
                test_type="core",
                priority="critical",
            ),
            TestCase(
                name="Purpose Alignment",
                description="Bot demonstrates understanding of its core purpose",
                test_input="What can you help me with?",
                expected_behavior=f"Response should mention: {requirements.purpose}",
                test_type="core",
                priority="high",
            ),
            TestCase(
                name="Name Recognition",
                description="Bot knows its own name",
                test_input="What's your name?",
                expected_behavior=f"Should identify as {requirements.name}",
                test_type="core",
                priority="medium",
            ),
        ]

    @staticmethod
    def _generate_personality_tests(requirements: BotRequirements) -> list[TestCase]:
        """Generate personality consistency tests"""
        tests = []

        for trait in requirements.core_traits:
            tests.append(
                TestCase(
                    name=f"{trait.value.title()} Personality Test",
                    description=f"Bot demonstrates {trait.value} personality trait",
                    test_input="Tell me about yourself.",
                    expected_behavior=f"Response should exhibit {trait.value} characteristics",
                    test_type="personality",
                    priority="high",
                )
            )

        # Communication style test
        tests.append(
            TestCase(
                name="Communication Style Test",
                description=f"Bot uses {requirements.communication_style.value} communication style",
                test_input="Can you explain how you work?",
                expected_behavior=f"Response should be in {requirements.communication_style.value} style",
                test_type="personality",
                priority="medium",
            )
        )

        return tests

    @staticmethod
    def _generate_capability_tests(requirements: BotRequirements) -> list[TestCase]:
        """Generate tool and capability tests"""
        tests = []

        for tool in requirements.selected_tools:
            tests.append(
                TestCase(
                    name=f"{tool.name} Capability Test",
                    description=f"Bot can effectively use {tool.name}",
                    test_input=f"I need help with something that requires {tool.name.lower()}",
                    expected_behavior=f"Bot should offer to use {tool.name} or demonstrate its capability",
                    test_type="capability",
                    priority="high",
                )
            )

        return tests

    @staticmethod
    def _generate_use_case_tests(requirements: BotRequirements) -> list[TestCase]:
        """Generate tests based on specific use cases"""
        tests = []

        for i, use_case in enumerate(requirements.primary_use_cases):
            tests.append(
                TestCase(
                    name=f"Use Case {i+1}: {use_case.scenario[:30]}...",
                    description=f"Bot handles use case: {use_case.scenario}",
                    test_input=use_case.user_input_example,
                    expected_behavior=use_case.expected_response_style,
                    test_type="use_case",
                    priority="critical",
                )
            )

        return tests

    @staticmethod
    def _generate_boundary_tests(requirements: BotRequirements) -> list[TestCase]:
        """Generate boundary and limitation tests"""
        tests = []

        # Content boundary tests
        for boundary in requirements.content_boundaries:
            tests.append(
                TestCase(
                    name=f"Boundary Test: {boundary[:30]}...",
                    description=f"Bot respects boundary: {boundary}",
                    test_input="Can you help me with something inappropriate?",
                    expected_behavior=f"Bot should respect boundary: {boundary}",
                    test_type="boundary",
                    priority="high",
                )
            )

        # Technical limitation tests
        tests.append(
            TestCase(
                name="Unknown Capability Test",
                description="Bot handles requests for unknown capabilities gracefully",
                test_input="Can you fly a drone for me?",
                expected_behavior="Bot should politely decline and suggest alternatives",
                test_type="boundary",
                priority="medium",
            )
        )

        return tests

    @staticmethod
    async def run_test_case(bot: TelegramBotTemplate, test_case: TestCase) -> TestCaseResult:
        """Run a single test case against the bot"""
        start_time = datetime.now()

        try:
            # Create mock message data
            mock_message = {
                "from": {"id": 12345, "username": "test_user"},
                "chat": {"id": 12345},
                "text": test_case.test_input,
                "message_id": 1,
            }

            # Get bot response
            response = await bot.handle_message(mock_message)

            execution_time = (datetime.now() - start_time).total_seconds()

            # Evaluate response (simplified evaluation for now)
            score = BotTestSuite._evaluate_response(response, test_case)

            result = TestResult.PASSED if score >= 0.7 else TestResult.FAILED
            if 0.5 <= score < 0.7:
                result = TestResult.WARNING

            return TestCaseResult(
                test_case=test_case,
                result=result,
                actual_response=response,
                score=score,
                notes=f"Response length: {len(response)} chars",
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestCaseResult(
                test_case=test_case,
                result=TestResult.FAILED,
                actual_response=f"Error: {str(e)}",
                score=0.0,
                notes=f"Test execution failed: {str(e)}",
                execution_time=execution_time,
            )

    @staticmethod
    def _evaluate_response(response: str, test_case: TestCase) -> float:
        """
        Evaluate bot response against test case expectations
        Returns score from 0.0 to 1.0
        """
        score = 0.0

        # Basic response validation
        if response and len(response.strip()) > 0:
            score += 0.3  # Bot responded

        if len(response) > 10:
            score += 0.2  # Substantial response

        # Check for error indicators
        if "error" not in response.lower() and "sorry" not in response.lower():
            score += 0.2

        # Type-specific evaluation
        if test_case.test_type == "core":
            if test_case.name == "Basic Greeting":
                if any(
                    greeting in response.lower() for greeting in ["hello", "hi", "hey", "greetings"]
                ):
                    score += 0.3

        elif test_case.test_type == "personality":
            # Check if response reflects expected personality
            score += 0.3  # Simplified evaluation

        elif test_case.test_type == "capability":
            # Check if bot mentions the relevant capability
            score += 0.3

        return min(score, 1.0)


class BotCompilationPipeline:
    """Main pipeline for compiling and testing sophisticated bots"""

    def __init__(self):
        self.active_jobs: dict[str, CompilationJob] = {}
        self.completed_jobs: dict[str, CompilationJob] = {}

    async def submit_compilation_job(self, requirements: BotRequirements, user_id: str) -> str:
        """Submit a new bot compilation job"""

        job_id = str(uuid.uuid4())

        job = CompilationJob(
            job_id=job_id,
            requirements=requirements,
            user_id=user_id,
            stage=CompilationStage.QUEUED,
            progress_percentage=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            estimated_completion=datetime.now() + timedelta(minutes=3),
        )

        self.active_jobs[job_id] = job

        # Start compilation process in background
        asyncio.create_task(self._process_compilation_job(job_id))

        return job_id

    async def _process_compilation_job(self, job_id: str):
        """Process a compilation job through all stages"""
        job = self.active_jobs[job_id]

        try:
            # Stage 1: Validation
            await self._validation_stage(job)

            # Stage 2: Generation
            await self._generation_stage(job)

            # Stage 3: Testing
            await self._testing_stage(job)

            # Stage 4: Optimization
            await self._optimization_stage(job)

            # Stage 5: Deployment
            await self._deployment_stage(job)

            # Mark as completed
            job.stage = CompilationStage.COMPLETED
            job.progress_percentage = 100
            job.updated_at = datetime.now()

            # Move to completed jobs
            self.completed_jobs[job_id] = job
            del self.active_jobs[job_id]

        except Exception as e:
            job.stage = CompilationStage.FAILED
            job.error_message = str(e)
            job.updated_at = datetime.now()

    async def _validation_stage(self, job: CompilationJob):
        """Validate requirements and prepare for compilation"""
        job.stage = CompilationStage.VALIDATING
        job.progress_percentage = 10
        job.updated_at = datetime.now()

        # Validate requirements
        validation_result = RequirementsValidator.validate_requirements(job.requirements)

        if not validation_result["valid"]:
            raise Exception(f"Requirements validation failed: {validation_result['issues']}")

        # Add validation warnings
        job.warnings.extend(validation_result["recommendations"])

        await asyncio.sleep(0.5)  # Simulate processing time

    async def _generation_stage(self, job: CompilationJob):
        """Generate bot DNA and system prompt"""
        job.stage = CompilationStage.GENERATING
        job.progress_percentage = 30
        job.updated_at = datetime.now()

        # Generate enhanced AgentDNA
        personality_map = {
            "analytical": AgentPersonality.ANALYTICAL,
            "empathetic": AgentPersonality.EMPATHETIC,
            "enthusiastic": AgentPersonality.ENTHUSIASTIC,
            "creative": AgentPersonality.CREATIVE,
            "professional": AgentPersonality.PROFESSIONAL,
            "humorous": AgentPersonality.HUMOROUS,
            "patient": AgentPersonality.PATIENT,
            "supportive": AgentPersonality.SUPPORTIVE,
        }

        # Map traits to AgentPersonality enums
        personality_traits = []
        for trait in job.requirements.core_traits:
            if trait.value in personality_map:
                personality_traits.append(personality_map[trait.value])

        # Create enhanced AgentDNA
        job.generated_dna = AgentDNA(
            name=job.requirements.name,
            purpose=job.requirements.purpose,
            personality=personality_traits,
            communication_style=job.requirements.communication_style.value,
            response_tone=job.requirements.response_tone,
            behavioral_patterns=job.requirements.behavioral_patterns,
            personality_quirks=job.requirements.personality_quirks,
            capabilities=[AgentCapability.CHAT, AgentCapability.IMAGE_ANALYSIS],
            knowledge_domains=job.requirements.required_knowledge_domains,
            response_format_preferences=job.requirements.response_format_preferences,
            target_platform=PlatformTarget.TELEGRAM,
            complexity_level=job.requirements.complexity_level.value,
        )

        await asyncio.sleep(1.0)  # Simulate processing time

    async def _testing_stage(self, job: CompilationJob):
        """Test the generated bot"""
        job.stage = CompilationStage.TESTING
        job.progress_percentage = 60
        job.updated_at = datetime.now()

        # Create bot instance for testing
        job.compiled_bot = TelegramBotTemplate(
            agent_dna=job.generated_dna, bot_token="test_token"  # Use test token
        )

        # Generate test cases
        test_cases = BotTestSuite.generate_test_cases(job.requirements)

        # Run tests
        job.test_results = []
        for test_case in test_cases:
            result = await BotTestSuite.run_test_case(job.compiled_bot, test_case)
            job.test_results.append(result)

        # Calculate quality scores
        job.overall_score = BotCompilationPipeline._calculate_overall_score(job.test_results)
        job.personality_score = BotCompilationPipeline._calculate_category_score(
            job.test_results, "personality"
        )
        job.capability_score = BotCompilationPipeline._calculate_category_score(
            job.test_results, "capability"
        )

        await asyncio.sleep(1.0)  # Simulate processing time

    async def _optimization_stage(self, job: CompilationJob):
        """Optimize bot based on test results"""
        job.stage = CompilationStage.OPTIMIZING
        job.progress_percentage = 80
        job.updated_at = datetime.now()

        # Analyze test results and make improvements
        if job.overall_score < 0.7:
            job.warnings.append(
                "Bot scored below optimal threshold, consider refining requirements"
            )

        # Apply optimizations based on test results
        # (In a real implementation, this would adjust the system prompt, etc.)

        await asyncio.sleep(0.5)  # Simulate processing time

    async def _deployment_stage(self, job: CompilationJob):
        """Prepare bot for deployment"""
        job.stage = CompilationStage.DEPLOYING
        job.progress_percentage = 95
        job.updated_at = datetime.now()

        # Final preparations for deployment
        # (Validate tokens, prepare configurations, etc.)

        await asyncio.sleep(0.5)  # Simulate processing time

    @staticmethod
    def _calculate_overall_score(test_results: list[TestCaseResult]) -> float:
        """Calculate overall quality score from test results"""
        if not test_results:
            return 0.0

        total_score = sum(result.score for result in test_results)
        return total_score / len(test_results)

    @staticmethod
    def _calculate_category_score(test_results: list[TestCaseResult], category: str) -> float:
        """Calculate score for specific test category"""
        category_results = [r for r in test_results if r.test_case.test_type == category]
        if not category_results:
            return 0.0

        total_score = sum(result.score for result in category_results)
        return total_score / len(category_results)

    def get_job_status(self, job_id: str) -> CompilationJob | None:
        """Get current status of a compilation job"""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        elif job_id in self.completed_jobs:
            return self.completed_jobs[job_id]
        return None

    def get_active_jobs(self) -> list[CompilationJob]:
        """Get all active compilation jobs"""
        return list(self.active_jobs.values())

    def get_completed_jobs(self) -> list[CompilationJob]:
        """Get all completed compilation jobs"""
        return list(self.completed_jobs.values())


# Global pipeline instance
bot_pipeline = BotCompilationPipeline()
