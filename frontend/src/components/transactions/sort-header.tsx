"use client";

import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { TableHead } from "@/components/ui/table";
import type { SortDirection, SortField } from "@/lib/types";
import { cn } from "@/lib/utils";

export function SortHeader({
  field,
  label,
  sortBy,
  direction,
  onSort,
  className,
}: {
  field: SortField;
  label: string;
  sortBy: SortField;
  direction: SortDirection;
  onSort: (field: SortField) => void;
  className?: string;
}) {
  const active = sortBy === field;
  const Icon = !active ? ArrowUpDown : direction === "asc" ? ArrowUp : ArrowDown;
  return (
    <TableHead
      aria-sort={active ? (direction === "asc" ? "ascending" : "descending") : "none"}
      className={className}
    >
      <button
        type="button"
        onClick={() => onSort(field)}
        className={cn(
          "-mx-1 inline-flex items-center gap-1 rounded px-1 py-0.5 outline-none hover:text-foreground focus-visible:ring-[3px] focus-visible:ring-ring/40",
          active && "text-foreground",
        )}
      >
        {label}
        <Icon className="size-3.5" aria-hidden="true" />
      </button>
    </TableHead>
  );
}
