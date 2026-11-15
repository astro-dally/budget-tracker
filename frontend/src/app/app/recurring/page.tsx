"use client";

import { CalendarClock, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { RecurringFormDialog } from "@/components/recurring/recurring-form-dialog";
import { Amount } from "@/components/shared/amount";
import { CategoryIcon } from "@/components/shared/category-icon";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { errorMessage } from "@/lib/api";
import { FREQUENCY_LABEL, formatDate, formatMoney, formatRelativeDue, toNumber } from "@/lib/format";
import { useCategoryMap, useDeleteRecurring, useRecurring, useToggleRecurring } from "@/lib/queries";
import type { Frequency, RecurringPayment } from "@/lib/types";

const MONTHLY_FACTOR: Record<Frequency, number> = { daily: 30.44, weekly: 4.35, monthly: 1 };

function status(payment: RecurringPayment): "active" | "paused" | "ended" {
  if (payment.is_active && payment.next_due === null) return "ended";
  return payment.is_active ? "active" : "paused";
}

export default function RecurringPage() {
  const { data, error, isPending, refetch } = useRecurring();
  const categories = useCategoryMap();
  const toggle = useToggleRecurring();
  const remove = useDeleteRecurring();
  const [formOpen, setFormOpen] = useState(false);
  const [deleting, setDeleting] = useState<RecurringPayment | undefined>();

  const committed = (data ?? [])
    .filter((p) => status(p) === "active" && p.type === "expense")
    .reduce((sum, p) => sum + toNumber(p.amount) * MONTHLY_FACTOR[p.frequency], 0);
  const activeCount = (data ?? []).filter((p) => status(p) === "active").length;

  return (
    <div className="grid gap-6">
      <PageHeader
        title="Recurring payments"
        description={
          data
            ? `${activeCount} active, committing about ${formatMoney(committed, { whole: true })} a month in expenses.`
            : "Payments that repeat are recorded for you on their due dates."
        }
        actions={
          <Button onClick={() => setFormOpen(true)}>
            <Plus /> New recurring payment
          </Button>
        }
      />

      <Card className="overflow-hidden">
        {isPending ? (
          <div className="grid gap-3 p-6">
            {Array.from({ length: 6 }, (_, i) => (
              <Skeleton key={i} className="h-14" />
            ))}
          </div>
        ) : error ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : data.length === 0 ? (
          <EmptyState
            icon={CalendarClock}
            title="No recurring payments"
            description="Add rent, subscriptions or EMIs once and stop forgetting them."
            action={
              <Button size="sm" onClick={() => setFormOpen(true)}>
                <Plus /> New recurring payment
              </Button>
            }
          />
        ) : (
          <ul className="divide-y">
            {data.map((payment) => {
              const category = payment.category_id ? categories.get(payment.category_id) : undefined;
              const state = status(payment);
              return (
                <li
                  key={payment.id}
                  className="flex flex-wrap items-center gap-x-4 gap-y-3 px-5 py-4 sm:flex-nowrap sm:px-6"
                >
                  <CategoryIcon
                    icon={payment.type === "income" ? "wallet" : (category?.icon ?? "repeat")}
                    color={payment.type === "income" ? "#1f8a5b" : (category?.color ?? "#64748b")}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="flex items-center gap-2">
                      <span className="truncate font-medium">{payment.description}</span>
                      <Badge variant="secondary">{FREQUENCY_LABEL[payment.frequency]}</Badge>
                    </p>
                    <p className="mt-0.5 truncate text-sm text-muted-foreground">
                      {state === "active" && payment.next_due
                        ? formatRelativeDue(payment.next_due)
                        : state === "paused"
                          ? "Paused"
                          : `Ended ${payment.end_date ? formatDate(payment.end_date) : ""}`}
                      {category ? ` · ${category.name}` : ""}
                    </p>
                  </div>
                  <Amount value={payment.amount} type={payment.type} className="ml-auto sm:ml-0" />
                  <div className="flex items-center gap-2">
                    {state === "ended" ? (
                      <Badge variant="outline">Ended</Badge>
                    ) : (
                      <label className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Switch
                          checked={payment.is_active}
                          onCheckedChange={(active) =>
                            toggle.mutate(
                              { id: payment.id, active },
                              {
                                onSuccess: () =>
                                  toast.success(active ? `${payment.description} resumed` : `${payment.description} paused`),
                                onError: (e) => toast.error("Couldn't update", { description: errorMessage(e) }),
                              },
                            )
                          }
                          aria-label={`${payment.is_active ? "Pause" : "Resume"} ${payment.description}`}
                        />
                        <span className="w-14">{payment.is_active ? "Active" : "Paused"}</span>
                      </label>
                    )}
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label={`Delete ${payment.description}`}
                      onClick={() => setDeleting(payment)}
                    >
                      <Trash2 />
                    </Button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </Card>

      <RecurringFormDialog open={formOpen} onOpenChange={setFormOpen} />
      <ConfirmDialog
        open={Boolean(deleting)}
        onOpenChange={(open) => !open && setDeleting(undefined)}
        title={`Delete ${deleting?.description ?? "recurring payment"}?`}
        description="No new transactions will be created. Transactions it already recorded are kept."
        confirmLabel="Delete recurring payment"
        onConfirm={() => {
          if (!deleting) return;
          const name = deleting.description;
          remove.mutate(deleting.id, {
            onSuccess: () => toast.success(`${name} deleted`),
            onError: (e) => toast.error("Couldn't delete", { description: errorMessage(e) }),
          });
          setDeleting(undefined);
        }}
      />
    </div>
  );
}
