"use client";

import { Receipt } from "lucide-react";
import Link from "next/link";
import { Amount } from "@/components/shared/amount";
import { CategoryIcon } from "@/components/shared/category-icon";
import { EmptyState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatShortDate } from "@/lib/format";
import { useCategoryMap } from "@/lib/queries";
import type { Transaction } from "@/lib/types";

export function RecentTransactions({ transactions }: { transactions: Transaction[] }) {
  const categories = useCategoryMap();
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Recent activity</CardTitle>
        <Button asChild variant="ghost" size="sm">
          <Link href="/app/transactions">All transactions</Link>
        </Button>
      </CardHeader>
      <CardContent className="flex-1">
        {transactions.length === 0 ? (
          <EmptyState
            icon={Receipt}
            title="No transactions yet"
            description="Record your first expense or income to get started."
          />
        ) : (
          <ul className="grid gap-4">
            {transactions.map((tx) => {
              const category = tx.category_id ? categories.get(tx.category_id) : undefined;
              return (
                <li key={tx.id} className="flex items-center gap-3">
                  <CategoryIcon
                    icon={tx.type === "income" ? "wallet" : (category?.icon ?? "tag")}
                    color={tx.type === "income" ? "#1f8a5b" : (category?.color ?? "#64748b")}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{tx.description}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {formatShortDate(tx.occurred_on)}
                      {category ? ` · ${category.name}` : tx.type === "income" ? " · Income" : ""}
                    </p>
                  </div>
                  <Amount value={tx.amount} type={tx.type} className="text-sm" />
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
