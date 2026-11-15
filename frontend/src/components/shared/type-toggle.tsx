"use client";

import type { TransactionType } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Segmented Expense / Income control (a radio group for assistive tech). */
export function TypeToggle({
  value,
  onChange,
}: {
  value: TransactionType;
  onChange: (value: TransactionType) => void;
}) {
  const options: Array<{ value: TransactionType; label: string }> = [
    { value: "expense", label: "Expense" },
    { value: "income", label: "Income" },
  ];
  return (
    <div role="radiogroup" aria-label="Type" className="grid grid-cols-2 gap-1 rounded-lg bg-secondary p-1">
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(option.value)}
            className={cn(
              "h-8 rounded-md text-sm font-medium text-muted-foreground transition-colors outline-none focus-visible:ring-[3px] focus-visible:ring-ring/40",
              selected && "bg-card text-foreground shadow-sm",
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
