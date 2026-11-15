"use client";

import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartTooltip } from "@/components/shared/chart-tooltip";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatShortDate } from "@/lib/format";
import type { DailyCount } from "@/lib/types";

export function DailyChart({
  title,
  description,
  data,
  series,
  kind,
}: {
  title: string;
  description: string;
  data: DailyCount[];
  series: string;
  kind: "bar" | "area";
}) {
  const rows = data.map((d) => ({ day: formatShortDate(d.day), count: d.count }));
  const axis = { fill: "var(--muted-foreground)", fontSize: 12 };
  const tooltip = (
    <Tooltip
      cursor={{ fill: "var(--muted)", stroke: "var(--border)" }}
      content={(p) => (
        <ChartTooltip active={p.active} payload={p.payload} label={p.label} formatValue={(v) => v.toLocaleString()} />
      )}
    />
  );
  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-56" role="img" aria-label={`${title}, last 14 days`}>
          <ResponsiveContainer width="100%" height="100%">
            {kind === "bar" ? (
              <BarChart data={rows} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="var(--border)" />
                <XAxis dataKey="day" tickLine={false} axisLine={false} tick={axis} interval={1} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={axis} />
                {tooltip}
                <Bar dataKey="count" name={series} fill="var(--chart-income)" radius={[6, 6, 0, 0]} maxBarSize={28} />
              </BarChart>
            ) : (
              <AreaChart data={rows} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
                <defs>
                  <linearGradient id="admin-activity" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--chart-3)" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="var(--chart-3)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="var(--border)" />
                <XAxis dataKey="day" tickLine={false} axisLine={false} tick={axis} interval={1} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={axis} />
                {tooltip}
                <Area type="monotone" dataKey="count" name={series} stroke="var(--chart-3)" strokeWidth={2} fill="url(#admin-activity)" />
              </AreaChart>
            )}
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
