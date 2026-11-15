"use client";

import { Lock, MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { BudgetBar, HEALTH_LABEL, HEALTH_TEXT } from "@/components/shared/budget-bar";
import { CategoryIcon } from "@/components/shared/category-icon";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { formatMoney, formatPercent, toNumber } from "@/lib/format";
import type { BudgetStatus, Category } from "@/lib/types";
import { cn } from "@/lib/utils";

export function CategoryCard({
  category,
  status,
  onEdit,
  onDelete,
}: {
  category: Category;
  status?: BudgetStatus;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <li className="flex flex-col gap-4 rounded-xl border bg-card p-5">
      <div className="flex items-start gap-3">
        <CategoryIcon icon={category.icon} color={category.color} />
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-2 font-medium">
            <span className="truncate">{category.name}</span>
            {category.is_system ? (
              <Lock className="size-3.5 text-muted-foreground" aria-label="System category" />
            ) : null}
          </p>
          <p className="text-sm text-muted-foreground tabular">
            {category.monthly_limit
              ? `${formatMoney(category.monthly_limit, { whole: true })} a month`
              : "No monthly limit"}
          </p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon-sm" aria-label={`Actions for ${category.name}`}>
              <MoreHorizontal />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onSelect={onEdit}>
              <Pencil /> {category.monthly_limit ? "Edit" : "Edit or set limit"}
            </DropdownMenuItem>
            {!category.is_system ? (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem variant="destructive" onSelect={onDelete}>
                  <Trash2 /> Delete
                </DropdownMenuItem>
              </>
            ) : null}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      {status ? (
        <div>
          <div className="mb-2 flex items-baseline justify-between text-sm">
            <span className="tabular">
              <span className="font-semibold">{formatMoney(status.spent, { whole: true })}</span>
              <span className="text-muted-foreground"> spent</span>
            </span>
            <Badge
              variant={status.health === "ok" ? "success" : status.health === "warning" ? "warning" : "danger"}
            >
              {HEALTH_LABEL[status.health]}
            </Badge>
          </div>
          <BudgetBar
            percent={toNumber(status.percent_used)}
            health={status.health}
            label={`${category.name} budget`}
          />
          <p className="mt-2 text-xs text-muted-foreground tabular">
            <span className={cn("font-medium", HEALTH_TEXT[status.health])}>
              {formatPercent(status.percent_used)}
            </span>{" "}
            used ·{" "}
            {toNumber(status.remaining) >= 0
              ? `${formatMoney(status.remaining, { whole: true })} left`
              : `${formatMoney(-toNumber(status.remaining), { whole: true })} over`}
          </p>
        </div>
      ) : (
        <Button variant="outline" size="sm" className="w-fit" onClick={onEdit}>
          Set a monthly limit
        </Button>
      )}
    </li>
  );
}
