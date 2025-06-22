# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mini-mancer is a Python project that uses `agno` as its main AI agent framework, integrating OpenServ → Agno → Telegram for bot creation and deployment. The project uses uv for dependency management and virtual environment handling.

## Development Environment

- Python version: 3.11+ (specified in .python-version)
- Package manager: uv
- Virtual environment: `.venv/` (managed by uv)

## Common Commands

### Setup
```bash
# Install dependencies
uv sync
# Add new dependencies to the local venv
uv add <package>

# Activate virtual environment (if needed)
source .venv/bin/activate
```

### Running the Application
```bash
# Run the main application
uv run python main.py
```

### Code Quality & Testing
```bash
# Run comprehensive code quality check
./scripts/format.sh

# Individual quality tools
uv run ruff check --fix src/ main.py     # Linting & auto-fixes
uv run black src/ main.py                # Code formatting
uv run isort src/ main.py                # Import organization
uv run mypy src/ main.py                 # Type checking

# Run tests
uv run pytest tests/                     # Run test suite
```

## Code Style Guidelines

### Clean Code Principles
- Write self-documenting code with clear variable and function names
- Keep functions small and focused on a single responsibility
- Prefer explicit over implicit behavior
- Use meaningful names that reveal intent

### DRY (Don't Repeat Yourself)
- Extract common functionality into reusable functions
- Use constants for repeated values
- Factor out duplicate logic into utility functions

### Type Hints
- Use modern Python 3.11+ built-in generics instead of typing imports:
  - Use `list[str]` instead of `List[str]`
  - Use `dict[str, int]` instead of `Dict[str, int]`
  - Use `set[int]` instead of `Set[int]`
  - Use `tuple[str, ...]` instead of `Tuple[str, ...]`
  - Use `str | None` instead of `Union[str, None]` or `Optional[str]`
- Only import from typing when necessary (e.g., `Protocol`, `TypeVar`, `Generic`)

### Control Flow
- **Use guard clauses and early returns** - Avoid deep nesting:
  ```python
  # Good
  def process_data(data):
      if not data:
          return None
      if not data.is_valid():
          return None
      
      return data.transform()
  
  # Avoid
  def process_data(data):
      if data:
          if data.is_valid():
              return data.transform()
      return None
  ```

- **No nested conditionals** - Extract complex conditions into functions:
  ```python
  # Good
  def is_valid_user(user):
      return user.is_active and user.email_verified and user.has_permission()
  
  if not is_valid_user(user):
      return
  
  # Avoid
  if user.is_active:
      if user.email_verified:
          if user.has_permission():
              # nested logic
  ```

### Loop Handling
- **Extract loop bodies into separate functions** when complex:
  ```python
  # Good
  def process_item(item):
      # complex processing logic
      return transformed_item
  
  def process_all_items(items):
      return [process_item(item) for item in items]
  
  # Avoid putting complex logic directly in loop bodies
  ```

### Indentation and Nesting
- Keep indentation shallow (max 2-3 levels)
- Use early returns to reduce nesting
- Extract nested logic into separate functions
- Prefer flat structure over deeply nested code

### Error Handling
- Avoid excessive or comprehensive error handling; let exceptions and tracebacks bubble up
- Only catch exceptions when there’s a clear, necessary recovery path

### Comments and Documentation
- Avoid comments unless code isn’t self-explanatory
- Provide short, concise docstrings for public-facing methods

## Project Structure

### Core Application
- `main.py` - Entry point with dual Telegram + FastAPI servers
- `src/agent_controller.py` - Core AgentController orchestrating all components
- `src/prototype_agent.py` - Compatibility layer and main exports

### Bot System
- `src/agents/telegram_bot_template.py` - Telegram bot template and webhook handler
- `src/models/agent_dna.py` - Agent DNA system and templates
- `src/models/bot_requirements.py` - Comprehensive bot requirements and validation
- `src/bot_compilation_pipeline.py` - Advanced bot testing and quality assurance

### Integration & APIs
- `src/api_router.py` - FastAPI route handlers for OpenServ integration
- `src/api_models.py` - Pydantic models for API requests/responses
- `src/telegram_integration.py` - Telegram bot lifecycle management

### Utilities & Infrastructure
- `src/utils/` - Error handling and utility functions
- `src/constants/` - User-facing messages and constants
- `src/tools/thinking_tool.py` - Advanced reasoning capabilities
- `src/test_monitor.py` - Real-time test monitoring and WebSocket dashboard

### Configuration & Quality
- `pyproject.toml` - Project configuration, dependencies, and quality tool settings
- `scripts/format.sh` - Automated code quality script
- `tests/` - Comprehensive test suite
- `docker-compose.yaml` - PostgreSQL + app containerization

## Key Dependencies

- `agno` - The main AI agent framework for intelligent bot creation
- `fastapi` - Web framework for OpenServ integration endpoints
- `python-telegram-bot` - Telegram bot API integration
- `psycopg[binary]` - PostgreSQL database connectivity

## Git Guidelines

### CRITICAL RULES - NEVER BREAK THESE:

 • **NEVER** use `git add -A` or `git add .` - these are dangerous and can add unintended files
 • **ALWAYS** add files explicitly by name: `git add specific_file.py`
 • **ALWAYS** check `git status` and `git diff --staged` before committing
 • **NEVER** commit without reviewing exactly what is being staged

### Commit Message Rules:
 • **NEVER** add "Co-Authored-By: Claude" or any AI attribution to commit messages
 • **NEVER** add "Generated with Claude Code" to commit messages  
 • Keep commit messages clean and professional
 • Focus on what changed and why, not who/what wrote it

## Code Quality Standards

### Automated Quality Pipeline
The project uses a comprehensive quality pipeline with three integrated tools:

- **Ruff** - Fast Python linter and formatter with extensive rule coverage
- **Black** - Opinionated code formatter for consistent styling
- **isort** - Import organization and sorting
- **MyPy** - Static type checking for type safety

### Quality Metrics
- **Ruff violations**: Target < 10 cosmetic issues
- **MyPy compliance**: All type annotations must pass validation
- **Test coverage**: Maintain comprehensive test suite
- **Import organization**: No star imports, explicit imports only

### Running Quality Checks
```bash
# Complete quality check (recommended)
./scripts/format.sh

# Fix most issues automatically
uv run ruff check --fix src/ main.py

# Manual quality tools
uv run black src/ main.py        # Format code
uv run isort src/ main.py        # Organize imports  
uv run mypy src/ main.py         # Type checking
```

### Quality Gates
- All code must pass MyPy type checking
- Ruff violations should be minimal (< 10 cosmetic issues)
- No F-series errors (undefined names, imports, etc.)
- Modern Python 3.11+ type annotations required
