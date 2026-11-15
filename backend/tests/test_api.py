"""API integration tests with FastAPI's TestClient and a real SQLite file."""

from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.fakes import FixedClock

TODAY = date(2026, 11, 14)
API = "/api/v1"


def make_client(tmp_path: Path, seed: bool = False) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'api.db'}",
        seed_demo_data=seed,
        scheduler_enabled=False,
        notification_channels="console,in_app",
        _env_file=None,  # type: ignore[call-arg]
    )
    return TestClient(create_app(settings, FixedClock(TODAY)))


def sign_up(client: TestClient, email: str = "me@test.dev") -> dict[str, str]:
    response = client.post(
        f"{API}/auth/register", json={"name": "Test User", "email": email, "password": "secret123"}
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    """A signed-in client for a brand-new account (which gets the starter kit)."""
    with make_client(tmp_path) as test_client:
        test_client.headers.update(sign_up(test_client))
        yield test_client


def create_category(client: TestClient, name: str = "Groceries", limit: str | None = "1000") -> str:
    body = {"name": name, "color": "#e2a23b", "icon": "utensils", "monthly_limit": limit}
    response = client.post(f"{API}/categories", json=body)
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def add_expense(client: TestClient, amount: str, category_id: str | None, text: str = "Lunch"):  # type: ignore[no-untyped-def]
    return client.post(
        f"{API}/transactions",
        json={
            "type": "expense",
            "amount": amount,
            "description": text,
            "occurred_on": TODAY.isoformat(),
            "category_id": category_id,
        },
    )


def test_health_and_docs(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    assert "/api/v1/reports/{report_type}" in client.get("/openapi.json").json()["paths"]


def test_category_crud_and_conflicts(client: TestClient) -> None:
    food = create_category(client)
    duplicate = client.post(f"{API}/categories", json={"name": "groceries"})
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "conflict"
    renamed = client.put(
        f"{API}/categories/{food}",
        json={
            "name": "Weekly shop",
            "color": "#000000",
            "icon": "utensils",
            "monthly_limit": "1500",
        },
    )
    assert renamed.json()["monthly_limit"] == "1500.00"
    names = [c["name"] for c in client.get(f"{API}/categories").json()]
    assert "Weekly shop" in names
    assert names[-1] == "Uncategorized"
    assert client.delete(f"{API}/categories/{food}").status_code == 204


def test_expense_crossing_thresholds_creates_alerts_once(client: TestClient) -> None:
    food = create_category(client)
    assert add_expense(client, "850", food).status_code == 201
    assert add_expense(client, "100", food).status_code == 201
    alerts = client.get(f"{API}/alerts").json()
    assert [a["threshold"] for a in alerts] == ["80"]
    add_expense(client, "100", food)
    assert client.get(f"{API}/alerts/unread-count").json() == {"count": 2}
    first = client.get(f"{API}/alerts").json()[0]["id"]
    assert client.post(f"{API}/alerts/{first}/read").status_code == 204
    assert client.post(f"{API}/alerts/read-all").json() == {"updated": 1}
    assert client.post(f"{API}/alerts/missing/read").status_code == 404


def test_transaction_lifecycle_and_listing(client: TestClient) -> None:
    food = create_category(client, limit=None)
    created = add_expense(client, "120.50", food, "Team lunch").json()
    assert created["amount"] == "120.50"
    tx_id = created["id"]
    updated = client.put(
        f"{API}/transactions/{tx_id}",
        json={
            "type": "expense",
            "amount": "99.99",
            "description": "Team lunch",
            "occurred_on": "2026-11-02",
            "category_id": food,
        },
    )
    assert updated.json()["amount"] == "99.99"
    page = client.get(f"{API}/transactions", params={"search": "team", "month": "2026-11"}).json()
    assert page["total"] == 1
    assert client.delete(f"{API}/transactions/{tx_id}").status_code == 204
    missing = client.get(f"{API}/transactions/{tx_id}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


def test_validation_errors_use_the_envelope(client: TestClient) -> None:
    response = add_expense(client, "-5", None, "")
    assert response.status_code == 422
    fields = {d["field"] for d in response.json()["error"]["details"]}
    assert fields == {"amount", "description"}
    food = create_category(client, limit=None)
    zero = client.put(f"{API}/budgets/{food}", json={"monthly_limit": "0"})
    assert zero.status_code == 422
    assert client.get(f"{API}/dashboard", params={"month": "2026-13"}).status_code == 422


def test_budgets_endpoints(client: TestClient) -> None:
    food = create_category(client, limit=None)
    status = client.put(f"{API}/budgets/{food}", json={"monthly_limit": "500"}).json()
    assert status["health"] == "ok"
    add_expense(client, "450", food)
    [row] = client.get(f"{API}/budgets").json()
    assert (row["health"], row["percent_used"]) == ("warning", "90.0")
    assert client.delete(f"{API}/budgets/{food}").status_code == 204
    assert client.get(f"{API}/budgets").json() == []


def test_rules_and_suggestions(client: TestClient) -> None:
    cabs = create_category(client, "Cabs", None)
    rule = client.post(f"{API}/rules", json={"keyword": "BluSmart", "category_id": cabs})
    assert rule.json()["keyword"] == "blusmart"
    suggestion = client.get(f"{API}/categorize/suggest", params={"description": "BluSmart home"})
    assert suggestion.json()["matched_by"] == "keyword"
    assert suggestion.json()["category_name"] == "Cabs"
    starter = client.get(f"{API}/categorize/suggest", params={"description": "Uber home"})
    assert starter.json()["category_name"] == "Transport"
    fallback = client.get(f"{API}/categorize/suggest", params={"description": "???"}).json()
    assert fallback["category_name"] == "Uncategorized"
    assert client.delete(f"{API}/rules/{rule.json()['id']}").status_code == 204


def test_reports(client: TestClient) -> None:
    food = create_category(client)
    add_expense(client, "300", food)
    types = [r["key"] for r in client.get(f"{API}/reports").json()]
    assert types == ["monthly-summary", "category-wise", "spending-trend"]
    report = client.get(f"{API}/reports/category-wise", params={"month": "2026-11"}).json()
    assert report["rows"][0]["spent"] == "300.00"
    assert report["chart"]["kind"] == "pie"
    assert client.get(f"{API}/reports/unknown").status_code == 404


def test_recurring_endpoints_are_idempotent(client: TestClient) -> None:
    created = client.post(
        f"{API}/recurring",
        json={
            "description": "Rent",
            "amount": "20000",
            "frequency": "monthly",
            "start_date": "2026-09-01",
        },
    ).json()
    assert created["next_due"] == "2026-12-01"
    assert client.post(f"{API}/recurring/run").json() == {"created": 0}
    rent = client.get(f"{API}/transactions", params={"search": "rent"}).json()
    assert rent["total"] == 3
    paused = client.post(f"{API}/recurring/{created['id']}/pause").json()
    assert paused["is_active"] is False
    assert client.post(f"{API}/recurring/{created['id']}/resume").json()["is_active"] is True
    assert client.delete(f"{API}/recurring/{created['id']}").status_code == 204
    bad = client.post(
        f"{API}/recurring",
        json={
            "description": "X",
            "amount": "1",
            "frequency": "daily",
            "start_date": "2026-09-02",
            "end_date": "2026-09-01",
        },
    )
    assert bad.status_code == 422


def test_dashboard(client: TestClient) -> None:
    food = create_category(client)
    add_expense(client, "250", food)
    data = client.get(f"{API}/dashboard").json()
    assert data["period"] == "2026-11"
    assert data["expenses"] == "250.00"
    assert data["budget_used_percent"] == "25.0"
    assert len(data["trend"]) == 6


def test_seed_runs_once_across_restarts(tmp_path: Path) -> None:
    """Restarting the app must not duplicate seed data or recurring transactions."""

    def demo_total(client: TestClient) -> tuple[int, dict[str, str]]:
        login = client.post(
            f"{API}/auth/login", json={"email": "aarav@demo.dev", "password": "Demo@1234"}
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        page = client.get(f"{API}/transactions", params={"page_size": 1}, headers=headers)
        return page.json()["total"], headers

    with make_client(tmp_path, seed=True) as first:
        accounts = first.get(f"{API}/auth/demo-accounts").json()
        assert [a["role"] for a in accounts].count("admin") == 1
        total, headers = demo_total(first)
        assert total > 100
        assert first.get(f"{API}/alerts/unread-count", headers=headers).json()["count"] >= 1
    with make_client(tmp_path, seed=True) as second:
        again, headers = demo_total(second)
        assert second.post(f"{API}/recurring/run", headers=headers).json() == {"created": 0}
        assert again == total


# --- Accounts, isolation and administration ----------------------------------


def test_protected_routes_require_a_session(tmp_path: Path) -> None:
    with make_client(tmp_path) as anonymous:
        response = anonymous.get(f"{API}/dashboard")
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
        assert response.json()["error"]["code"] == "unauthenticated"
        bad = anonymous.get(f"{API}/dashboard", headers={"Authorization": "Bearer nope"})
        assert bad.status_code == 401
        assert anonymous.get(f"{API}/alerts/stream", params={"token": "nope"}).status_code == 401


def test_register_login_and_me(tmp_path: Path) -> None:
    with make_client(tmp_path) as c:
        sign_up(c, "asha@test.dev")
        assert (
            c.post(
                f"{API}/auth/register",
                json={"name": "Again", "email": "ASHA@test.dev", "password": "secret123"},
            ).status_code
            == 409
        )
        weak = c.post(
            f"{API}/auth/register",
            json={"name": "W", "email": "w@test.dev", "password": "password"},
        )
        assert weak.status_code == 422
        wrong = c.post(f"{API}/auth/login", json={"email": "asha@test.dev", "password": "x"})
        assert wrong.status_code == 401
        ok = c.post(f"{API}/auth/login", json={"email": "asha@test.dev", "password": "secret123"})
        token = ok.json()["access_token"]
        me = c.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
        assert (me["email"], me["role"]) == ("asha@test.dev", "user")
        assert "password_hash" not in me


def test_users_cannot_see_or_touch_each_others_data(tmp_path: Path) -> None:
    with make_client(tmp_path) as c:
        alice, bob = sign_up(c, "alice@test.dev"), sign_up(c, "bob@test.dev")
        groceries = c.post(
            f"{API}/categories", json={"name": "Groceries", "monthly_limit": "100"}, headers=alice
        ).json()["id"]
        tx = c.post(
            f"{API}/transactions",
            json={
                "type": "expense",
                "amount": "90",
                "description": "Veg",
                "occurred_on": TODAY.isoformat(),
                "category_id": groceries,
            },
            headers=alice,
        ).json()["id"]
        assert c.get(f"{API}/transactions", headers=bob).json()["total"] == 0
        assert c.get(f"{API}/transactions/{tx}", headers=bob).status_code == 404
        assert c.delete(f"{API}/transactions/{tx}", headers=bob).status_code == 404
        assert c.delete(f"{API}/categories/{groceries}", headers=bob).status_code == 404
        steal = c.post(
            f"{API}/transactions",
            json={
                "type": "expense",
                "amount": "1",
                "description": "x",
                "occurred_on": TODAY.isoformat(),
                "category_id": groceries,
            },
            headers=bob,
        )
        assert steal.status_code == 404
        assert c.get(f"{API}/alerts/unread-count", headers=alice).json() == {"count": 1}
        assert c.get(f"{API}/alerts/unread-count", headers=bob).json() == {"count": 0}
        # Same category name is fine for different users.
        assert (
            c.post(f"{API}/categories", json={"name": "Groceries"}, headers=bob).status_code == 201
        )


def test_admin_console(tmp_path: Path) -> None:
    with make_client(tmp_path, seed=True) as c:

        def login(email: str, password: str) -> dict[str, str]:
            r = c.post(f"{API}/auth/login", json={"email": email, "password": password})
            return {"Authorization": f"Bearer {r.json()['access_token']}"}

        admin = login("admin@budgettracker.dev", "Admin@1234")
        member = login("priya@demo.dev", "Demo@1234")
        assert c.get(f"{API}/admin/overview", headers=member).status_code == 403
        overview = c.get(f"{API}/admin/overview", headers=admin).json()
        assert overview["total_users"] >= 4
        assert len(overview["signups_by_day"]) == 14
        users = c.get(f"{API}/admin/users", headers=admin).json()
        priya = next(u for u in users if u["email"] == "priya@demo.dev")
        assert priya["transaction_count"] > 0
        me = next(u for u in users if u["email"] == "admin@budgettracker.dev")
        assert (
            c.patch(
                f"{API}/admin/users/{me['id']}", json={"is_active": False}, headers=admin
            ).status_code
            == 409
        )
        off = c.patch(f"{API}/admin/users/{priya['id']}", json={"is_active": False}, headers=admin)
        assert off.json()["is_active"] is False
        assert c.get(f"{API}/dashboard", headers=member).status_code == 401
        blocked = c.post(
            f"{API}/auth/login", json={"email": "priya@demo.dev", "password": "Demo@1234"}
        )
        assert blocked.status_code == 401
