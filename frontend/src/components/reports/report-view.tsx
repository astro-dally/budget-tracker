"use client";

import { CategoryLabel } from "@/components/shared/category-icon";
import { ReportChart, SERIES_COLORS } from "@/components/reports/report-chart";
import { formatCell } from "@/components/reports/format-cell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Report } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Generic renderer for any report strategy: metrics, chart hint and table. */
export function ReportView({ report }: { report: Report }) {
  return (
    <div className="grid gap-6">
      <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border bg-border md:grid-cols-3 xl:grid-cols-6">
        {report.metrics.map((metric) => (
          <div key={metric.label} className="bg-card px-5 py-4">
            <dt className="text-xs text-muted-foreground">{metric.label}</dt>
            <dd className="mt-1 truncate text-lg font-semibold tracking-tight tabular">
              {formatCell(metric.value, metric.kind)}
            </dd>
          </div>
        ))}
      </dl>

      {report.chart && report.rows.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>{report.title}</CardTitle>
            {report.chart.kind !== "pie" ? (
              <ul className="flex gap-4 text-xs text-muted-foreground">
                {report.chart.y_keys.map((key, index) => (
                  <li key={key} className="flex items-center gap-1.5">
                    <span
                      className="size-2 rounded-full"
                      style={{ backgroundColor: SERIES_COLORS[index % SERIES_COLORS.length] }}
                    />
                    {report.columns.find((c) => c.key === key)?.label ?? key}
                  </li>
                ))}
              </ul>
            ) : null}
          </CardHeader>
          <CardContent>
            <div className="h-72" role="img" aria-label={`${report.chart.kind} chart of ${report.title}`}>
              <ReportChart report={report} chart={report.chart} />
            </div>
          </CardContent>
        </Card>
      ) : null}

      <Card className="overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              {report.columns.map((column) => (
                <TableHead key={column.key} className={cn(column.kind !== "text" && "text-right")}>
                  {column.label}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={report.columns.length} className="py-10 text-center text-muted-foreground">
                  Nothing to report for this month yet.
                </TableCell>
              </TableRow>
            ) : (
              report.rows.map((row, index) => (
                <TableRow key={`${String(row[report.columns[0]?.key ?? ""])}-${index}`}>
                  {report.columns.map((column, columnIndex) => (
                    <TableCell
                      key={column.key}
                      className={cn(column.kind !== "text" && "text-right tabular", columnIndex === 0 && "font-medium")}
                    >
                      {columnIndex === 0 && typeof row.color === "string" ? (
                        <CategoryLabel name={String(row[column.key])} color={row.color} />
                      ) : (
                        formatCell(row[column.key], column.kind)
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
