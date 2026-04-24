# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Spendly** — A Flask-based expense tracker web app. Educational project with incremental implementation steps (database → auth → expense CRUD → analytics).

## Commands

All commands run from `expense-tracker/` (the inner directory containing `app.py`):

```bash
# Activate virtual environment (Windows)
source venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Run development server (http://localhost:5001)
python app.py

# Run tests
pytest

# Run a single test file
pytest tests/test_foo.py

# Run a single test
pytest tests/test_foo.py::test_function_name
```

## Architecture

```
expense-tracker/        ← repo root
└── expense-tracker/    ← app root (run commands here)
    ├── app.py          ← Flask app, all routes defined here
    ├── database/
    │   └── db.py       ← DB setup (placeholder, to be implemented)
    ├── static/
    │   ├── css/style.css
    │   └── js/main.js
    └── templates/
        ├── base.html   ← shared navbar/footer, loads Google Fonts
        └── *.html      ← Jinja2 templates extending base.html
```

**Stack:** Flask 3.1.3, Werkzeug, pytest + pytest-flask. Frontend is vanilla JS only — no frameworks.

**Route map:**

| Route | Status |
|---|---|
| `GET /` | Landing page |
| `GET /register`, `GET /login` | UI only (POST not implemented) |
| `GET /terms`, `GET /privacy` | Complete |
| `GET /logout`, `GET /profile` | Placeholder |
| `GET/POST /expenses/add` | Placeholder |
| `GET/POST /expenses/<id>/edit` | Placeholder |
| `GET /expenses/<id>/delete` | Placeholder |

**Implementation order** (per project plan): database setup → user auth → session/logout → profile → expense CRUD → analytics.

## Design System

- **Colors:** Primary dark green `#1a472a`, accent gold `#c17f24`, neutrals for text/backgrounds
- **Fonts:** DM Serif Display (headings), DM Sans (body) via Google Fonts in `base.html`
- **Responsive breakpoints:** 900px and 600px in `style.css`
- CSS variables used for theming — add new colors/sizes there, not inline
