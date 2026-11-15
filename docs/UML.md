# UML diagrams

All diagrams are Mermaid and render directly on GitHub, GitLab and in VS Code (with a Mermaid extension).

## 1. Architecture (components and dependencies)

Arrows show "depends on". Every arrow points inwards towards the domain, except the composition root, which knows everything because its job is to wire it.

```mermaid
flowchart TB
    subgraph Browser["Next.js frontend"]
        UI["Pages and components"]
        Hooks["TanStack Query hooks"]
        Client["Typed API client"]
        SSE["EventSource for alerts"]
        UI --> Hooks --> Client
        UI --> SSE
    end

    subgraph API["api layer (FastAPI)"]
        Routers["Routers"]
        Schemas["Pydantic schemas and mappers"]
        Errors["Exception handlers"]
    end

    subgraph App["application layer"]
        Auth["AuthService and AdminService"]
        Services["Per-user services: Transaction, Category, Budget, Rule, Recurring, Report, Alert, Dashboard"]
        Monitor["BudgetMonitor (subject)"]
        Dispatcher["NotificationDispatcher (observer)"]
        Ports["Ports: repository Protocols, Clock, NotificationChannel"]
    end

    subgraph Domain["domain layer (standard library only)"]
        Entities["Entities and value objects"]
        Rules["AlertRule strategies"]
        Chain["Categorisation chain"]
        Reports["ReportStrategy and registry"]
    end

    subgraph Infra["infrastructure layer"]
        Repos["Owner-scoped SQLAlchemy repositories"]
        Security["scrypt hasher and JWT issuer"]
        Channels["Console, Email, SMS, InApp channels"]
        Hub["AlertBroadcaster (SSE hub)"]
        Sched["APScheduler job"]
        Clock["SystemClock"]
    end

    DB[("SQLite or PostgreSQL")]
    Root["container.py (composition root)"]

    Client -->|"REST /api/v1"| Routers
    SSE -->|"GET /alerts/stream"| Routers
    Routers --> Services
    Routers --> Auth
    Auth --> Ports
    Security -.->|implements| Ports
    Routers --> Schemas
    Services --> Ports
    Services --> Monitor
    Monitor --> Dispatcher
    Services --> Domain
    Monitor --> Rules
    Repos -.->|implements| Ports
    Channels -.->|implements| Ports
    Clock -.->|implements| Ports
    Repos --> DB
    Channels --> Hub
    Hub --> Routers
    Sched --> Services
    Root --> API
    Root --> App
    Root --> Infra
```

## 2. Observer: budget alerts

```mermaid
classDiagram
    direction LR
    class AlertObserver {
        <<abstract>>
        +on_alert(alert: Alert) None
    }
    class BudgetMonitor {
        -rules: tuple~AlertRule~
        -observers: list~AlertObserver~
        +attach(observer: AlertObserver) None
        +detach(observer: AlertObserver) None
        +check(category_id: str, period: Period) list~Alert~
        -notify(alert: Alert) None
    }
    class NotificationDispatcher {
        -channels: tuple~NotificationChannel~
        +on_alert(alert: Alert) None
    }
    class NotificationChannel {
        <<abstract>>
        +name: str
        +send(alert: Alert) None
    }
    class ConsoleChannel
    class EmailChannel
    class SmsChannel
    class InAppChannel
    class AlertRepository {
        <<Protocol>>
        +add_if_absent(alert: Alert) bool
    }
    class Alert {
        +category_id: str
        +period: Period
        +rule_key: str
        +level: AlertLevel
        +message: str
    }

    BudgetMonitor o--> "*" AlertObserver : notifies
    AlertObserver <|-- NotificationDispatcher
    NotificationDispatcher o--> "*" NotificationChannel
    NotificationChannel <|-- ConsoleChannel
    NotificationChannel <|-- EmailChannel
    NotificationChannel <|-- SmsChannel
    NotificationChannel <|-- InAppChannel
    BudgetMonitor --> AlertRepository : de-duplicates via
    BudgetMonitor ..> Alert : creates
```

## 3. Strategy: alert rules

`BudgetMonitor` is the context. Rules are configured from `ALERT_THRESHOLDS` in the composition root.

```mermaid
classDiagram
    direction LR
    class AlertRule {
        <<abstract>>
        +key: str
        +evaluate(usage: BudgetUsage) AlertDecision
    }
    class PercentageThresholdRule {
        -percent: Decimal
        -level: AlertLevel
        +key: str
        +evaluate(usage: BudgetUsage) AlertDecision
    }
    class ProjectedOverspendRule {
        -clock: Clock
        +key: str
        +evaluate(usage: BudgetUsage) AlertDecision
    }
    class BudgetUsage {
        +limit: Money
        +spent: Money
        +percent_used: Decimal
        +has_reached(percent: Decimal) bool
        +health: BudgetHealth
    }
    class AlertDecision {
        +level: AlertLevel
        +message: str
        +threshold: Decimal
    }
    class BudgetMonitor

    AlertRule <|-- PercentageThresholdRule
    AlertRule <|-- ProjectedOverspendRule
    BudgetMonitor o--> "*" AlertRule : evaluates
    AlertRule ..> BudgetUsage : reads
    AlertRule ..> AlertDecision : returns
    note for ProjectedOverspendRule "Extension example from EXTENDING.md"
```

