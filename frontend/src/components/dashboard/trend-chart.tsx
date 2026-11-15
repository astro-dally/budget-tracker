"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartTooltip } from "@/components/shared/chart-tooltip";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCompactMoney, formatMonth, toNumber } from "@/lib/format";
import type { TrendPoint } from "@/lib/types";

const SERIES = [
  { key: "income", label: "Income", color: "var(--chart-income)" },
  { key: "expenses", label: "Expenses", color: "var(--chart-expense)" },
] as const;

export function TrendChart({ trend }: { trend: TrendPoint[] }) {
  const data = trend.map((point) => ({
    month: formatMonth(point.period, "short"),
    income: toNumber(point.income),
    expenses: toNumber(point.expenses),
  }));
  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>Six-month trend</CardTitle>
          <CardDescription>Money in and out, month by month.</CardDescription>
        </div>
        <ul className="flex gap-4 text-xs text-muted-foreground">
          {SERIES.map((s) => (
            <li key={s.key} className="flex items-center gap-1.5">
              <span className="size-2 rounded-full" style={{ backgroundColor: s.color }} />
              {s.label}
            </li>
          ))}
        </ul>
      </CardHeader>
      <CardContent>
        <div className="h-64" role="img" aria-label="Area chart of income and expenses over six months">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 4, left: 0, bottom: 0 }}>
              <defs>
                {SERIES.map((s) => (
                  <linearGradient key={s.key} id={`fill-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={s.color} stopOpacity={0.22} />
                    <stop offset="100%" stopColor={s.color} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid vertical={false} stroke="var(--border)" />
              <XAxis
                dataKey="month"
                tickLine={false}
                axisLine={false}
                tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                tickMargin={8}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                width={56}
                tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                tickFormatter={(v: number) => formatCompactMoney(v)}
              />
              <Tooltip
                cursor={{ stroke: "var(--border)" }}
                content={(props) => (
                  <ChartTooltip active={props.active} payload={props.payload} label={props.label} />
                )}
              />
              {SERIES.map((s) => (
                <Area
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  name={s.label}
                  stroke={s.color}
                  strokeWidth={2}
                  fill={`url(#fill-${s.key})`}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
