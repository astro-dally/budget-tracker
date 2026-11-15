import { formatMoney, formatNumber, formatPercent } from "@/lib/format";
import type { CellValue, ColumnKind } from "@/lib/types";

/** Format a report cell according to its column kind; empty values render as a dash. */
export function formatCell(value: CellValue | undefined, kind: ColumnKind): string {
  if (value === undefined || value === "") return "—";
  switch (kind) {
    case "money":
      return formatMoney(value);
    case "percent":
      return formatPercent(value);
    case "number":
      return formatNumber(value);
    default:
      return String(value);
  }
}
