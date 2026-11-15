# Design

This document explains how the Personal Budget Tracker is built and, more importantly, *why*. Every claim points to a file you can open.

## 1. Problem and approach

People notice overspending at month-end, when it is too late. The tracker attacks this from three angles:

1. **Warnings during the month.** Alerts fire at 80% and 100% of a category limit, the moment the transaction that crosses the threshold is saved. The dashboard's hero compares *budget used* against *month elapsed* on one bar, so "spending faster than the month" is visible at a glance.
2. **Less manual work.** Expenses are categorised automatically by a configurable chain of rules, and recurring payments (rent, subscriptions, EMIs) are recorded on their due dates without user action.
3. **Clear reporting.** Monthly summary, category-wise and six-month trend reports, all discovered by the UI at runtime.

It is a multi-user web app: anyone can create an account, every account's data is isolated, and administrators get a console for platform statistics and user management (section 11).

## 2. Architecture

The backend is a layered, hexagonal ("ports and adapters") design. Dependencies point inwards only.

```
┌──────────────────────────────────────────────────────────────────────┐
│ api/            FastAPI routers, Pydantic schemas, mappers, errors    │  HTTP adapter
├──────────────────────────────────────────────────────────────────────┤
│ infrastructure/ SQLAlchemy repositories, channels, SSE hub,          │  Driven adapters
│                 scheduler, system clock, seed data                   │
├──────────────────────────────────────────────────────────────────────┤
│ application/    Services (use cases), BudgetMonitor, ports           │  Application core
├──────────────────────────────────────────────────────────────────────┤
│ domain/         Entities, value objects, pattern participants         │  Pure Python
└──────────────────────────────────────────────────────────────────────┘
          container.py — the composition root — wires all of it
```

| Layer | May import | Must not import |
|---|---|---|
| `app/domain` | Python standard library, `app.domain` | Anything else |
| `app/application` | Standard library, `app.domain`, `app.application` | FastAPI, SQLAlchemy, Pydantic, infrastructure, api |
| `app/infrastructure` | Everything inward plus SQLAlchemy, APScheduler | `app.api` |
| `app/api` | Everything inward plus FastAPI, Pydantic | — |

These rules are **enforced by tests**, not just stated: `tests/test_architecture.py` parses every module's imports with `ast` and fails if the domain imports anything outside the standard library, or if the application layer imports a framework.

### Package structure

```
backend/
├── app/
│   ├── domain/
│   │   ├── money.py              Money and Period value objects
│   │   ├── enums.py              TransactionType, Frequency, AlertLevel, BudgetHealth, CategorySource
│   │   ├── errors.py             DomainError hierarchy
│   │   ├── transaction.py        Transaction entity
│   │   ├── category.py           Category entity
│   │   ├── budget.py             Budget entity, BudgetUsage snapshot
│   │   ├── category_rule.py      CategoryRule entity (keyword → category)
│   │   ├── recurrence.py         RecurrenceSchedule value object, RecurringPayment entity
│   │   ├── user.py               User entity, password policy
│   │   ├── alert.py              Alert entity
│   │   ├── alert_rules.py        Strategy: AlertRule, PercentageThresholdRule
│   │   ├── alert_observer.py     Observer: AlertObserver interface
│   │   ├── categorization.py     Chain of Responsibility + Builder
│   │   ├── reports.py            Strategy: ReportStrategy, three reports, ReportRegistry
│   │   └── analytics.py          Pure aggregation helpers shared by reports and dashboard
│   ├── application/
│   │   ├── ports.py              Repository Protocols, Clock Protocol, NotificationChannel ABC
│   │   ├── queries.py            TransactionQuery, Page
│   │   ├── budget_monitor.py     Observer subject / AlertRule context
│   │   ├── observers.py          NotificationDispatcher (concrete observer)
│   │   ├── transaction_service.py, category_service.py, budget_service.py,
│   │   ├── rule_service.py, recurring_service.py, report_service.py,
│   │   ├── alert_service.py, categorization_service.py, dashboard_service.py,
│   │   ├── auth_service.py       Sign-up, sign-in, sessions, LoginThrottle
│   │   ├── admin_service.py      Platform overview, user management
│   │   └── onboarding.py         StarterKit for new accounts
│   ├── infrastructure/
│   │   ├── persistence/          database.py, models.py, migrations.py, platform_stats.py,
│   │   │                         repositories/* (owner-scoped, plus users)
│   │   ├── security.py           ScryptPasswordHasher, JwtTokenIssuer
│   │   ├── demo_accounts.py      Demo personas
│   │   ├── notifications/        console.py, email.py, sms.py, in_app.py
│   │   ├── realtime.py           Thread-safe SSE broadcaster
│   │   ├── scheduler.py          APScheduler job for recurring payments
│   │   ├── clock.py              SystemClock
│   │   ├── merchant_directory.py Known merchants and their statement aliases
│   │   └── seed.py               Demo accounts and their data (created through the services)
│   ├── api/                      routers/*, schemas.py, mappers.py, deps.py, errors.py
│   ├── config.py                 Pydantic settings (environment variables)
│   ├── container.py              Composition root: Container + per-user UserScope
│   └── main.py                   App factory and lifespan
├── alembic/                      Migrations
└── tests/                        151 tests: patterns, services, auth, admin, adapters, API, architecture
```

