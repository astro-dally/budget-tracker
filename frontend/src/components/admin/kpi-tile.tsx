"use client";

import type { LucideIcon } from "lucide-react";
import { useCountUp } from "@/hooks/use-count-up";
import { cn } from "@/lib/utils";

export function KpiTile({
  icon: Icon,
  label,
  value,
  format = (v) => Math.round(v).toLocaleString(),
  note,
  className,
}: {
  icon: LucideIcon;
  label: string;
  value: number;
  format?: (value: number) => string;
  note?: string;
  className?: string;
}) {
  const animated = useCountUp(value);
  return (
    <div className={cn("rounded-2xl border bg-card p-5", className)}>
      <span className="flex items-center gap-2 text-sm text-muted-foreground">
        <Icon className="size-4" aria-hidden="true" /> {label}
      </span>
      <p className="mt-3 font-display text-4xl font-semibold tracking-[-0.03em] tabular">{format(animated)}</p>
      {note ? <p className="mt-1 text-xs text-muted-foreground">{note}</p> : null}
    </div>
  );
}