## 4. Strategy: reports

```mermaid
classDiagram
    direction LR
    class ReportStrategy {
        <<abstract>>
        +key: str
        +title: str
        +description: str
        +generate(period: Period, data: ReportDataSource) Report
    }
    class MonthlySummaryReport
    class CategoryWiseReport
    class SpendingTrendReport
    class ReportRegistry {
        -strategies: dict
        +register(strategy: ReportStrategy) ReportRegistry
        +get(key: str) ReportStrategy
        +available() list~ReportStrategy~
    }
    class ReportService {
        +available() list~ReportStrategy~
        +generate(key: str, period: Period) Report
    }
    class ReportDataSource {
        <<Protocol>>
        +transactions_between(start, end) Sequence~Transaction~
        +categories() Sequence~Category~
        +budgets() Sequence~Budget~
    }
    class Report {
        +columns: tuple~ReportColumn~
        +rows: tuple
        +metrics: tuple~ReportMetric~
        +chart: ChartSpec
    }

    ReportStrategy <|-- MonthlySummaryReport
    ReportStrategy <|-- CategoryWiseReport
    ReportStrategy <|-- SpendingTrendReport
    ReportRegistry o--> "*" ReportStrategy
    ReportService --> ReportRegistry : selects from
    ReportService --> ReportDataSource
    ReportStrategy ..> Report : produces
```

## 5. Chain of Responsibility: categorisation

```mermaid
classDiagram
    direction TB
    class CategorizationHandler {
        <<abstract>>
        -next: CategorizationHandler
        +name: str
        +set_next(handler) CategorizationHandler
        +handle(request) CategorizationResult
        #try_handle(request) CategorizationResult
    }
    class KeywordRuleHandler {
        -rules: KeywordRuleSource
    }
    class MerchantRuleHandler {
        -directory: Mapping
        -categories: CategoryNameLookup
    }
    class UserDefinedRuleHandler {
        -history: CategorizationHistory
    }
    class DefaultCategoryHandler {
        -categories: CategoryNameLookup
        -fallback_name: str
    }
    class CategorizationChainBuilder {
        +add(handler) CategorizationChainBuilder
        +build() CategorizationHandler
    }
    class CategorizationService {
        +categorize(description) CategorizationResult
        +suggest(description) CategorySuggestion
    }

    CategorizationHandler <|-- KeywordRuleHandler
    CategorizationHandler <|-- MerchantRuleHandler
    CategorizationHandler <|-- UserDefinedRuleHandler
    CategorizationHandler <|-- DefaultCategoryHandler
    CategorizationHandler --> CategorizationHandler : next
    CategorizationChainBuilder ..> CategorizationHandler : links
    CategorizationService --> CategorizationHandler : head of chain
```

Runtime chain (default `CATEGORIZATION_ORDER`):

```mermaid
flowchart LR
    R["Description: Uber to airport"] --> K{"KeywordRuleHandler"}
    K -->|match| Done["Result: Transport"]
    K -->|no match| M{"MerchantRuleHandler"}
    M -->|match| Done
    M -->|no match| U{"UserDefinedRuleHandler"}
    U -->|match| Done
    U -->|no match| D["DefaultCategoryHandler: Uncategorized"]
    D --> Done
```

## 6. Sequence: add expense → categorise → budget check → alert → UI

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Next.js page
    participant API as POST /api/v1/transactions
    participant TS as TransactionService
    participant Chain as Categorisation chain
    participant Repo as TransactionRepository
    participant Mon as BudgetMonitor
    participant Rule as AlertRules (80%, 100%)
    participant AR as AlertRepository
    participant Disp as NotificationDispatcher
    participant InApp as InAppChannel
    participant Hub as AlertBroadcaster
    participant Stream as GET /alerts/stream

    Note over UI,Stream: The browser already holds an open EventSource to /alerts/stream
    User->>UI: Submit "Uber to airport", 450, category Auto
    UI->>API: JSON body (category_id null)
    API->>TS: record(TransactionInput)
    TS->>Chain: categorize("Uber to airport")
    Chain-->>TS: Transport (keyword "uber")
    TS->>Repo: add(transaction)
    TS->>Mon: check(Transport, 2026-11)
    Mon->>Repo: expense_total(Transport, 2026-11)
    Repo-->>Mon: 4,150 of 5,000
    loop each rule, ascending
        Mon->>Rule: evaluate(usage)
        Rule-->>Mon: decision or none
    end
    Mon->>AR: add_if_absent(alert percent-80)
    AR-->>Mon: true (first time this month)
    Mon->>Disp: on_alert(alert)
    Disp->>InApp: send(alert)
    InApp->>Hub: publish(alert), thread-safe
    Disp->>Disp: Console, Email, SMS channels
    TS-->>API: Transaction
    API-->>UI: 201 Created
    Hub-->>Stream: alert queued for each subscriber
    Stream-->>UI: event: alert
    UI->>User: Toast "Budget warning" and bell badge +1
