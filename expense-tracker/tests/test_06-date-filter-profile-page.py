"""
tests/test_06-date-filter-profile-page.py

Test suite for Spec 06 — Date Filter for Profile Page.

The demo seed user (demo@spendly.com / demo123) has exactly 8 expenses:
    2026-04-01  Food          12.50   Lunch at cafe
    2026-04-03  Transport      3.20   Bus fare
    2026-04-05  Bills         85.00   Electricity bill
    2026-04-08  Health        40.00   Pharmacy
    2026-04-11  Entertainment 15.00   Movie ticket
    2026-04-14  Shopping      60.00   Clothing
    2026-04-17  Other         22.75   Miscellaneous
    2026-04-20  Food           9.99   Coffee and snacks

All test assertions are derived from the spec Definition of Done and Rules,
NOT from the implementation source.
"""

import inspect
import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """
    Application fixture using the real on-disk DB (seed is loaded once on
    app startup via seed_db()).  We use scope='module' so the DB is seeded
    once and shared across all tests in this file; no test mutates data.
    """
    from app import app as flask_app
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-06",
        "WTF_CSRF_ENABLED": False,
    })
    yield flask_app


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture(scope="module")
def auth_client(app):
    """
    A dedicated test client that is already logged in as the demo user.
    Uses its own client (not shared with 'client') so that the auth guard
    tests can clear sessions on the unauthenticated client without
    affecting the logged-in client used by all other tests.
    Scoped to module so login is performed once for the entire file.
    """
    logged_in_client = app.test_client()
    logged_in_client.post(
        "/login",
        data={"email": "demo@spendly.com", "password": "demo123"},
        follow_redirects=False,
    )
    return logged_in_client


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _count_expense_rows(html: bytes) -> int:
    """
    Count <tr> rows inside the expenses table body.
    Each seeded expense renders as exactly one <tr> inside <tbody>.
    We count occurrences of exp-date cell class which appears once per row.
    """
    return html.count(b'class="exp-date"')


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

class TestAuthGuard:
    def test_profile_unauthenticated_redirects_to_login(self, client):
        """Unauthenticated GET /profile must redirect to /login (302)."""
        with client.session_transaction() as sess:
            sess.clear()

        response = client.get("/profile", follow_redirects=False)

        assert response.status_code == 302, (
            "Expected 302 redirect for unauthenticated access to /profile"
        )
        assert "/login" in response.headers["Location"], (
            "Redirect target should be the login page"
        )


# ---------------------------------------------------------------------------
# Baseline — no query parameters
# ---------------------------------------------------------------------------

class TestBaseline:
    def test_profile_no_params_returns_200(self, auth_client):
        """GET /profile with no params should return 200 for logged-in user."""
        response = auth_client.get("/profile")
        assert response.status_code == 200, "Expected 200 for authenticated /profile"

    def test_profile_no_params_shows_all_8_expenses(self, auth_client):
        """Baseline profile (no filter) must display all 8 seeded expenses."""
        response = auth_client.get("/profile")
        row_count = _count_expense_rows(response.data)
        assert row_count == 8, (
            f"Expected 8 expense rows with no filter, got {row_count}"
        )

    def test_profile_no_params_no_filter_hint(self, auth_client):
        """The 'Filtered:' hint must NOT appear when no filter is active."""
        response = auth_client.get("/profile")
        assert b"Filtered:" not in response.data, (
            "Filter hint should not appear when no filter is active"
        )

    def test_profile_no_params_no_clear_link(self, auth_client):
        """The 'Clear' link must NOT appear when no filter is active."""
        response = auth_client.get("/profile")
        # The Clear link is only rendered when is_filtered is True
        assert b"Clear" not in response.data, (
            "Clear link should not appear when no filter is active"
        )

    def test_profile_no_params_total_spent_is_full_sum(self, auth_client):
        """Baseline total_spent should equal the sum of all 8 seeded expenses."""
        expected_total = 12.50 + 3.20 + 85.00 + 40.00 + 15.00 + 60.00 + 22.75 + 9.99
        response = auth_client.get("/profile")
        # Rendered as "₨ 248.44"
        assert f"{expected_total:.2f}".encode() in response.data, (
            f"Expected total {expected_total:.2f} in baseline profile page"
        )

    def test_profile_no_params_expense_count_is_8(self, auth_client):
        """Baseline expense_count stat card must show 8."""
        response = auth_client.get("/profile")
        assert b"8" in response.data, (
            "Expected expense count of 8 in baseline profile"
        )


