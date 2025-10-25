# Modern Development Tooling

This project uses cutting-edge development tools that represent 2025 best practices in Python development.

---

## Overview

This project incorporates three modern tools that demonstrate professional development practices:

1. **UV** - Lightning-fast Python package manager (10-100x faster than pip)
2. **Just** - Modern command runner for simplified project workflows
3. **Commitizen** - Automated conventional commits and versioning

---

## 1. UV: Fast Python Package Manager

### What is UV?

UV is an extremely fast Python package manager written in Rust by Astral (creators of Ruff). It's a drop-in replacement for pip that's **10-100x faster**.

### Why Use UV?

- **Speed**: 80-115x faster than pip with warm cache
- **All-in-One**: Replaces pip, pip-tools, pipx, poetry, pyenv, virtualenv
- **Compatible**: Works with existing requirements.txt and PyPI packages
- **Modern**: Shows you're using cutting-edge Python tooling

### Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Usage

```bash
# Create virtual environment (replaces: python -m venv venv)
uv venv

# Install dependencies (replaces: pip install -r requirements.txt)
uv pip install -r requirements.txt

# Install package (replaces: pip install pandas)
uv pip install pandas

# Sync dependencies (like pip-sync)
uv pip sync requirements.txt
```

### Speed Comparison

| Operation | pip | uv | Speedup |
|-----------|-----|-----|---------|
| Cold install | 45s | 5s | 9x |
| Warm install | 30s | 0.3s | 100x |
| Resolve deps | 15s | 0.5s | 30x |

---

## 2. Just: Command Runner

### What is Just?

Just is a modern command runner that simplifies project commands. It's like Make, but simpler and designed for development workflows.

### Why Use Just?

