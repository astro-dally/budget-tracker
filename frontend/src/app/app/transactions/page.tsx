"use client";

import { ChevronLeft, ChevronRight, Plus, Receipt, Search, SearchX } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { CategorySelect } from "@/components/shared/category-select";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { NEW_TRANSACTION_HASH } from "@/components/layout/command-palette";
import { TransactionFormDialog } from "@/components/transactions/transaction-form-dialog";
import { TransactionsTable } from "@/components/transactions/transactions-table";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { errorMessage } from "@/lib/api";
import { formatMonth, formatNumber } from "@/lib/format";
import { recentMonths } from "@/lib/month";
import { useCategories, useCategoryMap, useDeleteTransaction, useTransactions } from "@/lib/queries";
import type { SortField, Transaction, TransactionFilters, TransactionType } from "@/lib/types";

const ALL = "all";
const PAGE_SIZE = 15;

export default function TransactionsPage() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 300);
  const [filters, setFilters] = useState<Omit<TransactionFilters, "search">>({
    page: 1,
    page_size: PAGE_SIZE,
    sort_by: "occurred_on",
    sort_direction: "desc",
  });
  const query: TransactionFilters = { ...filters, search: debouncedSearch.trim() || undefined };
  const { data, error, isPending, isFetching, refetch } = useTransactions(query);
  const categoryList = useCategories().data ?? [];
  const categories = useCategoryMap();
  const remove = useDeleteTransaction();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Transaction | undefined>();
  const [deleting, setDeleting] = useState<Transaction | undefined>();

  // Opened from the command palette ("Add transaction") via /app/transactions#new.
  useEffect(() => {
    const openFromHash = () => {
      if (window.location.hash === NEW_TRANSACTION_HASH) {
        setEditing(undefined);
        setFormOpen(true);
        window.history.replaceState(null, "", window.location.pathname);
      }
    };
    openFromHash();
    window.addEventListener("hashchange", openFromHash);
    return () => window.removeEventListener("hashchange", openFromHash);
  }, []);

  const update = (patch: Partial<TransactionFilters>) =>
    setFilters((current) => ({ ...current, page: 1, ...patch }));

  const onSort = (field: SortField) =>
    setFilters((current) => ({
      ...current,
      sort_by: field,
      sort_direction:
        current.sort_by === field && current.sort_direction === "desc" ? "asc" : "desc",
    }));

  const hasFilters = Boolean(query.search || filters.type || filters.category_id || filters.month);
  const first = data && data.total > 0 ? (data.page - 1) * data.page_size + 1 : 0;
  const last = data ? Math.min(data.page * data.page_size, data.total) : 0;

  return (
    <div className="grid gap-6">
      <PageHeader
        title="Transactions"
        description="Every expense and income, searchable and editable."
        actions={
          <Button
            onClick={() => {
              setEditing(undefined);
              setFormOpen(true);
            }}
          >
            <Plus /> Add transaction
          </Button>
        }
      />

      <Card className="overflow-hidden">
        <div className="flex flex-col gap-3 border-b p-4 sm:px-6 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              type="search"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setFilters((c) => ({ ...c, page: 1 }));
              }}
              placeholder="Search descriptions"
              aria-label="Search transactions"
              className="pl-9"
            />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:flex">
            <Select
              value={filters.type ?? ALL}
              onValueChange={(v) => update({ type: v === ALL ? undefined : (v as TransactionType) })}
            >
              <SelectTrigger aria-label="Filter by type" className="lg:w-36">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>All types</SelectItem>
                <SelectItem value="expense">Expenses</SelectItem>
                <SelectItem value="income">Income</SelectItem>
              </SelectContent>
            </Select>
            <div className="lg:w-48">
              <CategorySelect
                label="Filter by category"
                value={filters.category_id ?? ALL}
                onChange={(v) => update({ category_id: v === ALL ? undefined : v })}
                categories={categoryList}
                special={{ value: ALL, label: "All categories" }}
              />
            </div>
            <Select
              value={filters.month ?? ALL}
              onValueChange={(v) => update({ month: v === ALL ? undefined : v })}
            >
              <SelectTrigger aria-label="Filter by month" className="lg:w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>All months</SelectItem>
                {recentMonths(12).map((m) => (
                  <SelectItem key={m} value={m}>
                    {formatMonth(m)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {isPending ? (
          <div className="grid gap-3 p-6" aria-busy="true" aria-label="Loading transactions">
            {Array.from({ length: 8 }, (_, i) => (
              <Skeleton key={i} className="h-10" />
            ))}
          </div>
        ) : error ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : data.items.length === 0 ? (
          hasFilters ? (
            <EmptyState
              icon={SearchX}
              title="No matching transactions"
              description="Try a different search term or clear the filters."
              action={
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSearch("");
                    update({ type: undefined, category_id: undefined, month: undefined });
                  }}
                >
                  Clear filters
                </Button>
              }
            />
          ) : (
            <EmptyState
              icon={Receipt}
              title="No transactions yet"
              description="Add your first expense or income to start tracking."
              action={
                <Button size="sm" onClick={() => setFormOpen(true)}>
                  <Plus /> Add transaction
                </Button>
              }
            />
          )
        ) : (
          <div className={isFetching ? "opacity-70 transition-opacity" : undefined}>
            <TransactionsTable
              transactions={data.items}
              categories={categories}
              sortBy={filters.sort_by}
              direction={filters.sort_direction}
              onSort={onSort}
              onEdit={(tx) => {
                setEditing(tx);
                setFormOpen(true);
              }}
              onDelete={setDeleting}
            />
            <div className="flex items-center justify-between gap-4 border-t px-5 py-3 text-sm text-muted-foreground sm:px-6">
              <span className="tabular">
                {formatNumber(first)}–{formatNumber(last)} of {formatNumber(data.total)}
              </span>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon-sm"
                  aria-label="Previous page"
                  disabled={data.page <= 1}
                  onClick={() => setFilters((c) => ({ ...c, page: c.page - 1 }))}
                >
                  <ChevronLeft />
                </Button>
                <span className="px-2 tabular">
                  Page {data.page} of {data.pages}
                </span>
                <Button
                  variant="outline"
                  size="icon-sm"
                  aria-label="Next page"
                  disabled={data.page >= data.pages}
                  onClick={() => setFilters((c) => ({ ...c, page: c.page + 1 }))}
                >
                  <ChevronRight />
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>

      <TransactionFormDialog open={formOpen} onOpenChange={setFormOpen} transaction={editing} />
      <ConfirmDialog
        open={Boolean(deleting)}
        onOpenChange={(open) => !open && setDeleting(undefined)}
        title="Delete this transaction?"
        description={`“${deleting?.description ?? ""}” will be removed and budgets recalculated. This can't be undone.`}
        confirmLabel="Delete transaction"
        onConfirm={() => {
          if (!deleting) return;
          remove.mutate(deleting.id, {
            onSuccess: () => toast.success("Transaction deleted"),
            onError: (e) => toast.error("Couldn't delete", { description: errorMessage(e) }),
          });
          setDeleting(undefined);
        }}
      />
    </div>
  );
}
