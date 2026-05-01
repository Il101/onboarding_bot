# Contributing to V-Brain

Thank you for your interest in contributing to V-Brain!

## Development Setup

### Prerequisites

- Python 3.12+
- Docker + Docker Compose
- `uv` package manager: `pip install uv`

### Installation

```bash
# Clone and install dependencies
git clone <repo-url>
cd onboarding_bot
uv sync --extra dev

# Start infrastructure
docker compose up -d

# Apply migrations
uv run alembic upgrade head
```

### Running the Project

```bash
# API + admin panel (port 8000)
uv run uvicorn src.api.main:app --reload

# Celery worker (background processing)
uv run celery -A src.tasks.ingest worker --loglevel=info

# Telegram bot
uv run python -m src.bot.telegram_app
```

## Code Quality

### Before Committing

```bash
# Run linter
uv run ruff check .

# Run formatter
uv run ruff format .

# Run tests
uv run pytest -q

# Full check (CI runs this)
uv run ruff check . && uv run pytest -q
```

### Pre-commit Hooks (recommended)

```bash
uv run pre-commit install
```

## Project Structure

```
src/
├── api/          # FastAPI routes and admin panel
├── ai/           # LLM client and RAG pipeline
├── bot/          # Telegram bot handlers
├── core/         # Configuration, logging, utilities
├── models/       # SQLAlchemy database models
├── pipeline/     # Ingestion, parsing, processing
└── tasks/        # Celery background tasks
```

## Adding New Features

1. Add tests in `tests/` directory
2. Update README.md if user-facing changes
3. Run full test suite before PR
4. Follow existing code style (ruff enforces this)

## Database Changes

```bash
# Create new migration
uv run alembic revision -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback (if needed)
uv run alembic downgrade -1
```

## Questions?

Open an issue for questions, bugs, or feature requests.
