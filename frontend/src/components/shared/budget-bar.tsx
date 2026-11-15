import type { BudgetHealth } from "@/lib/types";
import { cn } from "@/lib/utils";

export const HEALTH_TEXT: Record<BudgetHealth, string> = {
  ok: "text-success",
  warning: "text-warning",
  exceeded: "text-danger",
};

const HEALTH_FILL: Record<BudgetHealth, string> = {
  ok: "bg-success",
  warning: "bg-warning",
  exceeded: "bg-danger",
};

export const HEALTH_LABEL: Record<BudgetHealth, string> = {
  ok: "On track",
  warning: "Above 80%",
  exceeded: "Over budget",
};

/** Accessible progress bar coloured by budget health (green / amber / red). */
export function BudgetBar({
  percent,
  health,
  label,
  className,
}: {
  percent: number;
  health: BudgetHealth;
  label: string;
  className?: string;
}) {
  const width = Math.min(100, Math.max(0, percent));
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(percent)}
      aria-valuetext={`${Math.round(percent)}% used, ${HEALTH_LABEL[health].toLowerCase()}`}
      className={cn("h-2 w-full overflow-hidden rounded-full bg-track", className)}
    >
      <div
        className={cn("h-full rounded-full transition-[width] duration-500", HEALTH_FILL[health])}
        style={{ width: `${width}%` }}
      />
    </div>
  );
}
