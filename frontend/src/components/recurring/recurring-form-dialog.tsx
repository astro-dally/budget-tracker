"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { CategorySelect } from "@/components/shared/category-select";
import { fieldAria, FormField } from "@/components/shared/form-field";
import { TypeToggle } from "@/components/shared/type-toggle";
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { applyServerErrors } from "@/lib/form-errors";
import { todayIso } from "@/lib/month";
import { useCategories, useCreateRecurring } from "@/lib/queries";
import { AUTO_CATEGORY, NO_CATEGORY, recurringSchema, type RecurringFormValues } from "@/lib/schemas";

const DEFAULTS = (): RecurringFormValues => ({
  description: "",
  amount: "",
  type: "expense",
  frequency: "monthly",
  start_date: todayIso(),
  end_date: "",
  category_id: AUTO_CATEGORY,
});

export function RecurringFormDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const categories = useCategories().data ?? [];
  const create = useCreateRecurring();
  const { register, handleSubmit, control, reset, watch, setValue, setError, formState } =
    useForm<RecurringFormValues>({ resolver: zodResolver(recurringSchema), defaultValues: DEFAULTS() });

  useEffect(() => {
    if (open) reset(DEFAULTS());
  }, [open, reset]);

  const type = watch("type");

  const onSubmit = handleSubmit(async (values) => {
    const special = values.category_id === AUTO_CATEGORY || values.category_id === NO_CATEGORY;
    try {
      const created = await create.mutateAsync({
        description: values.description,
        amount: values.amount,
        type: values.type,
        frequency: values.frequency,
        start_date: values.start_date,
        end_date: values.end_date || null,
        category_id: special ? null : values.category_id,
      });
      toast.success("Recurring payment added", {
        description: created.last_generated_on
          ? "Any payments already due have been recorded."
          : undefined,
      });
      onOpenChange(false);
    } catch (error) {
      applyServerErrors(error, setError, ["description", "amount", "start_date", "end_date"]);
    }
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New recurring payment</DialogTitle>
          <DialogDescription>
            Rent, subscriptions, EMIs or salary. Each occurrence is recorded automatically on its due
            date, including ones already past.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} noValidate className="grid gap-4">
          <Controller
            control={control}
            name="type"
            render={({ field }) => (
              <TypeToggle
                value={field.value}
                onChange={(next) => {
                  field.onChange(next);
                  setValue("category_id", next === "expense" ? AUTO_CATEGORY : NO_CATEGORY);
                }}
              />
            )}
          />
          <FormField id="rec-description" label="Description" error={formState.errors.description?.message}>
            <Input
              {...fieldAria("rec-description", formState.errors.description?.message)}
              placeholder="e.g. Apartment rent"
              autoFocus
              {...register("description")}
            />
          </FormField>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField id="rec-amount" label="Amount" error={formState.errors.amount?.message}>
              <Input
                {...fieldAria("rec-amount", formState.errors.amount?.message)}
                inputMode="decimal"
                placeholder="0.00"
                className="tabular"
                {...register("amount")}
              />
            </FormField>
            <FormField id="rec-frequency" label="Repeats">
              <Controller
                control={control}
                name="frequency"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger id="rec-frequency">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="daily">Every day</SelectItem>
                      <SelectItem value="weekly">Every week</SelectItem>
                      <SelectItem value="monthly">Every month</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </FormField>
            <FormField id="rec-start" label="First payment" error={formState.errors.start_date?.message}>
              <Input
                {...fieldAria("rec-start", formState.errors.start_date?.message)}
                type="date"
                {...register("start_date")}
              />
            </FormField>
            <FormField
              id="rec-end"
              label="Ends (optional)"
              error={formState.errors.end_date?.message}
              hint="Leave empty to repeat until you stop it."
            >
              <Input
                {...fieldAria("rec-end", formState.errors.end_date?.message)}
                type="date"
                {...register("end_date")}
              />
            </FormField>
          </div>
          <FormField id="rec-category" label="Category">
            <Controller
              control={control}
              name="category_id"
              render={({ field }) => (
                <CategorySelect
                  id="rec-category"
                  value={field.value}
                  onChange={field.onChange}
                  categories={categories}
                  special={
                    type === "expense"
                      ? { value: AUTO_CATEGORY, label: "Auto-categorise" }
                      : { value: NO_CATEGORY, label: "No category" }
                  }
                />
              )}
            />
          </FormField>
          <DialogFooter className="pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={formState.isSubmitting}>
              {formState.isSubmitting ? <Loader2 className="animate-spin" /> : null}
              Add recurring payment
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