## 3. Classes and responsibilities

| Class | File | Responsibility (one each) |
|---|---|---|
| `Money` | `domain/money.py` | Exact decimal amount, rounded to cents, rejects floats |
| `Period` | `domain/money.py` | A calendar month: boundaries, next/previous |
| `Transaction` | `domain/transaction.py` | One money movement and its invariants |
| `Category` | `domain/category.py` | Name and appearance of a spending bucket |
| `Budget` | `domain/budget.py` | A positive monthly limit for one category |
| `BudgetUsage` | `domain/budget.py` | Immutable snapshot: spent vs limit, health |
| `CategoryRule` | `domain/category_rule.py` | Keyword → category, whole-word matching |
| `RecurrenceSchedule` | `domain/recurrence.py` | Computes occurrence dates |
| `RecurringPayment` | `domain/recurrence.py` | A repeating payment and its generation mark |
| `Alert` | `domain/alert.py` | Record that a threshold was crossed |
| `PercentageThresholdRule` | `domain/alert_rules.py` | Decides whether usage reached N% |
| `KeywordRuleHandler` etc. | `domain/categorization.py` | One categorisation strategy each |
| `CategorizationChainBuilder` | `domain/categorization.py` | Links and validates the chain |
| `MonthlySummaryReport` etc. | `domain/reports.py` | One report each |
| `ReportRegistry` | `domain/reports.py` | Key → report strategy lookup |
| `BudgetMonitor` | `application/budget_monitor.py` | Re-evaluates a budget and publishes alerts |
| `NotificationDispatcher` | `application/observers.py` | Fans an alert out to channels, isolating failures |
| `TransactionService` | `application/transaction_service.py` | Record/edit/delete transactions; orchestrates categoriser and monitor |
| `RecurringService` | `application/recurring_service.py` | Manage recurring payments; generate due occurrences idempotently |
| `DashboardService` | `application/dashboard_service.py` | Read model composing the dashboard |
| `SqlAlchemy*Repository` | `infrastructure/persistence/repositories/` | Persist one aggregate each |
| `ConsoleChannel`, `EmailChannel`, `SmsChannel`, `InAppChannel` | `infrastructure/notifications/` | Deliver an alert one way each |
| `AlertBroadcaster` | `infrastructure/realtime.py` | Thread-safe fan-out to SSE clients |
| `RecurringTransactionScheduler` | `infrastructure/scheduler.py` | Run the generation job on an interval |
| `User` | `domain/user.py` | Identity and role of an account; never holds a plain password |
| `AuthService` | `application/auth_service.py` | Sign-up, sign-in and session validation |
| `LoginThrottle` | `application/auth_service.py` | Slow down password guessing per e-mail |
| `AdminService` | `application/admin_service.py` | Platform statistics and user management, admin only |
| `StarterKit` | `application/onboarding.py` | Default categories and keyword rules for new accounts |
| `UserScope` | `container.py` | One user's wired service graph |
| `ScryptPasswordHasher` | `infrastructure/security.py` | Salted, memory-hard password hashing |
| `JwtTokenIssuer` | `infrastructure/security.py` | Sign and verify session tokens |
| `SqlAlchemyPlatformStats` | `infrastructure/persistence/platform_stats.py` | Cross-user aggregates for admins (the only cross-owner reader) |

No class is a "god class": the biggest service, `TransactionService`, only coordinates collaborators and owns no business rule itself.

