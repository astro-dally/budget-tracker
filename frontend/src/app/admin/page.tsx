"use client";

import { ArrowLeftRight, BellRing, IndianRupee, ShieldCheck, UserPlus, Users } from "lucide-react";
import Link from "next/link";
import { DailyChart } from "@/components/admin/daily-chart";
import { KpiTile } from "@/components/admin/kpi-tile";
import { UserAvatar } from "@/components/layout/user-avatar";
import { PageHeader } from "@/components/shared/page-header";
import { ErrorState } from "@/components/shared/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCompactMoney, formatDate, toNumber } from "@/lib/format";
import { useAdminOverview, useAdminUsers } from "@/lib/queries";

export default function AdminOverviewPage() {
  const overview = useAdminOverview();
  const users = useAdminUsers();

  return (
    <div className="grid gap-6">
      <PageHeader
        title="Platform"
        description="Everyone using Budget Tracker, at a glance."
        actions={
          <Button asChild variant="outline">
            <Link href="/admin/users">
              <Users /> Manage users
            </Link>
          </Button>
        }
      />

      {overview.isPending ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="h-32 rounded-2xl" />
          ))}
        </div>
      ) : overview.error ? (
        <Card>
          <ErrorState error={overview.error} onRetry={() => void overview.refetch()} />
        </Card>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <KpiTile
              icon={Users}
              label="Total users"
              value={overview.data.total_users}
              note={`${overview.data.active_users} active, ${overview.data.total_users - overview.data.active_users} deactivated`}
              className="bg-gradient-to-br from-ledger to-ledger-2 text-white [&_p]:text-white [&_span]:text-white/70 border-transparent"
            />
            <KpiTile icon={UserPlus} label="New this week" value={overview.data.new_users_7d} note="Sign-ups in the last 7 days" />
            <KpiTile icon={ShieldCheck} label="Administrators" value={overview.data.admins} note="Accounts with admin access" />
            <KpiTile icon={ArrowLeftRight} label="Transactions" value={overview.data.transactions} note="Recorded across all accounts" />
            <KpiTile
              icon={IndianRupee}
              label="Spending tracked"
              value={toNumber(overview.data.expense_volume)}
              format={(v) => formatCompactMoney(v)}
              note="Total expenses on the platform"
            />
            <KpiTile icon={BellRing} label="Alerts sent" value={overview.data.alerts_30d} note="Budget alerts in the last 30 days" />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <DailyChart title="Sign-ups" description="New accounts per day, last 14 days." data={overview.data.signups_by_day} series="Sign-ups" kind="bar" />
            <DailyChart title="Activity" description="Transactions recorded per day, last 14 days." data={overview.data.activity_by_day} series="Transactions" kind="area" />
          </div>
        </>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Newest members</CardTitle>
          <Button asChild variant="ghost" size="sm">
            <Link href="/admin/users">All users</Link>
          </Button>
        </CardHeader>
        <CardContent>
          {users.isPending ? (
            <div className="grid gap-3">
              {Array.from({ length: 4 }, (_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          ) : users.error ? (
            <ErrorState error={users.error} onRetry={() => void users.refetch()} />
          ) : (
            <ul className="divide-y">
              {users.data.slice(0, 5).map((u) => (
                <li key={u.id} className="flex items-center gap-3 py-3">
                  <UserAvatar name={u.name} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{u.name}</p>
                    <p className="truncate text-xs text-muted-foreground">{u.email}</p>
                  </div>
                  {!u.is_active ? <Badge variant="danger">Deactivated</Badge> : null}
                  <span className="hidden text-xs text-muted-foreground sm:block">Joined {formatDate(u.created_at.slice(0, 10))}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
