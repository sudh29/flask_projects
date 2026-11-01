# AGENTS.md — Universal Agent Operating Standard: flask_projects

> **Repository:** `/home/liberprimus/code/flask_projects`  
> **Workspace Authority:** `sudh29` (`liberprimus`)  
> **Tier:** Tier C (Lightweight Microservices, REST APIs & Flask Platforms)  
> **Active Branch:** `main`  
> **Applicable Agents:** Antigravity, Claude Code, Cursor, Gemini, Codex


---

## 1. Repository Purpose & Architecture

- **Overview:** `flask_projects` demonstrates lightweight microservices, API gateways, and web applications built with Flask 3.1 and Flask-SQLAlchemy. It emphasizes simplicity, modular Flask blueprints, application factories (`create_app`), and clean test fixtures.
- **Key Directory Map:**
  - `app/`: Application factory, modular blueprints (auth, api, core), models, and views.
  - `tests/`: Automated Pytest suites testing endpoints with Flask test clients.
  - `pyproject.toml`: Dependency and environment configuration via `uv`.
- **Architectural Invariants:**
  - **Application Factory Pattern:** Always use `create_app()` factory function to initialize Flask apps and register blueprints.
  - **Context Cleanliness:** Tests must use `app.app_context()` and `app.test_client()` without leaking state between test cases.
  - **Config Isolation:** Separate Development, Testing, and Production configuration classes.

### Key Architecture & Entry Points

- **Manifest:** [`pyproject.toml`](file:///home/liberprimus/code/flask_projects/pyproject.toml)
- **App Factory:** `app/__init__.py` (`create_app`)
- **Blueprints:** `app/blueprints/`
- **Tests:** `tests/`

---

## 2. Coding Style & Engineering Conventions

- Modular Blueprints with distinct URL prefixes.
- Use Flask Application Factory pattern.
- Python 3.12 typing and Ruff formatting.

---

## 3. Toolchain & Environment Matrix

- **Runtime:** Python 3.12+
- **Framework:** Flask >= 3.1
- **Package Manager:** **`uv`** (`/home/liberprimus/.local/bin/uv` or subproject `.venv`)

### Canonical Commands
All commands run from `/home/liberprimus/code/flask_projects`:

| Action | Command | Purpose |
|:---|:---|:---|
| **Dev Server** | `uv run flask run` | Launch local development server |
| **Run Tests** | `uv run pytest` | Execute full API test suite |
| **Lint Code** | `uv run ruff check .` | Fast static analysis via Ruff |
| **Format Code** | `uv run ruff format .` | Auto-format Python code |

### Quick-Start Workflow

```bash
# Server & Testing
uv run flask run                        # Launch development server
uv run pytest                           # Run test suite
uv run pytest tests/test_api.py         # Run specific test
uv run ruff check .                     # Lint check
uv run ruff format .                    # Format code
```

---

## 4. Operational Safety & Agent Boundaries

1. **Blast Radius Containment:** Strictly confine edits to `/home/liberprimus/code/flask_projects`.
2. **Verification Mandate:** Always run `uv run pytest && uv run ruff check .` before concluding tasks.
3. **Branch Discipline:** Active working branch is `main`.
4. **Secret Hygiene:** Ensure `SECRET_KEY` is retrieved from environment variables.

---

## 5. Definition of Done
- [ ] Flask application factory initializes without errors.
- [ ] Pytest test cases pass cleanly.
- [ ] Code is formatted and lint-clean.
- [ ] Working tree is clean.
