/** Month (YYYY-MM) and date (YYYY-MM-DD) helpers in local time. */

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

export function toMonth(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}`;
}

export function currentMonth(): string {
  return toMonth(new Date());
}

export function shiftMonth(month: string, delta: number): string {
  const [year, m] = month.split("-").map(Number);
  return toMonth(new Date(year ?? 1970, (m ?? 1) - 1 + delta, 1));
}

export function todayIso(): string {
  const now = new Date();
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

export function recentMonths(count: number, from: string = currentMonth()): string[] {
  return Array.from({ length: count }, (_, index) => shiftMonth(from, -index));
}
