# Justfile for Feature Adoption A/B Testing Platform
# Modern command runner - use 'just <command>' instead of remembering complex commands
# Install: brew install just (macOS) or cargo install just

# List all available commands
default:
    @just --list

# Setup: Install dependencies using uv (fast pip replacement)
install:
    uv pip install -r requirements.txt

# Setup: Create virtual environment with uv
venv:
    uv venv
    @echo "Activate with: source venv/bin/activate"

# Development: Run all tests
test:
    pytest tests/ -v --cov=src --cov-report=term-missing

# Development: Run specific test file
test-file FILE:
    pytest {{FILE}} -v

# Development: Run linting with ruff
lint:
    ruff check src/ tests/ dashboard/ scripts/

# Development: Format code with ruff
format:
    ruff format src/ tests/ dashboard/ scripts/

# Data: Generate sample data (5K users)
generate-data:
    python scripts/generate_sample_data.py

# Data: Generate full dataset (50K users)
generate-full:
    python -c "from src.synthetic_data_generator import ExperimentDataGenerator; from src.config import DataGenerationConfig, ExperimentConfig; config = DataGenerationConfig(); config.n_users = 50000; gen = ExperimentDataGenerator(config, ExperimentConfig(), seed=42); data = gen.generate_all_data(); [data[k].to_csv(f'data/{k}.csv', index=False) for k in data.keys()]"

# Dashboard: Launch Streamlit dashboard
dashboard:
    streamlit run dashboard/dashboard.py

# Database: Create schema (requires .env with Supabase credentials)
db-schema:
    python -c "from src.database import DatabaseManager; db = DatabaseManager(); db.execute_sql_file('sql/schema.sql')"

# Database: Create materialized views
db-views:
    python -c "from src.database import DatabaseManager; db = DatabaseManager(); db.execute_sql_file('sql/materialized_views.sql')"

# Database: Setup complete database (schema + views)
db-setup: db-schema db-views
    @echo "✓ Database setup complete"

# Analysis: Run statistical analysis on generated data
analyze:
    python -c "from src.statistical_analysis import ABTestAnalyzer; import pandas as pd; print('Running analysis...'); analyzer = ABTestAnalyzer(); print('Analysis complete')"

# Git: Check conventional commit format (requires commitizen)
commit-check:
    cz check --rev-range HEAD

# Git: Create conventional commit interactively
commit:
    cz commit

# Git: Bump version based on commits
bump:
    cz bump --changelog

# CI: Run all checks (tests + lint + format check)
ci: test lint
    @echo "✓ All CI checks passed"

# Clean: Remove generated data files
clean-data:
    rm -f data/*.csv

# Clean: Remove Python cache files
clean-cache:
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Clean: Remove all generated files
clean: clean-data clean-cache
    @echo "✓ Cleaned all generated files"

# Docs: Serve documentation locally (if using mkdocs)
docs-serve:
    @echo "Documentation is in docs/ folder - open docs/experiment_design.md"

# Production: Full setup for new developer
setup: venv install db-setup generate-data
    @echo "✓ Project setup complete! Run 'just dashboard' to view results"

# Quick start for demonstrations
demo: generate-data dashboard
