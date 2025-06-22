#!/bin/bash
# Format code with isort, black, and ruff in correct order
# This ensures no conflicts between the tools

echo "🔧 Running code quality tools..."

echo "📦 Organizing imports with isort..."
uv run isort src/ main.py

echo "🖤 Formatting code with black..."
uv run black src/ main.py

echo "🦀 Final linting with ruff..."
uv run ruff check --fix src/ main.py

echo "🔍 Type checking with mypy..."
uv run mypy src/ main.py --no-error-summary | head -20

echo "✅ Code quality check complete!"