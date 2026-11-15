# Personal Budget Tracker with Smart Spending Alerts

A multi-user budgeting web app: anyone can sign up, set monthly limits per category, record income and expenses, and get warned **while** they spend, at 80% and again at 100% of a budget, once per category per month. Expenses are categorised automatically, recurring payments are recorded on their due dates, reports show where the money went, and an admin console manages the platform.

| | |
|---|---|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, APScheduler, Server-Sent Events |
| **Frontend** | Next.js 15 (App Router), TypeScript, Tailwind CSS 4, shadcn/ui, Recharts, TanStack Query, React Hook Form + Zod |
| **Accounts** | Sign-up and sign-in, scrypt password hashing, signed JWT sessions, login throttling, per-user data isolation, admin role |
| **Quality** | 151 pytest tests (97% coverage), `ruff`, `mypy --strict` on the whole backend, strict TypeScript, ESLint with zero warnings |

**Documentation:** [Design](docs/DESIGN.md) · [UML diagrams](docs/UML.md) · [Extending the system](docs/EXTENDING.md) · [Viva Q&A](docs/VIVA_QA.md)

---

## Quick start (about 3 minutes)

### Prerequisites

- **Python 3.12+** (`python3 --version`)
- **Node.js 20+** and npm (`node --version`)

No database server is needed: the backend uses a SQLite file by default.

### 1. Backend (terminal 1)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:create_app --factory --reload
```

On first start the backend creates `budget_tracker.db`, runs the migrations and creates the **demo accounts below**, each with six months of their own data. The API is now at <http://localhost:8000> and interactive docs at <http://localhost:8000/docs> (click **Authorize** and paste a token from `/api/v1/auth/login` to try protected routes).

> Upgrading from the single-user version? Delete `backend/budget_tracker.db*` first; the schema now includes accounts.

### 2. Frontend (terminal 2)

```bash
cd frontend
cp .env.example .env.local         # points the UI at http://localhost:8000
npm install
npm run dev
```

Open <http://localhost:3000> for the landing page, or go straight to <http://localhost:3000/login>.

### Demo accounts

The sign-in page lists these as one-click cards, so you never need to type them.

| Who | E-mail | Password | What you'll see |
|---|---|---|---|
| Maya Kapoor (**admin**) | `admin@budgettracker.dev` | `Admin@1234` | Admin console: platform stats, user management. Also has her own budget. |
| Aarav Sharma | `aarav@demo.dev` | `Demo@1234` | Young professional, several budgets running hot |
| Priya Nair | `priya@demo.dev` | `Demo@1234` | Student on a stipend, small tight budgets |
| Rohan Mehta | `rohan@demo.dev` | `Demo@1234` | Family with bigger bills |

Eight extra lightweight accounts (one deactivated) are also created so the admin user list looks realistic. Or just **create your own account** at `/signup`: you start with common categories and keyword rules already set up.

### Or with Docker

```bash
docker compose up --build
```

Frontend on port 3000, API on port 8000. Data persists in a Docker volume.

> The Compose and Dockerfile setup is provided but was not run in the environment where this project was built (no Docker there). The manual steps above were verified end to end.

---

## Demo walkthrough (6 minutes)

1. **Landing page** (`/`). Drag the two sliders in the hero: the budget bar races the "Day" marker, and crossing 80% or 100% pops the same alerts the real app sends. Scroll for the auto-categorisation ticker and the feature grid.
2. **Sign in.** Click **Try a demo account**, then the **Aarav Sharma** card. Visiting any `/app` page while signed out redirects here and returns you afterwards.
3. **Overview.** The greeting knows your name. The green headline panel compares *budget used* with *month gone*; if the bar runs ahead of the white "Today" marker, the badge says *Spending faster than the month*. "Safe per day" is what you can spend daily for the rest of the month and still finish on budget.
4. **Quick actions.** Press **⌘K** (Ctrl+K), type `add`, press Enter: the add-transaction form opens.
5. **Auto-categorisation.** Type a description and watch the live suggestion:
   - `Uber to airport` → Transport (your keyword rule)
   - `Uber Eats dinner` → Food & Dining (the longer keyword wins)
   - `POS 4411 AMZN MKTP` → Shopping (known merchant)
   - `Sharma Dairy` → Food & Dining (your past choice)
   - `Coca-Cola crate` → Uncategorized ("ola" only matches whole words)
6. **Real-time alerts.** Add an expense of **5000** described as `Myntra jacket`. Shopping jumps past 80% and 100% at once: **two** toasts appear and the bell goes up by two. Another Shopping expense adds no alert, because each threshold fires once per category per month.
7. **Privacy between users.** Open the avatar menu, **Sign out**, and sign in as **Priya**. Different data, different alerts, different budgets. Nothing of Aarav's is reachable, even by guessing IDs in the API.
8. **Admin console.** Sign out and pick **Maya Kapoor**. You land on **Platform**: user totals, sign-ups and activity over 14 days, money tracked, alerts sent. Open **Users**: search, filter, change a role, or switch an account off. Deactivate Priya, then try signing in as her: refused, and any session she had open ends immediately. You can't change your own account (that row is locked).
9. **Budgets, Recurring, Reports.** Edit limits and keyword rules, pause a recurring payment, switch report types and export CSV.
10. **Dark mode and mobile.** Sun/moon icon top right; resize to phone width.

To watch the out-of-band real-time path, keep Aarav's dashboard open and post an expense from a terminal with his token; the toasts appear in the browser without a refresh:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"aarav@demo.dev","password":"Demo@1234"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"expense","amount":"2500","description":"Electricity bill","occurred_on":"'"$(date +%F)"'"}'
```

