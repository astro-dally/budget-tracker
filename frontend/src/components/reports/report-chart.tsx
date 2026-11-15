"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartTooltip } from "@/components/shared/chart-tooltip";
import { formatCompactMoney, toNumber } from "@/lib/format";
import type { ChartSpec, Report } from "@/lib/types";

export const SERIES_COLORS = [
  "var(--chart-income)",
  "var(--chart-expense)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

const axisTick = { fill: "var(--muted-foreground)", fontSize: 12 };

/**
 * Draws whatever chart a report strategy asks for. The backend's ChartSpec
 * picks the kind and keys, so new report types need no changes here.
 */
export function ReportChart({ report, chart }: { report: Report; chart: ChartSpec }) {
  const label = (key: string) => report.columns.find((c) => c.key === key)?.label ?? key;
  const rows = report.rows.map((row) => {
    const numeric: Record<string, string | number> = { [chart.x_key]: String(row[chart.x_key] ?? "") };
    chart.y_keys.forEach((key) => (numeric[key] = toNumber(row[key])));
    if (typeof row.color === "string") numeric.color = row.color;
    return numeric;
  });
  const tooltip = (
    <Tooltip
      cursor={{ fill: "var(--muted)", stroke: "var(--border)" }}
      content={(props) => <ChartTooltip active={props.active} payload={props.payload} label={props.label} />}
    />
  );

  if (chart.kind === "pie") {
    const key = chart.y_keys[0] ?? "";
    const data = rows.filter((row) => toNumber(row[key]) > 0);
    return (
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey={key} nameKey={chart.x_key} innerRadius="55%" outerRadius="90%" paddingAngle={2} stroke="none">
            {data.map((row, index) => (
              <Cell
                key={String(row[chart.x_key])}
                fill={typeof row.color === "string" ? row.color : SERIES_COLORS[index % SERIES_COLORS.length]}
              />
            ))}
          </Pie>
          {tooltip}
        </PieChart>
      </ResponsiveContainer>
    );
  }

  const common = (
    <>
      <CartesianGrid vertical={false} stroke="var(--border)" />
      <XAxis dataKey={chart.x_key} tickLine={false} axisLine={false} tick={axisTick} tickMargin={8} />
      <YAxis tickLine={false} axisLine={false} width={56} tick={axisTick} tickFormatter={(v: number) => formatCompactMoney(v)} />
      {tooltip}
    </>
  );

  if (chart.kind === "line") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          {common}
          {chart.y_keys.map((key, index) => (
            <Line key={key} type="monotone" dataKey={key} name={label(key)} stroke={SERIES_COLORS[index % SERIES_COLORS.length]} strokeWidth={2} dot={{ r: 3 }} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        {common}
        {chart.y_keys.map((key, index) => (
          <Bar key={key} dataKey={key} name={label(key)} fill={SERIES_COLORS[index % SERIES_COLORS.length]} radius={[4, 4, 0, 0]} maxBarSize={36} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
