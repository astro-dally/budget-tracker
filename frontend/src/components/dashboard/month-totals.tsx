import { ArrowDownLeft, ArrowUpRight, Scale } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { formatMoney, formatPercent, toNumber } from "@/lib/format";
import type { Dashboard } from "@/lib/types";
import { cn } from "@/lib/utils";

function Figure({
  icon: Icon,
  label,
  value,
  note,
  tone,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  note: string;
  tone?: "positive" | "negative";
}) {
  return (
    <div className="flex flex-col gap-2 px-5 py-5 sm:px-6">
      <span className="flex items-center gap-2 text-sm text-muted-foreground">
        <Icon className="size-4" aria-hidden="true" />
        {label}
      </span>
      <span
        className={cn(
          "text-2xl font-semibold tracking-tight tabular",
          tone === "positive" && "text-success",
          tone === "negative" && "text-danger",
        )}
      >
        {value}
      </span>
      <span className="text-xs text-muted-foreground">{note}</span>
    </div>
  );
}

/** Income, expenses and net balance in one divided panel. */
export function MonthTotals({ data }: { data: Dashboard }) {
  const income = toNumber(data.income);
  const balance = toNumber(data.balance);
  const savingsRate = income > 0 ? (balance / income) * 100 : 0;
  const categories = data.spending_by_category.length;
  return (
    <Card className="grid divide-y sm:grid-cols-3 sm:divide-x sm:divide-y-0">
      <Figure
        icon={ArrowDownLeft}
        label="Income"
        value={formatMoney(data.income)}
        note="Salary, refunds and other money in"
      />
      <Figure
        icon={ArrowUpRight}
        label="Expenses"
        value={formatMoney(data.expenses)}
        note={`Across ${categories} ${categories === 1 ? "category" : "categories"}`}
      />
      <Figure
        icon={Scale}
        label="Net balance"
        value={formatMoney(data.balance)}
        note={income > 0 ? `${formatPercent(savingsRate)} of income saved` : "No income recorded yet"}
        tone={balance < 0 ? "negative" : balance > 0 ? "positive" : undefined}
      />
    </Card>
  );
}
