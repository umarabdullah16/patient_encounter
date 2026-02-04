# Patient Encounter System

A simple FastAPI-based backend for managing patient encounters, built with SQLAlchemy, Pydantic, and SQLite (default for local/dev/test).

## Features
- FastAPI for RESTful APIs
- SQLAlchemy ORM for database access
- Environment-based configuration
- Linting (ruff), formatting (black), security checks (bandit)
- Unit testing with pytest

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/umarabdullah16/patient_encounter.git
cd patient_encounter
```

### 2. Set up Python environment
It is recommended to use Python 3.12 or later. You can use [Poetry](https://python-poetry.org/) for dependency management:

```bash
pip install poetry
poetry install
```

Or, using pip:
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the root directory to configure the database connection. You can set a `DATABASE_URL` environment variable if you want to use a remote DB (e.g. Postgres or MySQL). If not provided, the app defaults to a local SQLite DB (`sqlite:///./test.db`).

Example (optional):
```
# Optional: use an explicit DB URL
DATABASE_URL=sqlite:///./test.db
```

### 4. Run database migrations (if any)
(You may need to set up your database schema manually or with Alembic.)

### 5. Run the application with Uvicorn
```bash
uvicorn src.main:app --reload
```

- The API will be available at http://127.0.0.1:8000
- Interactive docs: http://127.0.0.1:8000/docs

## Testing
To run tests:
```bash
pytest
```

## Linting, Formatting, and Security
- Lint: `ruff src tests`
- Format check: `black --check src tests`
- Security: `bandit -r src`

---

For more details, see the source code and comments.
