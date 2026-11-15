"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useSelectedMonth } from "@/components/month-context";
import { Button } from "@/components/ui/button";
import { formatMonth } from "@/lib/format";
import { currentMonth, shiftMonth } from "@/lib/month";

/** Previous / next month control bound to the shared month context. */
export function MonthSwitcher() {
  const { month, setMonth } = useSelectedMonth();
  const isCurrent = month === currentMonth();
  return (
    <div className="flex items-center gap-1 rounded-lg border bg-card p-0.5">
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Previous month"
        onClick={() => setMonth(shiftMonth(month, -1))}
      >
        <ChevronLeft />
      </Button>
      <span className="min-w-32 text-center text-sm font-medium tabular" aria-live="polite">
        {formatMonth(month)}
      </span>
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Next month"
        onClick={() => setMonth(shiftMonth(month, 1))}
      >
        <ChevronRight />
      </Button>
      {!isCurrent ? (
        <Button variant="ghost" size="sm" onClick={() => setMonth(currentMonth())}>
          Today
        </Button>
      ) : null}
    </div>
  );
}