---

## Running the checks

```bash
cd backend
source .venv/bin/activate
pytest                          # 151 tests
pytest --cov=app                # with coverage (97%)
ruff check . && ruff format --check .
mypy                            # strict, whole backend (configured in pyproject.toml)
```

```bash
cd frontend
npm run typecheck
npm run lint
npm run build
```

### What the tests cover

| File | Focus |
|---|---|
| `test_categorization_chain.py` | Chain order, fallback, longest match, word boundaries, configurable order, builder validation, substitutability |
| `test_alert_rules.py` | Exact 80%/100% boundaries, keys, levels, a new rule plugged in |
| `test_budget_monitor.py` | Observer fires once per month; both thresholds in one transaction; rollover; edits, moves, deletes, lowered limits; failing channels isolated |
| `test_recurrence.py` | Daily/weekly/monthly schedules, month-end clamping, idempotency across re-runs, restarts and a lost generation mark; pause/resume |
| `test_reports.py` | All three report strategies, registry, a new report plugged in |
| `test_services.py` | Every application service against in-memory repositories |
| `test_persistence.py` | SQLAlchemy adapters, exact money sums, unique constraints, owner scoping, migrations match the models |
| `test_auth.py` | Sign-up, password policy, sign-in, throttling, deactivated accounts, expired/tampered/forged tokens, scrypt hashing |
| `test_admin.py` | Admin overview statistics, user listing, role/status changes, admins can't change themselves, non-admins refused |
| `test_api.py` | End-to-end HTTP tests with `TestClient` and a real SQLite file: 401/403 handling, sign-up and sign-in, **cross-user isolation**, admin console, and "seed and recurring generation don't duplicate after a restart" |
| `test_architecture.py` | Domain imports only the standard library; application imports no frameworks |
| `test_extending_examples.py` | The three worked examples in `docs/EXTENDING.md` |

---

## Configuration

