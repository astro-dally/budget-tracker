"use client";

import { CategoryLabel } from "@/components/shared/category-icon";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Category } from "@/lib/types";

/** Category picker with an optional leading special option (e.g. "Auto-categorise"). */
export function CategorySelect({
  id,
  value,
  onChange,
  categories,
  special,
  placeholder = "Choose a category",
  invalid,
  describedBy,
  label,
}: {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  categories: Category[];
  special?: { value: string; label: string };
  placeholder?: string;
  invalid?: boolean;
  describedBy?: string;
  label?: string;
}) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger id={id} aria-invalid={invalid} aria-describedby={describedBy} aria-label={label}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {special ? (
          <>
            <SelectItem value={special.value}>{special.label}</SelectItem>
            <SelectSeparator />
          </>
        ) : null}
        {categories.map((c) => (
          <SelectItem key={c.id} value={c.id}>
            <CategoryLabel name={c.name} color={c.color} />
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
