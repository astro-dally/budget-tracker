"use client";

import { Plus, Tags } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { CategoryCard } from "@/components/budgets/category-card";
import { CategoryFormDialog } from "@/components/budgets/category-form-dialog";
import { RulesPanel } from "@/components/budgets/rules-panel";
import { useSelectedMonth } from "@/components/month-context";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { MonthSwitcher } from "@/components/shared/month-switcher";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { errorMessage } from "@/lib/api";
import { formatMoney, toNumber } from "@/lib/format";
import { useBudgets, useCategories, useDeleteCategory } from "@/lib/queries";
import type { Category } from "@/lib/types";

export default function BudgetsPage() {
  const { month } = useSelectedMonth();
  const categories = useCategories();
  const budgets = useBudgets(month);
  const remove = useDeleteCategory();
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Category | undefined>();
  const [deleting, setDeleting] = useState<Category | undefined>();

  const statusById = new Map((budgets.data ?? []).map((s) => [s.category_id, s]));
  const totalLimit = (categories.data ?? []).reduce((sum, c) => sum + toNumber(c.monthly_limit), 0);
  const budgeted = (categories.data ?? []).filter((c) => c.monthly_limit).length;

  const openForm = (category?: Category) => {
    setEditing(category);
    setFormOpen(true);
  };

  return (
    <div className="grid gap-6">
      <PageHeader
        title="Budgets"
        description={
          categories.data
            ? `${budgeted} of ${categories.data.length} categories have a limit, totalling ${formatMoney(totalLimit, { whole: true })} a month.`
            : "Monthly limits per category and the rules that file your expenses."
        }
        actions={
          <>
            <MonthSwitcher />
            <Button onClick={() => openForm()}>
              <Plus /> New category
            </Button>
          </>
        }
      />

      <Tabs defaultValue="categories" className="grid gap-5">
        <TabsList>
          <TabsTrigger value="categories">Categories and limits</TabsTrigger>
          <TabsTrigger value="rules">Keyword rules</TabsTrigger>
        </TabsList>

        <TabsContent value="categories">
          {categories.isPending ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }, (_, i) => (
                <Skeleton key={i} className="h-44 rounded-xl" />
              ))}
            </div>
          ) : categories.error ? (
            <Card>
              <ErrorState error={categories.error} onRetry={() => void categories.refetch()} />
            </Card>
          ) : categories.data.length === 0 ? (
            <Card>
              <EmptyState
                icon={Tags}
                title="No categories yet"
                description="Create categories like Food or Transport and give them monthly limits."
                action={
                  <Button size="sm" onClick={() => openForm()}>
                    <Plus /> New category
                  </Button>
                }
              />
            </Card>
          ) : (
            <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {categories.data.map((category) => (
                <CategoryCard
                  key={category.id}
                  category={category}
                  status={statusById.get(category.id)}
                  onEdit={() => openForm(category)}
                  onDelete={() => setDeleting(category)}
                />
              ))}
            </ul>
          )}
        </TabsContent>

        <TabsContent value="rules">
          <RulesPanel />
        </TabsContent>
      </Tabs>

      <CategoryFormDialog open={formOpen} onOpenChange={setFormOpen} category={editing} />
      <ConfirmDialog
        open={Boolean(deleting)}
        onOpenChange={(open) => !open && setDeleting(undefined)}
        title={`Delete ${deleting?.name ?? "category"}?`}
        description="Its transactions move to Uncategorized, and its limit and keyword rules are removed. This can't be undone."
        confirmLabel="Delete category"
        onConfirm={() => {
          if (!deleting) return;
          const name = deleting.name;
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
