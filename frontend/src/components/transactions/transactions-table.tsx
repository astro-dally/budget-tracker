"use client";

import { MoreHorizontal, Pencil, Repeat, Trash2 } from "lucide-react";
import { Amount } from "@/components/shared/amount";
import { CategoryLabel } from "@/components/shared/category-icon";
import { SortHeader } from "@/components/transactions/sort-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDate, formatShortDate } from "@/lib/format";
import type { Category, SortDirection, SortField, Transaction } from "@/lib/types";

export function TransactionsTable({
  transactions,
  categories,
  sortBy,
  direction,
  onSort,
  onEdit,
  onDelete,
}: {
  transactions: Transaction[];
  categories: Map<string, Category>;
  sortBy: SortField;
  direction: SortDirection;
  onSort: (field: SortField) => void;
  onEdit: (transaction: Transaction) => void;
  onDelete: (transaction: Transaction) => void;
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow className="hover:bg-transparent">
          <SortHeader field="occurred_on" label="Date" sortBy={sortBy} direction={direction} onSort={onSort} className="hidden md:table-cell" />
          <SortHeader field="description" label="Description" sortBy={sortBy} direction={direction} onSort={onSort} />
          <TableHead className="hidden md:table-cell">Category</TableHead>
          <SortHeader field="amount" label="Amount" sortBy={sortBy} direction={direction} onSort={onSort} className="text-right [&>button]:flex-row-reverse" />
          <TableHead className="w-12">
            <span className="sr-only">Actions</span>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {transactions.map((tx) => {
          const category = tx.category_id ? categories.get(tx.category_id) : undefined;
          return (
            <TableRow key={tx.id}>
              <TableCell className="hidden whitespace-nowrap text-muted-foreground md:table-cell tabular">
                {formatDate(tx.occurred_on)}
              </TableCell>
              <TableCell className="max-w-72">
                <div className="flex items-center gap-2">
                  <span className="truncate font-medium">{tx.description}</span>
                  {tx.recurring_id ? (
                    <Repeat className="size-3.5 shrink-0 text-muted-foreground" aria-label="Recurring" />
                  ) : null}
                  {tx.category_source === "auto" && tx.type === "expense" ? (
                    <Badge variant="secondary" className="hidden sm:inline-flex" title="Category chosen automatically">
                      Auto
                    </Badge>
                  ) : null}
                </div>
                <p className="mt-0.5 truncate text-xs text-muted-foreground md:hidden">
                  {formatShortDate(tx.occurred_on)}
                  {category ? ` · ${category.name}` : ""}
                </p>
              </TableCell>
              <TableCell className="hidden md:table-cell">
                {category ? (
                  <CategoryLabel name={category.name} color={category.color} />
                ) : (
                  <span className="text-muted-foreground">{tx.type === "income" ? "Income" : "—"}</span>
                )}
              </TableCell>
              <TableCell className="text-right whitespace-nowrap">
                <Amount value={tx.amount} type={tx.type} />
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon-sm" aria-label={`Actions for ${tx.description}`}>
                      <MoreHorizontal />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onSelect={() => onEdit(tx)}>
                      <Pencil /> Edit
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem variant="destructive" onSelect={() => onDelete(tx)}>
                      <Trash2 /> Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
