# Spec: Date Filter for Profile Page

## Overview
Add a date range filter to the profile/dashboard page so users can narrow the expenses table, totals, and category breakdown to a chosen window (e.g. last 30 days, a specific month, or a custom range). Filtering is driven by `start_date` and `end_date` query string parameters on `GET /profile`. When no range is supplied the page behaves exactly as it does today (all expenses shown). All summary cards and the category breakdown are recomputed from the filtered set so the page stays internally consistent.

## Depends on
- Step 01 — Database Setup (`expenses.date` column, `get_db`)
- Step 02 — Registration / Step 03 — Login (session-based auth)
- Step 04 / 05 — Profile Page Design and Backend Routes (existing `/profile` route, template, and `get_expenses_by_user` helper)

## Routes
- `GET /profile?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` — same route as today; the two query params are optional and either, both, or neither may be present — logged-in only

No new routes.

## Database changes
No new tables, columns, or constraints.

Add one new helper to `database/db.py`:

```python
def get_expenses_by_user_in_range(user_id: int, start_date: str | None, end_date: str | None):
    """Return user's expenses ordered by date desc, optionally bounded by ISO date strings."""
```

The helper must build the WHERE clause with parameterised query fragments — no string interpolation of user values. The existing `get_expenses_by_user` helper stays in place (other features may still use it).

## Templates
- **Modify:** `templates/profile.html`
  - Add a date filter form above the expenses panel (or inside the panel head) with two `<input type="date">` fields (`name="start_date"`, `name="end_date"`), a submit button, and a "Clear" link that points to `url_for('profile')`
  - Pre-fill the inputs with the currently active `start_date` / `end_date` values so the form reflects the active filter
  - Show a small "Showing X of Y" or "Filtered: <range>" hint when a filter is active
  - When the filtered set is empty but the user has expenses overall, show an empty-state message specific to the filter (e.g. "No expenses in this date range") instead of the generic "Add your first one" copy

- **Create:** No new templates.

## Files to change
- `expense-tracker/app.py` — read `start_date` / `end_date` from `request.args`, validate them as ISO `YYYY-MM-DD` strings, call the new helper, recompute `total_spent`, `expense_count`, `categories`, and `top_category` from the filtered list, and pass `start_date` / `end_date` (echoed back, possibly empty strings) to the template
- `expense-tracker/database/db.py` — add `get_expenses_by_user_in_range`
- `expense-tracker/templates/profile.html` — add the filter form, the active-filter hint, and the filter-aware empty state
- `expense-tracker/static/css/style.css` — add styles for the filter form using existing CSS variables (no new hex literals)

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never interpolate `start_date` / `end_date` into SQL
- Passwords hashed with werkzeug (unchanged in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate date inputs with `datetime.strptime(value, "%Y-%m-%d")` inside a `try/except`; on `ValueError` treat that bound as absent (do not 500)
- If `start_date > end_date`, treat the filter as invalid and fall back to no filter (do not crash)
- Stats (`total_spent`, `expense_count`, `categories`, `top_category`) MUST be derived from the filtered expense list, not from the full set
- Do not move the existing `get_expenses_by_user` helper or change its signature — add the new helper alongside it
- Form method must be `GET` so filters are bookmarkable and shareable

## Definition of done
- [ ] Visiting `/profile` with no query params behaves exactly as before (all expenses, full totals)
- [ ] Submitting the filter form with both dates set re-renders the page showing only expenses with `date` between `start_date` and `end_date` inclusive
- [ ] `total_spent`, `expense_count`, top category, and the category breakdown bars all recompute from the filtered set
- [ ] Submitting only `start_date` (or only `end_date`) applies a one-sided bound
- [ ] Submitting an invalid date (e.g. `2026-13-40`) does not 500 — the page renders as if that bound was not provided
- [ ] Submitting `start_date` after `end_date` does not 500 — the page falls back to no filter
- [ ] The two date inputs are pre-filled with the currently active filter values after submission
- [ ] A "Clear" link resets the filter and returns to the unfiltered profile page
- [ ] Filtered empty state shows a range-specific message, not the "Add your first one" copy
- [ ] No raw user input is interpolated into SQL (verified by reading `get_expenses_by_user_in_range`)
- [ ] App starts without errors and existing logged-out redirect on `/profile` still works
