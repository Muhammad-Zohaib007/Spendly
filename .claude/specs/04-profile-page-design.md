# Spec: Profile Page Design

## Overview
Build the profile page that authenticated users land on after login. The page displays the logged-in user's name, email address, and account creation date pulled from the `users` table. This step converts the `/profile` stub into a real, styled page that fits the Spendly design system — it is the first protected route in the app and establishes the pattern (session check → DB lookup → render) that all subsequent logged-in pages will follow.

## Depends on
- Step 01 — Database Setup (`get_db`, `users` table)
- Step 02 — Registration (`create_user`, `session["user_id"]` convention)
- Step 03 — Login and Logout (session is populated on login; `session.clear()` on logout)

## Routes
- `GET /profile` — render the profile page showing name, email, and member since date — logged-in only (redirect to `/login` if no session)

## Database changes
No new tables or columns.

Add one new helper function to `database/db.py`:

```python
def get_user_by_id(user_id: int):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user
```

No schema migrations required — all needed fields (`id`, `name`, `email`, `created_at`) already exist on the `users` table.

## Templates
- **Create:** `templates/profile.html`
  - Extends `base.html`
  - Displays a profile card with:
    - User's full name (large heading)
    - Email address
    - Member since date (formatted from `created_at`, e.g. "April 2026")
  - Uses only CSS variables from the design system (primary dark green, accent gold, neutral backgrounds)
  - Responsive: single column on mobile, centred card on desktop

- **Modify:** `templates/base.html`
  - Ensure the navbar "Profile" link points to `url_for('profile')` (update if currently a `#` placeholder)

## Files to change
- `expense-tracker/app.py` — implement `GET /profile` route; import `get_user_by_id`; redirect to `/login` if `session.get("user_id")` is absent
- `expense-tracker/database/db.py` — add `get_user_by_id` helper
- `expense-tracker/templates/base.html` — fix Profile nav link if it is a stub

## Files to create
- `expense-tracker/templates/profile.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (no changes to hashing in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Session guard must use `session.get("user_id")` — if absent or falsy, redirect to `url_for("login")` with no error message
- Do not expose `password_hash` to the template under any key
- Format `created_at` in Python before passing to the template — do not format dates in Jinja

## Definition of done
- [ ] `GET /profile` without a session redirects to `/login`
- [ ] After logging in as `demo@spendly.com` / `demo123`, visiting `/profile` renders the page without errors
- [ ] Page displays the correct name ("Demo User"), email ("demo@spendly.com"), and a formatted member-since date
- [ ] Page is styled using the Spendly design system (dark green / gold palette, DM Serif / DM Sans fonts)
- [ ] Page is responsive — readable on a 375 px wide viewport
- [ ] Navbar "Profile" link navigates to `/profile`
- [ ] `password_hash` is not visible anywhere in the rendered HTML
- [ ] App starts without errors after all changes
