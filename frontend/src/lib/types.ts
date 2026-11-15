/**
 * Types mirroring the backend's Pydantic schemas. Decimal amounts arrive as
 * strings (no precision loss over JSON) and are only converted to numbers
 * for display and charts.
 */

export type DecimalString = string;
export type IsoDate = string;
export type TransactionType = "income" | "expense";
export type CategorySource = "manual" | "auto";
export type Frequency = "daily" | "weekly" | "monthly";
export type AlertLevel = "warning" | "critical";
export type BudgetHealth = "ok" | "warning" | "exceeded";
export type SortField = "occurred_on" | "amount" | "description";
export type SortDirection = "asc" | "desc";

export interface Transaction {
  id: string;
  type: TransactionType;
  amount: DecimalString;
  description: string;
  occurred_on: IsoDate;
  category_id: string | null;
  category_source: CategorySource;
  recurring_id: string | null;
}

export interface TransactionPage {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface TransactionInput {
  type: TransactionType;
  amount: DecimalString;
  description: string;
  occurred_on: IsoDate;
  category_id: string | null;
}

export interface TransactionFilters {
  page: number;
  page_size: number;
  type?: TransactionType;
  category_id?: string;
  search?: string;
  month?: string;
  sort_by: SortField;
  sort_direction: SortDirection;
}

export interface Category {
  id: string;
  name: string;
  color: string;
  icon: string;
  is_system: boolean;
  monthly_limit: DecimalString | null;
}

export interface CategoryInput {
  name: string;
  color: string;
  icon: string;
  monthly_limit: DecimalString | null;
}

export interface BudgetStatus {
  category_id: string;
  category_name: string;
  color: string;
  icon: string;
  period: string;
  limit: DecimalString;
  spent: DecimalString;
  remaining: DecimalString;
  percent_used: DecimalString;
  health: BudgetHealth;
}

export interface Rule {
  id: string;
  keyword: string;
  category_id: string;
}

export interface RuleInput {
  keyword: string;
  category_id: string;
}

export interface Suggestion {
  category_id: string;
  category_name: string;
  color: string;
  icon: string;
  matched_by: "keyword" | "merchant" | "user_defined" | "default";
  reason: string;
}

export interface RecurringPayment {
  id: string;
  description: string;
  amount: DecimalString;
  type: TransactionType;
  frequency: Frequency;
  start_date: IsoDate;
  end_date: IsoDate | null;
  category_id: string | null;
  is_active: boolean;
  last_generated_on: IsoDate | null;
  next_due: IsoDate | null;
}

export interface RecurringInput {
  description: string;
  amount: DecimalString;
  type: TransactionType;
  frequency: Frequency;
  start_date: IsoDate;
  end_date: IsoDate | null;
  category_id: string | null;
}

export type ColumnKind = "text" | "money" | "percent" | "number";
export type CellValue = string | number;

export interface ReportType {
  key: string;
  title: string;
  description: string;
}

export interface ReportColumn {
  key: string;
  label: string;
  kind: ColumnKind;
}

export interface ReportMetric {
  label: string;
  value: CellValue;
  kind: ColumnKind;
}

export interface ChartSpec {
  kind: "bar" | "pie" | "line";
  x_key: string;
  y_keys: string[];
}

export interface Report {
  key: string;
  title: string;
  period: string;
  columns: ReportColumn[];
  rows: Array<Record<string, CellValue>>;
  metrics: ReportMetric[];
  chart: ChartSpec | null;
}

export interface Alert {
  id: string;
  category_id: string;
  category_name: string;
  period: string;
  level: AlertLevel;
  threshold: DecimalString;
  message: string;
  spent: DecimalString;
  limit: DecimalString;
  created_at: string;
  is_read: boolean;
}

export interface CategorySpend {
  category_id: string;
  name: string;
  color: string;
  amount: DecimalString;
}

export interface TrendPoint {
  period: string;
  income: DecimalString;
  expenses: DecimalString;
}

export interface UpcomingPayment {
  id: string;
  description: string;
  amount: DecimalString;
  type: TransactionType;
  frequency: Frequency;
  category_id: string | null;
  due_on: IsoDate;
}

export interface Dashboard {
  period: string;
  income: DecimalString;
  expenses: DecimalString;
  balance: DecimalString;
  budget_total: DecimalString;
  budget_spent: DecimalString;
  budget_used_percent: DecimalString;
  days_elapsed: number;
  days_in_month: number;
  spending_by_category: CategorySpend[];
  trend: TrendPoint[];
  budgets: BudgetStatus[];
  recent: Transaction[];
  upcoming: UpcomingPayment[];
}

export interface ApiErrorDetail {
  field: string;
  message: string;
}

export interface ApiErrorBody {
  error: { code: string; message: string; details: ApiErrorDetail[] };
}

export type UserRole = "user" | "admin";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  user: User;
}

export interface DemoAccount {
  name: string;
  email: string;
  password: string;
  role: UserRole;
  tagline: string;
}

export interface DailyCount {
  day: IsoDate;
  count: number;
}

export interface PlatformOverview {
  total_users: number;
  active_users: number;
  admins: number;
  new_users_7d: number;
  transactions: number;
  expense_volume: DecimalString;
  alerts_30d: number;
  signups_by_day: DailyCount[];
  activity_by_day: DailyCount[];
}

export interface AdminUser extends User {
  transaction_count: number;
  category_count: number;
  last_transaction_on: IsoDate | null;
}

export interface AdminUserUpdate {
  is_active?: boolean;
  role?: UserRole;
}
