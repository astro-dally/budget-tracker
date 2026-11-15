"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Sparkles } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { CategorySelect } from "@/components/shared/category-select";
import { CategoryLabel } from "@/components/shared/category-icon";
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
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { applyServerErrors } from "@/lib/form-errors";
import { todayIso } from "@/lib/month";
import { useCategories, useSaveTransaction, useSuggestion } from "@/lib/queries";
import {
  AUTO_CATEGORY,
  NO_CATEGORY,
  transactionSchema,
  type TransactionFormValues,
} from "@/lib/schemas";
import type { Transaction } from "@/lib/types";

const MATCHED_BY_LABEL = {
  keyword: "your keyword rule",
  merchant: "a known merchant",
  user_defined: "your past choice",
  default: "no rule matched",
} as const;

function defaults(transaction?: Transaction): TransactionFormValues {
  if (!transaction) {
    return { type: "expense", amount: "", description: "", occurred_on: todayIso(), category_id: AUTO_CATEGORY };
  }
  return {
    type: transaction.type,
    amount: transaction.amount,
    description: transaction.description,
    occurred_on: transaction.occurred_on,
    category_id: transaction.category_id ?? (transaction.type === "expense" ? AUTO_CATEGORY : NO_CATEGORY),
  };
}

export function TransactionFormDialog({
  open,
  onOpenChange,
  transaction,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  transaction?: Transaction;
}) {
  const categories = useCategories().data ?? [];
  const save = useSaveTransaction();
  const form = useForm<TransactionFormValues>({
    resolver: zodResolver(transactionSchema),
    defaultValues: defaults(transaction),
  });
  const { register, handleSubmit, control, watch, setValue, reset, setError, formState } = form;

  useEffect(() => {
    if (open) reset(defaults(transaction));
  }, [open, transaction, reset]);

  const type = watch("type");
  const categoryId = watch("category_id");
  const description = useDebouncedValue(watch("description"), 350);
  const suggestion = useSuggestion(description, open && type === "expense");
  const isAuto = categoryId === AUTO_CATEGORY;
  const isEdit = Boolean(transaction);

  const onSubmit = handleSubmit(async (values) => {
    const special = values.category_id === AUTO_CATEGORY || values.category_id === NO_CATEGORY;
    try {
      await save.mutateAsync({
        id: transaction?.id,
        input: {
          type: values.type,
          amount: values.amount,
          description: values.description,
          occurred_on: values.occurred_on,
          category_id: special ? null : values.category_id,
        },
      });
      toast.success(isEdit ? "Transaction updated" : "Transaction added");
      onOpenChange(false);
    } catch (error) {
      applyServerErrors(error, setError, ["amount", "description", "occurred_on", "category_id"]);
    }
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit transaction" : "Add transaction"}</DialogTitle>
          <DialogDescription>
            Leave the category on auto and we&apos;ll file expenses using your rules.
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
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField id="tx-amount" label="Amount" error={formState.errors.amount?.message}>
              <Input
                {...fieldAria("tx-amount", formState.errors.amount?.message)}
                inputMode="decimal"
                placeholder="0.00"
                className="tabular"
                autoFocus
                {...register("amount")}
              />
            </FormField>
            <FormField id="tx-date" label="Date" error={formState.errors.occurred_on?.message}>
              <Input
                {...fieldAria("tx-date", formState.errors.occurred_on?.message)}
                type="date"
                {...register("occurred_on")}
              />
            </FormField>
          </div>
          <FormField
            id="tx-description"
            label="Description"
            error={formState.errors.description?.message}
            hint={
              type === "expense" && suggestion.data ? (
                <span className="flex flex-wrap items-center gap-x-2 gap-y-1" aria-live="polite">
                  <Sparkles className="size-3.5 text-primary" aria-hidden="true" />
                  <span>{isAuto ? "Will be filed under" : "Suggested:"}</span>
                  <span className="font-medium text-foreground">
                    <CategoryLabel name={suggestion.data.category_name} color={suggestion.data.color} />
                  </span>
                  <span>({MATCHED_BY_LABEL[suggestion.data.matched_by]})</span>
                  {!isAuto && suggestion.data.category_id !== categoryId ? (
                    <button
                      type="button"
                      className="font-medium text-primary underline-offset-2 hover:underline"
                      onClick={() => setValue("category_id", suggestion.data.category_id)}
                    >
                      Use it
                    </button>
                  ) : null}
                </span>
              ) : type === "expense" ? (
                "Try “Uber to airport” or “Swiggy order”."
              ) : undefined
            }
          >
            <Input
              {...fieldAria("tx-description", formState.errors.description?.message)}
              placeholder="What was it for?"
              autoComplete="off"
              {...register("description")}
            />
          </FormField>
          <FormField id="tx-category" label="Category" error={formState.errors.category_id?.message}>
            <Controller
              control={control}
              name="category_id"
              render={({ field }) => (
                <CategorySelect
                  id="tx-category"
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
              {isEdit ? "Save changes" : "Add transaction"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
