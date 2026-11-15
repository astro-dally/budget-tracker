"use client";

import type { TooltipContentProps } from "recharts";
import { formatMoney, toNumber } from "@/lib/format";

type Props = Partial<Pick<TooltipContentProps<number | string, string>, "active" | "payload" | "label">> & {
  formatValue?: (value: number) => string;
  labelFormatter?: (label: string) => string;
};

/** Themed tooltip shared by every chart. */
export function ChartTooltip({
  active,
  payload,
  label,
  formatValue = (v) => formatMoney(v),
  labelFormatter,
}: Props) {
  if (!active || !payload?.length) return null;
  const title = label === undefined ? undefined : String(label);
  return (
    <div className="min-w-40 rounded-lg border bg-popover px-3 py-2 text-xs shadow-lg">
      {title ? (
        <p className="mb-1.5 font-medium text-foreground">
          {labelFormatter ? labelFormatter(title) : title}
        </p>
      ) : null}
      <ul className="grid gap-1">
        {payload.map((entry) => (
          <li key={String(entry.dataKey ?? entry.name)} className="flex items-center gap-2">
            <span
              className="size-2 rounded-full"
              style={{ backgroundColor: entry.color ?? entry.payload?.fill }}
            />
            <span className="text-muted-foreground capitalize">{String(entry.name ?? "")}</span>
            <span className="ml-auto pl-4 font-medium tabular text-foreground">
              {formatValue(toNumber(entry.value as number | string | undefined))}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
