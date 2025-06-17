# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mini-mancer is a Python project that uses `pydantic-ai-slim[mcp]` as its main dependency. The project uses uv for dependency management and virtual environment handling.

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

The project currently has a minimal structure:
- `main.py` - Entry point with a simple `main()` function
- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Locked dependency versions

## Key Dependencies

- `pydantic-ai-slim[mcp]` - The main framework dependency for AI/MCP functionality
```