### Backend (`backend/.env`, all optional)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./budget_tracker.db` | Any SQLAlchemy URL. For PostgreSQL: `pip install -e ".[postgres]"` and `postgresql+psycopg://user:pass@host:5432/db` |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Origins allowed to call the API |
| `AUTO_MIGRATE` | `true` | Run Alembic migrations on start-up |
| `SEED_DEMO_DATA` | `true` | Create the demo accounts (and their data) in an empty database, and list them on the sign-in page |
| `SCHEDULER_ENABLED` | `true` | Background generation of recurring transactions |
| `RECURRING_JOB_INTERVAL_MINUTES` | `60` | How often the generator runs (it also runs at start-up) |
| `ALERT_THRESHOLDS` | `80,100` | One alert rule per percentage |
| `NOTIFICATION_CHANNELS` | `console,in_app,email,sms` | Enabled channels |
| `CATEGORIZATION_ORDER` | `keyword,merchant,user_defined,default` | Chain of Responsibility order; must end with `default` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS` | empty / `587` / … | Real e-mail. With no `SMTP_HOST` e-mails are logged (stub mode) |
| `ALERT_EMAIL_FROM` | placeholder | Sender address; alerts go to each user's own e-mail |
| `ALERT_SMS_TO` | empty | Phone number for the SMS stub (logged) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `JWT_SECRET` | dev placeholder | **Set a long random value in production.** Signs session tokens |
| `TOKEN_LIFETIME_HOURS` | `24` | How long a sign-in lasts |

See `backend/.env.example` for a commented template.

### Frontend (`frontend/.env.local`)

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Backend base URL, without `/api/v1` |
| `NEXT_PUBLIC_CURRENCY` | `INR` | ISO currency code for formatting |
| `NEXT_PUBLIC_LOCALE` | `en-IN` | Locale for numbers and dates |

### Database migrations

Migrations run automatically on start-up. To manage them by hand:

```bash
cd backend
alembic upgrade head                          # apply
alembic revision --autogenerate -m "message"  # after changing app/infrastructure/persistence/models.py
```

To reset the demo, stop the backend and delete `backend/budget_tracker.db*`; demo accounts are recreated on the next start.

---

## API

Base path `/api/v1`. Interactive documentation at `/docs` (Swagger UI) and `/redoc`. Amounts are decimal **strings** (`"1250.00"`) so no precision is lost. Months are `YYYY-MM` and default to the current month.

**Authentication.** `POST /auth/login` (or `/auth/register`) returns `{"access_token": "...", "user": {...}}`. Send `Authorization: Bearer <token>` on every other request. Every user route only ever sees the signed-in user's data; `admin` routes also require the admin role. The SSE stream takes the token as a `?token=` query parameter because browsers' `EventSource` cannot send headers.

| Method | Path | Auth | Success | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/register` | — | 201 | Create an account with starter categories and keyword rules, and sign in. |
| `POST` | `/api/v1/auth/login` | — | 200 | Exchange e-mail and password for a bearer token. Repeated failures are throttled. |
| `GET` | `/api/v1/auth/me` | user | 200 | The signed-in user. |
| `GET` | `/api/v1/auth/demo-accounts` | — | 200 | Ready-made logins for trying the app (empty when demo data is disabled). |
| `GET` | `/api/v1/dashboard` | user | 200 | Summary cards, charts, budget progress, recent and upcoming payments. |
| `GET` | `/api/v1/transactions` | user | 200 | Search, filter, sort and paginate transactions. `month` overrides the date range. |
| `POST` | `/api/v1/transactions` | user | 201 | Record a transaction. Expenses without a category are auto-categorised. |
| `GET` | `/api/v1/transactions/{transaction_id}` | user | 200 | Fetch a single transaction. |
| `PUT` | `/api/v1/transactions/{transaction_id}` | user | 200 | Replace a transaction; the affected budget is re-checked. |
| `DELETE` | `/api/v1/transactions/{transaction_id}` | user | 204 | Delete a transaction. |
| `GET` | `/api/v1/categories` | user | 200 | All categories with their monthly limits. |
| `POST` | `/api/v1/categories` | user | 201 | Create a category, optionally with a monthly budget. |
| `GET` | `/api/v1/categories/{category_id}` | user | 200 | Fetch one category. |
| `PUT` | `/api/v1/categories/{category_id}` | user | 200 | Update a category. Omitting `monthly_limit` removes its budget. |
| `DELETE` | `/api/v1/categories/{category_id}` | user | 204 | Delete a category; its transactions move to *Uncategorized*. |
| `GET` | `/api/v1/budgets` | user | 200 | Spent, remaining and health (ok / warning / exceeded) for every budget. |
| `PUT` | `/api/v1/budgets/{category_id}` | user | 200 | Create or change a category's limit. Lowering it may raise alerts immediately. |
| `DELETE` | `/api/v1/budgets/{category_id}` | user | 204 | Remove a category's limit. |
| `GET` | `/api/v1/rules` | user | 200 | All keyword → category rules. |
| `POST` | `/api/v1/rules` | user | 201 | Add a keyword rule. |
| `PUT` | `/api/v1/rules/{rule_id}` | user | 200 | Change a rule. |
| `DELETE` | `/api/v1/rules/{rule_id}` | user | 204 | Delete a rule. |
| `GET` | `/api/v1/categorize/suggest` | user | 200 | Run the categorisation chain without saving anything. |
| `GET` | `/api/v1/recurring` | user | 200 | All recurring payments with their next due date. |
| `POST` | `/api/v1/recurring` | user | 201 | Create a recurring payment; occurrences already due are generated immediately. |
| `POST` | `/api/v1/recurring/run` | user | 200 | Run the (idempotent) generation job on demand; the scheduler also runs it. |
| `GET` | `/api/v1/recurring/{recurring_id}` | user | 200 | Fetch one recurring payment. |
| `DELETE` | `/api/v1/recurring/{recurring_id}` | user | 204 | Delete a recurring payment (generated transactions are kept). |
| `POST` | `/api/v1/recurring/{recurring_id}/pause` | user | 200 | Stop generating transactions. |
| `POST` | `/api/v1/recurring/{recurring_id}/resume` | user | 200 | Resume from today without back-filling the paused period. |
| `GET` | `/api/v1/reports` | user | 200 | Every registered report strategy; the UI builds its picker from this list. |
| `GET` | `/api/v1/reports/{report_type}` | user | 200 | Run the report strategy registered under `report_type` for `month`. |
| `GET` | `/api/v1/alerts` | user | 200 | Newest alerts first. |
| `GET` | `/api/v1/alerts/unread-count` | user | 200 | Number of unread alerts for the bell badge. |
| `POST` | `/api/v1/alerts/read-all` | user | 200 | Mark every alert as read. |
| `POST` | `/api/v1/alerts/{alert_id}/read` | user | 204 | Mark one alert as read. |
| `GET` | `/api/v1/alerts/stream` | token (query) | 200 | Push the signed-in user's new alerts as `alert` events; keep-alive every 15 s. |
| `GET` | `/api/v1/admin/overview` | admin | 200 | Users, activity, money tracked and alerts across the platform. |
| `GET` | `/api/v1/admin/users` | admin | 200 | Every account with activity counts, newest first. |
| `PATCH` | `/api/v1/admin/users/{user_id}` | admin | 200 | Activate or deactivate an account, or change its role. You can't change yourself. |
| `GET` | `/health` | — | 200 | Liveness probe |