- **Simplicity**: Easy-to-read syntax (no Make's quirks)
- **Discoverability**: `just --list` shows all available commands
- **Cross-platform**: Works on macOS, Linux, Windows
- **Professional**: Shows understanding of modern DevOps practices

### Installation

```bash
# macOS
brew install just

# Linux
cargo install just

# Windows
scoop install just
```

### Usage

```bash
# List all available commands
just

# Run specific command
just install        # Install dependencies
just test          # Run tests
just dashboard     # Launch Streamlit dashboard
just generate-data # Generate sample data
just ci            # Run all CI checks

# Chain commands
just install generate-data dashboard
```

### Available Commands

Run `just` to see all commands. Key commands:

| Command | Description |
|---------|-------------|
| `just setup` | Complete project setup for new developers |
| `just install` | Install dependencies with uv |
| `just test` | Run pytest with coverage |
| `just lint` | Run ruff linter |
| `just format` | Format code with ruff |
| `just dashboard` | Launch Streamlit dashboard |
| `just commit` | Create conventional commit |
| `just ci` | Run all CI checks |

### Example: New Developer Onboarding

**Without Just** (old way):
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "from src.database import DatabaseManager; ..."
python scripts/generate_sample_data.py
streamlit run dashboard/dashboard.py
```

**With Just** (new way):
```bash
just setup
just dashboard
```

---

## 3. Commitizen: Conventional Commits

### What is Commitizen?

Commitizen enforces conventional commit messages and automates versioning and changelog generation.

### Why Use Commitizen?

- **Standardization**: Consistent commit message format
- **Automation**: Auto-generates changelogs and version bumps
- **Best Practice**: Industry standard for professional projects
- **Collaboration**: Makes git history readable and meaningful

### Installation

Already included in requirements.txt:

```bash
uv pip install commitizen
```

### Usage

**Creating Commits** (replaces `git commit`):

```bash
# Interactive commit creation
just commit
# or
cz commit

# Follow the prompts:
# ? Select type: feat
# ? Scope (optional): dashboard
# ? Subject: add new statistical visualizations
# ? Body (optional): Added time-series plots for metric trends
# ? Footer (optional):
```

**Checking Commits**:

```bash
# Validate commit message format
just commit-check
# or
cz check --rev-range HEAD
```

**Version Bumping**:

```bash
# Auto-bump version based on commits
just bump
# or
cz bump --changelog
```

### Conventional Commit Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature (bumps MINOR version)
- `fix`: Bug fix (bumps PATCH version)
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:

```bash
# Feature
feat(dashboard): add CUPED variance reduction toggle

# Bug fix
fix(data-gen): resolve numpy int64 type conversion issue

# Breaking change
feat(api): redesign statistical analysis interface

BREAKING CHANGE: ABTestAnalyzer.analyze() now returns dict instead of tuple
```

### Benefits

1. **Readable History**: Clear, searchable commit messages
2. **Auto Changelog**: Generates CHANGELOG.md automatically
3. **Semantic Versioning**: Auto-increments version based on commits
4. **Team Alignment**: Everyone follows same commit convention

---

## 4. Ruff: Fast Linter & Formatter

### What is Ruff?

Ruff is an extremely fast Python linter and formatter (also by Astral). It replaces Black, Flake8, isort, and more.

### Why Use Ruff?

- **Speed**: 10-100x faster than existing tools
- **All-in-One**: Replaces 5+ separate tools
- **Compatible**: Drop-in replacement for Black formatting
- **Comprehensive**: 800+ lint rules

### Usage (via Just)

```bash
# Check code quality
just lint

# Auto-format code
just format
```

---

## Interview Talking Points

Using these modern tools demonstrates:

### Technical Awareness
> "I stay current with modern Python tooling - this project uses UV for package management, which is 100x faster than pip and represents the direction the Python ecosystem is moving in 2025."

### DevOps Understanding
> "I implemented Just as a command runner to standardize workflows. It simplifies onboarding - a new developer can run 'just setup' instead of remembering 10 different commands."

### Professional Standards
> "I use Commitizen to enforce conventional commits, which enables automated versioning and changelog generation. This is the standard practice at companies like Google and Microsoft."

### Efficiency
> "These tools aren't just trendy - UV cuts CI/CD times from 45 seconds to 5 seconds, and Ruff lints the entire codebase in milliseconds instead of minutes."

---

## Migration from Traditional Tools

### Before (Traditional Approach)

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Development
black src/
flake8 src/
isort src/
pytest tests/

# Manual commit
git commit -m "fixed bug"
```

### After (Modern Approach)

```bash
# Setup
just setup

# Development
just ci

# Commit
just commit
```

**Result**: 5 commands → 3 commands, 100x faster execution

---

## Configuration Files

### justfile
Defines all project commands. See root `justfile` for available commands.

### .cz.toml
Commitizen configuration for conventional commits and versioning.

### ruff.toml
Ruff configuration for linting and formatting rules.

---

## Best Practices

### Daily Workflow

1. **Start work**: `just setup` (first time only)
2. **Make changes**: Edit code
3. **Check quality**: `just lint`
4. **Format code**: `just format`
5. **Run tests**: `just test`
6. **Commit**: `just commit` (not `git commit`)
7. **Before PR**: `just ci`

### CI/CD Integration

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install just
        run: cargo install just
      - name: Run CI
        run: just ci
```

---

## Resources

### UV
- Documentation: https://docs.astral.sh/uv/
- GitHub: https://github.com/astral-sh/uv
- Speed benchmarks: https://astral.sh/blog/uv

### Just
- Documentation: https://just.systems/man/en/
- GitHub: https://github.com/casey/just
- Cookbook: https://just.systems/man/en/chapter_20.html

### Commitizen
- Documentation: https://commitizen-tools.github.io/commitizen/
- Conventional Commits Spec: https://www.conventionalcommits.org/
- GitHub: https://github.com/commitizen-tools/commitizen

### Ruff
- Documentation: https://docs.astral.sh/ruff/
- GitHub: https://github.com/astral-sh/ruff
- Rules: https://docs.astral.sh/ruff/rules/

---

**This modern tooling stack represents 2025 best practices and demonstrates awareness of cutting-edge development workflows in the Python ecosystem.**
