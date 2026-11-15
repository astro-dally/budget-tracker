import { formatMoney, toNumber } from "@/lib/format";
import type { TransactionType } from "@/lib/types";
import { cn } from "@/lib/utils";

/** A signed amount: income in green with "+", expenses in the default ink with "−". */
export function Amount({
  value,
  type,
  className,
}: {
  value: string;
  type: TransactionType;
  className?: string;
}) {
  const income = type === "income";
  return (
    <span className={cn("font-medium tabular", income && "text-success", className)}>
      <span className="sr-only">{income ? "Income of " : "Expense of "}</span>
      <span aria-hidden="true">{income ? "+" : "−"}</span>
      {formatMoney(toNumber(value))}
    </span>
  );
}
