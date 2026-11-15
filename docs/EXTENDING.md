# Extending the system without modifying existing classes

This guide is the Open/Closed Principle in practice. Each example adds a feature by **writing a new class** and **registering it in the composition root** (`backend/app/container.py`). No existing domain, application or infrastructure class is edited.

The code below is not illustrative pseudo-code: it is copied verbatim from `backend/tests/test_extending_examples.py`, where each class is exercised by a passing test. Run them with:

```bash
cd backend
pytest tests/test_extending_examples.py -v
```

| You want to add | Implement | Register in `container.py` | Existing classes edited |
|---|---|---|---|
| An alert rule | `AlertRule` (`app/domain/alert_rules.py`) | `build_alert_rules` | None |
| A report | `ReportStrategy` (`app/domain/reports.py`) | `build_report_registry` | None, including the frontend |
| A notification channel | `NotificationChannel` (`app/application/ports.py`) | `build_channels` + `NOTIFICATION_CHANNELS` | None |
| A categorisation handler | `CategorizationHandler` (`app/domain/categorization.py`) | `build_categorization_chain` + `CATEGORIZATION_ORDER` | None |

---

## Example 1: a new alert rule, "projected overspend"

The built-in rules fire when spending *has reached* 80% or 100%. This rule warns earlier: on day 10 of a 30-day month, ₹1,200 spent against a ₹3,000 budget projects to ₹3,600 by month-end, so it fires now.

Create `app/domain/alert_rules_projection.py` (or any module in the domain):

```python
from decimal import Decimal

from app.application.ports import Clock  # a Protocol; any object with today() works
from app.domain.alert_rules import AlertDecision, AlertRule
from app.domain.budget import BudgetUsage
from app.domain.enums import AlertLevel
from app.domain.money import Money


class ProjectedOverspendRule(AlertRule):
    """Warns early when the current pace of spending would exceed the limit by month-end."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    @property
    def key(self) -> str:
        return "projected-overspend"

    def evaluate(self, usage: BudgetUsage) -> AlertDecision | None:
        today = self._clock.today()
        if not usage.period.contains(today):
            return None
        projected = usage.spent.amount / today.day * usage.period.days
        if projected <= usage.limit.amount:
            return None
        return AlertDecision(
            level=AlertLevel.WARNING,
            message=(
                f"At this pace {usage.category_name} will reach "
                f"{Money(projected)} by month-end, over its {usage.limit} budget."
            ),
            threshold=Decimal(100),
        )
```

Register it in the composition root. `build_alert_rules` takes the clock it needs (already available inside `build_user_scope`, which passes it in); nothing outside `container.py` changes:

```python
def build_alert_rules(settings: Settings, clock: Clock) -> list[AlertRule]:
    rules: list[AlertRule] = [
        PercentageThresholdRule(threshold) for threshold in settings.alert_threshold_list
    ]
    rules.append(ProjectedOverspendRule(clock))
    return rules
```

**Why nothing else changes.** `BudgetMonitor` only knows the `AlertRule` interface. The rule's stable `key` ("projected-overspend") becomes part of the alert's unique `(category_id, period, rule_key)` constraint, so this alert also fires at most once per category per month, for free. The SSE stream, toast, bell badge and alert history all work unchanged.

> In a strictly pure domain you would not import `Clock` from the application layer. Either declare a one-method `Today` Protocol next to the rule, or pass `today: date` in through the usage. The test version imports `Clock` for brevity.

---

## Example 2: a new report, "largest expenses"

```python
from app.domain.money import Money, Period
from app.domain.reports import (
    ColumnKind,
    Report,
    ReportColumn,
    ReportDataSource,
    ReportMetric,
    ReportStrategy,
)


class LargestExpensesReport(ReportStrategy):
    """The ten biggest expenses of the month."""

    key = "largest-expenses"
    title = "Largest expenses"
    description = "Your ten biggest expenses this month."

    def generate(self, period: Period, data: ReportDataSource) -> Report:
        expenses = [t for t in data.transactions_between(period.start, period.end) if t.is_expense]
        top = sorted(expenses, key=lambda t: t.amount, reverse=True)[:10]
        return Report(
            key=self.key,
            title=self.title,
            period=period,
            columns=(
                ReportColumn("date", "Date", ColumnKind.TEXT),
                ReportColumn("description", "Description", ColumnKind.TEXT),
                ReportColumn("amount", "Amount", ColumnKind.MONEY),
            ),
            rows=tuple(
                {
                    "date": t.occurred_on.isoformat(),
                    "description": t.description,
                    "amount": t.amount.amount,
                }
                for t in top
            ),
            metrics=(
                ReportMetric(
                    "Top 10 total",
                    sum((t.amount for t in top), Money.zero()).amount,
                    ColumnKind.MONEY,
                ),
            ),
        )
```

