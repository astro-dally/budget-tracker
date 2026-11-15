"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Check, Loader2 } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { CATEGORY_COLORS, CATEGORY_ICONS } from "@/components/shared/category-icon";
import { fieldAria, FormField } from "@/components/shared/form-field";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { applyServerErrors } from "@/lib/form-errors";
import { useSaveCategory } from "@/lib/queries";
import { categorySchema, type CategoryFormValues } from "@/lib/schemas";
import type { Category } from "@/lib/types";
import { cn } from "@/lib/utils";

const PICKABLE_ICONS = Object.keys(CATEGORY_ICONS).filter((name) => name !== "circle-help");

function defaults(category?: Category): CategoryFormValues {
  return {
    name: category?.name ?? "",
    color: category?.color ?? CATEGORY_COLORS[0] ?? "#5b6cf0",
    icon: category?.icon ?? "tag",
    monthly_limit: category?.monthly_limit ? String(Number(category.monthly_limit)) : "",
  };
}

export function CategoryFormDialog({
  open,
  onOpenChange,
  category,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  category?: Category;
}) {
  const save = useSaveCategory();
  const { register, handleSubmit, control, reset, setError, formState } = useForm<CategoryFormValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: defaults(category),
  });

  useEffect(() => {
    if (open) reset(defaults(category));
  }, [open, category, reset]);

  const isEdit = Boolean(category);
  const isSystem = Boolean(category?.is_system);

  const onSubmit = handleSubmit(async (values) => {
    try {
      await save.mutateAsync({
        id: category?.id,
        input: {
          name: values.name,
          color: values.color,
          icon: values.icon,
          monthly_limit: values.monthly_limit === "" ? null : values.monthly_limit,
        },
      });
      toast.success(isEdit ? "Category updated" : "Category created");
      onOpenChange(false);
    } catch (error) {
      applyServerErrors(error, setError, ["name", "monthly_limit", "color", "icon"]);
    }
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit category" : "New category"}</DialogTitle>
          <DialogDescription>
            Add a monthly limit to get warned at 80% and again when it&apos;s reached.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} noValidate className="grid gap-5">
          <FormField
            id="cat-name"
            label="Name"
            error={formState.errors.name?.message}
            hint={isSystem ? "The fallback category can't be renamed." : undefined}
          >
            <Input
              {...fieldAria("cat-name", formState.errors.name?.message)}
              placeholder="e.g. Groceries"
              disabled={isSystem}
              {...register("name")}
            />
          </FormField>
          <FormField
            id="cat-limit"
            label="Monthly limit"
            error={formState.errors.monthly_limit?.message}
            hint="Leave empty for no budget."
          >
            <Input
              {...fieldAria("cat-limit", formState.errors.monthly_limit?.message)}
              inputMode="decimal"
              placeholder="No limit"
              className="tabular"
              {...register("monthly_limit")}
            />
          </FormField>
          <Controller
            control={control}
            name="color"
            render={({ field }) => (
              <fieldset className="grid gap-2">
                <Label asChild>
                  <legend>Colour</legend>
                </Label>
                <div className="flex flex-wrap gap-2">
                  {CATEGORY_COLORS.map((color) => (
                    <button
                      key={color}
                      type="button"
                      aria-label={`Colour ${color}`}
                      aria-pressed={field.value === color}
                      onClick={() => field.onChange(color)}
                      className="flex size-8 items-center justify-center rounded-full outline-none ring-offset-2 ring-offset-card focus-visible:ring-2 focus-visible:ring-ring"
                      style={{ backgroundColor: color }}
                    >
                      {field.value === color ? <Check className="size-4 text-white" /> : null}
                    </button>
                  ))}
                </div>
              </fieldset>
            )}
          />
          <Controller
            control={control}
            name="icon"
            render={({ field }) => (
              <fieldset className="grid gap-2">
                <Label asChild>
                  <legend>Icon</legend>
                </Label>
                <div className="grid grid-cols-8 gap-1.5 sm:grid-cols-10">
                  {PICKABLE_ICONS.map((name) => {
                    const Icon = CATEGORY_ICONS[name];
                    if (!Icon) return null;
                    const selected = field.value === name;
                    return (
                      <button
                        key={name}
                        type="button"
                        aria-label={name.replace(/-/g, " ")}
                        aria-pressed={selected}
                        onClick={() => field.onChange(name)}
                        className={cn(
                          "flex aspect-square items-center justify-center rounded-lg border text-muted-foreground outline-none hover:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/40",
                          selected && "border-primary bg-primary/10 text-primary",
                        )}
                      >
                        <Icon className="size-4" />
                      </button>
                    );
                  })}
                </div>
              </fieldset>
            )}
          />
          <DialogFooter className="pt-1">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={formState.isSubmitting}>
              {formState.isSubmitting ? <Loader2 className="animate-spin" /> : null}
              {isEdit ? "Save changes" : "Create category"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
