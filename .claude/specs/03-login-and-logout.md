# Spec: Login and Logout

## Overview
Implement user login and logout so registered users can authenticate and end their session. This step wires up `POST /login` to verify credentials against the database and start a session, and converts the `GET /logout` stub into a real route that clears the session and redirects. Together these routes complete the authentication lifecycle begun in Step 02 and are a prerequisite for all protected pages that follow.

## Depends on
- Step 01 — Database Setup (`get_db`, `users` table)
- Step 02 — Registration (`get_user_by_email`, `session["user_id"]` convention, `secret_key`)

## Routes
- `GET /login` — render login form — public (already exists, no change to GET)
- `POST /login` — validate credentials, start session, redirect to dashboard — public
- `GET /logout` — clear session, redirect to landing page — public (no login required to call)

## Database changes
No new tables or columns.

Add one import to `database/db.py`:
```python
from werkzeug.security import generate_password_hash, check_password_hash
```
`check_password_hash` is already installed (same package); it just needs to be imported so the route can verify passwords.

No new DB helper functions are needed — `get_user_by_email` from Step 02 is sufficient.

## Templates
- **Modify:** `templates/login.html`
  - The form already has `method="POST" action="/login"`, email field, password field, and `{% if error %}` block — **no structural changes needed**
  - No changes required

## Files to change
- `expense-tracker/app.py` — implement `POST /login` handler; implement `GET /logout`; add `check_password_hash` to werkzeug import
- `expense-tracker/database/db.py` — add `check_password_hash` to the werkzeug import line

## Files to create
None.

## New dependencies
No new pip packages. Uses only:
- `werkzeug.security.check_password_hash` (already installed, just needs importing)

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (already enforced via `get_user_by_email`)
- Never reveal which field (email vs password) was wrong — always use the generic message: **"Invalid email or password."**
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plaintext
- `session["user_id"]` is the single source of truth for the logged-in user (integer)
- Logout must use `session.clear()` — do not selectively pop keys
- After logout, redirect to `url_for("landing")` (the `/` landing page)
- After successful login, redirect to `url_for("dashboard")`
- On login validation failure: re-render `login.html` with `error=` template variable (do not redirect)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done
- [ ] `GET /login` renders the form without errors
- [ ] Submitting blank fields shows a validation error on the same page
- [ ] Submitting a non-existent email shows "Invalid email or password."
- [ ] Submitting a correct email with wrong password shows "Invalid email or password."
- [ ] Submitting correct credentials (`demo@spendly.com` / `demo123`) sets `session["user_id"]` and redirects to `/dashboard`
- [ ] After login, visiting `/logout` clears the session and redirects to the landing page (`/`)
- [ ] After logout, `session["user_id"]` no longer exists
- [ ] App starts without errors after changes to `app.py` and `db.py`
