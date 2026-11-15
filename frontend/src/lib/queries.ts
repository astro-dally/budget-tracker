"use client";

/**
 * TanStack Query hooks: one place that knows cache keys, invalidation and
 * optimistic updates. Components never call `api` directly.
 */
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";
import { useMemo } from "react";
import { api } from "@/lib/api";
import type {
  AdminUser,
  AdminUserUpdate,
  Alert,
  Category,
  CategoryInput,
  RecurringInput,
  RecurringPayment,
  RuleInput,
  TransactionFilters,
  TransactionInput,
  TransactionPage,
} from "@/lib/types";

export const queryKeys = {
  dashboard: (month: string) => ["dashboard", month] as const,
  transactions: (filters: TransactionFilters) => ["transactions", filters] as const,
  categories: ["categories"] as const,
  budgets: (month: string) => ["budgets", month] as const,
  rules: ["rules"] as const,
  recurring: ["recurring"] as const,
  reportTypes: ["report-types"] as const,
  report: (type: string, month: string) => ["report", type, month] as const,
  alerts: (unreadOnly: boolean) => ["alerts", "list", unreadOnly] as const,
  unreadCount: ["alerts", "unread-count"] as const,
  suggestion: (description: string) => ["suggestion", description] as const,
};

/** Anything that changes money movements can change these views. */
export function invalidateMoneyViews(client: QueryClient): Promise<void[]> {
  return Promise.all(
    [["transactions"], ["dashboard"], ["budgets"], ["report"], ["alerts"], ["recurring"]].map(
      (queryKey) => client.invalidateQueries({ queryKey }),
    ),
  );
}

// --- Queries -------------------------------------------------------------------

export function useDashboard(month: string) {
  return useQuery({ queryKey: queryKeys.dashboard(month), queryFn: () => api.dashboard(month) });
}

export function useTransactions(filters: TransactionFilters) {
  return useQuery({
    queryKey: queryKeys.transactions(filters),
    queryFn: () => api.transactions.list(filters),
    placeholderData: keepPreviousData,
  });
}

export function useCategories() {
  return useQuery({ queryKey: queryKeys.categories, queryFn: api.categories.list });
}

export function useCategoryMap(): Map<string, Category> {
  const { data } = useCategories();
  return useMemo(() => new Map((data ?? []).map((c) => [c.id, c])), [data]);
}

export function useBudgets(month: string) {
  return useQuery({ queryKey: queryKeys.budgets(month), queryFn: () => api.budgets.list(month) });
}

export function useRules() {
  return useQuery({ queryKey: queryKeys.rules, queryFn: api.rules.list });
}

export function useRecurring() {
  return useQuery({ queryKey: queryKeys.recurring, queryFn: api.recurring.list });
}

export function useReportTypes() {
  return useQuery({
    queryKey: queryKeys.reportTypes,
    queryFn: api.reports.types,
    staleTime: Infinity,
  });
}

export function useReport(type: string | undefined, month: string) {
  return useQuery({
    queryKey: queryKeys.report(type ?? "", month),
    queryFn: () => api.reports.get(type ?? "", month),
    enabled: Boolean(type),
    placeholderData: keepPreviousData,
  });
}

export function useAlerts(unreadOnly = false) {
  return useQuery({
    queryKey: queryKeys.alerts(unreadOnly),
    queryFn: () => api.alerts.list(unreadOnly, 100),
  });
}

export function useUnreadCount() {
  return useQuery({ queryKey: queryKeys.unreadCount, queryFn: api.alerts.unreadCount });
}

export function useSuggestion(description: string, enabled: boolean) {
  const trimmed = description.trim();
  return useQuery({
    queryKey: queryKeys.suggestion(trimmed.toLowerCase()),
    queryFn: () => api.categorize.suggest(trimmed),
    enabled: enabled && trimmed.length >= 2,
    staleTime: 30_000,
    retry: false,
  });
}

// --- Mutations -----------------------------------------------------------------

export function useSaveTransaction() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id?: string; input: TransactionInput }) =>
      id ? api.transactions.update(id, input) : api.transactions.create(input),
    onSettled: () => invalidateMoneyViews(client),
  });
}

export function useDeleteTransaction() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.transactions.remove(id),
    onMutate: async (id) => {
      await client.cancelQueries({ queryKey: ["transactions"] });
      const snapshots = client.getQueriesData<TransactionPage>({ queryKey: ["transactions"] });
      client.setQueriesData<TransactionPage>({ queryKey: ["transactions"] }, (page) =>
        page
          ? { ...page, total: page.total - 1, items: page.items.filter((t) => t.id !== id) }
          : page,
      );
      return { snapshots };
    },
    onError: (_error, _id, context) => {
      context?.snapshots.forEach(([key, data]) => client.setQueryData(key, data));
    },
    onSettled: () => invalidateMoneyViews(client),
  });
}

