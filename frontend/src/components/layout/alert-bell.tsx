"use client";

import { Bell, CheckCheck } from "lucide-react";
import Link from "next/link";
import { AlertLevelIcon } from "@/components/alerts/alert-level-icon";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { formatTimeAgo } from "@/lib/format";
import { useAlerts, useMarkAllAlertsRead, useMarkAlertRead, useUnreadCount } from "@/lib/queries";
import { cn } from "@/lib/utils";

/** Bell with unread badge and a preview of the latest alerts. */
export function AlertBell() {
  const unread = useUnreadCount().data?.count ?? 0;
  const { data: alerts } = useAlerts();
  const markRead = useMarkAlertRead();
  const markAll = useMarkAllAlertsRead();
  const latest = (alerts ?? []).slice(0, 5);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label={unread ? `Alerts, ${unread} unread` : "Alerts"}
        >
          <Bell />
          {unread > 0 ? (
            <span className="absolute top-1 right-1 flex min-w-4 items-center justify-center rounded-full bg-danger px-1 text-[10px] leading-4 font-semibold text-white tabular">
              {unread > 9 ? "9+" : unread}
            </span>
          ) : null}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 p-0">
        <div className="flex items-center justify-between px-3 py-2.5">
          <p className="text-sm font-semibold">Alerts</p>
          <Button
            variant="ghost"
            size="sm"
            disabled={unread === 0}
            onClick={() => markAll.mutate()}
          >
            <CheckCheck /> Mark all read
          </Button>
        </div>
        <DropdownMenuSeparator className="mx-0 my-0" />
        {latest.length === 0 ? (
          <p className="px-3 py-6 text-center text-sm text-muted-foreground">
            No alerts yet. You&apos;ll hear from us when a budget reaches 80%.
          </p>
        ) : (
          <div className="max-h-80 overflow-y-auto p-1">
            {latest.map((alert) => (
              <DropdownMenuItem
                key={alert.id}
                className="items-start gap-3 py-2"
                onSelect={() => !alert.is_read && markRead.mutate(alert.id)}
              >
                <AlertLevelIcon level={alert.level} />
                <span className="min-w-0 flex-1">
                  <span
                    className={cn(
                      "line-clamp-2 text-sm",
                      alert.is_read ? "text-muted-foreground" : "text-foreground",
                    )}
                  >
                    {alert.message}
                  </span>
                  <span className="mt-0.5 block text-xs text-muted-foreground">
                    {formatTimeAgo(alert.created_at)}
                  </span>
                </span>
                {!alert.is_read ? (
                  <span className="mt-1.5 size-2 shrink-0 rounded-full bg-primary">
                    <span className="sr-only">Unread</span>
                  </span>
                ) : null}
              </DropdownMenuItem>
            ))}
          </div>
        )}
        <DropdownMenuSeparator className="mx-0 my-0" />
        <DropdownMenuItem asChild className="justify-center rounded-none py-2.5 text-primary">
          <Link href="/app/alerts">View alert history</Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