Register it:

```python
def build_report_registry() -> ReportRegistry:
    return (
        ReportRegistry()
        .register(MonthlySummaryReport())
        .register(CategoryWiseReport())
        .register(SpendingTrendReport())
        .register(LargestExpensesReport())  # new
    )
```

**What happens with no further work:**

- `GET /api/v1/reports` now lists `largest-expenses`.
- `GET /api/v1/reports/largest-expenses?month=2026-11` returns it.
- The Reports page shows a new tab, because it builds its tabs from that list.
- The table renders from `columns`, the metrics from `metrics`, and CSV export works, because the frontend renders any `Report` generically (`frontend/src/components/reports/report-view.tsx`). This report has no `ChartSpec`, so no chart is drawn. Add `chart=ChartSpec(ChartKind.BAR, "description", ("amount",))` and a bar chart appears.

---

## Example 3: a new notification channel, "webhook"

Posts every alert to a Slack, Microsoft Teams, Discord or Zapier webhook. The HTTP call is injected, so the class is testable without a network.

Create `app/infrastructure/notifications/webhook.py`:

```python
import json
import urllib.request
from collections.abc import Callable

from app.application.ports import NotificationChannel
from app.domain.alert import Alert


def _http_post(url: str, body: bytes) -> None:
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(request, timeout=10):
        pass


class WebhookChannel(NotificationChannel):
    """Posts alerts as JSON to a webhook (Slack, Teams, Discord, Zapier...)."""

    name = "webhook"

    def __init__(self, url: str, post: Callable[[str, bytes], None] = _http_post) -> None:
        self._url = url
        self._post = post

    def send(self, alert: Alert) -> None:
        self._post(self._url, json.dumps({"text": alert.message}).encode())
```

Register it in `build_channels` (which is called once per user scope, so a channel can use `user.email` or `user.id` if it needs to) and enable it by configuration:

```python
factories: dict[str, Callable[[], NotificationChannel]] = {
    ConsoleChannel.name: ConsoleChannel,
    InAppChannel.name: lambda: InAppChannel(broadcaster),
    EmailChannel.name: lambda: EmailChannel(...),
    SmsChannel.name: lambda: SmsChannel(settings.alert_sms_to),
    WebhookChannel.name: lambda: WebhookChannel(settings.alert_webhook_url),  # new
}
```

```bash
# .env
NOTIFICATION_CHANNELS=console,in_app,email,sms,webhook
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/...
```

(Add `alert_webhook_url: str = ""` to `Settings` in `app/config.py`; configuration is an outer-layer concern.)

**Why nothing else changes.** `NotificationDispatcher` iterates over whatever channels it was given and isolates failures: if the webhook times out, the console, e-mail, SMS and in-app channels still deliver.

---

## Bonus: a new categorisation handler

Suppose you want amount-based rules ("any expense over ₹20,000 on the 1st is rent"). Subclass `CategorizationHandler`, implement `_try_handle`, return `None` when it does not apply, and add it to the factory map in `build_categorization_chain`:

```python
class AmountRuleHandler(CategorizationHandler):
    name = "amount"

    def __init__(self, categories: CategoryNameLookup) -> None:
        super().__init__()
        self._categories = categories

    def _try_handle(self, request: CategorizationRequest) -> CategorizationResult | None:
        ...  # return a result, or None to pass the request down the chain
```

Then place it anywhere in the chain by configuration alone:

```bash
CATEGORIZATION_ORDER=keyword,amount,merchant,user_defined,default
```

The `CategorizationChainBuilder` still guarantees the chain ends with the default handler, so every expense always gets a category.

> Note: amount-based rules would need the amount on `CategorizationRequest`. Adding an optional field to a value object is a backwards-compatible change; existing handlers ignore it.
