import { Target } from "lucide-react";
import Link from "next/link";
import { BudgetBar, HEALTH_TEXT } from "@/components/shared/budget-bar";
import { CategoryIcon } from "@/components/shared/category-icon";
import { EmptyState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatMoney, formatPercent, toNumber } from "@/lib/format";
import type { BudgetStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

export function BudgetRow({ status }: { status: BudgetStatus }) {
  const percent = toNumber(status.percent_used);
  return (
    <li className="flex items-center gap-3">
      <CategoryIcon icon={status.icon} color={status.color} />
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-3">
          <span className="truncate text-sm font-medium">{status.category_name}</span>
          <span className={cn("text-sm font-semibold tabular", HEALTH_TEXT[status.health])}>
            {formatPercent(percent)}
          </span>
        </div>
        <BudgetBar
          className="mt-2"
          percent={percent}
          health={status.health}
          label={`${status.category_name} budget`}
        />
        <p className="mt-1.5 text-xs text-muted-foreground tabular">
          {formatMoney(status.spent, { whole: true })} of {formatMoney(status.limit, { whole: true })}
          {toNumber(status.remaining) < 0
            ? ` · ${formatMoney(-toNumber(status.remaining), { whole: true })} over`
            : ` · ${formatMoney(status.remaining, { whole: true })} left`}
        </p>
      </div>
    </li>
  );
}

export function BudgetProgressList({ budgets }: { budgets: BudgetStatus[] }) {
  const sorted = [...budgets].sort((a, b) => toNumber(b.percent_used) - toNumber(a.percent_used));
  return (
    <Card className="flex h-full flex-col">
      <CardHeader>
        <CardTitle>Budgets this month</CardTitle>
        <Button asChild variant="ghost" size="sm">
          <Link href="/app/budgets">Manage</Link>
        </Button>
      </CardHeader>
      <CardContent className="flex-1">
        {sorted.length === 0 ? (
          <EmptyState
            icon={Target}
            title="No budgets yet"
            description="Add a monthly limit to a category to see its progress here."
          />
        ) : (
          <ul className="grid gap-5 sm:grid-cols-2 sm:gap-x-8">
            {sorted.map((status) => (
              <BudgetRow key={status.category_id} status={status} />
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
