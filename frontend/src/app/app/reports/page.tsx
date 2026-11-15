"use client";

import { Download } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { useSelectedMonth } from "@/components/month-context";
import { ReportView } from "@/components/reports/report-view";
import { MonthSwitcher } from "@/components/shared/month-switcher";
import { PageHeader } from "@/components/shared/page-header";
import { ErrorState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { downloadCsv, toCsv } from "@/lib/csv";
import { useReport, useReportTypes } from "@/lib/queries";

export default function ReportsPage() {
  const { month } = useSelectedMonth();
  const types = useReportTypes();
  const [selected, setSelected] = useState<string | undefined>();
  const active = selected ?? types.data?.[0]?.key;
  const report = useReport(active, month);
  const activeType = types.data?.find((t) => t.key === active);

  const exportCsv = () => {
    if (!report.data) return;
    downloadCsv(`${report.data.key}-${report.data.period}.csv`, toCsv(report.data.columns, report.data.rows));
    toast.success("CSV downloaded");
  };

  return (
    <div className="grid gap-6">
      <PageHeader
        title="Reports"
        description={activeType?.description ?? "Summaries of your money, month by month."}
        actions={
          <>
            <MonthSwitcher />
            <Button variant="outline" onClick={exportCsv} disabled={!report.data || report.data.rows.length === 0}>
              <Download /> Export CSV
            </Button>
          </>
        }
      />

      {types.isPending ? (
        <Skeleton className="h-9 w-96 max-w-full" />
      ) : types.error ? (
        <Card>
          <ErrorState error={types.error} onRetry={() => void types.refetch()} />
        </Card>
      ) : (
        <Tabs value={active} onValueChange={setSelected}>
          <TabsList aria-label="Report type">
            {types.data.map((type) => (
              <TabsTrigger key={type.key} value={type.key}>
                {type.title}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      )}

      {report.isPending && active ? (
        <div className="grid gap-6">
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="h-80 rounded-xl" />
        </div>
      ) : report.error ? (
        <Card>
          <ErrorState error={report.error} onRetry={() => void report.refetch()} />
        </Card>
      ) : report.data ? (
        <div className={report.isFetching ? "opacity-70 transition-opacity" : undefined}>
          <ReportView report={report.data} />
        </div>
      ) : null}
    </div>
  );
}
