"use client";

import { BellOff, CheckCheck } from "lucide-react";
import { useState } from "react";
import { AlertLevelIcon } from "@/components/alerts/alert-level-icon";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { formatMoney, formatMonth, formatTimeAgo } from "@/lib/format";
import { useAlerts, useMarkAllAlertsRead, useMarkAlertRead, useUnreadCount } from "@/lib/queries";
import { cn } from "@/lib/utils";

export default function AlertsPage() {
  const [filter, setFilter] = useState<"all" | "unread">("all");
  const { data, error, isPending, refetch } = useAlerts(filter === "unread");
  const unread = useUnreadCount().data?.count ?? 0;
  const markRead = useMarkAlertRead();
  const markAll = useMarkAllAlertsRead();

  return (
    <div className="grid gap-6">
      <PageHeader
        title="Alerts"
        description="You're warned once at 80% of a budget and once when it's reached, each month."
        actions={
          <Button variant="outline" disabled={unread === 0} onClick={() => markAll.mutate()}>
            <CheckCheck /> Mark all as read
          </Button>
        }
      />

      <Tabs value={filter} onValueChange={(v) => setFilter(v === "unread" ? "unread" : "all")}>
        <TabsList aria-label="Filter alerts">
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="unread">
            Unread
            {unread > 0 ? <Badge variant="danger" className="px-1.5 py-0">{unread}</Badge> : null}
          </TabsTrigger>
        </TabsList>
      </Tabs>

      <Card className="overflow-hidden">
        {isPending ? (
          <div className="grid gap-3 p-6">
            {Array.from({ length: 5 }, (_, i) => (
              <Skeleton key={i} className="h-16" />
            ))}
          </div>
        ) : error ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : data.length === 0 ? (
          <EmptyState
            icon={BellOff}
            title={filter === "unread" ? "You're all caught up" : "No alerts yet"}
            description={
              filter === "unread"
                ? "There are no unread alerts."
                : "When a category reaches 80% of its monthly limit, you'll see it here."
            }
          />
        ) : (
          <ul className="divide-y">
            {data.map((alert) => (
              <li
                key={alert.id}
                className={cn("flex items-start gap-4 px-5 py-4 sm:px-6", !alert.is_read && "bg-primary/[0.03]")}
              >
                <AlertLevelIcon level={alert.level} />
                <div className="min-w-0 flex-1">
                  <p className={cn("text-sm", alert.is_read ? "text-muted-foreground" : "font-medium")}>
                    {alert.message}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {alert.category_name} · {formatMonth(alert.period)} ·{" "}
                    <span className="tabular">
                      {formatMoney(alert.spent, { whole: true })} of {formatMoney(alert.limit, { whole: true })}
                    </span>{" "}
                    · {formatTimeAgo(alert.created_at)}
                  </p>
                </div>
                {!alert.is_read ? (
                  <Button variant="ghost" size="sm" onClick={() => markRead.mutate(alert.id)}>
                    Mark as read
                  </Button>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