```

## 7. Sequence: idempotent recurring generation

```mermaid
sequenceDiagram
    autonumber
    participant Job as Scheduler (hourly and at start-up)
    participant RS as RecurringService
    participant RP as RecurringPayment
    participant TS as TransactionService
    participant DB as transactions table

    Job->>RS: generate_due()
    loop each active payment
        RS->>RP: due_occurrences(today)
        RP-->>RS: dates after last_generated_on
        loop each date
            RS->>TS: record_recurring(payment, date)
            TS->>DB: exists for (recurring_id, date)?
            alt already exists
                DB-->>TS: yes
                TS-->>RS: false (skip)
            else new
                TS->>DB: insert
                Note right of DB: unique (recurring_id, occurred_on) rejects any race
                TS-->>RS: true
            end
        end
        RS->>RS: mark_generated(payment, today)
    end
```

## 8. Accounts and per-user scoping

```mermaid
classDiagram
    direction LR
    class AuthService {
        +register(name, email, password) AuthResult
        +login(email, password) AuthResult
        +authenticate(token) User
        +create_account(...) User
    }
    class LoginThrottle {
        +check(email) None
        +record_failure(email) None
        +reset(email) None
    }
    class UserRepository {
        <<Protocol>>
        +get(user_id) User
        +get_by_email(email) User
    }
    class PasswordHasher {
        <<Protocol>>
        +hash(password) str
        +verify(password, hash) bool
    }
    class TokenIssuer {
        <<Protocol>>
        +issue(user) str
        +verify(token) TokenClaims
    }
    class ScryptPasswordHasher
    class JwtTokenIssuer
    class User {
        +email: str
        +role: UserRole
        +is_active: bool
    }
    class Container {
        +auth: AuthService
        +admin: AdminService
        +scope_for(user) UserScope
    }
    class UserScope {
        +transactions: TransactionService
        +budgets: BudgetService
        +monitor: BudgetMonitor
        +reports: ReportService
    }
    class SqlAlchemyTransactionRepository {
        -owner_id: str
    }
    class AdminService {
        +overview(actor) PlatformOverview
        +list_users(actor) list~UserSummary~
        +update_user(actor, user_id) UserSummary
    }

    AuthService --> UserRepository
    AuthService --> PasswordHasher
    AuthService --> TokenIssuer
    AuthService --> LoginThrottle
    PasswordHasher <|.. ScryptPasswordHasher
    TokenIssuer <|.. JwtTokenIssuer
    AuthService ..> User : returns
    Container --> AuthService
    Container --> AdminService
    Container ..> UserScope : builds per request
    UserScope --> SqlAlchemyTransactionRepository : bound to one owner
```

## 9. Sequence: sign in, then a scoped request

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Login page
    participant API as FastAPI
    participant Auth as AuthService
    participant Throttle as LoginThrottle
    participant Users as UserRepository
    participant Hasher as ScryptPasswordHasher
    participant Tokens as JwtTokenIssuer
    participant Root as Container
    participant Repo as Owner-scoped repository

    User->>UI: E-mail and password (or a demo card)
    UI->>API: POST /auth/login
    API->>Auth: login(email, password)
    Auth->>Throttle: check(email)
    Auth->>Users: get_by_email(email)
    Auth->>Hasher: verify(password, stored hash)
    alt wrong password or unknown e-mail
        Auth->>Throttle: record_failure(email)
        Auth-->>API: AuthenticationError
        API-->>UI: 401 Incorrect e-mail or password
    else valid and active
        Auth->>Tokens: issue(user)
        Auth-->>API: user and token
        API-->>UI: 200 access_token
    end
    UI->>UI: store token, clear query cache
    UI->>API: GET /transactions with Authorization Bearer
    API->>Auth: authenticate(token)
    Auth->>Tokens: verify(token)
    Auth->>Users: get(user_id), must be active
    API->>Root: scope_for(user)
    Root-->>API: services wired to repositories for this owner
    API->>Repo: search(query)
    Note right of Repo: WHERE owner_id = signed-in user
    Repo-->>API: only this user's rows
    API-->>UI: 200 page of transactions
```