## 4. Interface map

| Abstraction | Kind | Defined in | Implementations |
|---|---|---|---|
| `TransactionRepository` | `Protocol` | `application/ports.py` | `SqlAlchemyTransactionRepository`, `tests/fakes.InMemoryTransactionRepository` |
| `CategoryRepository` | `Protocol` | `application/ports.py` | SQLAlchemy + in-memory |
| `BudgetRepository` | `Protocol` | `application/ports.py` | SQLAlchemy + in-memory |
| `CategoryRuleRepository` | `Protocol` | `application/ports.py` | SQLAlchemy + in-memory |
| `RecurringPaymentRepository` | `Protocol` | `application/ports.py` | SQLAlchemy + in-memory |
| `AlertRepository` | `Protocol` | `application/ports.py` | SQLAlchemy + in-memory |
| `Clock` | `Protocol` | `application/ports.py` | `SystemClock`, `tests/fakes.FixedClock` |
| `NotificationChannel` | `ABC` | `application/ports.py` | Console, Email, SMS, InApp (+ Webhook example) |
| `AlertObserver` | `ABC` | `domain/alert_observer.py` | `NotificationDispatcher`, test `RecordingObserver` |
| `AlertRule` | `ABC` | `domain/alert_rules.py` | `PercentageThresholdRule` (+ examples) |
| `ReportStrategy` | `ABC` | `domain/reports.py` | Three reports (+ example) |
| `ReportDataSource` | `Protocol` | `domain/reports.py` | `RepositoryReportDataSource` |
| `CategorizationHandler` | `ABC` | `domain/categorization.py` | Keyword, Merchant, UserDefined, Default |
| `KeywordRuleSource`, `CategoryNameLookup`, `CategorizationHistory` | `Protocol` | `domain/categorization.py` | Satisfied structurally by the repositories |
| `AlertPublisher` | `Protocol` | `infrastructure/notifications/in_app.py` | `AlertBroadcaster` (per-user topics) |
| `UserRepository` | `Protocol` | `application/ports.py` | `SqlAlchemyUserRepository`, `tests/fakes.InMemoryUserRepository` |
| `PasswordHasher` | `Protocol` | `application/ports.py` | `ScryptPasswordHasher`, `tests/fakes.FastHasher` |
| `TokenIssuer` | `Protocol` | `application/ports.py` | `JwtTokenIssuer` |
| `PlatformStatsReader` | `Protocol` | `application/ports.py` | `SqlAlchemyPlatformStats`, `tests/fakes.InMemoryPlatformStats` |