export function useSaveCategory() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id?: string; input: CategoryInput }) =>
      id ? api.categories.update(id, input) : api.categories.create(input),
    onSettled: async () => {
      await client.invalidateQueries({ queryKey: queryKeys.categories });
      await invalidateMoneyViews(client);
    },
  });
}

export function useDeleteCategory() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.categories.remove(id),
    onMutate: async (id) => {
      await client.cancelQueries({ queryKey: queryKeys.categories });
      const previous = client.getQueryData<Category[]>(queryKeys.categories);
      client.setQueryData<Category[]>(queryKeys.categories, (list) =>
        list?.filter((c) => c.id !== id),
      );
      return { previous };
    },
    onError: (_error, _id, context) => {
      client.setQueryData(queryKeys.categories, context?.previous);
    },
    onSettled: async () => {
      await client.invalidateQueries({ queryKey: queryKeys.categories });
      await client.invalidateQueries({ queryKey: queryKeys.rules });
      await invalidateMoneyViews(client);
    },
  });
}

export function useCreateRule() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: RuleInput) => api.rules.create(input),
    onSettled: () => client.invalidateQueries({ queryKey: queryKeys.rules }),
  });
}

export function useDeleteRule() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.rules.remove(id),
    onSettled: () => client.invalidateQueries({ queryKey: queryKeys.rules }),
  });
}

export function useCreateRecurring() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: RecurringInput) => api.recurring.create(input),
    onSettled: () => invalidateMoneyViews(client),
  });
}

function patchRecurring(
  client: QueryClient,
  update: (list: RecurringPayment[]) => RecurringPayment[],
) {
  client.setQueryData<RecurringPayment[]>(queryKeys.recurring, (list) =>
    list ? update(list) : list,
  );
}

export function useToggleRecurring() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      active ? api.recurring.resume(id) : api.recurring.pause(id),
    onMutate: async ({ id, active }) => {
      await client.cancelQueries({ queryKey: queryKeys.recurring });
      const previous = client.getQueryData<RecurringPayment[]>(queryKeys.recurring);
      patchRecurring(client, (list) =>
        list.map((p) => (p.id === id ? { ...p, is_active: active } : p)),
      );
      return { previous };
    },
    onError: (_error, _vars, context) => client.setQueryData(queryKeys.recurring, context?.previous),
    onSettled: () => invalidateMoneyViews(client),
  });
}

export function useDeleteRecurring() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.recurring.remove(id),
    onMutate: async (id) => {
      await client.cancelQueries({ queryKey: queryKeys.recurring });
      const previous = client.getQueryData<RecurringPayment[]>(queryKeys.recurring);
      patchRecurring(client, (list) => list.filter((p) => p.id !== id));
      return { previous };
    },
    onError: (_error, _id, context) => client.setQueryData(queryKeys.recurring, context?.previous),
    onSettled: () => invalidateMoneyViews(client),
  });
}

function markAlertsRead(client: QueryClient, predicate: (alert: Alert) => boolean) {
  client.setQueriesData<Alert[]>({ queryKey: ["alerts", "list"] }, (list) =>
    list?.map((a) => (predicate(a) ? { ...a, is_read: true } : a)),
  );
}

export function useMarkAlertRead() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.alerts.markRead(id),
    onMutate: async (id) => {
      await client.cancelQueries({ queryKey: ["alerts"] });
      markAlertsRead(client, (a) => a.id === id);
      client.setQueryData<{ count: number }>(queryKeys.unreadCount, (c) =>
        c ? { count: Math.max(0, c.count - 1) } : c,
      );
    },
    onSettled: () => client.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

export function useMarkAllAlertsRead() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.alerts.markAllRead,
    onMutate: async () => {
      await client.cancelQueries({ queryKey: ["alerts"] });
      markAlertsRead(client, () => true);
      client.setQueryData(queryKeys.unreadCount, { count: 0 });
    },
    onSettled: () => client.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

// --- Admin ---------------------------------------------------------------------

export function useAdminOverview() {
  return useQuery({ queryKey: ["admin", "overview"], queryFn: api.admin.overview });
}

export function useAdminUsers() {
  return useQuery({ queryKey: ["admin", "users"], queryFn: api.admin.users });
}

export function useUpdateAdminUser() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, update }: { id: string; update: AdminUserUpdate }) =>
      api.admin.updateUser(id, update),
    onMutate: async ({ id, update }) => {
      await client.cancelQueries({ queryKey: ["admin", "users"] });
      const previous = client.getQueryData<AdminUser[]>(["admin", "users"]);
      client.setQueryData<AdminUser[]>(["admin", "users"], (list) =>
        list?.map((u) => (u.id === id ? { ...u, ...update } : u)),
      );
      return { previous };
    },
    onError: (_error, _vars, context) => client.setQueryData(["admin", "users"], context?.previous),
    onSettled: () => client.invalidateQueries({ queryKey: ["admin"] }),
  });
}
