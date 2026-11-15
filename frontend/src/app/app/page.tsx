"use client";

import { BudgetProgressList } from "@/components/dashboard/budget-progress-list";
import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton";
import { MonthTotals } from "@/components/dashboard/month-totals";
import { PaceHero } from "@/components/dashboard/pace-hero";
import { RecentTransactions } from "@/components/dashboard/recent-transactions";
import { SpendingDonut } from "@/components/dashboard/spending-donut";
import { TrendChart } from "@/components/dashboard/trend-chart";
import { UpcomingRecurring } from "@/components/dashboard/upcoming-recurring";
import { useSelectedMonth } from "@/components/month-context";
import { MonthSwitcher } from "@/components/shared/month-switcher";
import { PageHeader } from "@/components/shared/page-header";
import { ErrorState } from "@/components/shared/states";
import { Card } from "@/components/ui/card";
import { formatMonth } from "@/lib/format";
import { useAuth } from "@/lib/auth";
import { useDashboard } from "@/lib/queries";

export default function DashboardPage() {
  const { month } = useSelectedMonth();
  const { data, error, isPending, refetch } = useDashboard(month);
  const { user } = useAuth();
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const firstName = user?.name.split(" ")[0] ?? "";

  return (
    <div className="grid gap-6">
      <PageHeader
        title={firstName ? `${greeting}, ${firstName}` : "Overview"}
        description={`Here's how ${formatMonth(month)} is going.`}
        actions={<MonthSwitcher />}
      />
      {isPending ? (
        <DashboardSkeleton />
      ) : error ? (
        <Card>
          <ErrorState error={error} onRetry={() => void refetch()} />
        </Card>
      ) : (
        <>
          <PaceHero data={data} />
          <MonthTotals data={data} />
          <div className="grid gap-6 lg:grid-cols-5">
            <div className="lg:col-span-3">
              <BudgetProgressList budgets={data.budgets} />
            </div>
            <div className="lg:col-span-2">
              <SpendingDonut spending={data.spending_by_category} />
            </div>
          </div>
          <div className="grid gap-6 lg:grid-cols-5">
            <div className="lg:col-span-3">
              <TrendChart trend={data.trend} />
            </div>
            <div className="lg:col-span-2">
              <UpcomingRecurring upcoming={data.upcoming} />
            </div>
          </div>
          <RecentTransactions transactions={data.recent} />
        </>
      )}
    </div>
  );
}