**Transaction list parameters:** `page`, `page_size` (≤ 100), `type` (`income`/`expense`), `category_id`, `search`, `month`, `date_from`, `date_to`, `sort_by` (`occurred_on`, `amount`, `description`), `sort_direction` (`asc`/`desc`).

**Errors** always use one envelope, with field-level details for validation errors:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request contains invalid fields",
    "details": [{ "field": "amount", "message": "Input should be greater than 0" }]
  }
}
```

| Status | `code` | When |
|---|---|---|
| 400 | `domain_error` | A business rule failed in an unexpected way |
| 401 | `unauthenticated` | Missing, invalid or expired token; wrong e-mail or password; deactivated account |
| 403 | `forbidden` | A non-admin calling an admin route |
| 429 | `too_many_attempts` | Five failed sign-ins for one e-mail within five minutes |
| 404 | `not_found` | Unknown id or report type, **including another user's id** |
| 409 | `conflict` | Duplicate e-mail, category name or keyword; deleting or renaming the system category; an admin changing their own account |
| 422 | `validation_error` | Invalid input (negative amount, zero limit, bad month...) |
| 500 | `internal_error` | Unexpected server error (logged) |

**Server-Sent Events:** `GET /api/v1/alerts/stream?token=...` emits `event: alert` with an alert object as `data` (only the signed-in user's alerts), plus a keep-alive comment every 15 seconds.

---

## Project structure

```
budget-tracker/
├── backend/
│   ├── app/
│   │   ├── domain/          Pure Python: entities, value objects, patterns (no frameworks)
│   │   ├── application/     Use-case services, BudgetMonitor, ports (interfaces)
│   │   ├── infrastructure/  SQLAlchemy, notification channels, SSE hub, scheduler, seed
│   │   ├── api/             FastAPI routers, Pydantic schemas, mappers, error handlers
│   │   ├── config.py        Settings from environment variables
│   │   ├── container.py     Composition root: the only place concrete classes are wired
│   │   └── main.py          App factory
│   ├── alembic/             Migrations
│   ├── tests/               151 tests
│   └── pyproject.toml       Dependencies and tool configuration
├── frontend/
│   └── src/
│       ├── app/             Routes: / (landing), /login, /signup, /app/* (budget), /admin/* (console)
│       ├── components/      ui/ (shadcn primitives), layout/, shared/, and one folder per page
│       ├── hooks/           SSE alert stream, debounce, count-up animation
│       └── lib/             Typed API client, auth provider, session store, query hooks, Zod schemas
├── docs/                    DESIGN, UML, EXTENDING, VIVA_QA
└── docker-compose.yml
```

## Design patterns at a glance

| Concept | Where |
|---|---|
| Observer | `BudgetMonitor` (subject) → `AlertObserver` ← `NotificationDispatcher` |
| Strategy (alerts) | `AlertRule` ← `PercentageThresholdRule(80)`, `PercentageThresholdRule(100)` |
| Strategy (reports) | `ReportStrategy` ← `MonthlySummaryReport`, `CategoryWiseReport`, `SpendingTrendReport`, chosen via `ReportRegistry` |
| Chain of Responsibility | `KeywordRuleHandler` → `MerchantRuleHandler` → `UserDefinedRuleHandler` → `DefaultCategoryHandler` |
| Builder | `CategorizationChainBuilder` |
| Extensible channels | `NotificationChannel` ← `ConsoleChannel`, `EmailChannel`, `SmsChannel`, `InAppChannel` |
| Dependency Inversion | Repository, `Clock`, `PasswordHasher` and `TokenIssuer` Protocols in `application/ports.py`, wired only in `container.py` |
| Multi-tenancy | `UserScope`: the same services, wired per request to repositories bound to the signed-in user |

Full mapping, SOLID justification with file references, edge cases and trade-offs: [docs/DESIGN.md](docs/DESIGN.md).

## Going live

The app is deploy-ready; it needs a host for the API and one for the web app. Two straightforward options:

**One server with Docker** (any VPS):
```bash
JWT_SECRET="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')" docker compose up -d --build
```
Then put a reverse proxy with HTTPS (Caddy or Nginx) in front, and rebuild the frontend with `NEXT_PUBLIC_API_BASE_URL` set to your public API URL.

**Managed hosting:** deploy `backend/` to a Python host (Render, Railway, Fly.io) with the start command `uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT`, a PostgreSQL database (`DATABASE_URL`, plus `pip install ".[postgres]"`) and a strong `JWT_SECRET`. Deploy `frontend/` to Vercel or Netlify with `NEXT_PUBLIC_API_BASE_URL` pointing at the API, and add the frontend's URL to the backend's `CORS_ORIGINS`.

Production checklist: a strong `JWT_SECRET`; HTTPS everywhere; `SEED_DEMO_DATA=false` unless you want public demo logins; real SMTP settings if you want e-mail alerts.

> These steps were not run as part of building the project (no Docker or cloud account was available); the local setup above was verified end to end.

## Assumptions

- **Single currency** (INR by default; change `NEXT_PUBLIC_CURRENCY`).
- **Self-service sign-up**, no e-mail verification or password reset (documented as next steps in `docs/DESIGN.md`).
- **"User-defined rule" handler** learns from each user's own manual categorisations; explicit keyword rules (managed in the UI) are checked first.
- **Alerts don't re-arm within a month.** If spending drops below a threshold and rises again, no second alert is sent, honouring "once per category per month".
- **Resuming a paused recurring payment** does not back-fill dates missed while paused.
- **Income** is not auto-categorised; categories and budgets apply to expenses.
- **PostgreSQL** is supported through `DATABASE_URL` and the `postgres` extra; the project was tested on SQLite.