**Why both `Protocol` and `ABC`?** Repositories and the clock are *capabilities* that adapters provide: structural typing (`Protocol`) means a SQLAlchemy class or a dictionary-backed fake satisfies them without inheriting anything, keeping infrastructure decoupled. Pattern participants (rules, handlers, channels, observers, reports) are *roles in a design* that classes explicitly sign up for: `ABC` makes that intent visible in the class declaration, shares behaviour where useful (the handler's template method `handle`), and fails fast at instantiation if a method is missing.

## 5. Pattern-to-class mapping

| Pattern | Participant | Class | File |
|---|---|---|---|
| **Observer** | Subject | `BudgetMonitor` | `application/budget_monitor.py` |
| | Observer | `AlertObserver` | `domain/alert_observer.py` |
| | Concrete observer | `NotificationDispatcher` | `application/observers.py` |
| **Strategy (alerts)** | Strategy | `AlertRule` | `domain/alert_rules.py` |
| | Concrete strategies | `PercentageThresholdRule(80)`, `PercentageThresholdRule(100)` | `domain/alert_rules.py` |
| | Context | `BudgetMonitor` | `application/budget_monitor.py` |
| **Strategy (reports)** | Strategy | `ReportStrategy` | `domain/reports.py` |
| | Concrete strategies | `MonthlySummaryReport`, `CategoryWiseReport`, `SpendingTrendReport` | `domain/reports.py` |
| | Registry / factory | `ReportRegistry`, `build_report_registry()` | `domain/reports.py`, `container.py` |
| | Context | `ReportService` | `application/report_service.py` |
| **Chain of Responsibility** | Handler | `CategorizationHandler` | `domain/categorization.py` |
| | Concrete handlers | `KeywordRuleHandler` → `MerchantRuleHandler` → `UserDefinedRuleHandler` → `DefaultCategoryHandler` | `domain/categorization.py` |
| | Client | `CategorizationService` | `application/categorization_service.py` |
| **Builder** | Builder | `CategorizationChainBuilder` | `domain/categorization.py` |
| **Template Method** | Template | `CategorizationHandler.handle` / `_try_handle` | `domain/categorization.py` |
| **Factory Method** | Factories | `Transaction.create`, `Category.create`, `Alert.create`, ... | `domain/*.py` |
| **Adapter** | Adapters | `SqlAlchemy*Repository`, `RepositoryReportDataSource` | `infrastructure/...`, `application/report_service.py` |
| **Value Object** | — | `Money`, `Period`, `RecurrenceSchedule`, `BudgetUsage` | `domain/` |
| **Composition Root** | — | `build_container`, `build_user_scope` | `container.py` |
| **Facade** (per request) | — | `UserScope`: one object exposing a user's services | `container.py` |

### Observer: how an alert travels

1. `TransactionService.record` saves an expense, then calls `BudgetMonitor.check(category_id, period)`.
2. The monitor recomputes spending from the repository and asks every `AlertRule` to evaluate the `BudgetUsage`.
3. For each decision it creates an `Alert` and calls `AlertRepository.add_if_absent`. The database's unique constraint on `(category_id, period, rule_key)` makes this atomic: only the first writer succeeds.
4. Only newly stored alerts are passed to `notify`, which calls `on_alert` on every attached observer.
5. `NotificationDispatcher` sends the alert to each configured channel. `InAppChannel` hands it to the `AlertBroadcaster`, which pushes it onto every connected client's asyncio queue; the `/alerts/stream` endpoint writes it as a Server-Sent Event; the browser shows a toast and refreshes the bell badge.

### Chain of Responsibility: why this order

| # | Handler | Data source | Rationale |
|---|---|---|---|
| 1 | `KeywordRuleHandler` | Keyword rules the user manages in the UI | Explicit instructions win. Longest keyword wins, so "uber eats" beats "uber". |
| 2 | `MerchantRuleHandler` | Built-in merchant directory (`merchant_directory.py`) | Recognises bank-statement aliases such as "AMZN MKTP". Longest alias wins. |
| 3 | `UserDefinedRuleHandler` | The user's own past manual categorisations | Rules the user defined implicitly: filing "Sharma Dairy" under Food once teaches the system. Only `MANUAL` choices count, so the system never learns from its own guesses. |
| 4 | `DefaultCategoryHandler` | The system "Uncategorized" category | Terminal handler. The builder refuses to build a chain without it. |

The order is configuration (`CATEGORIZATION_ORDER`), not code. `tests/test_categorization_chain.py::test_order_is_configurable` reorders the chain so personal history beats keywords, with no class changes.

## 6. SOLID, principle by principle

### S: Single Responsibility
- Separate entities for each concept: `Transaction` (`domain/transaction.py`), `Category` (`domain/category.py`), `Budget` (`domain/budget.py`), `Alert` (`domain/alert.py`), `Report` (`domain/reports.py`), `RecurringPayment` + `RecurrenceSchedule` (`domain/recurrence.py`).
- `Category` deliberately does **not** hold its limit; `Budget` does. Renaming a category and changing money rules are different reasons to change.
- Detection (`BudgetMonitor`), persistence (`AlertRepository`), and delivery (`NotificationDispatcher` and channels) of alerts are three classes.
- `TransactionService` orchestrates; it delegates categorisation to the chain, alerting to the monitor, and validation to the entity.

### O: Open/Closed
- New alert rule: subclass `AlertRule`, add it in `build_alert_rules` (`container.py`). `BudgetMonitor` is untouched.
- New report: subclass `ReportStrategy`, register it in `build_report_registry` (`container.py`). The API lists it at `/reports` and the UI renders it generically from its `columns`, `metrics` and `ChartSpec`; **no frontend change either**.
- New channel: subclass `NotificationChannel`, add it to the factory map in `build_channels` (`container.py`) and to `NOTIFICATION_CHANNELS`.
- New categorisation handler: subclass `CategorizationHandler`, add it to `build_categorization_chain`.
- Proof: `tests/test_extending_examples.py` adds `ProjectedOverspendRule`, `LargestExpensesReport` and `WebhookChannel` without editing a single existing class. See `docs/EXTENDING.md`.

The composition root is the one place that *does* change when you add something; that is its job. Business classes stay closed.

### L: Liskov Substitution
- Every `AlertRule` returns a decision or `None` and never mutates the usage; `tests/test_alert_rules.py::test_new_rule_is_substitutable` mixes a new rule with the built-in one.
- Every `CategorizationHandler` returns a result or `None` for a miss and never raises for one; `tests/test_categorization_chain.py::test_every_handler_is_substitutable` runs each handler alone.
- Every repository fake honours the same Protocol as its SQL counterpart, so all service tests run against fakes and the API tests run the same services against SQLite.

### I: Interface Segregation
- Categorisation handlers depend on one-method ports (`KeywordRuleSource`, `CategoryNameLookup`, `CategorizationHistory` in `domain/categorization.py`), not on whole repositories.
- Reports depend on the read-only `ReportDataSource` (`domain/reports.py`): three query methods, no writes.
- `InAppChannel` depends on a one-method `AlertPublisher` (`infrastructure/notifications/in_app.py`), not on the broadcaster class.
- Repository ports are split per aggregate (six small Protocols) rather than one generic data-access interface.

### D: Dependency Inversion
- Services receive abstractions through their constructors: e.g. `BudgetMonitor(rules, categories, budgets, transactions, alerts, clock)`.
- Ports are declared by the core (`application/ports.py`), implemented by infrastructure. The arrow points inwards.
- `Clock` is injected everywhere time matters, so tests freeze or advance time (`tests/fakes.FixedClock`) to test month rollover and recurrence.
- Multi-user support was added **without changing a single service**: the same `TransactionService`, `BudgetMonitor` and friends are simply wired to repositories bound to the signed-in user (`build_user_scope`). That is Dependency Inversion paying off: the services depend on repository abstractions, so changing what sits behind them (now owner-scoped) needs no edits above.
- Password hashing (`PasswordHasher`) and token signing (`TokenIssuer`) are ports too, so `AuthService` has no cryptography imports and is tested with a fast fake hasher.
- Concrete classes are chosen **only** in `app/container.py`. No module-level singletons hold dependencies; the app uses a factory (`create_app`) and builds the container inside the lifespan.

## 7. Data model

| Table | Key columns | Notes |
|---|---|---|
| `users` | `id`, `email` (unique, normalised), `password_hash`, `role`, `is_active`, `last_login_at` | scrypt hash with salt and parameters |
| `categories` | `id`, `owner_id`, `name`, `name_key` | **Unique `(owner_id, name_key)`**: names unique per user |
| `budgets` | `category_id` (PK, FK cascade), `limit_minor` | One budget per category |
| `category_rules` | `id`, `owner_id`, `keyword`, `category_id` (FK cascade) | **Unique `(owner_id, keyword)`** |
| `recurring_payments` | `id`, `frequency`, `start_date`, `end_date`, `is_active`, `last_generated_on` | Generation mark for efficiency |
| `transactions` | `id`, `type`, `amount_minor`, `description_key`, `occurred_on`, `category_id`, `category_source`, `recurring_id` | **Unique `(recurring_id, occurred_on)`** |
| `alerts` | `id`, `category_id`, `period`, `rule_key`, `level`, `is_read` | **Unique `(category_id, period, rule_key)`** |

Every user-data table (`categories`, `budgets`, `category_rules`, `recurring_payments`, `transactions`, `alerts`) has an indexed `owner_id` foreign key to `users` with `ON DELETE CASCADE`. The ORM uses a naming convention so future migrations get deterministic constraint names.

Money is stored as integer minor units (paise/cents). SQLite has no decimal type, so this keeps `SUM()` exact on every database. Conversion happens only in the repository adapters (`Money.to_minor_units` / `from_minor_units`).

## 8. Edge cases and how they are handled

| Edge case | Handling | Test |
|---|---|---|
| One transaction crosses 80% **and** 100% | Monitor evaluates all rules in ascending order; both alerts fire, warning first | `test_budget_monitor.py::test_one_transaction_crossing_both_thresholds_fires_both_in_order` |
| Duplicate alerts | Unique DB constraint + `add_if_absent`; re-checks are harmless | `test_alert_is_not_repeated_within_the_month`, `test_api.py::test_expense_crossing_thresholds_creates_alerts_once` |
| Editing raises an amount or moves a category | Usage is always recomputed from transactions, never tracked incrementally; the new budget is re-checked | `test_editing_an_amount_upwards_can_cross_a_threshold`, `test_moving_an_expense_to_another_category_checks_that_budget` |
| Delete then re-add | Usage drops immediately; the alert does not re-fire that month | `test_delete_and_recross_does_not_spam` |
| Lowering a limit below current spend | `BudgetService.set_limit` re-checks immediately | `test_lowering_a_limit_raises_alerts_immediately` |
| Month rollover | The period is part of the alert key, so a new month starts fresh with no reset job | `test_month_rollover_resets_alert_state` |
| Zero or negative limit | Rejected by `Budget` (domain) and `gt=0` (API schema) → 422 | `test_value_objects.py::test_budget_rejects_zero_or_negative_limits`, `test_api.py::test_validation_errors_use_the_envelope` |
| Duplicate recurring generation after restart | Generation asks for dates after `last_generated_on`; the unique `(recurring_id, occurred_on)` constraint rejects any repeat; the repository turns that into `DuplicateRecurrenceError`, which the service treats as "already done" | `test_recurrence.py::test_generation_is_idempotent_across_runs_and_restarts`, `test_lost_generation_mark_does_not_duplicate`, `test_api.py::test_seed_runs_once_across_restarts` |
| Pause during generation | The job advances only `last_generated_on` via `mark_generated`, so it never overwrites a concurrent pause | `RecurringPaymentRepository.mark_generated` |
| Monthly on the 31st | Clamped to the month end but re-anchored: 31 Jan → 28 Feb → 31 Mar | `test_monthly_clamps_and_re_anchors` |
| A failing channel (SMTP down) | Dispatcher logs and continues with the other channels | `test_failing_channel_does_not_block_others` |
| Floating-point money | `Money.of(0.1)` raises; all amounts are `Decimal`; JSON carries them as strings | `test_value_objects.py::test_rejects_float` |
| "ola" matching "Coca-Cola" | Whole-word matching | `test_keywords_respect_word_boundaries` |

## 9. Trade-offs and decisions

- **Alerts do not re-arm within a month.** If spending drops below 80% after a delete and then rises again, no second alert is sent. The requirement says "once per category per month"; re-arming would reintroduce the spam it forbids. The progress bars still reflect the live state.
- **Resuming a paused payment does not back-fill.** Missed dates while paused are skipped, because pausing usually means "I stopped paying".
- **One session per repository call.** Repositories open a short-lived session per method instead of a per-request unit of work. This keeps services free of transaction plumbing and suits SQLite; the cost is that a multi-step use case is not one database transaction. Correctness-critical steps (alert de-duplication, recurrence idempotency) rely on unique constraints instead, which are safe without a surrounding transaction.
- **Single currency.** Amounts carry no currency code; the UI formats with `NEXT_PUBLIC_CURRENCY` (INR by default). Multi-currency would add a currency to `Money` and conversion rates.
- **Session tokens in `localStorage`.** Simple and works across origins (frontend on :3000, API on :8000). The trade-off is exposure to XSS; React escapes output and there is no raw-HTML rendering, which keeps that risk low. Hardening path: an httpOnly, `SameSite` cookie on a shared domain.
- **SSE token in the query string.** Browsers' `EventSource` cannot send headers. The token is short-lived and only accepted on that one endpoint; a cookie-based session would remove the need.
- **Stateless JWT, checked against the database.** Each request still loads the user, so deactivating an account ends its sessions immediately, at the cost of one indexed primary-key look-up per request.
- **In-process login throttle and SSE hub.** Both work for one server process. Scaling to several processes would back both with Redis behind the same interfaces.
- **No e-mail verification or password reset yet.** Both slot into `AuthService` with a new `MailSender` port; the e-mail channel's SMTP settings already exist.

## 10. Frontend design

- **Stack:** Next.js 15 App Router, TypeScript (strict, `noUncheckedIndexedAccess`, no `any`), Tailwind CSS 4, shadcn/ui primitives on Radix, Recharts 3, TanStack Query 5, React Hook Form + Zod, next-themes, sonner.
- **Routes:** `/` public landing page, `/login` and `/signup`, `/app/*` for the signed-in budget, `/admin/*` for administrators. `AuthGuard` (`src/components/auth-guard.tsx`) protects the last two; the backend enforces the same rules independently, so the guard is a UX convenience, not the security boundary.
- **Auth state** lives in `AuthProvider` (`src/lib/auth.tsx`): the token is stored by `src/lib/session.ts`, the profile comes from `/auth/me`, and signing in or out clears the query cache so one user's data can never flash up for another. Any 401 from the API signs the user out with a message.
- **One API client** (`src/lib/api.ts`) attaches the bearer token and handles the error envelope and network failures. **One hooks module** (`src/lib/queries.ts`) owns cache keys, invalidation and optimistic updates (delete transaction, delete category, pause/resume recurring, mark alerts read).
- **Generic report rendering** (`src/components/reports/report-view.tsx`, `report-chart.tsx`) mirrors the backend Strategy: the UI draws whatever `columns`, `metrics` and `ChartSpec` a strategy returns.
- **Visual system:** mineral canvas, white surfaces and a deep "ledger green" for hero moments, with lime, gold and coral for budget health so colour always carries meaning. Bricolage Grotesque for headlines and big figures, IBM Plex Sans with tabular figures for everything else. The signature element is the pace bar (budget used vs month elapsed with a "Today" marker): playable on the landing page, live on the dashboard.
- **Command palette** (⌘K / Ctrl+K) for keyboard navigation and quick actions.
- **Accessibility:** skip link, `aria-current` navigation, labelled icon buttons, `role="progressbar"` with value text on budget bars, `aria-sort` on sortable headers, inline form errors linked with `aria-describedby`, visible focus rings, reduced-motion support, light/dark themes.

## 11. Accounts, multi-tenancy and administration

### Sign-up and sign-in

| Concern | Implementation |
|---|---|
| Password storage | `ScryptPasswordHasher`: scrypt (memory-hard, OWASP-recommended) from the standard library, 16-byte random salt per hash, parameters stored in the hash so they can be raised later |
| Password policy | `validate_password` in the domain: 8–128 characters, at least one letter and one digit; mirrored in the sign-up form |
| Sessions | `JwtTokenIssuer`: HS256-signed JWT with `sub` (user id), `role`, `iat`, `exp` (24 hours by default), secret from `JWT_SECRET` |
| Session validation | `AuthService.authenticate` verifies the signature and expiry **and** reloads the user, so deactivated accounts are rejected even with an unexpired token |
| Brute force | `LoginThrottle`: five failures per e-mail in five minutes returns 429 |
| User enumeration | Identical error for unknown e-mail and wrong password; a dummy hash is verified for unknown e-mails so response time doesn't reveal which accounts exist |
| Onboarding | `StarterKit` gives new accounts eight common categories (no limits) and the default keyword rules |

### Multi-tenancy: why services didn't change

Isolation is enforced at the **adapter boundary**. Each SQLAlchemy repository is constructed with an `owner_id`; every read, update and delete filters by it, and every insert stamps it. `build_user_scope` wires a fresh service graph per request for the signed-in user.

Consequences:

- A service can't forget to filter by user, because it never sees anyone else's rows.
- Guessing another user's ID returns **404**, not 403, so the API doesn't even confirm the row exists (`tests/test_api.py::test_users_cannot_see_or_touch_each_others_data`).
- Real-time alerts go to per-user SSE topics; `InAppChannel` is constructed with the owner's id, and e-mail alerts go to the owner's address.
- The scheduler generates recurring transactions for every active user by iterating over scopes.
- The domain needed **no** `user_id` fields: ownership is a persistence concern.

The only class that reads across owners is `SqlAlchemyPlatformStats`, and only `AdminService`, which checks the admin role in every method, uses it.

### Admin console

| Capability | Endpoint | Rule |
|---|---|---|
| Platform overview (users, sign-ups, activity, money tracked, alerts) | `GET /admin/overview` | Admin only |
| User list with activity counts | `GET /admin/users` | Admin only |
| Activate / deactivate, change role | `PATCH /admin/users/{id}` | Admin only; admins can't change their own account, so the last admin can't lock everyone out by accident |

Authorisation is checked twice: the `AdminUser` FastAPI dependency rejects non-admins with 403 before the route runs, and `AdminService` checks again so the rule holds no matter which adapter calls it.

### Migrations

The schema was squashed into a single baseline (`alembic/versions/0001_initial_schema.py`) when accounts were introduced, before any release, which is standard practice. `tests/test_persistence.py::test_migrations_match_models` proves the migration and the models are identical.
