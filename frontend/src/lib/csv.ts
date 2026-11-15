import type { CellValue, ReportColumn } from "@/lib/types";

function escape(value: CellValue | undefined): string {
  const text = value === undefined ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/** Build RFC 4180 CSV text from report columns and rows. */
export function toCsv(columns: ReportColumn[], rows: Array<Record<string, CellValue>>): string {
  const header = columns.map((column) => escape(column.label)).join(",");
  const lines = rows.map((row) => columns.map((column) => escape(row[column.key])).join(","));
  return [header, ...lines].join("\n");
}

/** Trigger a browser download of `content` as a CSV file. */
export function downloadCsv(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
