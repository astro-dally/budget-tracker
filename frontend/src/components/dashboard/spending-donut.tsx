"use client";

import { PieChart as PieIcon } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { ChartTooltip } from "@/components/shared/chart-tooltip";
import { EmptyState } from "@/components/shared/states";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCompactMoney, formatMoney, formatPercent, toNumber } from "@/lib/format";
import type { CategorySpend } from "@/lib/types";

export function SpendingDonut({ spending }: { spending: CategorySpend[] }) {
  const data = spending.map((s) => ({ name: s.name, value: toNumber(s.amount), fill: s.color }));
  const total = data.reduce((sum, d) => sum + d.value, 0);
  return (
    <Card className="flex h-full flex-col">
      <CardHeader>
        <CardTitle>Where it went</CardTitle>
      </CardHeader>
      <CardContent className="flex-1">
        {total === 0 ? (
          <EmptyState
            icon={PieIcon}
            title="No spending yet"
            description="Expenses you record this month will be broken down by category here."
          />
        ) : (
          <div className="grid items-center gap-6 sm:grid-cols-[11rem_1fr] lg:grid-cols-1">
            <div className="relative mx-auto size-44">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data}
                    dataKey="value"
                    nameKey="name"
                    innerRadius="68%"
                    outerRadius="100%"
                    paddingAngle={2}
                    stroke="none"
                    isAnimationActive={false}
                  >
                    {data.map((entry) => (
                      <Cell key={entry.name} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip
                    content={(props) => (
                      <ChartTooltip active={props.active} payload={props.payload} />
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-xs text-muted-foreground">Spent</span>
                <span className="text-lg font-semibold tabular">{formatCompactMoney(total)}</span>
              </div>
            </div>
            <ul className="grid gap-2.5">
              {data.slice(0, 6).map((entry) => (
                <li key={entry.name} className="flex items-center gap-2 text-sm">
                  <span className="size-2.5 shrink-0 rounded-full" style={{ backgroundColor: entry.fill }} />
                  <span className="min-w-0 flex-1 truncate">{entry.name}</span>
                  <span className="w-10 text-right text-xs text-muted-foreground tabular">
                    {formatPercent((entry.value / total) * 100)}
                  </span>
                  <span className="text-right font-medium tabular">
                    {formatMoney(entry.value, { whole: true })}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
