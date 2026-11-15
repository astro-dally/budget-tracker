/** Formatting helpers. All amounts use one currency and locale from env. */

const CURRENCY = process.env.NEXT_PUBLIC_CURRENCY ?? "INR";
const LOCALE = process.env.NEXT_PUBLIC_LOCALE ?? "en-IN";

const moneyFormat = new Intl.NumberFormat(LOCALE, {
  style: "currency",
  currency: CURRENCY,
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const wholeMoneyFormat = new Intl.NumberFormat(LOCALE, {
  style: "currency",
  currency: CURRENCY,
  maximumFractionDigits: 0,
});

const compactMoneyFormat = new Intl.NumberFormat(LOCALE, {
  style: "currency",
  currency: CURRENCY,
  notation: "compact",
  maximumFractionDigits: 1,
});

const numberFormat = new Intl.NumberFormat(LOCALE);

export function toNumber(value: string | number | null | undefined): number {
  const parsed = typeof value === "number" ? value : Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function formatMoney(value: string | number, options: { whole?: boolean } = {}): string {
  return (options.whole ? wholeMoneyFormat : moneyFormat).format(toNumber(value));
}

export function formatCompactMoney(value: string | number): string {
  return compactMoneyFormat.format(toNumber(value));
}

export function formatNumber(value: string | number): string {
  return numberFormat.format(toNumber(value));
}

export function formatPercent(value: string | number): string {
  const n = toNumber(value);
  return `${n.toLocaleString(LOCALE, { maximumFractionDigits: n < 10 ? 1 : 0 })}%`;
}

/** Parse YYYY-MM-DD as a local date (no timezone shift). */
export function parseIsoDate(iso: string): Date {
  const [year, month, day] = iso.split("-").map(Number);
  return new Date(year ?? 1970, (month ?? 1) - 1, day ?? 1);
}

export function formatDate(iso: string): string {
  return parseIsoDate(iso).toLocaleDateString(LOCALE, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatShortDate(iso: string): string {
  return parseIsoDate(iso).toLocaleDateString(LOCALE, { day: "numeric", month: "short" });
}

export function formatMonth(month: string, style: "long" | "short" = "long"): string {
  const [year, m] = month.split("-").map(Number);
  return new Date(year ?? 1970, (m ?? 1) - 1, 1).toLocaleDateString(LOCALE, {
    month: style,
    year: "numeric",
  });
}

export function formatMonthName(month: string): string {
  const [year, m] = month.split("-").map(Number);
  return new Date(year ?? 1970, (m ?? 1) - 1, 1).toLocaleDateString(LOCALE, { month: "long" });
}

export function formatRelativeDue(iso: string, today: Date = new Date()): string {
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const days = Math.round((parseIsoDate(iso).getTime() - start.getTime()) / 86_400_000);
  if (days === 0) return "Due today";
  if (days === 1) return "Due tomorrow";
  if (days > 1 && days <= 7) return `Due in ${days} days`;
  return `Due ${formatShortDate(iso)}`;
}

export function formatTimeAgo(isoTimestamp: string, now: Date = new Date()): string {
  const seconds = Math.max(0, Math.round((now.getTime() - new Date(isoTimestamp).getTime()) / 1000));
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  return days === 1 ? "yesterday" : `${days} days ago`;
}

export const FREQUENCY_LABEL = { daily: "Daily", weekly: "Weekly", monthly: "Monthly" } as const;