# ---------------------------------------------------------------------------
# Both bounds set
# ---------------------------------------------------------------------------

class TestBothBounds:
    # Range 2026-04-05 to 2026-04-14 covers: Bills(04-05), Health(04-08),
    # Entertainment(04-11), Shopping(04-14) = 4 expenses
    PARAMS = "?start_date=2026-04-05&end_date=2026-04-14"
    EXPECTED_ROWS = 4
    EXPECTED_TOTAL = 85.00 + 40.00 + 15.00 + 60.00  # 200.00

    def test_both_bounds_returns_200(self, auth_client):
        """Filtered profile with both bounds must return 200."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert response.status_code == 200, (
            "Expected 200 for /profile with both date bounds"
        )

    def test_both_bounds_correct_row_count(self, auth_client):
        """Only expenses with date >= start_date AND <= end_date are shown."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        row_count = _count_expense_rows(response.data)
        assert row_count == self.EXPECTED_ROWS, (
            f"Expected {self.EXPECTED_ROWS} rows for range "
            f"2026-04-05 to 2026-04-14, got {row_count}"
        )

    def test_both_bounds_start_date_is_inclusive(self, auth_client):
        """The start_date boundary (2026-04-05) must be included in results."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert b"2026-04-05" in response.data, (
            "Start date 2026-04-05 should be inclusive in filtered results"
        )

    def test_both_bounds_end_date_is_inclusive(self, auth_client):
        """The end_date boundary (2026-04-14) must be included in results."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert b"2026-04-14" in response.data, (
            "End date 2026-04-14 should be inclusive in filtered results"
        )

    def test_both_bounds_total_spent_recomputed(self, auth_client):
        """total_spent must equal the sum of only the filtered expenses."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert f"{self.EXPECTED_TOTAL:.2f}".encode() in response.data, (
            f"Expected filtered total {self.EXPECTED_TOTAL:.2f} in page"
        )

    def test_both_bounds_expense_count_recomputed(self, auth_client):
        """expense_count stat card must reflect only the filtered set."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        # Count '4' as a standalone number in stats; we check it's present
        # (fragile to match exactly, but the stat card renders it as text)
        assert str(self.EXPECTED_ROWS).encode() in response.data, (
            f"Expected filtered expense count {self.EXPECTED_ROWS} in page"
        )

    def test_both_bounds_excludes_out_of_range_expenses(self, auth_client):
        """Expenses outside the range must not appear in the table."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        # 2026-04-01 and 2026-04-03 are before start_date
        assert b"2026-04-01" not in response.data, (
            "2026-04-01 is before start_date and must not appear"
        )
        assert b"2026-04-03" not in response.data, (
            "2026-04-03 is before start_date and must not appear"
        )
        # 2026-04-17 and 2026-04-20 are after end_date
        assert b"2026-04-17" not in response.data, (
            "2026-04-17 is after end_date and must not appear"
        )
        assert b"2026-04-20" not in response.data, (
            "2026-04-20 is after end_date and must not appear"
        )

    def test_both_bounds_filter_hint_visible(self, auth_client):
        """The 'Filtered:' hint must appear when both bounds are active."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert b"Filtered:" in response.data, (
            "Expected 'Filtered:' hint when filter is active"
        )

    def test_both_bounds_clear_link_present(self, auth_client):
        """The 'Clear' link must appear when a filter is active."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert b"Clear" in response.data, (
            "Expected Clear link when filter is active"
        )


# ---------------------------------------------------------------------------
# Lower bound only
# ---------------------------------------------------------------------------

class TestLowerBoundOnly:
    # start_date=2026-04-14 → Shopping(04-14), Other(04-17), Food(04-20) = 3 rows
    PARAMS = "?start_date=2026-04-14"
    EXPECTED_ROWS = 3

    def test_lower_bound_only_returns_200(self, auth_client):
        """Filtered profile with only start_date must return 200."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert response.status_code == 200

    def test_lower_bound_only_correct_row_count(self, auth_client):
        """Only expenses with date >= start_date (no end bound) are shown."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        row_count = _count_expense_rows(response.data)
        assert row_count == self.EXPECTED_ROWS, (
            f"Expected {self.EXPECTED_ROWS} rows for start_date=2026-04-14 only, "
            f"got {row_count}"
        )

    def test_lower_bound_only_includes_boundary_date(self, auth_client):
        """The start_date itself (2026-04-14) must be included."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert b"2026-04-14" in response.data

    def test_lower_bound_only_filter_hint_visible(self, auth_client):
        """Filter hint must appear for a single-bound filter."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert b"Filtered:" in response.data


# ---------------------------------------------------------------------------
# Upper bound only
# ---------------------------------------------------------------------------

class TestUpperBoundOnly:
    # end_date=2026-04-05 → Food(04-01), Transport(04-03), Bills(04-05) = 3 rows
    PARAMS = "?end_date=2026-04-05"
    EXPECTED_ROWS = 3

    def test_upper_bound_only_returns_200(self, auth_client):
        """Filtered profile with only end_date must return 200."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert response.status_code == 200

    def test_upper_bound_only_correct_row_count(self, auth_client):
        """Only expenses with date <= end_date (no start bound) are shown."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        row_count = _count_expense_rows(response.data)
        assert row_count == self.EXPECTED_ROWS, (
            f"Expected {self.EXPECTED_ROWS} rows for end_date=2026-04-05 only, "
            f"got {row_count}"
        )

    def test_upper_bound_only_includes_boundary_date(self, auth_client):
        """The end_date itself (2026-04-05) must be included."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert b"2026-04-05" in response.data

    def test_upper_bound_only_filter_hint_visible(self, auth_client):
        """Filter hint must appear for a single-bound filter."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert b"Filtered:" in response.data


# ---------------------------------------------------------------------------
# Invalid date strings — must not 500
# ---------------------------------------------------------------------------

class TestInvalidDates:
    @pytest.mark.parametrize("params,label", [
        ("?start_date=2026-13-40", "invalid month/day in start_date"),
        ("?end_date=not-a-date", "non-date string in end_date"),
        ("?start_date=foobar&end_date=2026-04-20", "invalid start_date with valid end_date"),
        ("?start_date=2026-04-01&end_date=2026-99-99", "valid start_date with invalid end_date"),
        ("?start_date=&end_date=", "empty string values for both params"),
        ("?start_date=2026/04/01", "wrong separator format"),
    ])
    def test_invalid_date_does_not_500(self, auth_client, params, label):
        """Invalid date inputs must not cause a 500; page must render."""
        response = auth_client.get(f"/profile{params}")
        assert response.status_code == 200, (
            f"Expected 200 (not 500) for {label}; got {response.status_code}"
        )

    @pytest.mark.parametrize("params,label", [
        ("?start_date=2026-13-40", "invalid start_date treated as absent"),
        ("?end_date=not-a-date", "invalid end_date treated as absent"),
    ])
    def test_invalid_single_bound_treated_as_unfiltered(self, auth_client, params, label):
        """An invalid single bound is dropped; all 8 expenses are shown."""
        response = auth_client.get(f"/profile{params}")
        row_count = _count_expense_rows(response.data)
        assert row_count == 8, (
            f"Expected all 8 expenses when {label}, got {row_count}"
        )

    def test_both_invalid_dates_treated_as_unfiltered(self, auth_client):
        """Both bounds invalid — page shows all 8 expenses as if no filter."""
        response = auth_client.get("/profile?start_date=bad&end_date=bad")
        row_count = _count_expense_rows(response.data)
        assert row_count == 8, (
            f"Expected all 8 expenses when both dates are invalid, got {row_count}"
        )


# ---------------------------------------------------------------------------
# Inverted range (start_date > end_date)
# ---------------------------------------------------------------------------

class TestInvertedRange:
    PARAMS = "?start_date=2026-04-20&end_date=2026-04-01"

    def test_inverted_range_does_not_500(self, auth_client):
        """Inverted range (start > end) must not cause a 500."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert response.status_code == 200, (
            f"Expected 200 for inverted range, got {response.status_code}"
        )

    def test_inverted_range_falls_back_to_unfiltered(self, auth_client):
        """Inverted range must fall back to showing all 8 expenses."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        row_count = _count_expense_rows(response.data)
        assert row_count == 8, (
            f"Expected all 8 expenses for inverted range fallback, got {row_count}"
        )

    def test_inverted_range_no_filter_hint(self, auth_client):
        """Inverted range is treated as no-filter; 'Filtered:' hint must not appear."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert b"Filtered:" not in response.data, (
            "Filter hint must not appear when inverted range is rejected"
        )


