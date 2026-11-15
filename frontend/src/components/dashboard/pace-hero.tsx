"use client";

import { ArrowRight, Target } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useCountUp } from "@/hooks/use-count-up";
import { formatMoney, formatMonthName, formatPercent, toNumber } from "@/lib/format";
import type { BudgetHealth, Dashboard } from "@/lib/types";
import { cn } from "@/lib/utils";

const FILL: Record<BudgetHealth, string> = {
  ok: "from-emerald-300 to-lime",
  warning: "from-amber-300 to-gold",
  exceeded: "from-orange-400 to-coral",
};

const DOT: Record<BudgetHealth, string> = { ok: "bg-lime", warning: "bg-gold", exceeded: "bg-coral" };

function pace(used: number, timeShare: number, inProgress: boolean): { label: string; health: BudgetHealth } {
  if (used >= 100) return { label: "Over budget", health: "exceeded" };
  if (!inProgress) return { label: timeShare >= 100 ? "Month closed" : "Not started", health: "ok" };
  if (used - timeShare > 5) return { label: "Spending faster than the month", health: "warning" };
  return { label: "On pace", health: "ok" };
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-white/55">{label}</dt>
      <dd className="mt-1 text-lg font-semibold tracking-tight tabular">{value}</dd>
    </div>
  );
}

/**
 * The dashboard's signature element: budget used and month elapsed on one
 * track, so it's obvious *during* the month whether spending is running ahead.
 */
export function PaceHero({ data }: { data: Dashboard }) {
  const total = toNumber(data.budget_total);
  const spent = toNumber(data.budget_spent);
  const used = toNumber(data.budget_used_percent);
  const remaining = total - spent;
  const animated = useCountUp(Math.abs(remaining));
  const monthName = formatMonthName(data.period);

  if (total <= 0) {
    return (
      <section className="relative overflow-hidden rounded-3xl bg-ledger p-6 text-white sm:p-10">
        <div className="ledger-grid absolute inset-0" aria-hidden="true" />
        <div className="relative flex flex-col items-start gap-5 sm:flex-row sm:items-center">
          <span className="flex size-12 items-center justify-center rounded-2xl bg-lime text-ledger">
            <Target className="size-6" aria-hidden="true" />
          </span>
          <div className="flex-1">
            <h2 className="font-display text-2xl font-semibold tracking-tight">Set your first monthly limit</h2>
            <p className="mt-1 max-w-prose text-sm text-white/70">
              Give a category a budget and this panel will show whether you&apos;re spending faster than the
              month is passing.
            </p>
          </div>
          <Button asChild className="bg-lime text-ledger hover:bg-lime/90">
            <Link href="/app/budgets">
              Set a budget <ArrowRight />
            </Link>
          </Button>
        </div>
      </section>
    );
  }

  const timeShare = (data.days_elapsed / data.days_in_month) * 100;
  const inProgress = data.days_elapsed > 0 && data.days_elapsed < data.days_in_month;
  const daysLeft = data.days_in_month - data.days_elapsed + (inProgress ? 1 : 0);
  const health: BudgetHealth = used >= 100 ? "exceeded" : used >= 80 ? "warning" : "ok";
  const status = pace(used, timeShare, inProgress);
  const perDay = inProgress && remaining > 0 ? remaining / daysLeft : 0;

  return (
    <section
      aria-labelledby="pace-heading"
      className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-ledger to-ledger-2 p-6 text-white sm:p-9"
    >
      <div className="ledger-grid absolute inset-0" aria-hidden="true" />
      <div
        className="pointer-events-none absolute -top-32 -right-24 size-96 rounded-full bg-lime/20 blur-3xl"
        aria-hidden="true"
      />
      <div className="relative">
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium ring-1 ring-white/15">
            <span className="relative flex size-2">
              <span className={cn("ping-soft absolute inset-0 rounded-full", DOT[status.health])} />
              <span className={cn("relative size-2 rounded-full", DOT[status.health])} />
            </span>
            {status.label}
          </span>
          {inProgress ? (
            <span className="text-xs text-white/60">
              {monthName}, day {data.days_elapsed} of {data.days_in_month}
            </span>
          ) : null}
        </div>

        <div className="mt-6 flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
          <h2 id="pace-heading">
            <span
              className={cn(
                "block font-display text-5xl font-semibold tracking-[-0.04em] tabular sm:text-7xl",
                remaining < 0 && "text-coral",
              )}
            >
              {formatMoney(animated, { whole: true })}
            </span>
            <span className="mt-2 block text-base font-normal text-white/70">
              {remaining >= 0 ? `left to spend in ${monthName}` : `over budget in ${monthName}`}
            </span>
          </h2>
          <dl className="grid grid-cols-3 gap-6 sm:gap-10">
            <Stat label="Spent" value={formatMoney(spent, { whole: true })} />
            <Stat label="Budgeted" value={formatMoney(total, { whole: true })} />
            <Stat label="Safe per day" value={perDay > 0 ? formatMoney(perDay, { whole: true }) : "—"} />
          </dl>
        </div>

        <div className="mt-10">
          <div
            role="img"
            aria-label={`${formatPercent(used)} of the budget used${
              inProgress ? ` with ${Math.round(timeShare)}% of the month gone` : ""
            }`}
            className="relative h-4 rounded-full bg-white/10 ring-1 ring-white/10"
          >
            <div
              className={cn(
                "absolute inset-y-0 left-0 rounded-full bg-gradient-to-r shadow-[0_0_24px_-2px] shadow-current transition-[width] duration-1000",
                FILL[health],
              )}
              style={{ width: `${Math.min(100, used)}%` }}
            />
            {inProgress ? (
              <div
                className="absolute -top-2 -bottom-2 w-0.5 -translate-x-1/2 rounded-full bg-white"
                style={{ left: `${timeShare}%` }}
                aria-hidden="true"
              >
                <span className="absolute bottom-full left-1/2 mb-1.5 -translate-x-1/2 rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold whitespace-nowrap text-ledger">
                  Today
                </span>
              </div>
            ) : null}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-white/60">
            <span>
              Budget used <span className="font-semibold text-white tabular">{formatPercent(used)}</span>
            </span>
            {inProgress ? (
              <span>
                Month gone <span className="font-semibold text-white tabular">{Math.round(timeShare)}%</span>
              </span>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}
