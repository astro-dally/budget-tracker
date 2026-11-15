/**
 * The single typed API client. Every request goes through `request`, so
 * error handling (the backend's `{error: {...}}` envelope, network failures)
 * lives in exactly one place.
 */
import { session } from "@/lib/session";
import type {
  AdminUser,
  AdminUserUpdate,
  Alert,
  ApiErrorBody,
  ApiErrorDetail,
  BudgetStatus,
  Category,
  CategoryInput,
  AuthResponse,
  Dashboard,
  DemoAccount,
  PlatformOverview,
  RecurringInput,
  RecurringPayment,
  Report,
  ReportType,
  Rule,
  RuleInput,
  Suggestion,
  Transaction,
  TransactionFilters,
  TransactionInput,
  TransactionPage,
  User,
} from "@/lib/types";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

const API_ROOT = `${API_BASE_URL}/api/v1`;

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details: ApiErrorDetail[] = [],
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type QueryValue = string | number | boolean | null | undefined;
type Query = Record<string, QueryValue>;
type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

function buildUrl(path: string, query?: Query): string {
  const url = new URL(`${API_ROOT}${path}`);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

function isErrorBody(value: unknown): value is ApiErrorBody {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as ApiErrorBody).error?.message === "string"
  );
}

async function toApiError(response: Response): Promise<ApiError> {
  const body: unknown = await response.json().catch(() => null);
  if (isErrorBody(body)) {
    return new ApiError(response.status, body.error.code, body.error.message, body.error.details);
  }
  return new ApiError(response.status, "http_error", `Request failed with status ${response.status}`);
}

async function send(method: Method, path: string, query?: Query, body?: unknown): Promise<Response> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = session.getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      0,
      "network_error",
      `Can't reach the server at ${API_BASE_URL}. Start the backend and try again.`,
    );
  }
  if (!response.ok) {
    const error = await toApiError(response);
    // An expired or revoked session anywhere outside the sign-in calls signs the user out.
    if (response.status === 401 && token && !path.startsWith("/auth/login")) {
      session.notifyExpired();
    }
    throw error;
  }
  return response;
}

async function json<T>(method: Method, path: string, query?: Query, body?: unknown): Promise<T> {
  const response = await send(method, path, query, body);
  return (await response.json()) as T;
}

async function empty(method: Method, path: string): Promise<void> {
  await send(method, path);
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      json<AuthResponse>("POST", "/auth/login", undefined, { email, password }),
    register: (name: string, email: string, password: string) =>
      json<AuthResponse>("POST", "/auth/register", undefined, { name, email, password }),
    me: () => json<User>("GET", "/auth/me"),
    demoAccounts: () => json<DemoAccount[]>("GET", "/auth/demo-accounts"),
  },

  admin: {
    overview: () => json<PlatformOverview>("GET", "/admin/overview"),
    users: () => json<AdminUser[]>("GET", "/admin/users"),
    updateUser: (id: string, update: AdminUserUpdate) =>
      json<AdminUser>("PATCH", `/admin/users/${id}`, undefined, update),
  },

  dashboard: (month: string) => json<Dashboard>("GET", "/dashboard", { month }),

  transactions: {
    list: (filters: TransactionFilters) =>
      json<TransactionPage>("GET", "/transactions", { ...filters }),
    create: (input: TransactionInput) => json<Transaction>("POST", "/transactions", undefined, input),
    update: (id: string, input: TransactionInput) =>
      json<Transaction>("PUT", `/transactions/${id}`, undefined, input),
    remove: (id: string) => empty("DELETE", `/transactions/${id}`),
  },

  categories: {
    list: () => json<Category[]>("GET", "/categories"),
    create: (input: CategoryInput) => json<Category>("POST", "/categories", undefined, input),
    update: (id: string, input: CategoryInput) =>
      json<Category>("PUT", `/categories/${id}`, undefined, input),
    remove: (id: string) => empty("DELETE", `/categories/${id}`),
  },

  budgets: {
    list: (month: string) => json<BudgetStatus[]>("GET", "/budgets", { month }),
  },

  rules: {
    list: () => json<Rule[]>("GET", "/rules"),
    create: (input: RuleInput) => json<Rule>("POST", "/rules", undefined, input),
    remove: (id: string) => empty("DELETE", `/rules/${id}`),
  },

  categorize: {
    suggest: (description: string) =>
      json<Suggestion>("GET", "/categorize/suggest", { description }),
  },

  recurring: {
    list: () => json<RecurringPayment[]>("GET", "/recurring"),
    create: (input: RecurringInput) =>
      json<RecurringPayment>("POST", "/recurring", undefined, input),
    pause: (id: string) => json<RecurringPayment>("POST", `/recurring/${id}/pause`),
    resume: (id: string) => json<RecurringPayment>("POST", `/recurring/${id}/resume`),
    remove: (id: string) => empty("DELETE", `/recurring/${id}`),
  },

  reports: {
    types: () => json<ReportType[]>("GET", "/reports"),
    get: (type: string, month: string) => json<Report>("GET", `/reports/${type}`, { month }),
  },

  alerts: {
    list: (unreadOnly = false, limit = 50) =>
      json<Alert[]>("GET", "/alerts", { unread_only: unreadOnly, limit }),
    unreadCount: () => json<{ count: number }>("GET", "/alerts/unread-count"),
    markRead: (id: string) => empty("POST", `/alerts/${id}/read`),
    markAllRead: () => json<{ updated: number }>("POST", "/alerts/read-all"),
    /** EventSource can't send headers, so the token travels as a query parameter. */
    streamUrl: (token: string) =>
      `${API_ROOT}/alerts/stream?token=${encodeURIComponent(token)}`,
  },
} as const;

/** Human-readable message for any thrown value. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}