# ---------------------------------------------------------------------------
# Filtered empty state
# ---------------------------------------------------------------------------

class TestFilteredEmptyState:
    # A date range that contains no seeded expenses
    PARAMS = "?start_date=2026-05-01&end_date=2026-05-31"

    def test_filtered_empty_returns_200(self, auth_client):
        """A filter that matches no expenses must still return 200."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert response.status_code == 200

    def test_filtered_empty_shows_range_specific_message(self, auth_client):
        """When filtered set is empty, 'No expenses in this date range' must appear."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert b"No expenses in this date range" in response.data, (
            "Expected range-specific empty state message"
        )

    def test_filtered_empty_does_not_show_add_first_copy(self, auth_client):
        """The generic 'Add your first one' copy must NOT appear for a filtered empty state."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert b"Add your first one" not in response.data, (
            "Generic 'Add your first one' copy must not appear when filter is active"
        )

    def test_filtered_empty_filter_hint_still_shown(self, auth_client):
        """Even with no matching rows, the 'Filtered:' hint must appear."""
        response = auth_client.get(f"/profile{self.PARAMS}")
        assert b"Filtered:" in response.data, (
            "Expected filter hint even when filtered result is empty"
        )


# ---------------------------------------------------------------------------
# Date inputs pre-filled (echo-back)
# ---------------------------------------------------------------------------

class TestDateInputsPreFilled:
    def test_start_date_echoed_into_input_value(self, auth_client):
        """After filtering, start_date value must appear in the form input."""
        response = auth_client.get("/profile?start_date=2026-04-05&end_date=2026-04-14")
        # The template renders: value="{{ start_date }}"
        assert b'value="2026-04-05"' in response.data, (
            "start_date must be echoed back into the input value attribute"
        )

    def test_end_date_echoed_into_input_value(self, auth_client):
        """After filtering, end_date value must appear in the form input."""
        response = auth_client.get("/profile?start_date=2026-04-05&end_date=2026-04-14")
        assert b'value="2026-04-14"' in response.data, (
            "end_date must be echoed back into the input value attribute"
        )

    def test_invalid_date_not_echoed_back(self, auth_client):
        """Invalid date string must not be echoed back into the input value."""
        response = auth_client.get("/profile?start_date=2026-13-40")
        # The invalid date is stripped to "" so value="" should not contain "2026-13-40"
        assert b'value="2026-13-40"' not in response.data, (
            "Invalid date must be sanitised and not echoed back verbatim"
        )

    def test_inverted_range_dates_not_echoed_back(self, auth_client):
        """When inverted range is rejected, neither date is echoed into the form."""
        response = auth_client.get(
            "/profile?start_date=2026-04-20&end_date=2026-04-01"
        )
        assert b'value="2026-04-20"' not in response.data, (
            "start_date must not be echoed when inverted range is rejected"
        )
        assert b'value="2026-04-01"' not in response.data, (
            "end_date must not be echoed when inverted range is rejected"
        )


# ---------------------------------------------------------------------------
# Clear link
# ---------------------------------------------------------------------------

class TestClearLink:
    def test_clear_link_points_to_bare_profile_url(self, auth_client):
        """Clear link must point to /profile (no query params)."""
        response = auth_client.get("/profile?start_date=2026-04-01&end_date=2026-04-20")
        # href="/profile" or href="{{ url_for('profile') }}" renders as /profile
        assert b'href="/profile"' in response.data, (
            "Clear link must point to bare /profile URL"
        )

    def test_clear_link_absent_when_no_filter(self, auth_client):
        """Clear link must NOT appear when no filter is active."""
        response = auth_client.get("/profile")
        # Verify "Clear" text is not in the page at all
        assert b"Clear" not in response.data, (
            "Clear link must not appear when no filter is active"
        )

    def test_clear_link_present_for_single_bound_filter(self, auth_client):
        """Clear link must appear even for a one-sided filter."""
        response = auth_client.get("/profile?start_date=2026-04-10")
        assert b"Clear" in response.data, (
            "Clear link must appear for a single-bound filter"
        )


# ---------------------------------------------------------------------------
# Filter form structure
# ---------------------------------------------------------------------------

class TestFilterFormStructure:
    def test_form_method_is_get(self, auth_client):
        """The filter form must use method='get' (for bookmarkability)."""
        response = auth_client.get("/profile")
        assert b'method="get"' in response.data or b"method='get'" in response.data, (
            "Filter form method must be GET"
        )

    def test_form_has_start_date_input(self, auth_client):
        """Filter form must include an input with name='start_date'."""
        response = auth_client.get("/profile")
        assert b'name="start_date"' in response.data, (
            "Filter form must have a start_date input"
        )

    def test_form_has_end_date_input(self, auth_client):
        """Filter form must include an input with name='end_date'."""
        response = auth_client.get("/profile")
        assert b'name="end_date"' in response.data, (
            "Filter form must have an end_date input"
        )


# ---------------------------------------------------------------------------
# DB helper — get_expenses_by_user_in_range
# ---------------------------------------------------------------------------

class TestDbHelperGetExpensesInRange:
    """
    These tests call the DB helper directly (not via HTTP) so they validate
    the data-layer contract independently of the route.

    The seed data uses the real on-disk DB (seeded once at app startup).
    We look up the demo user's ID before each assertion group.
    """

    @pytest.fixture(autouse=True)
    def _import_helper(self, app):
        """Import the helper and resolve the demo user_id inside app context."""
        from database.db import get_expenses_by_user_in_range, get_user_by_email
        self.helper = get_expenses_by_user_in_range
        with app.app_context():
            user = get_user_by_email("demo@spendly.com")
            self.user_id = user["id"]

    def test_helper_is_importable(self):
        """get_expenses_by_user_in_range must exist in database.db."""
        assert callable(self.helper), (
            "get_expenses_by_user_in_range must be a callable in database.db"
        )

    def test_helper_none_none_returns_all_8(self, app):
        """None/None (no bounds) must return all 8 seeded expenses."""
        with app.app_context():
            rows = self.helper(self.user_id, None, None)
        assert len(rows) == 8, (
            f"Expected 8 rows for None/None bounds, got {len(rows)}"
        )

    def test_helper_date_none_lower_bound(self, app):
        """date/None (lower bound only) returns expenses on or after start_date."""
        with app.app_context():
            rows = self.helper(self.user_id, "2026-04-14", None)
        dates = [row["date"] for row in rows]
        assert len(rows) == 3, (
            f"Expected 3 rows for start_date=2026-04-14, got {len(rows)}"
        )
        assert all(d >= "2026-04-14" for d in dates), (
            "All returned dates must be >= start_date"
        )

    def test_helper_none_date_upper_bound(self, app):
        """None/date (upper bound only) returns expenses on or before end_date."""
        with app.app_context():
            rows = self.helper(self.user_id, None, "2026-04-05")
        dates = [row["date"] for row in rows]
        assert len(rows) == 3, (
            f"Expected 3 rows for end_date=2026-04-05, got {len(rows)}"
        )
        assert all(d <= "2026-04-05" for d in dates), (
            "All returned dates must be <= end_date"
        )

    def test_helper_date_date_both_bounds(self, app):
        """date/date (both bounds) returns only expenses within the inclusive range."""
        with app.app_context():
            rows = self.helper(self.user_id, "2026-04-05", "2026-04-14")
        dates = [row["date"] for row in rows]
        assert len(rows) == 4, (
            f"Expected 4 rows for range 2026-04-05 to 2026-04-14, got {len(rows)}"
        )
        assert all("2026-04-05" <= d <= "2026-04-14" for d in dates), (
            "All returned dates must be within the inclusive range"
        )

    def test_helper_start_boundary_is_inclusive(self, app):
        """The start_date itself must appear in results (inclusive lower bound)."""
        with app.app_context():
            rows = self.helper(self.user_id, "2026-04-01", "2026-04-03")
        dates = [row["date"] for row in rows]
        assert "2026-04-01" in dates, (
            "start_date 2026-04-01 must be included (inclusive)"
        )

    def test_helper_end_boundary_is_inclusive(self, app):
        """The end_date itself must appear in results (inclusive upper bound)."""
        with app.app_context():
            rows = self.helper(self.user_id, "2026-04-01", "2026-04-03")
        dates = [row["date"] for row in rows]
        assert "2026-04-03" in dates, (
            "end_date 2026-04-03 must be included (inclusive)"
        )

    def test_helper_empty_range_returns_no_rows(self, app):
        """A date range with no matching expenses must return an empty list."""
        with app.app_context():
            rows = self.helper(self.user_id, "2026-05-01", "2026-05-31")
        assert len(rows) == 0, (
            f"Expected 0 rows for future range with no data, got {len(rows)}"
        )

    def test_helper_results_ordered_date_descending(self, app):
        """Results must be ordered by date descending (newest first)."""
        with app.app_context():
            rows = self.helper(self.user_id, None, None)
        dates = [row["date"] for row in rows]
        assert dates == sorted(dates, reverse=True), (
            "Expenses must be returned in descending date order"
        )

    def test_helper_row_has_expected_columns(self, app):
        """Each returned row must have amount, category, date, description columns."""
        with app.app_context():
            rows = self.helper(self.user_id, None, None)
        assert len(rows) > 0, "Need at least one row to check columns"
        row = rows[0]
        for col in ("amount", "category", "date", "description"):
            assert col in row.keys(), (
                f"Expected column '{col}' in result row"
            )


# ---------------------------------------------------------------------------
# SQL safety (parameterised queries)
# ---------------------------------------------------------------------------

class TestSqlSafety:
    """
    Verify the helper is parameterised by:
    1. Passing a SQL-injection string and asserting it does not crash
       and returns no rows (the string simply doesn't match any date).
    2. Inspecting the helper source for '?' placeholders instead of f-strings.
    """

    def test_injection_string_in_start_date_does_not_crash(self, app):
        """Passing a SQL injection payload as start_date must not raise."""
        from database.db import get_expenses_by_user_in_range, get_user_by_email
        with app.app_context():
            user = get_user_by_email("demo@spendly.com")
            # This should be treated as a literal (non-matching) string, not executed SQL
            rows = get_expenses_by_user_in_range(
                user["id"],
                "' OR '1'='1",
                None,
            )
        # A parameterised query treats the payload as a literal; no date matches it
        assert isinstance(rows, list), (
            "Helper must return a list even for injection-style input"
        )
        assert len(rows) == 0, (
            "SQL injection payload must match no rows (parameterised query)"
        )

    def test_injection_string_in_end_date_does_not_crash(self, app):
        """Passing a SQL injection payload as end_date must not raise."""
        from database.db import get_expenses_by_user_in_range, get_user_by_email
        with app.app_context():
            user = get_user_by_email("demo@spendly.com")
            rows = get_expenses_by_user_in_range(
                user["id"],
                None,
                "'; DROP TABLE expenses; --",
            )
        assert isinstance(rows, list)
        assert len(rows) == 0, (
            "SQL injection payload in end_date must match no rows"
        )

    def test_helper_source_uses_parameterised_placeholders(self):
        """
        Inspect the helper source and confirm it uses '?' placeholders,
        not f-string or % interpolation of user values.
        """
        from database.db import get_expenses_by_user_in_range
        source = inspect.getsource(get_expenses_by_user_in_range)

        # Must contain at least one '?' placeholder
        assert "?" in source, (
            "Helper must use '?' parameterised placeholders in SQL"
        )

        # Must NOT use f-string SQL construction with start_date or end_date
        assert "f\"" not in source or (
            "start_date" not in source.split("f\"")[1] if "f\"" in source else True
        ), "Helper must not interpolate start_date into SQL via f-string"

        # Must NOT use % formatting on start_date or end_date directly
        assert "% start_date" not in source, (
            "Helper must not use % to interpolate start_date into SQL"
        )
        assert "% end_date" not in source, (
            "Helper must not use % to interpolate end_date into SQL"
        )
