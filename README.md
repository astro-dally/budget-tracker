# 💸 Budget Tracker

### Personal budgeting with smart spending alerts — warned *while* you spend, not at month-end.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/tests-151_passing-brightgreen)](#-testing--quality)
[![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen)](#-testing--quality)
[![mypy](https://img.shields.io/badge/mypy-strict-1F5082)](https://mypy-lang.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](#or-everything-with-docker)

[Features](#-features) · [Quick start](#-quick-start) · [Demo](#-demo-walkthrough) · [Architecture](#%EF%B8%8F-architecture) · [API](#-api) · [Docs](#-documentation)

---

## About

Most people notice overspending at the end of the month, when it's too late to do anything about it. **Budget Tracker** flips that around: you set a monthly limit per category, and the app warns you **the moment a transaction pushes a budget past 80%, and again at 100%** — once per category per month, pushed live to your browser.

It's a full multi-user web app: anyone can sign up, every account's data is isolated, expenses are categorised automatically, recurring payments record themselves on their due dates, reports show where the money went, and an admin console manages the platform.

<!--
  Screenshots: add images to docs/screenshots/ and uncomment this block.
  <p align="center">
    <img src="docs/screenshots/dashboard.png" alt="Dashboard" width="49%">
    <img src="docs/screenshots/budgets.png" alt="Budgets" width="49%">
  </p>
-->

## ✨ Features

| | |
|---|---|
| 🔔 **Real-time spending alerts** | Warnings at 80% and 100% of a budget, fired the instant the crossing transaction is saved and streamed over Server-Sent Events. Never duplicated, even across edits, deletes or restarts. |
| 📈 **Pace tracking** | The dashboard compares *budget used* against *month elapsed* on one bar and shows a **safe amount to spend per day** for the rest of the month. |
| 🤖 **Auto-categorisation** | A configurable rule chain: your keyword rules → known merchants → your past choices → *Uncategorized*. Longest keyword wins, and matches respect word boundaries (`ola` won't match `Coca-Cola`). |
| 🔁 **Recurring payments** | Rent, subscriptions and EMIs (daily / weekly / monthly) are recorded on their due dates by a background scheduler. Idempotent across restarts; pause and resume anytime. |
| 📊 **Reports & CSV export** | Monthly summary, category-wise breakdown and six-month spending trend, all discovered by the UI at runtime. |
| 👥 **Accounts & privacy** | Sign-up and sign-in, scrypt password hashing, signed JWT sessions, login throttling. Users can never see each other's data, even by guessing IDs. |
| 🛡️ **Admin console** | Platform stats (users, sign-ups, activity, money tracked, alerts sent) and user management: search, change roles, deactivate accounts (sessions end immediately). |
| ⌨️ **Polished UI** | Command palette (<kbd>⌘</kbd>/<kbd>Ctrl</kbd> + <kbd>K</kbd>), dark mode, responsive down to phone width, interactive landing page. |

## 🧰 Tech stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · APScheduler · Server-Sent Events · PyJWT |
| **Frontend** | Next.js 15 (App Router) · React 19 · TypeScript · Tailwind CSS 4 · shadcn/ui · Recharts · TanStack Query · React Hook Form + Zod |
| **Database** | SQLite by default (zero setup) · PostgreSQL supported via `DATABASE_URL` |
| **Quality** | pytest (151 tests, 97% coverage) · ruff · mypy `--strict` · ESLint (zero warnings) · strict TypeScript |
| **Ops** | Docker · Docker Compose |

---

## 🚀 Quick start

### Prerequisites

- **Python 3.12+** — `python3 --version`
- **Node.js 20+** and npm — `node --version`

No database server needed: the backend uses a local SQLite file.

```bash
git clone https://github.com/<your-username>/budget-tracker.git
cd budget-tracker
```

### 1. Backend (terminal 1)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:create_app --factory --reload
```

On first start the backend creates `budget_tracker.db`, runs migrations and seeds the [demo accounts](#-demo-accounts), each with six months of data.

- API: <http://localhost:8000>
- Interactive docs: <http://localhost:8000/docs> (click **Authorize** and paste a token from `/api/v1/auth/login`)

### 2. Frontend (terminal 2)

```bash
cd frontend
cp .env.example .env.local         # points the UI at http://localhost:8000
npm install
npm run dev
```

Open <http://localhost:3000> 🎉

### Or: everything with Docker

```bash
docker compose up --build
```

Frontend on <http://localhost:3000>, API on <http://localhost:8000>. Data persists in a Docker volume.

> [!TIP]
> Upgrading from the old single-user version? Delete `backend/budget_tracker.db*` first — the schema now includes accounts.

### 🔑 Demo accounts

The sign-in page shows these as one-click cards, so you never have to type them.

| Who | E-mail | Password | What you'll see |
|---|---|---|---|
| Maya Kapoor (**admin**) | `admin@budgettracker.dev` | `Admin@1234` | Admin console + her own budget |
| Aarav Sharma | `aarav@demo.dev` | `Demo@1234` | Young professional, several budgets running hot |
| Priya Nair | `priya@demo.dev` | `Demo@1234` | Student on a stipend, small tight budgets |
| Rohan Mehta | `rohan@demo.dev` | `Demo@1234` | Family with bigger bills |

Eight extra lightweight accounts (one deactivated) are also created so the admin user list looks realistic. You can also **create your own account** at `/signup`; it starts with common categories and keyword rules already set up.

> [!WARNING]
> Demo accounts use publicly known passwords, including an admin. Set `SEED_DEMO_DATA=false` if the app is reachable by anyone else.

---

## 🎬 Demo walkthrough

<details>
<summary><b>A 6-minute tour of everything the app does</b> (click to expand)</summary>

<br>

1. **Landing page** (`/`) — drag the two hero sliders: the budget bar races the "Day" marker, and crossing 80% or 100% pops the same alerts the real app sends.
2. **Sign in** — click **Try a demo account**, then **Aarav Sharma**. Visiting any `/app` page while signed out redirects here and returns you afterwards.
3. **Overview** — the headline panel compares *budget used* with *month gone*. If the bar runs ahead of the "Today" marker, the badge says *Spending faster than the month*. "Safe per day" is what you can spend daily and still finish on budget.
4. **Quick actions** — press <kbd>⌘K</kbd> / <kbd>Ctrl+K</kbd>, type `add`, press Enter.
5. **Auto-categorisation** — type a description and watch the live suggestion:
   - `Uber to airport` → Transport *(your keyword rule)*
   - `Uber Eats dinner` → Food & Dining *(longer keyword wins)*
   - `POS 4411 AMZN MKTP` → Shopping *(known merchant)*
   - `Sharma Dairy` → Food & Dining *(your past choice)*
   - `Coca-Cola crate` → Uncategorized *("ola" only matches whole words)*
6. **Real-time alerts** — add a **5000** expense described as `Myntra jacket`. Shopping jumps past 80% *and* 100%: **two** toasts appear and the bell goes up by two. Another Shopping expense adds nothing, because each threshold fires once per category per month.
7. **Privacy** — sign out and sign in as **Priya**. Different data, alerts and budgets; nothing of Aarav's is reachable.
8. **Admin console** — sign in as **Maya Kapoor**. See platform stats, then open **Users**: search, filter, change a role, or deactivate Priya and watch her sign-in get refused (and any open session end immediately). Your own row is locked.
9. **Budgets, Recurring, Reports** — edit limits and keyword rules, pause a recurring payment, switch report types and export CSV.
10. **Dark mode & mobile** — sun/moon icon top right; resize to phone width.

**Watch alerts arrive out-of-band.** Keep Aarav's dashboard open and post an expense from a terminal; the toasts appear without a refresh:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"aarav@demo.dev","password":"Demo@1234"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"expense","amount":"2500","description":"Electricity bill","occurred_on":"'"$(date +%F)"'"}'
```

</details>

---

## 🏗️ Architecture

The backend is a layered **hexagonal (ports & adapters)** design. Dependencies only point inwards, and that rule is **enforced by a test** (`tests/test_architecture.py`), not just documented.

```mermaid
flowchart LR
    UI["🖥️ Next.js UI<br/>TanStack Query"]
    subgraph Backend["FastAPI backend"]
        API["api/<br/>routers · schemas · errors"]
        APP["application/<br/>services · BudgetMonitor · ports"]
        DOM["domain/<br/>pure Python, no frameworks"]
        INF["infrastructure/<br/>SQLAlchemy · SSE hub · scheduler"]
    end
    DB[("SQLite /<br/>PostgreSQL")]
    CH["📣 Channels<br/>in-app · e-mail · SMS · console"]

    UI -- "REST + JWT" --> API
    INF -. "SSE alert stream" .-> UI
    API --> APP --> DOM
    INF -- "implements ports" --> APP
    INF --> DB
    INF --> CH
```

| Layer | May import | Must not import |
|---|---|---|
| `app/domain` | Standard library only | Anything else |
| `app/application` | Standard library, `domain` | FastAPI, SQLAlchemy, Pydantic, infrastructure |
| `app/infrastructure` | Inner layers + SQLAlchemy, APScheduler | `app.api` |
| `app/api` | Everything inward + FastAPI, Pydantic | — |

`container.py` is the single **composition root**: the only place concrete classes are wired together.

### Design patterns

| Pattern | Where it lives |
|---|---|
| **Observer** | `BudgetMonitor` (subject) → `AlertObserver` ← `NotificationDispatcher` |
| **Strategy** (alerts) | `AlertRule` ← `PercentageThresholdRule(80)`, `PercentageThresholdRule(100)` |
| **Strategy** (reports) | `ReportStrategy` ← `MonthlySummaryReport`, `CategoryWiseReport`, `SpendingTrendReport` via `ReportRegistry` |
| **Chain of Responsibility** | `KeywordRuleHandler` → `MerchantRuleHandler` → `UserDefinedRuleHandler` → `DefaultCategoryHandler` |
| **Builder** | `CategorizationChainBuilder` |
| **Extensible channels** | `NotificationChannel` ← `ConsoleChannel`, `EmailChannel`, `SmsChannel`, `InAppChannel` |
| **Dependency Inversion** | Repository, `Clock`, `PasswordHasher`, `TokenIssuer` protocols in `application/ports.py` |
| **Multi-tenancy** | `UserScope`: the same services, wired per request to repositories bound to the signed-in user |

Full mapping, SOLID justification with file references, edge cases and trade-offs: **[docs/DESIGN.md](docs/DESIGN.md)**.

### Project structure

```
budget-tracker/
├── backend/
│   ├── app/
│   │   ├── domain/          # Entities, value objects, pattern participants (pure Python)
│   │   ├── application/     # Use-case services, BudgetMonitor, ports (interfaces)
│   │   ├── infrastructure/  # SQLAlchemy, notification channels, SSE hub, scheduler, seed
│   │   ├── api/             # FastAPI routers, Pydantic schemas, mappers, error handlers
│   │   ├── config.py        # Settings from environment variables
│   │   ├── container.py     # Composition root
│   │   └── main.py          # App factory
│   ├── alembic/             # Database migrations
│   ├── tests/               # 151 tests
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── app/             # Routes: / · /login · /signup · /app/* · /admin/*
│       ├── components/      # ui/ (shadcn), layout/, shared/, one folder per page
│       ├── hooks/           # SSE alert stream, debounce, count-up
│       └── lib/             # Typed API client, auth, session, queries, Zod schemas
├── docs/                    # DESIGN · UML · EXTENDING · VIVA_QA
└── docker-compose.yml       # Run everything with one command
```

---

## ⚙️ Configuration

### Backend — `backend/.env` (all optional)

Copy `backend/.env.example` for a commented template.

| Variable | Default | Purpose |
|---|---|---|
| `JWT_SECRET` | dev placeholder | ⚠️ **Set a long random value in production.** Signs session tokens. |
| `DATABASE_URL` | `sqlite:///./budget_tracker.db` | Any SQLAlchemy URL. PostgreSQL: `pip install -e ".[postgres]"` + `postgresql+psycopg://user:pass@host:5432/db` |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Origins allowed to call the API |
| `SEED_DEMO_DATA` | `true` | Create demo accounts in an empty database and list them on the sign-in page |
| `AUTO_MIGRATE` | `true` | Run Alembic migrations on start-up |
| `SCHEDULER_ENABLED` | `true` | Background generation of recurring transactions |
| `RECURRING_JOB_INTERVAL_MINUTES` | `60` | How often the generator runs (it also runs at start-up) |
| `ALERT_THRESHOLDS` | `80,100` | One alert rule per percentage |
| `NOTIFICATION_CHANNELS` | `console,in_app,email,sms` | Enabled channels |
| `CATEGORIZATION_ORDER` | `keyword,merchant,user_defined,default` | Chain order; must end with `default` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS` | unset / `587` / … | Real e-mail. Without `SMTP_HOST`, e-mails are only logged |
| `ALERT_EMAIL_FROM` | placeholder | Sender address; alerts go to each user's own e-mail |
| `ALERT_SMS_TO` | unset | Phone number for the SMS stub (logged) |
| `TOKEN_LIFETIME_HOURS` | `24` | How long a sign-in lasts |
| `LOG_LEVEL` | `INFO` | Logging level |

### Frontend — `frontend/.env.local`

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Backend base URL, without `/api/v1` |
| `NEXT_PUBLIC_CURRENCY` | `INR` | ISO currency code for formatting |
| `NEXT_PUBLIC_LOCALE` | `en-IN` | Locale for numbers and dates |

> [!IMPORTANT]
> `NEXT_PUBLIC_*` values are **baked into the JavaScript at build time**. Changing them means rebuilding the frontend.

### Database migrations

Migrations run automatically on start-up. To manage them by hand:

```bash
cd backend
alembic upgrade head                          # apply
alembic revision --autogenerate -m "message"  # after editing app/infrastructure/persistence/models.py
```

To reset the demo, stop the backend and delete `backend/budget_tracker.db*`; demo accounts are recreated on the next start.

---

## 🔌 API

Base path **`/api/v1`** · Swagger UI at `/docs` · ReDoc at `/redoc`

- **Auth:** `POST /auth/login` or `/auth/register` returns `{"access_token": "...", "user": {...}}`. Send `Authorization: Bearer <token>` on every other request.
- **Amounts** are decimal **strings** (`"1250.00"`) so no precision is lost. **Months** are `YYYY-MM` and default to the current month.
- **Isolation:** every user route only sees the signed-in user's data. Another user's ID returns `404`, not `403`.
- **SSE:** `GET /alerts/stream?token=...` emits `event: alert` messages plus a keep-alive every 15 s. The token goes in the query string because `EventSource` can't send headers.

<details>
<summary><b>All endpoints</b> (click to expand)</summary>

<br>

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | — | Create an account (with starter categories and rules) and sign in |
| `POST` | `/auth/login` | — | Exchange e-mail and password for a token; repeated failures are throttled |
| `GET` | `/auth/me` | user | The signed-in user |
| `GET` | `/auth/demo-accounts` | — | Demo logins (empty when demo data is disabled) |
| `GET` | `/dashboard` | user | Summary cards, charts, budget progress, recent and upcoming payments |
| `GET` | `/transactions` | user | Search, filter, sort and paginate |
| `POST` | `/transactions` | user | Record a transaction; expenses without a category are auto-categorised |
| `GET` | `/transactions/{id}` | user | Fetch one transaction |
| `PUT` | `/transactions/{id}` | user | Replace a transaction; the affected budget is re-checked |
| `DELETE` | `/transactions/{id}` | user | Delete a transaction |
| `GET` | `/categories` | user | All categories with their monthly limits |
| `POST` | `/categories` | user | Create a category, optionally with a budget |
| `GET` | `/categories/{id}` | user | Fetch one category |
| `PUT` | `/categories/{id}` | user | Update a category (omitting `monthly_limit` removes its budget) |
| `DELETE` | `/categories/{id}` | user | Delete; its transactions move to *Uncategorized* |
| `GET` | `/budgets` | user | Spent, remaining and health (ok / warning / exceeded) per budget |
| `PUT` | `/budgets/{category_id}` | user | Create or change a limit; lowering it may raise alerts immediately |
| `DELETE` | `/budgets/{category_id}` | user | Remove a limit |
| `GET` | `/rules` | user | All keyword → category rules |
| `POST` | `/rules` | user | Add a keyword rule |
| `PUT` | `/rules/{id}` | user | Change a rule |
| `DELETE` | `/rules/{id}` | user | Delete a rule |
| `GET` | `/categorize/suggest` | user | Run the categorisation chain without saving |
| `GET` | `/recurring` | user | All recurring payments with next due date |
| `POST` | `/recurring` | user | Create one; occurrences already due are generated immediately |
| `POST` | `/recurring/run` | user | Run the idempotent generation job on demand |
| `GET` | `/recurring/{id}` | user | Fetch one recurring payment |
| `DELETE` | `/recurring/{id}` | user | Delete (generated transactions are kept) |
| `POST` | `/recurring/{id}/pause` | user | Stop generating |
| `POST` | `/recurring/{id}/resume` | user | Resume from today without back-filling |
| `GET` | `/reports` | user | Every registered report strategy |
| `GET` | `/reports/{report_type}` | user | Run a report for `month` |
| `GET` | `/alerts` | user | Newest alerts first |
| `GET` | `/alerts/unread-count` | user | Unread count for the bell badge |
| `POST` | `/alerts/read-all` | user | Mark all as read |
| `POST` | `/alerts/{id}/read` | user | Mark one as read |
| `GET` | `/alerts/stream` | token (query) | Live alert stream (SSE) |
| `GET` | `/admin/overview` | admin | Platform-wide users, activity, money tracked and alerts |
| `GET` | `/admin/users` | admin | Every account with activity counts |
| `PATCH` | `/admin/users/{id}` | admin | Activate/deactivate or change role (not yourself) |
| `GET` | `/health` *(no prefix)* | — | Liveness probe |

**Transaction list parameters:** `page`, `page_size` (≤ 100), `type` (`income`/`expense`), `category_id`, `search`, `month`, `date_from`, `date_to`, `sort_by` (`occurred_on`, `amount`, `description`), `sort_direction` (`asc`/`desc`).

</details>

**Errors** always share one envelope, with field-level details for validation errors:

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
| 400 | `domain_error` | A business rule failed unexpectedly |
| 401 | `unauthenticated` | Missing/invalid/expired token, wrong credentials, deactivated account |
| 403 | `forbidden` | Non-admin calling an admin route |
| 404 | `not_found` | Unknown ID or report type, **including another user's ID** |
| 409 | `conflict` | Duplicate e-mail/category/keyword, protected system category, admin editing themselves |
| 422 | `validation_error` | Invalid input (negative amount, zero limit, bad month…) |
| 429 | `too_many_attempts` | Five failed sign-ins for one e-mail within five minutes |
| 500 | `internal_error` | Unexpected server error (logged) |

---

## 🧪 Testing & quality

```bash
# Backend
cd backend && source .venv/bin/activate
pytest                                  # 151 tests
pytest --cov=app                        # 97% coverage
ruff check . && ruff format --check .   # lint + format
mypy                                    # strict, whole backend

# Frontend
cd frontend
npm run typecheck
npm run lint                            # zero warnings allowed
npm run build
```

<details>
<summary><b>What the tests cover</b></summary>

<br>

| File | Focus |
|---|---|
| `test_categorization_chain.py` | Chain order, fallback, longest match, word boundaries, configurable order, builder validation |
| `test_alert_rules.py` | Exact 80%/100% boundaries, keys, levels, plugging in a new rule |
| `test_budget_monitor.py` | Fires once per month; both thresholds in one transaction; rollover; edits, moves, deletes, lowered limits; failing channels isolated |
| `test_recurrence.py` | Daily/weekly/monthly schedules, month-end clamping, idempotency across re-runs and restarts; pause/resume |
| `test_reports.py` | All three report strategies, registry, plugging in a new report |
| `test_services.py` | Every application service against in-memory repositories |
| `test_persistence.py` | SQLAlchemy adapters, exact money sums, unique constraints, owner scoping, migrations match models |
| `test_auth.py` | Sign-up, password policy, sign-in, throttling, deactivation, expired/tampered/forged tokens, scrypt |
| `test_admin.py` | Admin statistics, user listing, role/status changes, self-change blocked, non-admins refused |
| `test_api.py` | End-to-end HTTP tests on a real SQLite file: auth, **cross-user isolation**, admin console, no duplicates after restart |
| `test_architecture.py` | Domain imports only the standard library; application imports no frameworks |
| `test_extending_examples.py` | The worked examples in `docs/EXTENDING.md` |

</details>

---

## 📌 Assumptions & limitations

- **Single currency** — INR by default; change `NEXT_PUBLIC_CURRENCY`.
- **Self-service sign-up** with no e-mail verification or password reset yet.
- **Alerts don't re-arm within a month** — if spending drops below a threshold and rises again, no second alert is sent, honouring "once per category per month".
- **Resuming a paused recurring payment** doesn't back-fill dates missed while paused.
- **Income isn't auto-categorised** — categories and budgets apply to expenses.
- **One backend process** — the login throttle and SSE hub live in memory, so run a single worker.
- **PostgreSQL** is supported through `DATABASE_URL`, but the test suite runs on SQLite.

## 🗺️ Roadmap

- [ ] E-mail verification and password reset
- [ ] httpOnly cookie sessions instead of `localStorage`
- [ ] Redis-backed SSE hub and login throttle for horizontal scaling
- [ ] Multi-currency support

## 📚 Documentation

| Document | What's inside |
|---|---|
| [DESIGN.md](docs/DESIGN.md) | Architecture, pattern mapping, SOLID, data model, edge cases, trade-offs |
| [UML.md](docs/UML.md) | Component, class and sequence diagrams for every pattern and flow |
| [EXTENDING.md](docs/EXTENDING.md) | Worked examples: a new alert rule, report, notification channel and categorisation handler |

## 🤝 Contributing

Issues and pull requests are welcome. Before opening a PR, please make sure all checks pass:

```bash
cd backend  && pytest && ruff check . && ruff format --check . && mypy
cd frontend && npm run typecheck && npm run lint && npm run build
```

## 📄 License

No license has been chosen yet. Until a `LICENSE` file is added, all rights are reserved by the author.

---

**If this project helped you, consider giving it a ⭐**
