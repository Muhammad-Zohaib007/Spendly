# Spec: Registration

## Overview
Implement user registration so new visitors can create a Spendly account. This step wires up the `POST /register` route, adds a `create_user` database helper, and introduces Flask sessions so a newly registered user is shown with a success message and then redirected to  immediately logged in. It is the first step that persists user-generated data and the gateway to all authenticated features that follow.

## Depends on
- Step 01 — Database Setup (users table must exist; `get_db` and `generate_password_hash` must be available)

## Routes
- `GET /register` — render registration form — public (already exists, no change needed)
- `POST /register` — validate form data, create user, start session, redirect to `/expenses` — public

## Database changes
No new tables or columns. The existing `users` table already has all required fields (`name`, `email`, `password_hash`, `created_at`).

Add one new helper function to `database/db.py`:

```python
def create_user(name: str, email: str, password: str) -> int:
    """Insert a new user and return the new user id."""

def get_user_by_email(email: str) -> sqlite3.Row | None:
    """Return the user row for a given email, or None."""
```

## Templates
- **Modify:** `templates/register.html`
  - Add `method="POST"` and `action="/register"` to the `<form>` tag
  - Add a `name` field (text, required)
  - Add an `email` field (email, required)
  - Add a `password` field (password, required, minlength 8)
  - Add a `confirm_password` field (password, required)
  - Render flashed error/success messages above the form using `get_flashed_messages(with_categories=True)`
  - Include `{{ csrf_token() }}` **only if** Flask-WTF is added; otherwise omit (no CSRF library in this step)

## Files to change
- `expense-tracker/app.py` — convert `register` view to handle GET + POST; add `secret_key`; import `session`, `redirect`, `url_for`, `flash`, `request`
- `expense-tracker/database/db.py` — add `create_user` and `get_user_by_email`
- `expense-tracker/templates/register.html` — wire up the form (see Templates section)

## Files to create
None.

## New dependencies
No new pip packages. Uses only:
- `flask` (session, redirect, url_for, flash, request — already installed)
- `werkzeug.security` (generate_password_hash, check_password_hash — already installed)
- `sqlite3` (standard library)

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never use f-strings or `.format()` in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash` before storage; never store plaintext
- `app.secret_key` must be set (use a hard-coded dev string for now; note it must be changed for production)
- Session key for the logged-in user: `session["user_id"]` (integer)
- On duplicate email, catch the `sqlite3.IntegrityError` and flash a user-friendly error — do not let the 500 bubble up
- Server-side validation required:
  - All fields non-empty
  - `password == confirm_password`
  - Password at least 8 characters
  - Email not already registered
- On validation failure: re-render the form (do not redirect) and flash the specific error
- On success: set `session["user_id"]`, flash a welcome message, and `redirect(url_for("dashboard"))` — add a stub `GET /dashboard` route if it does not exist yet
- Use CSS variables — never hardcode hex values in templates or new CSS
- All templates extend `base.html`

## Definition of done
- [ ] `GET /register` renders the form without errors
- [ ] Submitting blank fields shows a validation error on the same page
- [ ] Submitting mismatched passwords shows a validation error
- [ ] Submitting a password shorter than 8 characters shows a validation error
- [ ] Submitting a duplicate email shows "Email already registered" error
- [ ] Submitting valid data creates a new row in the `users` table with a hashed password (not plaintext)
- [ ] After successful registration, `session["user_id"]` is set to the new user's id
- [ ] After successful registration, user is redirected away from `/register`
- [ ] Registering a second time with the same email is rejected even if the app is restarted (persisted in DB)
- [ ] App starts without errors after changes to `app.py` and `db.py`
