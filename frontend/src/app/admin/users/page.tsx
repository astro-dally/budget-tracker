"use client";

import { Search, SearchX } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { UserAvatar } from "@/components/layout/user-avatar";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDate, formatNumber, formatTimeAgo } from "@/lib/format";
import { useAdminUsers, useUpdateAdminUser } from "@/lib/queries";
import type { AdminUser, UserRole } from "@/lib/types";

type Filter = "all" | "active" | "inactive" | "admins";

const FILTERS: Record<Filter, (u: AdminUser) => boolean> = {
  all: () => true,
  active: (u) => u.is_active,
  inactive: (u) => !u.is_active,
  admins: (u) => u.role === "admin",
};

export default function AdminUsersPage() {
  const { user: me } = useAuth();
  const { data, error, isPending, refetch } = useAdminUsers();
  const update = useUpdateAdminUser();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("all");

  const rows = useMemo(() => {
    const term = search.trim().toLowerCase();
    return (data ?? [])
      .filter(FILTERS[filter])
      .filter((u) => !term || u.name.toLowerCase().includes(term) || u.email.includes(term));
  }, [data, filter, search]);

  const change = (target: AdminUser, patch: { is_active?: boolean; role?: UserRole }, message: string) =>
    update.mutate(
      { id: target.id, update: patch },
      {
        onSuccess: () => toast.success(message),
        onError: (e) => toast.error("Couldn't update user", { description: errorMessage(e) }),
      },
    );

  return (
    <div className="grid gap-6">
      <PageHeader
        title="Users"
        description={data ? `${data.length} accounts. Deactivated users can't sign in and their sessions end immediately.` : "Every account on the platform."}
      />

      <Card className="overflow-hidden">
        <div className="flex flex-col gap-3 border-b p-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative lg:w-80">
            <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search name or e-mail"
              aria-label="Search users"
              className="pl-9"
            />
          </div>
          <Tabs value={filter} onValueChange={(v) => setFilter(v as Filter)}>
            <TabsList aria-label="Filter users">
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="active">Active</TabsTrigger>
              <TabsTrigger value="inactive">Deactivated</TabsTrigger>
              <TabsTrigger value="admins">Admins</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {isPending ? (
          <div className="grid gap-3 p-6">
            {Array.from({ length: 6 }, (_, i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </div>
        ) : error ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : rows.length === 0 ? (
          <EmptyState icon={SearchX} title="No users match" description="Try another search or filter." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="hidden text-right md:table-cell">Transactions</TableHead>
                <TableHead className="hidden lg:table-cell">Last activity</TableHead>
                <TableHead className="hidden lg:table-cell">Joined</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((u) => {
                const isMe = u.id === me?.id;
                return (
                  <TableRow key={u.id} className={!u.is_active ? "opacity-60" : undefined}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <UserAvatar name={u.name} />
                        <div className="min-w-0">
                          <p className="flex items-center gap-2 truncate font-medium">
                            {u.name}
                            {isMe ? <Badge variant="secondary">You</Badge> : null}
                          </p>
                          <p className="truncate text-xs text-muted-foreground">{u.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Select
                        value={u.role}
                        disabled={isMe}
                        onValueChange={(role) =>
                          change(u, { role: role as UserRole }, `${u.name} is now ${role === "admin" ? "an admin" : "a regular user"}`)
                        }
                      >
                        <SelectTrigger className="h-8 w-28" aria-label={`Role for ${u.name}`}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="user">User</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <label className="flex items-center gap-2 text-sm">
                        <Switch
                          checked={u.is_active}
                          disabled={isMe}
                          onCheckedChange={(active) =>
                            change(u, { is_active: active }, active ? `${u.name} reactivated` : `${u.name} deactivated`)
                          }
                          aria-label={`${u.is_active ? "Deactivate" : "Activate"} ${u.name}`}
                        />
                        <span className={u.is_active ? "text-success" : "text-danger"}>{u.is_active ? "Active" : "Off"}</span>
                      </label>
                    </TableCell>
                    <TableCell className="hidden text-right tabular md:table-cell">{formatNumber(u.transaction_count)}</TableCell>
                    <TableCell className="hidden text-muted-foreground lg:table-cell">
                      {u.last_login_at ? `Signed in ${formatTimeAgo(u.last_login_at)}` : u.last_transaction_on ? `Spent on ${formatDate(u.last_transaction_on)}` : "—"}
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground lg:table-cell">{formatDate(u.created_at.slice(0, 10))}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
