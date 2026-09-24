# Contributing to Resume Tailor

Thank you for your interest in contributing to **Resume Tailor**! We welcome contributions ranging from bug fixes and documentation improvements to new parser integrations and exporter backends.

---

## 🚀 Quick Setup & Development Environment

This project uses [`uv`](https://github.com/astral-sh/uv) for fast, deterministic Python virtual environment and dependency management.

### 1. Prerequisites
- Python 3.12+
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- `pdflatex` (TeX Live or MacTeX) if testing LaTeX PDF compilation

### 2. Fork and Clone
```bash
git clone https://github.com/<your-username>/resume-tailor.git
cd resume-tailor
```

### 3. Install Dependencies
```bash
# Sync all core and development dependencies into .venv
uv sync --all-extras
```

### 4. Configure Local Environment
```bash
cp .env.example .env
# Edit .env with your Google Gemini API key for local LLM integration tests
```

---

## 🧪 Quality Standards & Testing

Before submitting a Pull Request, please ensure that all QA checks pass:

### Run the Test Suite
```bash
uv run pytest
```

### Code Formatting and Linting (Ruff)
```bash
# Check code style and imports
uv run ruff check .

# Automatically apply safe fixes
uv run ruff check --fix .

# Enforce code formatting
uv run ruff format .
```

### Static Type Checking (MyPy)
```bash
# Run strict type checking
uv run mypy src
```

---

## 📝 Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/) to keep git history readable and automated release-ready:

- `feat:` A new user-facing feature or capability (e.g. `feat(exporter): add typst exporter`)
- `fix:` A bug fix (e.g. `fix(scraper): resolve 403 status on protected portals`)
- `docs:` Documentation changes only (e.g. `docs: update installation instructions`)
- `test:` Adding or updating unit tests (e.g. `test: add edge cases for LaTeX escaping`)
- `refactor:` Code refactoring without changing user-facing behavior
- `chore:` Maintenance, build, or configuration updates

---

## 🔀 Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/my-new-feature
   ```
2. Commit your changes adhering to conventional commit messages.
3. Ensure all tests (`pytest`), linter checks (`ruff`), and type annotations (`mypy`) pass cleanly.
4. Push your branch to your GitHub fork:
   ```bash
   git push origin feat/my-new-feature
   ```
5. Open a Pull Request on GitHub against the `main` branch, describing your changes using the provided PR template.

---

## 🛡️ Security

Never commit API keys or private candidate credentials. If you find a security vulnerability, please do not open a public issue; report it privately following our security guidelines.
