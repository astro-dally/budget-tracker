"use client";

import { CalendarClock } from "lucide-react";
import Link from "next/link";
import { CategoryIcon } from "@/components/shared/category-icon";
import { Amount } from "@/components/shared/amount";
import { EmptyState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FREQUENCY_LABEL, formatRelativeDue } from "@/lib/format";
import { useCategoryMap } from "@/lib/queries";
import type { UpcomingPayment } from "@/lib/types";

export function UpcomingRecurring({ upcoming }: { upcoming: UpcomingPayment[] }) {
  const categories = useCategoryMap();
  return (
    <Card className="flex h-full flex-col">
      <CardHeader>
        <CardTitle>Coming up</CardTitle>
        <Button asChild variant="ghost" size="sm">
          <Link href="/app/recurring">All recurring</Link>
        </Button>
      </CardHeader>
      <CardContent className="flex-1">
        {upcoming.length === 0 ? (
          <EmptyState
            icon={CalendarClock}
            title="Nothing scheduled"
            description="Add rent, subscriptions or EMIs as recurring payments and they'll appear here."
          />
        ) : (
          <ul className="grid gap-4">
            {upcoming.map((item) => {
              const category = item.category_id ? categories.get(item.category_id) : undefined;
              return (
                <li key={item.id} className="flex items-center gap-3">
                  <CategoryIcon
                    icon={item.type === "income" ? "wallet" : (category?.icon ?? "repeat")}
                    color={item.type === "income" ? "#1f8a5b" : (category?.color ?? "#64748b")}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{item.description}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatRelativeDue(item.due_on)} · {FREQUENCY_LABEL[item.frequency]}
                    </p>
                  </div>
                  <Amount value={item.amount} type={item.type} className="text-sm" />
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
